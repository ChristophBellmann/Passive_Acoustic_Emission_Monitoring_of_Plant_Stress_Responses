"""Peak detection in spectral data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np
from scipy import signal as sp_signal

from .spectral import WelchResult, amplitude_to_db


@dataclass
class SpectralPeak:
    frequency_hz: float
    amplitude: float
    amplitude_db: float
    prominence_db: float
    bandwidth_hz: float = 0.0
    q_factor: float = 0.0
    snr_db: float = 0.0
    is_mains_related: bool = False
    is_repeatable: bool = False
    plausibility_label: str = "uncertain"
    notes: str = ""
    channel: int = 0
    capture_id: int = 0


def detect_peaks_in_welch(
    welch: WelchResult,
    prominence_db: float = 8.0,
    min_distance_hz: float = 20.0,
    max_peaks: int = 20,
    ignore_bands_hz: Optional[list[list[float]]] = None,
    channel: int = 0,
    capture_id: int = 0,
) -> list[SpectralPeak]:
    if len(welch.frequencies) == 0 or len(welch.psd) == 0:
        return []

    psd_db = amplitude_to_db(np.sqrt(welch.psd))

    if min_distance_hz > 0 and len(welch.frequencies) > 1:
        freq_resolution = welch.frequencies[1] - welch.frequencies[0]
        distance_samples = max(1, int(min_distance_hz / freq_resolution))
    else:
        distance_samples = 1

    peaks_idx, properties = sp_signal.find_peaks(
        psd_db,
        prominence=prominence_db,
        distance=distance_samples,
    )

    if len(peaks_idx) == 0:
        return []

    sorted_order = np.argsort(properties["prominences"])[::-1]
    peaks_idx = peaks_idx[sorted_order]
    proms = properties["prominences"][sorted_order]

    if max_peaks > 0:
        peaks_idx = peaks_idx[:max_peaks]
        proms = proms[:max_peaks]

    noise_floor = np.median(psd_db)
    peaks: list[SpectralPeak] = []
    for idx, prom in zip(peaks_idx, proms):
        freq = float(welch.frequencies[idx])
        amp = float(np.sqrt(welch.psd[idx]))
        amp_db = float(psd_db[idx])
        snr = amp_db - noise_floor

        bw = _estimate_bandwidth(psd_db, idx, prom)
        q = freq / bw if bw > 0 else 0.0

        is_mains = _is_in_ignore_bands(freq, ignore_bands_hz)
        if is_mains:
            continue

        peaks.append(SpectralPeak(
            frequency_hz=freq,
            amplitude=amp,
            amplitude_db=amp_db,
            prominence_db=float(prom),
            bandwidth_hz=bw,
            q_factor=q,
            snr_db=snr,
            is_mains_related=is_mains,
            channel=channel,
            capture_id=capture_id,
        ))

    return peaks


def _estimate_bandwidth(
    spectrum_db: np.ndarray, peak_idx: int, prominence: float
) -> float:
    threshold = spectrum_db[peak_idx] - prominence
    left = peak_idx
    while left > 0 and spectrum_db[left] > threshold:
        left -= 1
    right = peak_idx
    while right < len(spectrum_db) - 1 and spectrum_db[right] > threshold:
        right += 1
    return float(right - left)


def _is_in_ignore_bands(
    freq: float, bands: Optional[list[list[float]]]
) -> bool:
    if bands is None:
        return False
    for lo, hi in bands:
        if lo <= freq <= hi:
            return True
    return False


def assess_repeatability(
    all_peaks: list[list[SpectralPeak]],
    freq_tolerance_hz: float = 5.0,
    min_fraction: float = 0.4,
) -> dict[float, bool]:
    if not all_peaks:
        return {}
    all_freqs: list[float] = []
    for capture_peaks in all_peaks:
        for p in capture_peaks:
            all_freqs.append(p.frequency_hz)
    if not all_freqs:
        return {}
    all_freqs.sort()
    clusters: list[list[float]] = []
    current_cluster = [all_freqs[0]]
    for f in all_freqs[1:]:
        if f - current_cluster[-1] <= freq_tolerance_hz:
            current_cluster.append(f)
        else:
            clusters.append(current_cluster)
            current_cluster = [f]
    clusters.append(current_cluster)

    n_captures = len(all_peaks)
    result: dict[float, bool] = {}
    for cluster in clusters:
        representative = float(np.mean(cluster))
        fraction = len(cluster) / n_captures
        result[representative] = fraction >= min_fraction
    return result
