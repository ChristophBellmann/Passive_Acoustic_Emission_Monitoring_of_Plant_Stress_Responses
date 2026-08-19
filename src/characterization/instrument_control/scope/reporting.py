"""Markdown report generation."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from .config import ExperimentConfig, get_git_commit
from .peak_detection import SpectralPeak
from .plausibility import PlausibilityResult
from .preprocessing import PreprocessingResult


def generate_report(
    config: ExperimentConfig,
    config_path: str,
    preprocessing_results: dict[int, PreprocessingResult],
    peaks_by_channel: dict[int, list[SpectralPeak]],
    plausibility_results: dict[int, list[PlausibilityResult]],
    plot_paths: dict[str, Path],
    output_path: Path,
    n_captures: int = 0,
    sample_rate: float = 0.0,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    commit = get_git_commit()

    lines: list[str] = []
    lines.append(f"# Vibration Characterization Report")
    lines.append(f"")
    lines.append(f"**Generated:** {timestamp}")
    lines.append(f"**Git commit:** {commit}")
    lines.append(f"**Config:** {config_path}")
    lines.append(f"**Captures:** {n_captures}")
    lines.append(f"**Sample rate:** {sample_rate:.1f} Sa/s")
    lines.append("")

    lines.append("## Experiment Metadata")
    lines.append("")
    lines.append("### Instrument")
    lines.append(f"- VISA resource: `{config.instrument.visa_resource}`")
    lines.append(f"- Expected IDN contains: {config.instrument.idn_expected_contains}")
    lines.append(f"- Timeout: {config.instrument.timeout_ms} ms")
    lines.append("")

    lines.append("### Sensor Channels")
    for ch_num, ch_cfg in config.oscilloscope.channel_settings.items():
        lines.append(f"#### CH{ch_num}: {ch_cfg.label}")
        lines.append(f"- Probe ratio: {ch_cfg.probe_ratio}:1")
        lines.append(f"- Coupling: {ch_cfg.coupling}")
        lines.append(f"- Amplitude calibrated: {ch_cfg.amplitude_calibrated}")
        lines.append(f"- Notes: {ch_cfg.notes}")
        lines.append("")

    lines.append("## Warnings and Limitations")
    lines.append("")
    lines.append("> **CH1 amplitude is not calibrated** because the LM358 gain and bias are unknown.")
    lines.append(">")
    lines.append("> **Phase 2 setup (since 2026-06-22): active channels are CH1, CH3, CH4. CH2 is disabled (hardware fault).**")
    lines.append("> See `experiment_continuous_plant_ae_20260622/HARDWARE_CHANGELOG.md` for the full setup history.")
    lines.append(">")
    lines.append("> **Frequency estimates are valid only within the acquired bandwidth and sample-rate limits.**")
    lines.append("")

    lines.append("## Time-Domain Summary")
    lines.append("")
    for ch, pre in preprocessing_results.items():
        lines.append(f"### CH{ch}")
        lines.append(f"- DC removed: {pre.dc_removed}")
        lines.append(f"- Detrended: {pre.detrended}")
        lines.append(f"- Clipping detected: {pre.is_clipped} (fraction: {pre.clipping_fraction:.4f})")
        lines.append(f"- Flatline: {pre.is_flatline}")
        lines.append(f"- NaN/Inf: {pre.has_nan_or_inf}")
        lines.append("")

    lines.append("## Spectral Summary")
    lines.append("")
    for ch, peaks in peaks_by_channel.items():
        lines.append(f"### CH{ch}")
        lines.append(f"- Peaks detected: {len(peaks)}")
        lines.append("")

    lines.append("## Detected Frequencies")
    lines.append("")
    lines.append("| Channel | Freq (Hz) | Amplitude (dB) | Prominence (dB) | BW (Hz) | Q | SNR (dB) | Mains? | Repeatable? | Label | Notes |")
    lines.append("|---------|-----------|-----------------|-----------------|---------|---|----------|--------|-------------|-------|-------|")
    for ch in sorted(peaks_by_channel.keys()):
        for p in peaks_by_channel[ch]:
            lines.append(
                f"| CH{ch} | {p.frequency_hz:.1f} | {p.amplitude_db:.1f} | "
                f"{p.prominence_db:.1f} | {p.bandwidth_hz:.1f} | {p.q_factor:.1f} | "
                f"{p.snr_db:.1f} | {'Yes' if p.is_mains_related else 'No'} | "
                f"{'Yes' if p.is_repeatable else 'No'} | {p.plausibility_label} | {p.notes} |"
            )
    lines.append("")

    lines.append("## Plausibility Assessment")
    lines.append("")
    for ch, results in plausibility_results.items():
        lines.append(f"### CH{ch}")
        for r in results:
            lines.append(f"- **{r.peak.frequency_hz:.1f} Hz** → `{r.label}`: {', '.join(r.reasons)}")
        lines.append("")

    lines.append("## Channel Comparison")
    lines.append("")
    ch1_freqs = {round(p.frequency_hz, 1) for p in peaks_by_channel.get(1, [])}
    ch2_freqs = {round(p.frequency_hz, 1) for p in peaks_by_channel.get(2, [])}
    ch3_freqs = {round(p.frequency_hz, 1) for p in peaks_by_channel.get(3, [])}
    ch4_freqs = {round(p.frequency_hz, 1) for p in peaks_by_channel.get(4, [])}
    # CH2 is disabled since 2026-06-22 — kept in dict for backward compat with Phase 1 configs
    common = ch1_freqs & ch3_freqs
    ch1_only = ch1_freqs - ch3_freqs
    ch3_only = ch3_freqs - ch1_freqs
    lines.append(f"- Common frequencies CH1∩CH3 (±10 Hz): {len(common)}")
    lines.append(f"- CH1 only: {len(ch1_only)}")
    lines.append(f"- CH3 only: {len(ch3_only)}")
    lines.append(f"- CH2 data (Phase 1 only, disabled since 2026-06-22): {len(ch2_freqs)} peaks")
    lines.append(f"- CH4 data (Phase 2 only, added 2026-06-22): {len(ch4_freqs)} peaks")
    lines.append("")

    lines.append("## Plots")
    lines.append("")
    for name, path in sorted(plot_paths.items()):
        rel = path.name
        lines.append(f"### {name}")
        lines.append(f"![{name}]({rel})")
        lines.append("")

    lines.append("## Next Recommended Measurement Settings")
    lines.append("")
    _add_recommendations(lines, preprocessing_results, peaks_by_channel, sample_rate)
    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _add_recommendations(
    lines: list[str],
    preprocessing_results: dict[int, PreprocessingResult],
    peaks_by_channel: dict[int, list[SpectralPeak]],
    sample_rate: float,
) -> None:
    for ch, pre in preprocessing_results.items():
        if pre.is_clipped:
            lines.append(f"- **CH{ch}**: Reduce vertical scale or add attenuation to avoid clipping.")
        if pre.is_flatline:
            lines.append(f"- **CH{ch}**: No signal detected. Check sensor connection and amplifier.")
    nyquist = sample_rate / 2.0 if sample_rate > 0 else 0
    for ch, peaks in peaks_by_channel.items():
        max_freq = max((p.frequency_hz for p in peaks), default=0)
        if nyquist > 0 and max_freq > nyquist * 0.8:
            lines.append(f"- **CH{ch}**: Highest peak near Nyquist. Consider increasing sample rate.")
    lines.append("- Consider acquiring baseline (no excitation) for noise floor comparison.")
    lines.append("- Consider controlled excitation (tap, rub) on each sensor separately.")
