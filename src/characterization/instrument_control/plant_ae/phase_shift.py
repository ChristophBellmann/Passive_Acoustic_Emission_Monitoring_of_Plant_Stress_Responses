"""Phase-delay analysis for synchronized two-channel plant AE captures."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy import signal


@dataclass
class DelayEstimate:
    delay_s: float
    confidence: float
    peak_value: float
    search_window_s: float


@dataclass
class PhaseBandCandidate:
    f_low_hz: float
    f_high_hz: float
    center_hz: float
    delay_s: float
    delay_std_s: float
    mean_coherence: float
    phase_span_rad: float
    bins: int
    slope_rad_per_hz: float
    intercept_rad: float


def remove_dc_and_taper(values: np.ndarray) -> np.ndarray:
    data = np.asarray(values, dtype=np.float64)
    data = signal.detrend(data, type="constant")
    if data.size > 1:
        data = data * signal.windows.hann(data.size, sym=False)
    return data


def gcc_phat_delay(
    reference: np.ndarray,
    delayed: np.ndarray,
    sample_rate_hz: float,
    *,
    max_delay_s: float = 0.001,
    interpolation: int = 8,
    min_frequency_hz: float | None = None,
    max_frequency_hz: float | None = None,
) -> DelayEstimate:
    """Estimate broadband delay between two synchronized channels.

    Positive ``delay_s`` means ``delayed`` lags ``reference``.
    """
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    x = remove_dc_and_taper(reference)
    y = remove_dc_and_taper(delayed)
    if x.shape != y.shape:
        raise ValueError("reference and delayed must have the same shape")
    if x.size < 4:
        raise ValueError("at least four samples are required")

    n = x.size + y.size
    spectrum_x = np.fft.rfft(x, n=n)
    spectrum_y = np.fft.rfft(y, n=n)
    cross = spectrum_y * np.conj(spectrum_x)
    frequencies = np.fft.rfftfreq(n, d=1.0 / sample_rate_hz)
    frequency_mask = np.ones_like(frequencies, dtype=bool)
    if min_frequency_hz is not None:
        frequency_mask &= frequencies >= float(min_frequency_hz)
    if max_frequency_hz is not None:
        frequency_mask &= frequencies <= float(max_frequency_hz)
    cross = np.where(frequency_mask, cross, 0.0)
    cross /= np.maximum(np.abs(cross), np.finfo(float).eps)

    cc = np.fft.irfft(cross, n=interpolation * n)
    max_shift = int(round(interpolation * sample_rate_hz * max_delay_s))
    max_shift = min(max_shift, cc.size // 2)
    if max_shift < 1:
        raise ValueError("max_delay_s is smaller than one interpolated sample")
    cc = np.concatenate((cc[-max_shift:], cc[: max_shift + 1]))
    shifts = np.arange(-max_shift, max_shift + 1, dtype=float)
    peak_index = int(np.argmax(np.abs(cc)))
    delay_s = shifts[peak_index] / (interpolation * sample_rate_hz)
    peak = float(np.abs(cc[peak_index]))
    confidence = peak / float(np.mean(np.abs(cc)) + np.finfo(float).eps)
    return DelayEstimate(
        delay_s=float(delay_s),
        confidence=float(confidence),
        peak_value=peak,
        search_window_s=float(max_delay_s),
    )


def _contiguous_true_regions(mask: np.ndarray) -> list[tuple[int, int]]:
    regions: list[tuple[int, int]] = []
    start: int | None = None
    for index, value in enumerate(mask):
        if value and start is None:
            start = index
        elif not value and start is not None:
            regions.append((start, index))
            start = None
    if start is not None:
        regions.append((start, len(mask)))
    return regions


def cross_spectral_phase_candidates(
    reference: np.ndarray,
    delayed: np.ndarray,
    sample_rate_hz: float,
    *,
    min_frequency_hz: float = 500.0,
    max_frequency_hz: float = 100_000.0,
    nperseg: int = 16_384,
    coherence_threshold: float = 0.65,
    min_bandwidth_hz: float = 1_000.0,
    max_abs_delay_s: float = 0.001,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[PhaseBandCandidate]]:
    """Find coherent bands whose unwrapped cross-phase implies a stable delay.

    Positive candidate ``delay_s`` means ``delayed`` lags ``reference``.
    """
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    x = remove_dc_and_taper(reference)
    y = remove_dc_and_taper(delayed)
    if x.shape != y.shape:
        raise ValueError("reference and delayed must have the same shape")

    nperseg = min(int(nperseg), x.size)
    if nperseg < 16:
        raise ValueError("nperseg is too small for phase analysis")
    noverlap = nperseg // 2
    frequencies, cross_power = signal.csd(
        x,
        y,
        fs=sample_rate_hz,
        nperseg=nperseg,
        noverlap=noverlap,
        detrend="constant",
        scaling="density",
    )
    coh_freqs, coherence = signal.coherence(
        x,
        y,
        fs=sample_rate_hz,
        nperseg=nperseg,
        noverlap=noverlap,
        detrend="constant",
    )
    if not np.allclose(frequencies, coh_freqs):
        coherence = np.interp(frequencies, coh_freqs, coherence)
    phase = np.unwrap(np.angle(cross_power))

    in_band = (frequencies >= min_frequency_hz) & (frequencies <= max_frequency_hz)
    coherent = in_band & np.isfinite(coherence) & (coherence >= coherence_threshold)
    candidates: list[PhaseBandCandidate] = []
    for start, stop in _contiguous_true_regions(coherent):
        if stop - start < 3:
            continue
        f = frequencies[start:stop]
        p = phase[start:stop]
        c = coherence[start:stop]
        if f[-1] - f[0] < min_bandwidth_hz:
            continue
        weights = np.clip(c, 0.0, 1.0)
        slope, intercept = np.polyfit(f, p, deg=1, w=weights)
        delay_s = -float(slope) / (2.0 * np.pi)
        if abs(delay_s) > max_abs_delay_s:
            continue
        per_bin_delay = -np.gradient(p, f) / (2.0 * np.pi)
        delay_std_s = float(np.std(per_bin_delay))
        candidates.append(
            PhaseBandCandidate(
                f_low_hz=float(f[0]),
                f_high_hz=float(f[-1]),
                center_hz=float(np.average(f, weights=weights)),
                delay_s=delay_s,
                delay_std_s=delay_std_s,
                mean_coherence=float(np.mean(c)),
                phase_span_rad=float(p[-1] - p[0]),
                bins=int(stop - start),
                slope_rad_per_hz=float(slope),
                intercept_rad=float(intercept),
            )
        )

    candidates.sort(
        key=lambda item: (
            item.mean_coherence * np.log1p(item.bins) / (1.0 + item.delay_std_s * 1e6)
        ),
        reverse=True,
    )
    return frequencies, coherence, phase, candidates


def candidate_to_dict(candidate: PhaseBandCandidate) -> dict[str, Any]:
    return asdict(candidate) | {
        "delay_us": candidate.delay_s * 1e6,
        "delay_std_us": candidate.delay_std_s * 1e6,
    }


def delay_to_dict(delay: DelayEstimate) -> dict[str, Any]:
    return asdict(delay) | {"delay_us": delay.delay_s * 1e6}
