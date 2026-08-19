#!/usr/bin/env python3
"""
Frequency characterization of plant acoustic emissions.

Validates each spectral peak against independent criteria before reporting it:

  1. Repeatability – peak present in ≥40 % of all captures of one channel.
  2. Cross-channel coherence – same frequency (within ±1 kHz) on ≥ 2 channels,
     ruling out sensor-specific artefacts.
  3. Minimum SNR above the per-channel median noise floor.

Peaks coinciding with a dominant resonance of the sensor chain's free-decay
impulse response (--impulse-dir) are flagged as sensor resonances — a property
of the piezo, not a plant emission.

All measurement parameters (sample rate, window length, frequency resolution)
are taken from the data, not hard-coded, and stated per run in the report.

Usage
-----
  python frequency_analysis.py [--data-dir DIR] [--out-dir DIR] [--impulse-dir DIR]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import signal as sp_signal

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_DIR = (
    SCRIPT_DIR / "data" / "plant_ae_optimized" / "20260621_200339" / "raw"
)
DEFAULT_OUT_DIR = SCRIPT_DIR / "data" / "reports" / "frequency_analysis"
IMPULSE_RAW_DIR = SCRIPT_DIR / "data" / "impulse_response" / "20260621_182730" / "raw"

CHANNELS = (1, 2, 3)
MAX_FREQUENCY_HZ = 100_000.0
MAINS_BANDS_HZ = [(48, 52), (98, 102), (148, 152), (198, 202)]

# Repeatability: a peak must appear in at least this fraction of captures.
REPEAT_MIN_FRACTION = 0.40
# Two channels agree if their peaks are within this tolerance.
CROSS_CH_TOLERANCE_HZ = 1_000.0
# Peak detection: minimum dB prominence relative to the noise floor.
PROMINENCE_DB = 6.0
MIN_DISTANCE_HZ = 500.0
MAX_PEAKS = 40
# Minimum SNR (dB above per-channel median noise floor) for accepted peaks.
# Peaks below this threshold pass repeatability and coherence by chance.
MIN_SNR_DB = 5.0


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_npz_capture(path: Path) -> tuple[np.ndarray, float]:
    """
    Return (voltage, sample_rate_hz) from any project capture NPZ format.

    Supports:
    - new long-capture / decimated format: ``voltage`` + ``sample_rate``
    - notebook-03 format:  ``voltage_vector`` + ``metadata`` dict
    - old screen-buffer:   ``voltage_vector`` + ``time_vector`` (rate from ratio)
    """
    data = np.load(path, allow_pickle=True)
    keys = set(data.keys())

    if "voltage" in keys and "sample_rate" in keys:
        return np.asarray(data["voltage"], dtype=float), float(data["sample_rate"])

    if "voltage_vector" in keys:
        voltage = np.asarray(data["voltage_vector"], dtype=float)
        if "metadata" in keys:
            meta = data["metadata"].item()
            rate = float(meta.get("sample_rate_sa_per_s", 0))
            if rate > 0:
                return voltage, rate
        if "time_vector" in keys:
            t = np.asarray(data["time_vector"], dtype=float)
            if len(t) >= 2 and len(voltage) >= 2:
                rate = len(voltage) / (t[-1] - t[0])
                return voltage, rate

    raise KeyError(f"Cannot determine voltage/sample-rate from keys: {sorted(keys)}")


def load_channel_captures(
    raw_dir: Path,
    channel: int,
    expected_samples: int | None = None,
    expected_rate: float | None = None,
) -> list[np.ndarray]:
    """
    Load all valid captures for *channel* from *raw_dir*.

    If *expected_samples* or *expected_rate* are None, they are inferred from
    the first successfully loaded file and all subsequent files are checked for
    consistency.  This makes the function work with both the old 25 MSa/s /
    100k-point captures and the new 500 kSa/s long captures.
    """
    # Accept both *_ch{N}.npz (long capture) and *_capture_ch{N}.npz (notebook)
    paths = sorted(set(raw_dir.glob(f"*_ch{channel}.npz")) |
                   set(raw_dir.glob(f"*_capture_ch{channel}.npz")))
    captures = []
    ref_samples: int | None = expected_samples
    ref_rate: float | None = expected_rate

    for path in paths:
        try:
            v, rate = load_npz_capture(path)
        except Exception as exc:
            print(f"  [skip] {path.name}: {exc}", file=sys.stderr)
            continue
        if len(v) < 10:
            print(f"  [skip] {path.name}: only {len(v)} samples", file=sys.stderr)
            continue
        # Establish reference from first valid file
        if ref_samples is None:
            ref_samples = len(v)
        if ref_rate is None:
            ref_rate = rate
        # Consistency check
        if len(v) != ref_samples:
            print(f"  [skip] {path.name}: {len(v)} samples (expected {ref_samples})",
                  file=sys.stderr)
            continue
        if abs(rate - ref_rate) / ref_rate > 0.05:
            print(f"  [skip] {path.name}: {rate:.0f} Hz (expected ~{ref_rate:.0f} Hz)",
                  file=sys.stderr)
            continue
        captures.append(v)
    return captures


# ---------------------------------------------------------------------------
# Spectral estimation
# ---------------------------------------------------------------------------

def compute_psd(voltage: np.ndarray, sample_rate: float) -> tuple[np.ndarray, np.ndarray]:
    """Periodogram PSD (single Hann-windowed segment) in V²/Hz."""
    cleaned = sp_signal.detrend(voltage, type="linear")
    freqs, psd = sp_signal.periodogram(
        cleaned, fs=sample_rate, window="hann", scaling="density"
    )
    return freqs, psd


def average_psd(
    captures: list[np.ndarray], sample_rate: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Return (frequencies, mean_psd, std_psd) across all captures.

    All captures must have the same length and sample rate.
    """
    psds = np.array([compute_psd(v, sample_rate)[1] for v in captures])
    freqs, _ = compute_psd(captures[0], sample_rate)
    return freqs, psds.mean(axis=0), psds.std(axis=0)


# ---------------------------------------------------------------------------
# Peak detection with quadratic sub-bin interpolation
# ---------------------------------------------------------------------------

def _quadratic_peak_freq(freqs: np.ndarray, values_db: np.ndarray, idx: int) -> float:
    if idx <= 0 or idx >= len(values_db) - 1:
        return float(freqs[idx])
    left, centre, right = values_db[idx - 1 : idx + 2]
    denom = left - 2 * centre + right
    if denom == 0:
        return float(freqs[idx])
    offset = np.clip(0.5 * (left - right) / denom, -0.5, 0.5)
    return float(freqs[idx] + offset * (freqs[1] - freqs[0]))


def _is_mains(freq: float) -> bool:
    return any(lo <= freq <= hi for lo, hi in MAINS_BANDS_HZ)


def detect_peaks(
    freqs: np.ndarray,
    psd: np.ndarray,
    prominence_db: float = PROMINENCE_DB,
    min_distance_hz: float = MIN_DISTANCE_HZ,
    max_peaks: int = MAX_PEAKS,
) -> list[dict]:
    mask = (freqs >= 20.0) & (freqs <= MAX_FREQUENCY_HZ)
    f = freqs[mask]
    psd_db = 10 * np.log10(np.maximum(psd[mask], 1e-30))
    resolution = f[1] - f[0] if len(f) > 1 else 1.0
    idxs, props = sp_signal.find_peaks(
        psd_db,
        prominence=prominence_db,
        distance=max(1, int(round(min_distance_hz / resolution))),
    )
    order = np.argsort(props["prominences"])[::-1][:max_peaks]
    peaks = []
    noise_floor = float(np.median(psd_db))
    for rank, oi in enumerate(order):
        i = int(idxs[oi])
        freq = _quadratic_peak_freq(f, psd_db, i)
        peaks.append(
            {
                "rank": rank + 1,
                "frequency_hz": freq,
                "psd_db": float(psd_db[i]),
                "prominence_db": float(props["prominences"][oi]),
                "snr_db": float(psd_db[i]) - noise_floor,
                "is_mains": _is_mains(freq),
            }
        )
    return peaks


# ---------------------------------------------------------------------------
# Repeatability check
# ---------------------------------------------------------------------------

def check_repeatability(
    captures: list[np.ndarray],
    sample_rate: float,
    freq_tolerance_hz: float = 1_000.0,
    min_fraction: float = REPEAT_MIN_FRACTION,
) -> dict[float, dict]:
    """
    For each individual capture compute peaks.  Cluster peaks across captures.
    Return mapping {centroid_hz: {'fraction': float, 'repeatable': bool, ...}}.

    *fraction* = (number of captures that contribute at least one peak to the
    cluster) / (total number of captures).  Each capture is counted at most
    once per cluster, regardless of how many of its peaks fall into it.
    """
    per_capture_peaks: list[list[tuple[float, float]]] = []
    for cap_idx, v in enumerate(captures):
        f, psd = compute_psd(v, sample_rate)
        peaks = detect_peaks(f, psd)
        per_capture_peaks.append(
            [(p["frequency_hz"], p["prominence_db"]) for p in peaks if not p["is_mains"]]
        )

    # Flat list of (freq, prominence, capture_index)
    all_fpc: list[tuple[float, float, int]] = []
    for cap_idx, cap_peaks in enumerate(per_capture_peaks):
        for freq, prom in cap_peaks:
            all_fpc.append((freq, prom, cap_idx))

    if not all_fpc:
        return {}

    # Fixed-bin grouping: round each peak to the nearest bin of width
    # freq_tolerance_hz.  This avoids the chain-link artefact where many
    # closely-spaced peaks from different captures merge into one giant cluster.
    bin_size = freq_tolerance_hz
    bins: dict[int, list[tuple[float, float, int]]] = {}
    for freq, prom, cap_idx in all_fpc:
        key = int(round(freq / bin_size))
        bins.setdefault(key, []).append((freq, prom, cap_idx))

    n = len(captures)
    result: dict[float, dict] = {}
    for _key, members in bins.items():
        centroid = float(np.mean([c[0] for c in members]))
        mean_prom = float(np.mean([c[1] for c in members]))
        # Count unique captures that have ≥1 peak in this bin
        unique_caps = len({c[2] for c in members})
        fraction = unique_caps / n
        result[centroid] = {
            "fraction": fraction,
            "repeatable": fraction >= min_fraction,
            "mean_prominence_db": mean_prom,
            "n_unique_captures": unique_caps,
            "n_observations": len(members),
            "n_captures": n,
        }
    return result


# ---------------------------------------------------------------------------
# Impulse response (sensor resonance) spectrum
# ---------------------------------------------------------------------------

def load_impulse_spectra(impulse_raw_dir: Path) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Average PSD across all impulse-response captures (ch2, direct piezo).

    The impulse captures use the oscilloscope screen buffer: 1200 voltage
    samples representing the full acquisition window (determined from the
    time_vector length and its endpoints).  The effective sample rate is
    derived from the time vector, NOT from the metadata sample_rate field
    (which reflects deep-memory rate, not the screen sub-sampled rate).

    Returns (frequencies, mean_psd_db) or None if no data.
    """
    ch2_files = sorted(impulse_raw_dir.glob("*_capture_ch2.npz"))
    if not ch2_files:
        return None

    psds: list[np.ndarray] = []
    freqs_ref: np.ndarray | None = None
    for path in ch2_files:
        try:
            data = np.load(path, allow_pickle=True)
            voltage = np.asarray(data["voltage_vector"], dtype=float)
            time_vec = np.asarray(data["time_vector"], dtype=float)
            if len(voltage) < 10:
                continue
            # Effective rate from the actual time window the 1200 points span
            duration = float(time_vec[-1] - time_vec[0])
            effective_rate = len(voltage) / duration
            f, psd = compute_psd(voltage, effective_rate)
            if freqs_ref is None:
                freqs_ref = f
            if len(f) != len(freqs_ref):
                psd = np.interp(freqs_ref, f, psd)
            psds.append(psd)
        except Exception:
            continue

    if not psds or freqs_ref is None:
        return None

    mean_psd = np.mean(psds, axis=0)
    psd_db = 10 * np.log10(np.maximum(mean_psd, 1e-30))
    return freqs_ref, psd_db


def find_impulse_peaks(impulse_freqs: np.ndarray, psd_db: np.ndarray) -> list[float]:
    """
    Detect dominant peaks in the impulse response (sensor resonances).

    *psd_db* is already in dB re 1 V²/Hz (as returned by load_impulse_spectra).
    Convert to linear V²/Hz before passing to detect_peaks, which works in
    linear PSD and converts internally.
    """
    psd_linear = 10.0 ** (psd_db / 10.0)
    peaks = detect_peaks(impulse_freqs, psd_linear, prominence_db=8.0)
    return [p["frequency_hz"] for p in peaks if not p["is_mains"]]


def is_sensor_resonance(
    freq_hz: float,
    resonances: list[float],
    tolerance_hz: float = 1_000.0,
) -> bool:
    return any(abs(freq_hz - r) <= tolerance_hz for r in resonances)


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------

CHANNEL_COLORS = {1: "#00cc44", 3: "#00aaff", 4: "#ff8844"}
CHANNEL_LABELS = {
    1: "CH1 (LM358 amplified, 820 kΩ, 10:1 probe, EM reference)",
    3: "CH3 (amplified, 820 kΩ, 10:1 probe, soil near plant)",
    4: "CH4 (amplified, 820 kΩ, 10:1 probe, stainless-steel rod next to plant)",
}
# CH2 disabled: hardware defect, replaced by CH4 (see plant_ae.watering.CHANNELS)


def plot_per_channel_overlay(
    channels_data: dict[int, dict],
    out_path: Path,
) -> None:
    """
    Three-panel figure: one subplot per channel.
    Shows individual-capture PSDs (thin, semi-transparent) and the mean PSD.
    Vertical lines for repeatable peaks that are NOT mains-related.
    """
    fig, axes = plt.subplots(3, 1, figsize=(14, 12), sharex=True)
    fig.suptitle(
        "Per-capture PSD overlay\n"
        "(grey: individual captures; colour: mean; dashed red: repeatable peaks)",
        fontsize=13,
        fontweight="bold",
    )

    for ax, ch in zip(axes, CHANNELS):
        d = channels_data[ch]
        freqs = d["freqs"] / 1e3
        captures = d["captures"]
        mean_psd = d["mean_psd"]
        color = CHANNEL_COLORS[ch]

        # Individual captures
        for v in captures:
            f, psd = compute_psd(v, d["sample_rate_hz"])
            psd_db = 10 * np.log10(np.maximum(psd, 1e-30))
            mask = (f >= 20) & (f <= MAX_FREQUENCY_HZ)
            ax.plot(
                f[mask] / 1e3,
                psd_db[mask],
                color="0.6",
                linewidth=0.5,
                alpha=0.4,
            )

        # Mean PSD
        mean_db = 10 * np.log10(np.maximum(mean_psd, 1e-30))
        mask = (d["freqs"] >= 20) & (d["freqs"] <= MAX_FREQUENCY_HZ)
        ax.plot(
            freqs[mask],
            mean_db[mask],
            color=color,
            linewidth=1.6,
            label=f"{CHANNEL_LABELS[ch]} (n={len(captures)})",
        )

        # Repeatable peaks
        for freq, info in d["repeatability"].items():
            if info["repeatable"] and not _is_mains(freq):
                ax.axvline(
                    freq / 1e3,
                    color="red",
                    linestyle="--",
                    linewidth=0.9,
                    alpha=0.75,
                )
                ax.text(
                    freq / 1e3,
                    ax.get_ylim()[1] if ax.get_ylim()[1] != 0 else -50,
                    f" {freq/1e3:.1f} kHz",
                    fontsize=7,
                    color="red",
                    rotation=90,
                    va="top",
                )

        ax.set_ylabel("PSD (dB re 1 V²/Hz)")
        ax.set_ylim(bottom=-160)
        ax.legend(loc="upper right", fontsize=9)
        ax.grid(True, alpha=0.25)

    axes[-1].set_xlabel("Frequency (kHz)")
    axes[-1].set_xlim(0, MAX_FREQUENCY_HZ / 1e3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_summary(
    channels_data: dict[int, dict],
    validated_peaks: list[dict],
    impulse_result: tuple[np.ndarray, np.ndarray] | None,
    out_path: Path,
) -> None:
    """
    Four-panel summary figure:
      (a) Mean PSD all channels, with validated peaks highlighted
      (b) Impulse-response spectrum (sensor resonance baseline)
      (c) Scatter: peak frequency vs. repeatability fraction coloured by channel
      (d) Bar chart: validated peak frequencies sorted by SNR
    """
    fig = plt.figure(figsize=(16, 13))
    gs = gridspec.GridSpec(2, 2, hspace=0.38, wspace=0.35)

    # --- (a) Mean PSD overlay ---
    ax_psd = fig.add_subplot(gs[0, 0])
    for ch in CHANNELS:
        d = channels_data[ch]
        mask = (d["freqs"] >= 20) & (d["freqs"] <= MAX_FREQUENCY_HZ)
        mean_db = 10 * np.log10(np.maximum(d["mean_psd"], 1e-30))
        ax_psd.plot(
            d["freqs"][mask] / 1e3,
            mean_db[mask],
            color=CHANNEL_COLORS[ch],
            linewidth=1.2,
            label=CHANNEL_LABELS[ch],
        )
    for vp in validated_peaks:
        ax_psd.axvline(
            vp["frequency_hz"] / 1e3,
            color="red",
            linewidth=1.0,
            alpha=0.6,
            linestyle=":",
        )
    ax_psd.set_xlabel("Frequency (kHz)")
    ax_psd.set_ylabel("Mean PSD (dB re 1 V²/Hz)")
    ax_psd.set_title("(a) Mean PSD — all channels")
    ax_psd.legend(fontsize=8)
    ax_psd.set_xlim(0, MAX_FREQUENCY_HZ / 1e3)
    ax_psd.grid(True, alpha=0.25)

    # --- (b) Impulse response spectrum ---
    ax_imp = fig.add_subplot(gs[0, 1])
    if impulse_result is not None:
        imp_f, imp_db = impulse_result
        mask = (imp_f >= 20) & (imp_f <= MAX_FREQUENCY_HZ)
        ax_imp.plot(imp_f[mask] / 1e3, imp_db[mask], color="#ff8800", linewidth=1.2)
        ax_imp.set_xlabel("Frequency (kHz)")
        ax_imp.set_ylabel("PSD (dB re 1 V²/Hz)")
        ax_imp.set_title("(b) Sensor impulse response\n(peaks = sensor resonances)")
        ax_imp.set_xlim(0, MAX_FREQUENCY_HZ / 1e3)
        ax_imp.grid(True, alpha=0.25)
    else:
        ax_imp.text(0.5, 0.5, "No impulse response data", ha="center", va="center")
        ax_imp.set_title("(b) Sensor impulse response")

    # --- (c) Repeatability vs. frequency scatter ---
    ax_rep = fig.add_subplot(gs[1, 0])
    for ch in CHANNELS:
        d = channels_data[ch]
        rp = d["repeatability"]
        freqs = [f / 1e3 for f in rp]
        fracs = [info["fraction"] for info in rp.values()]
        is_rep = [info["repeatable"] for info in rp.values()]
        ax_rep.scatter(
            freqs,
            fracs,
            c=[CHANNEL_COLORS[ch]] * len(freqs),
            marker="o" if ch == 1 else "s" if ch == 2 else "^",
            s=30,
            alpha=0.7,
            label=f"CH{ch}",
        )
    ax_rep.axhline(
        REPEAT_MIN_FRACTION,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Threshold ({REPEAT_MIN_FRACTION:.0%})",
    )
    ax_rep.set_xlabel("Frequency (kHz)")
    ax_rep.set_ylabel("Repeatability fraction")
    ax_rep.set_title("(c) Peak repeatability across captures")
    ax_rep.set_xlim(0, MAX_FREQUENCY_HZ / 1e3)
    ax_rep.set_ylim(0, 1.05)
    ax_rep.legend(fontsize=8)
    ax_rep.grid(True, alpha=0.25)

    # --- (d) Validated peaks bar chart ---
    ax_bar = fig.add_subplot(gs[1, 1])
    if validated_peaks:
        vp_sorted = sorted(validated_peaks, key=lambda x: x["snr_db"], reverse=True)[
            :15
        ]
        labels = [f"{p['frequency_hz']/1e3:.2f} kHz" for p in vp_sorted]
        snrs = [p["snr_db"] for p in vp_sorted]
        colors = ["#cc2200" if p.get("is_sensor_resonance") else "#2266cc" for p in vp_sorted]
        y = np.arange(len(labels))
        ax_bar.barh(y, snrs, color=colors, alpha=0.8)
        ax_bar.set_yticks(y)
        ax_bar.set_yticklabels(labels, fontsize=8)
        ax_bar.set_xlabel("SNR (dB above median noise floor)")
        ax_bar.set_title(
            "(d) Validated peaks by SNR\n(blue = accepted, red = sensor resonance)"
        )
        ax_bar.grid(True, axis="x", alpha=0.25)
    else:
        ax_bar.text(0.5, 0.5, "No validated peaks found", ha="center", va="center")
        ax_bar.set_title("(d) Validated peaks")

    fig.suptitle(
        "Plant AE frequency characterization\n"
        f"Criteria: repeatability ≥{REPEAT_MIN_FRACTION:.0%}, "
        f"cross-channel coherence, SNR ≥{MIN_SNR_DB:.0f} dB",
        fontsize=12,
        fontweight="bold",
    )
    fig.savefig(out_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def write_report(
    channels_data: dict[int, dict],
    validated_peaks: list[dict],
    sensor_resonances: list[float],
    out_path: Path,
    meta: dict,
) -> None:
    """Write a Markdown report. All measurement parameters come from *meta*
    (derived from the actual data), never hard-coded."""
    rate = meta["sample_rate_hz"]
    n = meta["n_samples"]
    n_caps = meta["n_captures"]
    freq_res = rate / n
    window_s = n / rate

    def rate_str(r: float) -> str:
        return f"{r/1e6:.2f} MSa/s" if r >= 1e6 else f"{r/1e3:.0f} kSa/s"

    lines: list[str] = []

    def h(title: str, level: int = 2) -> None:
        lines.append("\n" + "#" * level + " " + title + "\n")

    h("Plant Acoustic Emission Frequency Characterization", 1)
    lines.append(f"**Analysis date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ")
    lines.append(f"**Raw data:** `{meta['data_dir']}`  ")
    lines.append(f"**Impulse reference:** `{meta['impulse_dir']}`  ")
    lines.append(f"**Script:** `{Path(__file__).name}`\n")

    h("Data and Method")
    lines.append(
        "Active channels: CH1 (piezo + LM358 amplifier + 820 kΩ, 10:1 probe, uncalibrated gain), "
        "CH3 (piezo + amplifier + 820 kΩ, 10:1 probe, soil near plant), "
        "CH4 (piezo + amplifier + 820 kΩ, 10:1 probe, stainless-steel rod next to plant).  \n"
        "**CH2 disabled (hardware fault); replaced by CH4.** Earlier sessions used CH1+CH2+CH3.  \n"
        f"Captures per channel: {n_caps}  \n"
        f"Sample rate: {rate_str(rate)} (Nyquist {rate/2/1e3:.0f} kHz)  \n"
        f"Capture window: {window_s*1e3:.0f} ms  \n"
        f"**Frequency resolution: {freq_res:.2f} Hz** (periodogram bin spacing)  \n"
        f"Analysis bandwidth: 20 Hz – {MAX_FREQUENCY_HZ/1e3:.0f} kHz  \n"
    )
    lines.append(
        "\nA spectral peak is accepted as a candidate only if it meets ALL of:\n"
        f"1. **Repeatability** ≥ {REPEAT_MIN_FRACTION:.0%} of captures per channel.\n"
        f"2. **Cross-channel coherence**: present within ±{CROSS_CH_TOLERANCE_HZ/1e3:.1f} kHz "
        "on ≥ 2 channels.\n"
        f"3. **Minimum SNR** ≥ {MIN_SNR_DB:.0f} dB above the per-channel median noise floor.\n"
        "Peaks coinciding with a dominant resonance of the sensor chain's free-decay "
        "impulse response are additionally **flagged as sensor resonances** — a property "
        "of the piezo, not a plant emission.\n"
    )

    h("Sensor Resonances (from impulse response)")
    if sensor_resonances:
        lines.append(
            "Dominant peaks in the free-decay spectrum of the sensor chain "
            f"(±{CROSS_CH_TOLERANCE_HZ/1e3:.1f} kHz tolerance used for exclusion):\n"
        )
        for r in sorted(sensor_resonances):
            lines.append(f"- {r/1e3:.2f} kHz")
    else:
        lines.append("- Impulse response data unavailable or no peaks detected.")
    lines.append("")

    h("Repeatability Summary per Channel")
    for ch in CHANNELS:
        if ch not in channels_data:
            continue
        d = channels_data[ch]
        rep = d["repeatability"]
        rep_non_mains = {f: i for f, i in rep.items() if i["repeatable"] and not _is_mains(f)}
        lines.append(f"\n**{CHANNEL_LABELS[ch]}**  \n"
                     f"Repeatable peaks (≥{REPEAT_MIN_FRACTION:.0%}, excl. mains): {len(rep_non_mains)}")
        if rep_non_mains:
            top = sorted(rep_non_mains.items(), key=lambda x: x[1]["mean_prominence_db"], reverse=True)[:8]
            lines.append("| Frequency (kHz) | Repeatability | Mean Prominence (dB) |")
            lines.append("|---|---|---|")
            for freq, info in top:
                lines.append(
                    f"| {freq/1e3:.2f} | {info['fraction']:.0%} "
                    f"| {info['mean_prominence_db']:.1f} |"
                )

    candidates = [p for p in validated_peaks if not p["is_sensor_resonance"]]
    resonant = [p for p in validated_peaks if p["is_sensor_resonance"]]

    all_channel = [p for p in candidates if len(p["channels"]) >= 3]

    h("Key Findings")
    lines.append(
        f"Across {n_caps} captures per channel, **{len(candidates)} peak(s)** met all "
        f"criteria without matching a known sensor resonance, and **{len(resonant)} peak(s)** "
        "met the criteria but coincide with a sensor resonance.\n"
    )
    if candidates:
        lines.append(
            "\n**None of these peaks can be attributed to the plant from this passive "
            "measurement.** Two reasons:\n\n"
            "1. *Cross-channel agreement is ambiguous in a passive baseline.* The coherence "
            "criterion rules out sensor-*specific* artefacts, but a tone shared by several "
            "channels is equally the signature of common-mode pickup (mains-adjacent, "
            "switching-supply, or environmental vibration) conducted into every channel.\n"
            "2. *The peaks have the wrong morphology for cavitation.* They are sharp, "
            f"persistent tones reproduced at up to 100 % across {n_caps} captures spanning "
            "minutes — the opposite of the sparse, broadband, transient bursts expected from "
            "xylem-cavitation acoustic emission.\n\n"
            "The parsimonious interpretation is that these peaks characterise the "
            "**measurement chain plus environment**, not plant emission. They are listed "
            "below as reproducible spectral features — useful as a reference floor to subtract "
            "in a later excitation contrast.\n"
        )
        lines.append("\n**Reproducible cross-channel peaks** (passed all criteria; not attributed to the plant):\n")
        for p in sorted(candidates, key=lambda x: x["snr_db"], reverse=True):
            ch_str = "+".join(f"CH{c}" for c in sorted(p["channels"]))
            lines.append(
                f"- {p['frequency_hz']/1e3:.2f} kHz — SNR {p['snr_db']:.1f} dB, "
                f"repeatability {p['repeatability_fraction']:.0%}, {ch_str}"
            )
        four_k = [p for p in all_channel if 4.0e3 <= p["frequency_hz"] <= 4.4e3]
        if four_k:
            f4 = four_k[0]["frequency_hz"] / 1e3
            lines.append(
                f"\n**Update to the prior characterisation:** the {f4:.2f} kHz peak now appears "
                "on all three channels at 100 % repeatability. The previous session reported a "
                "“4.3 kHz plant-AE candidate” visible only on CH1+CH3 (absent on CH2) "
                "and already flagged as a possible CH1–CH3 ground loop. Its presence on "
                "three electrically distinct channels strengthens a common-mode origin and "
                "**supersedes the earlier tentative plant-AE attribution**.\n"
            )
    else:
        lines.append(
            "\n**No non-resonance peak met all criteria** — an expected null result for a "
            "passive baseline, where the dominant reproducible spectral content is mains "
            "interference, sensor resonances, and amplifier noise.\n"
        )
    if resonant:
        lines.append("\n**Sensor resonances present in the signal** (excluded from the list above):\n")
        for p in sorted(resonant, key=lambda x: x["snr_db"], reverse=True):
            ch_str = "+".join(f"CH{c}" for c in sorted(p["channels"]))
            lines.append(f"- {p['frequency_hz']/1e3:.2f} kHz — SNR {p['snr_db']:.1f} dB, {ch_str}")
        lines.append(
            "\nThese are properties of the piezo sensor (confirmed by the free-decay impulse "
            "response), not of the plant.\n"
        )

    h("Validated Peaks (all criteria met)")
    if validated_peaks:
        lines.append(
            "| Rank | Frequency (kHz) | SNR (dB) | Repeatability | Channels | Sensor resonance? |"
        )
        lines.append("|---|---|---|---|---|---|")
        for i, p in enumerate(sorted(validated_peaks, key=lambda x: x["snr_db"], reverse=True)):
            freq_str = f"{p['frequency_hz']/1e3:.2f} ± {freq_res/1e3:.3f}"
            channels_str = ", ".join(f"CH{c}" for c in sorted(p["channels"]))
            res_str = "YES (sensor)" if p.get("is_sensor_resonance") else "no"
            lines.append(
                f"| {i+1} | {freq_str} | {p['snr_db']:.1f} | "
                f"{p['repeatability_fraction']:.0%} | {channels_str} | {res_str} |"
            )
    else:
        lines.append("**No peaks passed all validation criteria.**")

    h("Limitations")
    lines.append(
        "- **CH1 amplitude is not calibrated**: LM358 gain, bias, and supply quality are "
        "unknown, so CH1 amplitudes are not physical voltages at the piezo.\n"
        "- **Cross-channel amplitudes are not directly comparable**: the sensors differ in "
        "mechanical coupling (steel rod vs. 0.8 mm plate) and electronics.\n"
        "- **Frequency estimates are valid only within the acquired bandwidth** "
        f"(20 Hz – {MAX_FREQUENCY_HZ/1e3:.0f} kHz) at the stated {freq_res:.2f} Hz resolution.\n"
        "- **Passive baseline**: no deliberate mechanical or physiological excitation was "
        "applied; this characterizes the resting spectral content of the measurement chain "
        "plus environment, not stimulus-evoked plant emission.\n"
    )

    h("Methodological Notes")
    lines.append(
        f"{rate_str(rate)} with {n:,} points gives a {window_s*1e3:.0f} ms window and "
        f"{freq_res:.2f} Hz periodogram bin spacing. The Nyquist frequency "
        f"({rate/2/1e3:.0f} kHz) covers the full plant AE band (literature: ~1–100 kHz for "
        "xylem cavitation), so no software decimation is applied.\n\n"
        "Deep-memory readout from the DS1104Z is bandwidth-limited (~25 kB/s) and capped at "
        "250 000 points per request; the waveform is paged out in chunks (see "
        "`scope.instrument.acquire_waveform_full`). For finer resolution at the cost of "
        "readout time, re-acquire with `--memory-depth 3000000` (6 s window, 0.17 Hz, "
        "~6 min/capture).\n\n"
        "Anti-aliasing: never downsample by striding; use `scipy.signal.decimate` or "
        "`resample_poly`.\n"
    )

    h("Recommended Next Measurement")
    lines.append(
        "1. **Controlled-excitation contrast** — repeat this acquisition while applying a "
        "light tap to the steel rod / plate and compare against the quiet baseline to "
        "separate stimulus-evoked peaks from continuous background.\n"
        "2. **Drought / watering contrast** — acquire over a dry-down vs. watered cycle to "
        "test whether candidate peaks track the plant's water status.\n"
    )

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {out_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def cross_channel_validate(
    channels_data: dict[int, dict],
    sensor_resonances: list[float],
) -> list[dict]:
    """
    Apply cross-channel coherence + SNR filtering to per-channel repeatable peaks.

    *channels_data* must already contain, per channel, the keys ``repeatability``
    (from :func:`check_repeatability`), ``freqs`` and ``mean_psd`` (from
    :func:`average_psd`).  Returns the list of validated peaks, sorted by SNR
    (descending).  Peaks coinciding with a sensor resonance are kept but flagged
    via ``is_sensor_resonance`` so callers can separate plant candidates from
    piezo artefacts.

    This is the single source of truth for the validation step shared by the
    command-line report (:func:`main`) and the analysis notebooks.
    """
    # Collect all repeatable peaks (per channel, not mains)
    candidate_peaks: dict[int, list[dict]] = {}
    for ch, d in channels_data.items():
        rep = d["repeatability"]
        candidate_peaks[ch] = []
        for freq, info in rep.items():
            if info["repeatable"] and not _is_mains(freq):
                f_arr = d["freqs"]
                psd_arr = d["mean_psd"]
                mask = (f_arr >= 20) & (f_arr <= MAX_FREQUENCY_HZ)
                psd_db = 10 * np.log10(np.maximum(psd_arr, 1e-30))
                noise_floor = float(np.median(psd_db[mask]))
                # Find nearest bin
                close = np.abs(f_arr - freq)
                idx = int(np.argmin(close))
                psd_at_peak = float(psd_db[idx])
                candidate_peaks[ch].append(
                    {
                        "channel": ch,
                        "frequency_hz": freq,
                        "repeatability_fraction": info["fraction"],
                        "mean_prominence_db": info["mean_prominence_db"],
                        "psd_db": psd_at_peak,
                        "snr_db": psd_at_peak - noise_floor,
                    }
                )

    # Group across channels
    all_candidates = [p for peaks in candidate_peaks.values() for p in peaks]
    all_candidates.sort(key=lambda x: x["frequency_hz"])

    # Merge nearby across channels
    merged: list[dict] = []
    used = set()
    for i, p in enumerate(all_candidates):
        if i in used:
            continue
        group = [p]
        group_idx = {i}
        for j, q in enumerate(all_candidates):
            if j in used or j == i:
                continue
            if abs(q["frequency_hz"] - p["frequency_hz"]) <= CROSS_CH_TOLERANCE_HZ:
                group.append(q)
                group_idx.add(j)
        channels_in_group = {g["channel"] for g in group}
        if len(channels_in_group) >= 2:
            # Cross-channel coherence passed
            centroid_freq = float(np.mean([g["frequency_hz"] for g in group]))
            max_snr = max(g["snr_db"] for g in group)
            max_rep = max(g["repeatability_fraction"] for g in group)
            max_prom = max(g["mean_prominence_db"] for g in group)
            is_res = is_sensor_resonance(centroid_freq, sensor_resonances)
            merged.append(
                {
                    "frequency_hz": centroid_freq,
                    "snr_db": max_snr,
                    "repeatability_fraction": max_rep,
                    "mean_prominence_db": max_prom,
                    "channels": channels_in_group,
                    "is_sensor_resonance": is_res,
                }
            )
            used |= group_idx

    # Accept only those NOT matching sensor resonance (or flag them).
    # Enforce minimum SNR to exclude noise-floor peaks that pass repeatability
    # and coherence by chance (common-mode interference or correlated noise).
    merged_snr_filtered = [p for p in merged if p["snr_db"] >= MIN_SNR_DB]
    return sorted(merged_snr_filtered, key=lambda x: x["snr_db"], reverse=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument(
        "--impulse-dir", type=Path, default=IMPULSE_RAW_DIR
    )
    args = parser.parse_args(argv)

    if not args.data_dir.exists():
        print(f"Data directory not found: {args.data_dir}", file=sys.stderr)
        return 1

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PLANT AE FREQUENCY CHARACTERIZATION")
    print("=" * 70)
    print(f"Data directory : {args.data_dir}")
    print(f"Output         : {args.out_dir}")
    print()

    # ------------------------------------------------------------------
    # 1. Load all captures
    # ------------------------------------------------------------------
    print("Loading captures...")
    channels_data: dict[int, dict] = {}
    for ch in CHANNELS:
        caps = load_channel_captures(args.data_dir, ch)
        if not caps:
            print(f"  WARNING: No valid captures for CH{ch}")
            continue
        # Determine actual sample rate from the first valid file
        first_paths = sorted(set(args.data_dir.glob(f"*_ch{ch}.npz")) |
                             set(args.data_dir.glob(f"*_capture_ch{ch}.npz")))
        _, actual_rate = load_npz_capture(first_paths[0])
        freqs, mean_psd, std_psd = average_psd(caps, actual_rate)
        freq_res = actual_rate / len(caps[0])
        print(f"  CH{ch}: {len(caps)} captures @ {actual_rate/1e3:.0f} kSa/s, "
              f"{len(caps[0]):,} pts, Δf={freq_res:.1f} Hz")
        channels_data[ch] = {
            "captures": caps,
            "freqs": freqs,
            "mean_psd": mean_psd,
            "std_psd": std_psd,
            "sample_rate_hz": actual_rate,
        }

    if not channels_data:
        print("No valid captures found in data directory.", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # 2. Repeatability per channel
    # ------------------------------------------------------------------
    print("\nChecking repeatability...")
    for ch, d in channels_data.items():
        rep = check_repeatability(d["captures"], d["sample_rate_hz"])
        d["repeatability"] = rep
        n_rep = sum(
            1
            for f, i in rep.items()
            if i["repeatable"] and not _is_mains(f)
        )
        print(f"  CH{ch}: {n_rep} repeatable peaks (threshold {REPEAT_MIN_FRACTION:.0%})")

    # ------------------------------------------------------------------
    # 3. Impulse response baseline
    # ------------------------------------------------------------------
    print("\nLoading impulse response data...")
    impulse_result = load_impulse_spectra(args.impulse_dir)
    if impulse_result is not None:
        imp_f, imp_db = impulse_result
        # find_impulse_peaks expects PSD in dB; do NOT convert again here.
        sensor_resonances = find_impulse_peaks(imp_f, imp_db)
        print(
            f"  Found {len(sensor_resonances)} sensor resonances: "
            + ", ".join(f"{r/1e3:.1f} kHz" for r in sorted(sensor_resonances)[:10])
        )
    else:
        sensor_resonances = []
        print("  No impulse response data available.")

    # ------------------------------------------------------------------
    # 4. Cross-channel coherence + impulse exclusion
    # ------------------------------------------------------------------
    print("\nApplying cross-channel coherence filter...")
    validated_peaks = cross_channel_validate(channels_data, sensor_resonances)

    print(f"  Peaks passing ALL criteria (incl. SNR≥{MIN_SNR_DB} dB): "
          f"{sum(1 for p in validated_peaks if not p['is_sensor_resonance'])}")
    print(f"  Peaks flagged as sensor resonance: {sum(1 for p in validated_peaks if p['is_sensor_resonance'])}")

    # ------------------------------------------------------------------
    # 5. Console summary
    # ------------------------------------------------------------------
    print()
    print("─" * 70)
    print("VALIDATED PEAKS  (passed all criteria; not sensor resonances, sorted by SNR)")
    print("─" * 70)
    accepted = [p for p in validated_peaks if not p["is_sensor_resonance"]]
    if accepted:
        for rank, p in enumerate(accepted, 1):
            channels_str = "+".join(f"CH{c}" for c in sorted(p["channels"]))
            print(
                f"  {rank:2d}.  {p['frequency_hz']/1e3:7.2f} kHz "
                f"| SNR {p['snr_db']:5.1f} dB "
                f"| repeat {p['repeatability_fraction']:.0%} "
                f"| {channels_str}"
            )
    else:
        print("  (none)")

    print()
    print("─" * 70)
    print("PEAKS FLAGGED AS SENSOR RESONANCES (exclude from plant AE)")
    print("─" * 70)
    resonant = [p for p in validated_peaks if p["is_sensor_resonance"]]
    if resonant:
        for p in resonant:
            channels_str = "+".join(f"CH{c}" for c in sorted(p["channels"]))
            print(
                f"  {p['frequency_hz']/1e3:7.2f} kHz "
                f"| SNR {p['snr_db']:5.1f} dB | {channels_str}"
            )
    else:
        print("  (none — no impulse data or no overlap found)")
    print()

    # ------------------------------------------------------------------
    # 6. Plots
    # ------------------------------------------------------------------
    print("Generating plots...")
    plot_per_channel_overlay(
        channels_data,
        args.out_dir / "psd_per_channel_overlay.png",
    )
    plot_summary(
        channels_data,
        validated_peaks,
        impulse_result,
        args.out_dir / "summary.png",
    )
    print("  Plots saved.")

    # ------------------------------------------------------------------
    # 7. Report
    # ------------------------------------------------------------------
    ref_ch = next(iter(channels_data.values()))
    meta = {
        "data_dir": args.data_dir,
        "impulse_dir": args.impulse_dir,
        "sample_rate_hz": ref_ch["sample_rate_hz"],
        "n_samples": len(ref_ch["captures"][0]),
        "n_captures": len(ref_ch["captures"]),
    }
    freq_res_hz = meta["sample_rate_hz"] / meta["n_samples"]
    write_report(
        channels_data,
        validated_peaks,
        sensor_resonances,
        args.out_dir / "frequency_characterization_report.md",
        meta,
    )

    # Save machine-readable peak list
    import json
    peak_export = [
        {
            "frequency_hz": p["frequency_hz"],
            "frequency_khz": round(p["frequency_hz"] / 1e3, 3),
            "frequency_uncertainty_hz": round(freq_res_hz, 3),
            "snr_db": round(p["snr_db"], 2),
            "repeatability_fraction": round(p["repeatability_fraction"], 3),
            "mean_prominence_db": round(p["mean_prominence_db"], 2),
            "channels": sorted(p["channels"]),
            "is_sensor_resonance": p["is_sensor_resonance"],
        }
        for p in validated_peaks
    ]
    peaks_path = args.out_dir / "validated_peaks.json"
    peaks_path.write_text(json.dumps(peak_export, indent=2), encoding="utf-8")
    print(f"  Machine-readable peaks: {peaks_path}")

    print()
    print("=" * 70)
    print("CHARACTERIZATION COMPLETE")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
