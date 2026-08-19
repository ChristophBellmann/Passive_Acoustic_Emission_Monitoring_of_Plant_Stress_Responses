#!/usr/bin/env python3
"""Phase-3 MEMS characterisation from raw measurement data.

Evaluates the raw data acquired after the relocation and the piezo-to-MEMS
replacement (lettuce-plant setup, 2026-07-14):

  1. Frequency sweep calibration (records.jsonl, per-frame complex FFT bins):
     amplitude transfer, multi-frame coherence gamma^2 and MLE time-delay
     between the two MEMS channels, and the resulting calibrated band.
  2. Passive noise floor (deep-memory raw waveforms, capture_*.npz):
     per-5 kHz-band RMS for the soil piezo (CH1) and the two MEMS (CH3/CH4).

Coherence and time-delay are recomputed from the raw complex bins with the same
estimators as the piezo characterisation (paper Eqs. 1-2), so the MEMS result is
directly comparable. Produces figures/fig_mems_phase3.{pdf,png} and a markdown
report.

Run from src/characterization/:
    python3 scripts/analyze_mems_phase3.py
"""
from __future__ import annotations

import glob
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import signal as sp_signal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent  # src/characterization
SWEEP = ROOT / "data" / "pico_sweep_calibration_phase3" / "20260714_175557"
NOISE_RUN = ROOT / "data" / "test_measurements_phase3" / "20260714_221000"
FIG_DIR = ROOT / "paper" / "figures"
REPORT = ROOT / "data" / "pico_sweep_calibration_phase3" / "mems_characterization_report.md"

SNR_MIN = 3.0
COH_MIN = 0.9
CH_INDEX = {1: 0, 3: 1, 4: 2}  # channel -> row in npz voltages


def analyse_sweep(sweep_dir: Path):
    """Amplitude, coherence and MLE-TDE per band from the raw complex bins."""
    records = [json.loads(line) for line in (sweep_dir / "records.jsonl").open()]
    by_band: dict[int, list[dict]] = defaultdict(list)
    for r in records:
        by_band[r["band_hz"]].append(r)

    rows = []
    for f_hz in sorted(by_band):
        frames = by_band[f_hz]
        v3 = np.array([r["fft3_bin_real"] + 1j * r["fft3_bin_imag"] for r in frames])
        v4 = np.array([r["fft4_bin_real"] + 1j * r["fft4_bin_imag"] for r in frames])
        cross = np.sum(v3 * np.conj(v4))
        coherence = abs(cross) ** 2 / (np.sum(abs(v3) ** 2) * np.sum(abs(v4) ** 2))
        tde_us = -np.angle(cross) / (2 * np.pi * f_hz) * 1e6
        rows.append(
            dict(
                f_khz=f_hz / 1e3,
                n=len(frames),
                a3_mv=float(np.mean([r["amp3_V"] for r in frames]) * 1e3),
                a4_mv=float(np.mean([r["amp4_V"] for r in frames]) * 1e3),
                snr3=float(np.mean([r["snr3"] for r in frames])),
                snr4=float(np.mean([r["snr4"] for r in frames])),
                coherence=float(coherence),
                tde_us=float(tde_us),
            )
        )
    return rows


def analyse_noise(noise_dir: Path, band_hz: float = 5000.0, f_max: float = 60000.0):
    """Per-band RMS (mV) per channel from the deep-memory raw waveforms."""
    files = sorted(glob.glob(str(noise_dir / "capture_*.npz")))
    psd = {c: [] for c in CH_INDEX}
    rms = {c: [] for c in CH_INDEX}
    freqs = None
    fs = None
    for path in files:
        data = np.load(path, allow_pickle=True)
        fs = float(data["sample_rate_hz"])
        volts = data["voltages"]
        for ch, idx in CH_INDEX.items():
            x = volts[idx].astype(float)
            x -= np.mean(x)
            freqs, p = sp_signal.welch(x, fs, nperseg=8192)
            psd[ch].append(p)
            rms[ch].append(np.sqrt(np.mean(x ** 2)))

    edges = np.arange(0, f_max + band_hz, band_hz)
    centres = (edges[:-1] + edges[1:]) / 2 / 1e3
    band_rms = {}
    total_rms = {}
    for ch in CH_INDEX:
        p_mean = np.mean(psd[ch], axis=0)
        vals = []
        for lo, hi in zip(edges[:-1], edges[1:]):
            m = (freqs >= lo) & (freqs < hi)
            vals.append(np.sqrt(np.trapezoid(p_mean[m], freqs[m])) * 1e3)
        band_rms[ch] = np.array(vals)
        total_rms[ch] = float(np.mean(rms[ch]) * 1e3)
    return centres, band_rms, total_rms, len(files)


def make_figure(sweep_rows, centres, band_rms, out_stem: Path):
    f = np.array([r["f_khz"] for r in sweep_rows])
    coh = np.array([r["coherence"] for r in sweep_rows])
    a3 = np.array([r["a3_mv"] for r in sweep_rows])
    a4 = np.array([r["a4_mv"] for r in sweep_rows])
    reliable = np.array(
        [r["coherence"] >= COH_MIN and min(r["snr3"], r["snr4"]) >= SNR_MIN for r in sweep_rows]
    )
    band_hi = f[reliable].max() if reliable.any() else 0

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.4))

    ax = axes[0]
    ax.axvspan(2.5, band_hi + 2.5, color="#2ca02c", alpha=0.12, label="calibrated")
    ax.plot(f, coh, "o-", color="#1f3a5f", ms=4)
    ax.axhline(COH_MIN, ls="--", color="grey", lw=0.8)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel(r"Coherence $\hat\gamma^2$")
    ax.set_ylim(0, 1.05)
    ax.set_title("(a) CH3-CH4 coherence")
    ax.legend(fontsize=8, loc="lower left")

    ax = axes[1]
    ax.axvspan(2.5, band_hi + 2.5, color="#2ca02c", alpha=0.12)
    ax.semilogy(f, a3, "o-", ms=4, label="CH3 (MEMS A)")
    ax.semilogy(f, a4, "s-", ms=4, label="CH4 (MEMS B)")
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("RMS amplitude (mV)")
    ax.set_title("(b) Transfer amplitude")
    ax.legend(fontsize=8)

    ax = axes[2]
    style = {1: ("#c0392b", "-", "CH1 piezo (soil)"),
             3: ("#1f3a5f", "--", "CH3 MEMS A"),
             4: ("#2ca02c", ":", "CH4 MEMS B")}
    for ch, (col, ls, lab) in style.items():
        ax.semilogy(centres, band_rms[ch], ls, color=col, label=lab, lw=1.6)
    ax.set_xlabel("Frequency band (kHz)")
    ax.set_ylabel("Band RMS (mV)")
    ax.set_title("(c) Passive noise floor")
    ax.legend(fontsize=8)

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(out_stem.with_suffix("." + ext), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return band_hi


def write_report(sweep_rows, centres, band_rms, total_rms, n_noise, band_hi, out: Path):
    reliable = [
        r for r in sweep_rows
        if r["coherence"] >= COH_MIN and min(r["snr3"], r["snr4"]) >= SNR_MIN
    ]
    lines = []
    lines.append("# Phase-3 MEMS characterisation (lettuce-plant setup)\n")
    lines.append(
        "Raw data evaluated directly: frequency sweep "
        f"`{SWEEP.name}` (records.jsonl) and passive noise run "
        f"`{NOISE_RUN.name}` ({n_noise} deep-memory frames). Coherence and MLE "
        "time-delay recomputed from the raw complex FFT bins with the same "
        "estimators as the piezo characterisation.\n"
    )
    lines.append("## Frequency sweep (CH3/CH4 MEMS)\n")
    lines.append("| f (kHz) | N | CH3 (mV) | CH4 (mV) | SNR3 | SNR4 | coherence | TDE (us) |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in sweep_rows:
        lines.append(
            f"| {r['f_khz']:.0f} | {r['n']} | {r['a3_mv']:.2f} | {r['a4_mv']:.2f} "
            f"| {r['snr3']:.1f} | {r['snr4']:.1f} | {r['coherence']:.4f} | {r['tde_us']:+.3f} |"
        )
    rel_f = ", ".join(f"{r['f_khz']:.0f}" for r in reliable)
    tdes = np.array([r["tde_us"] for r in reliable])
    lines.append(
        f"\nCalibrated band (coherence >= {COH_MIN}, SNR >= {SNR_MIN} on both): "
        f"**{rel_f} kHz**, i.e. up to ~{band_hi:.0f} kHz. Time-delay across the "
        f"reliable bands: {tdes.min():+.2f} to {tdes.max():+.2f} us "
        f"(mean {tdes.mean():+.2f} us), consistent with near-equidistant MEMS placement.\n"
    )
    lines.append("## Passive noise floor (per 5 kHz band, mV RMS)\n")
    lines.append("| Band (kHz) | CH1 piezo | CH3 MEMS A | CH4 MEMS B |")
    lines.append("|---:|---:|---:|---:|")
    for i, c in enumerate(centres):
        lines.append(
            f"| {c-2.5:.0f}-{c+2.5:.0f} | {band_rms[1][i]:.2f} "
            f"| {band_rms[3][i]:.2f} | {band_rms[4][i]:.2f} |"
        )
    lines.append(
        f"\nTotal AC RMS: CH1 {total_rms[1]:.1f} mV, CH3 {total_rms[3]:.1f} mV, "
        f"CH4 {total_rms[4]:.1f} mV. The MEMS channels are dominated by a common-mode "
        "harmonic comb (fundamental ~5.36 kHz) in the 5-10 kHz band, coherent across "
        "all channel pairs (line coherence > 0.999). A controlled power-supply A/B "
        "swap shifted the comb by -35 Hz (5393->5358 Hz) but did not remove it: the "
        "original Raspberry Pi supply is thus not the sole source, yet the "
        "supply-tracking frequency shift shows the power-delivery path influences the "
        "artefact. The exact coupling source is not yet isolated. It is an "
        "instrumentation artefact, not a biological signal.\n"
    )
    out.write_text("\n".join(lines))


def main() -> None:
    sweep_rows = analyse_sweep(SWEEP)
    centres, band_rms, total_rms, n_noise = analyse_noise(NOISE_RUN)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    band_hi = make_figure(sweep_rows, centres, band_rms, FIG_DIR / "fig_mems_phase3")
    write_report(sweep_rows, centres, band_rms, total_rms, n_noise, band_hi, REPORT)
    print(f"calibrated band up to ~{band_hi:.0f} kHz")
    print(f"figure : {FIG_DIR / 'fig_mems_phase3.pdf'}")
    print(f"report : {REPORT}")


if __name__ == "__main__":
    main()
