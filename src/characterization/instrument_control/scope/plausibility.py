"""Plausibility checks for detected spectral peaks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .config import ExperimentConfig
from .peak_detection import SpectralPeak
from .preprocessing import PreprocessingResult


@dataclass
class PlausibilityResult:
    peak: SpectralPeak
    label: str
    reasons: list[str]


def run_plausibility_checks(
    peaks: list[SpectralPeak],
    preprocessing_results: dict[int, PreprocessingResult],
    sample_rate: float,
    config: ExperimentConfig,
    channel_peaks_by_ch: Optional[dict[int, list[SpectralPeak]]] = None,
) -> list[PlausibilityResult]:
    results: list[PlausibilityResult] = []
    for peak in peaks:
        label, reasons = _classify_peak(
            peak,
            preprocessing_results,
            sample_rate,
            config,
            channel_peaks_by_ch,
        )
        peak.plausibility_label = label
        peak.notes = "; ".join(reasons)
        results.append(PlausibilityResult(peak=peak, label=label, reasons=reasons))
    return results


def _classify_peak(
    peak: SpectralPeak,
    preprocessing_results: dict[int, PreprocessingResult],
    sample_rate: float,
    config: ExperimentConfig,
    channel_peaks_by_ch: Optional[dict[int, list[SpectralPeak]]],
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    plaus = config.plausibility

    ch = peak.channel
    pre = preprocessing_results.get(ch)
    if pre and pre.is_clipped:
        reasons.append("signal_clipped")

    if pre and pre.is_flatline:
        return "likely_clipping_artifact", ["flatline_detected"]

    if peak.is_mains_related:
        reasons.append("near_mains_frequency")
        return "likely_mains_noise", reasons

    if plaus.aliasing_check and sample_rate > 0:
        nyquist = sample_rate / 2.0
        if peak.frequency_hz > nyquist * 0.9:
            reasons.append("near_nyquist_frequency")
            return "likely_electronic_artifact", reasons

    if (
        plaus.switching_noise_check
        and ch == 1
        and channel_peaks_by_ch is not None
    ):
        ch2_peaks = channel_peaks_by_ch.get(2, [])
        ch2_freqs = [p.frequency_hz for p in ch2_peaks]
        tol = 10.0
        if not any(abs(f - peak.frequency_hz) < tol for f in ch2_freqs):
            if peak.frequency_hz > 1000 and peak.q_factor > 50:
                reasons.append("ch1_only_narrow_high_freq")
                return "likely_switching_noise", reasons

    if peak.is_repeatable:
        reasons.append("repeatable_across_captures")

    if channel_peaks_by_ch is not None:
        other_ch = 2 if ch == 1 else 1
        other_peaks = channel_peaks_by_ch.get(other_ch, [])
        tol = 10.0
        if any(abs(p.frequency_hz - peak.frequency_hz) < tol for p in other_peaks):
            reasons.append("present_on_both_channels")
            return "plausible_mechanical", reasons

    if peak.is_repeatable and peak.snr_db >= plaus.min_snr_db:
        reasons.append("repeatable_and_good_snr")
        return "possible_mechanical", reasons

    if not reasons:
        reasons.append("no_specific_concern")

    return "uncertain", reasons
