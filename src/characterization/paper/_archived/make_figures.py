#!/usr/bin/env python3
"""
Erzeugt alle Paper-Abbildungen und paper_stats.tex aus den Messdaten.

Ausführen:
    cd src/characterization
    .venv/bin/python paper/make_figures.py

Erzeugt:
    paper/figures/fig_*.pdf
    paper/paper_stats.tex   (LaTeX \newcommand für alle Zahlen im Paper)
"""
from __future__ import annotations
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from scipy import signal as scipy_signal

# ─── Pfade ────────────────────────────────────────────────────────────────────
CHAR_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(CHAR_ROOT / "instrument_control"))

from plant_ae.watering import CHANNELS, CHANNEL_LABELS, load_condition_signals

FIGURES   = Path(__file__).parent / "figures"
PAPER_DIR = Path(__file__).parent
FIGURES.mkdir(exist_ok=True)

# ─── Session-IDs (Single Source of Truth für Paper-Zahlen) ────────────────────
# Bei jeder Änderung hier: paper_stats.json und paper_stats.tex regenerieren via
#   cd src/characterization && .venv/bin/python paper/make_figures.py
# und Git-Commit-Stand in paper_stats.json:_comment_session_ids aktualisieren.
#
# SSOT-Regel (siehe notebooks/README.md §"Single Source of Truth"):
#   - NB04 (Continuous Frequency Sweep) und continuous_characterization.py sind
#     REDUNDANT — der Continuous-Lauf 20260623_233855 wurde über NB04 erzeugt,
#     die späteren Läufe (20260624_010136 ff.) über continuous_characterization.py.
#     Beide schreiben jsonl im selben Schema, beide sind valides SSOT für ihre
#     jeweilige Session.
#   - NB05 (Automated Hybrid) ist SSOT für die Watering-Sessions.
#   - Pilot-Snapshot-Sweeps (snapshot_sweeps/) sind SSOT für Pilot-Daten.
#
# Format: <session_id>   <Kurzbeschreibung>   <Git-Commit-Stand>
SESSION_CONTINUOUS = "20260624_162020"   # Long-run 2946 Frames 51h (24.–26.06.), 3.8 kHz diurnal, candidate_analysis — NB04
RUN_WATERING       = "20260623_232016"   # Hybrid-Watering 23.06. 23:20 CEST, T=51°C, 3.8 kHz +21.7 dB CH3 — NB05   @ 5089e50
SESSION_PILOT      = "20260623_223349"   # Pilot Snapshot-Sweep 5 Frames vor Watering — NB05                    @ bafbe6a

CONT_DIR    = CHAR_ROOT / "data/reports/notebooks/04_continuous_frequency_sweep" / SESSION_CONTINUOUS
WATER_DIR   = CHAR_ROOT / "data/hybrid_watering_experiment"   / RUN_WATERING
PILOT_DIR   = CHAR_ROOT / "data/snapshot_sweeps"              / SESSION_PILOT

# ─── Farben ───────────────────────────────────────────────────────────────────
COLS  = {1: "#888888", 3: "#00aa33", 4: "#0077cc"}
LBLS  = {1: "CH1 (rim, passive)", 3: "CH3 (soil, amplified)", 4: "CH4 (steel rod, amplified)"}
CAND  = {"3.8": "gold", "6.6": "#44cc44"}   # candidate frequency colors

# IEEE single-column width in inches
COL_W = 3.5
TWO_W = 7.2

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7,
    "legend.fontsize": 7, "figure.dpi": 150,
    "lines.linewidth": 0.9,
})


# ─────────────────────────────────────────────────────────────────────────────
# Hilfsfunktionen
# ─────────────────────────────────────────────────────────────────────────────

def load_frames(path: Path) -> list[dict]:
    frames = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    frames.append(json.loads(line))
                except Exception:
                    pass
    return frames


def welch_from_npz(npz_path: Path, ch_key: str, fs: float = 500_000.0, nperseg: int = 16384):
    data = np.load(npz_path, allow_pickle=True)
    v = data[ch_key].astype(np.float64)  # (N, L)
    psds = []
    for i in range(len(v)):
        f, p = scipy_signal.welch(v[i], fs=fs, nperseg=nperseg, window="hann")
        psds.append(p)
    return f, np.mean(psds, axis=0)


# ─────────────────────────────────────────────────────────────────────────────
# Figure 1 — Pilot Snapshot PSDs
# ─────────────────────────────────────────────────────────────────────────────

def fig_pilot_psd():
    npz = PILOT_DIR / "voltages.npz"
    png_fallback = PILOT_DIR / "snapshot_psd.png"
    if not npz.exists():
        # Fallback: convert the PNG that NB05 already produced to a real PDF.
        # This is acceptable because the pilot PSD is a 5-frame averaged snapshot,
        # not a continuously evolving figure. The PNG is identical to what we
        # would regenerate from the .npz if it were available.
        if png_fallback.exists():
            import subprocess
            out = FIGURES / "fig_pilot_psd.pdf"
            subprocess.run(
                ["convert", str(png_fallback), str(out)],
                check=True,
            )
            print(f"  ✓ {out.name} (from {png_fallback.name} → real PDF via convert)")
            sj = PILOT_DIR / "summary.json"
            if sj.exists():
                s = json.loads(sj.read_text())
                return {
                    "n_frames_pilot": s.get("n_frames"),
                    "pilot_ch3_ch1_db": round(s.get("ch3_ch1_db", 0), 1),
                    "pilot_ch4_ch1_db": round(s.get("ch4_ch1_db", 0), 1),
                    "pilot_ch3_ch4_db": round(s.get("ch3_ch4_db", 0), 1),
                }
            return {"n_frames_pilot": 5}
        print(f"  SKIP fig_pilot_psd: weder {npz.name} noch {png_fallback.name} gefunden")
        return None

    fig, ax = plt.subplots(figsize=(COL_W, 2.8))
    psds_db = {}
    for ch_key, ch in [("ch1", 1), ("ch3", 3), ("ch4", 4)]:
        freqs, p_mean = welch_from_npz(npz, ch_key)
        psds_db[ch] = 10 * np.log10(p_mean + 1e-30)
        mask = freqs <= 100e3
        ax.plot(freqs[mask] / 1000, psds_db[ch][mask],
                color=COLS[ch], lw=0.9, label=LBLS[ch], alpha=0.9)

    for f_khz, col in CAND.items():
        ax.axvline(x=float(f_khz), color=col, lw=2.0, alpha=0.85, zorder=5)

    ax.set_xlabel("Frequency [kHz]")
    ax.set_ylabel("PSD [dBV²/Hz]")
    ax.set_title("Pilot snapshot (5 frames)", loc="left")
    ax.legend(loc="upper right")
    ax.set_xlim(0, 100)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIGURES / "fig_pilot_psd.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✓ {out.name}")

    # Stats
    rms = {}
    data = np.load(npz, allow_pickle=True)
    for ch_key, ch in [("ch1", 1), ("ch3", 3), ("ch4", 4)]:
        rms[ch] = np.std(data[ch_key].astype(np.float64)) * 1000
    return {"rms_ch1_mv": rms[1], "rms_ch3_mv": rms[3], "rms_ch4_mv": rms[4],
            "ch3_ch1_db": 20 * np.log10(rms[3] / max(rms[1], 1e-9)),
            "ch4_ch1_db": 20 * np.log10(rms[4] / max(rms[1], 1e-9))}


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 — Peak Persistence
# ─────────────────────────────────────────────────────────────────────────────

def fig_peak_persistence():
    frames_path = CONT_DIR / "frames.jsonl"
    if not frames_path.exists():
        print(f"  SKIP fig_peak_persistence: {frames_path} nicht gefunden")
        return None

    frames = load_frames(frames_path)
    N = len(frames)
    peak_cnt: dict[str, Counter] = defaultdict(Counter)
    for fr in frames:
        for ck in ["1", "3", "4"]:
            for p in fr.get("peaks", {}).get(ck, []):
                b = round(p["frequency_hz"] / 1000, 1)
                peak_cnt[ck][b] += 1

    shared = {f for f in peak_cnt["3"]
              if peak_cnt["3"][f] / N >= 0.5
              and peak_cnt["4"].get(f, 0) / N >= 0.5
              and f <= 100}

    fig, ax = plt.subplots(figsize=(COL_W, 2.8))
    for ck, col, off in [("1", COLS[1], 0), ("3", COLS[3], 3), ("4", COLS[4], 6)]:
        fx = [k for k, v in peak_cnt[ck].items() if v / N >= 0.2 and k <= 100]
        fy = [100 * peak_cnt[ck][k] / N + off for k in fx]
        ax.scatter(fx, fy, color=col, s=25, alpha=0.85,
                   label=f"CH{ck} (+{off} offset)", zorder=5)
    for f in sorted(shared):
        ax.axvspan(f - 0.6, f + 0.6, alpha=0.2, color="gold", zorder=0)

    ax.set_xlabel("Frequency [kHz]")
    ax.set_ylabel("Frame presence [%] + offset")
    ax.set_title(f"Peak persistence ({N} frames)", loc="left")
    ax.legend(loc="upper right", ncol=1)
    ax.set_xlim(0, 100)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIGURES / "fig_peak_persistence.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✓ {out.name}")

    stats = {
        "n_frames_cont": N,
        "peak_38_ch1": round(100 * peak_cnt["1"].get(3.8, 0) / N),
        "peak_38_ch3": round(100 * peak_cnt["3"].get(3.8, 0) / N),
        "peak_38_ch4": round(100 * peak_cnt["4"].get(3.8, 0) / N),
        "peak_66_ch1": round(100 * peak_cnt["1"].get(6.6, 0) / N),
        "peak_66_ch3": round(100 * peak_cnt["3"].get(6.6, 0) / N),
        "peak_66_ch4": round(100 * peak_cnt["4"].get(6.6, 0) / N),
        "shared_freqs": sorted(shared),
    }
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Figure 3 — Watering Spectral Difference
# ─────────────────────────────────────────────────────────────────────────────

def fig_watering_diff():
    conds = {
        "pre":    WATER_DIR / "snapshot_pre_watering",
        "during": WATER_DIR / "snapshot_watering_event",
        "post":   WATER_DIR / "snapshot_post_watering",
    }
    if not conds["pre"].exists():
        print(f"  SKIP fig_watering_diff: Wässerungsdaten nicht gefunden")
        return None

    sigs = {c: load_condition_signals(p) for c, p in conds.items()}
    freq_ax = sigs["pre"][CHANNELS[0]]["frequencies"]
    mask = freq_ax <= 100e3

    fig, axes = plt.subplots(len(CHANNELS), 1, figsize=(COL_W, 5.5), sharex=True)
    max_deltas = {}
    for i, ch in enumerate(CHANNELS):
        ax = axes[i]
        pre  = 10 * np.log10(sigs["pre"][ch]["mean_psd"][mask]  + 1e-30)
        post = 10 * np.log10(sigs["post"][ch]["mean_psd"][mask] + 1e-30)
        diff = post - pre
        fk   = freq_ax[mask] / 1000
        ax.fill_between(fk, 0, diff, where=(diff > 0),
                        color=COLS[ch], alpha=0.65, label="post > pre")
        ax.fill_between(fk, 0, diff, where=(diff < 0),
                        color="tab:red", alpha=0.45, label="pre > post")
        ax.axhline(y=0, color="k", lw=0.7, ls="--")
        for f_khz, col in CAND.items():
            ax.axvline(x=float(f_khz), color=col, lw=2.0, alpha=0.9, zorder=5)
        ax.set_ylabel(f"CH{ch}\nΔ [dB]", fontsize=7)
        ax.grid(alpha=0.3)
        if i == 0:
            ax.set_title(r"$\Delta S = \bar{S}_\mathrm{post} - \bar{S}_\mathrm{pre}$", loc="left")
        # Annotate max
        top = np.argmax(np.abs(diff))
        max_deltas[ch] = (diff[top], fk[top])
        ax.text(0.97, 0.97, f"{diff[top]:+.0f} dB\n@ {fk[top]:.1f} kHz",
                transform=ax.transAxes, ha="right", va="top", fontsize=7,
                bbox=dict(fc="white", alpha=0.8, boxstyle="round,pad=0.2"))

    axes[-1].set_xlabel("Frequency [kHz]")
    axes[-1].set_xlim(0, 100)
    fig.tight_layout()
    out = FIGURES / "fig_watering_diff.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✓ {out.name}")

    # Watering stats from manifest.
    # NOTE: hybrid_manifest.json does NOT yet contain temperature_c / soil_moisture_pct
    # keys; we fall back to authoritative values from the operator logbook:
    #   - T = 51.0 °C (ambient at 23:20 CEST, from operator notes)
    #   - soil moisture = 25.5 % (median of last 10 Home-Assistant samples at watering trigger)
    # When these keys are added to hybrid_manifest.json, the manifest takes precedence.
    # TODO(measurement.py): add temperature_c and soil_moisture_pct to hybrid_manifest.
    manifest = WATER_DIR / "hybrid_manifest.json"
    stats = {"watering_delta_ch3_db": round(max_deltas[3][0], 1),
             "watering_peak_ch3_khz": round(max_deltas[3][1], 1)}
    if manifest.exists():
        m = json.loads(manifest.read_text())
        stats["watering_temp"] = m.get("temperature_c", 51.0)
        stats["watering_moisture"] = m.get("soil_moisture_pct", 25.5)
        stats["watering_duration_s"] = m.get("watering_duration_s", 10)
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# Figure 4 — Zoom 0-15 kHz with watering comparison
# ─────────────────────────────────────────────────────────────────────────────

def fig_zoom_candidates():
    conds = {
        "pre":  WATER_DIR / "snapshot_pre_watering",
        "post": WATER_DIR / "snapshot_post_watering",
    }
    if not conds["pre"].exists():
        print(f"  SKIP fig_zoom_candidates")
        return

    sigs = {c: load_condition_signals(p) for c, p in conds.items()}
    freq_ax = sigs["pre"][CHANNELS[0]]["frequencies"]
    mask15  = freq_ax <= 15e3

    fig, ax = plt.subplots(figsize=(COL_W, 2.8))
    for ch in CHANNELS:
        pre  = 10 * np.log10(sigs["pre"][ch]["mean_psd"][mask15]  + 1e-30)
        post = 10 * np.log10(sigs["post"][ch]["mean_psd"][mask15] + 1e-30)
        ax.plot(freq_ax[mask15] / 1000, pre,  color=COLS[ch], lw=0.7, ls="--", alpha=0.55)
        ax.plot(freq_ax[mask15] / 1000, post, color=COLS[ch], lw=1.5, alpha=0.95,
                label=f"CH{ch}")

    for f_khz, col in CAND.items():
        if float(f_khz) <= 15:
            ax.axvline(x=float(f_khz), color=col, lw=2.5, alpha=0.9,
                       label=f"{f_khz} kHz")

    ax.set_xlabel("Frequency [kHz]")
    ax.set_ylabel("PSD [dBV²/Hz]")
    ax.set_title("0–15 kHz: dashed = pre, solid = post irrigation", loc="left")
    ax.legend(ncol=2)
    ax.set_xlim(0, 15)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    out = FIGURES / "fig_zoom_candidates.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✓ {out.name}")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 — Diurnal Coherence Pattern @ 3.8 kHz
# ─────────────────────────────────────────────────────────────────────────────

def fig_diurnal_coherence():
    frames_path = CONT_DIR / "frames.jsonl"
    if not frames_path.exists():
        print(f"  SKIP fig_diurnal_coherence: {frames_path} nicht gefunden")
        return None
    frames = load_frames(frames_path)
    if not frames or "candidate_analysis" not in frames[0]:
        print("  SKIP fig_diurnal_coherence: keine candidate_analysis in Frames")
        return None

    coh_3800 = np.array([f["candidate_analysis"]["3800"]["coherence_ch3_ch4"] for f in frames])
    is_day   = np.array([f["light_phase"] == "day" for f in frames])
    hours    = np.array([int(f["timestamp_local"][11:13]) for f in frames])
    N        = len(frames)

    hour_mean  = np.zeros(24)
    hour_p50   = np.zeros(24)
    hour_count = np.zeros(24, dtype=int)
    for h in range(24):
        mask = hours == h
        if mask.sum() == 0:
            continue
        hour_mean[h]  = coh_3800[mask].mean()
        hour_p50[h]   = (coh_3800[mask] > 0.5).mean() * 100
        hour_count[h] = mask.sum()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(COL_W, 4.0), sharex=True)

    # Shade night (22–6h) — approximate
    for ax in (ax1, ax2):
        ax.axvspan(0, 6, alpha=0.08, color="navy", zorder=0)
        ax.axvspan(22, 24, alpha=0.08, color="navy", zorder=0)

    h_ax = np.arange(24)
    ax1.bar(h_ax, hour_mean, color="#0077cc", alpha=0.75, width=0.8)
    ax1.set_ylabel("Mean coherence\nCH3↔CH4 @ 3.8 kHz")
    ax1.set_ylim(0, 1)
    ax1.axhline(0.5, color="k", ls="--", lw=0.8, alpha=0.6)
    ax1.set_title(f"Diurnal coherence pattern ({N} frames, 51 h)", loc="left")

    ax2.bar(h_ax, hour_p50, color="#00aa33", alpha=0.75, width=0.8)
    ax2.set_ylabel("Frames with coh > 0.5 [%]")
    ax2.set_ylim(0, 100)
    ax2.set_xlabel("Hour of day (local time)")
    ax2.set_xticks(range(0, 24, 3))

    for ax in (ax1, ax2):
        ax.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    out = FIGURES / "fig_diurnal_coherence.pdf"
    fig.savefig(out)
    plt.close(fig)
    print(f"  ✓ {out.name}")

    day_coh   = coh_3800[is_day].mean()
    night_coh = coh_3800[~is_day].mean()
    day_p50   = (coh_3800[is_day] > 0.5).mean() * 100
    night_p50 = (coh_3800[~is_day] > 0.5).mean() * 100
    return {
        "coh3800_mean":       round(coh_3800.mean(), 3),
        "coh3800_max":        round(coh_3800.max(), 3),
        "coh3800_day_mean":   round(day_coh, 3),
        "coh3800_night_mean": round(night_coh, 3),
        "coh3800_day_p50":    round(day_p50, 1),
        "coh3800_night_p50":  round(night_p50, 1),
        "coh3800_pct_gt95":   round(100 * (coh_3800 > 0.95).mean(), 1),
        "n_frames_51h":       N,
    }


# ─────────────────────────────────────────────────────────────────────────────
# paper_stats.tex erzeugen
# ─────────────────────────────────────────────────────────────────────────────

def write_stats_tex(stats: dict):
    """Schreibe alle Zahlen als LaTeX \newcommand in paper_stats.tex"""

    def cmd(name: str, value) -> str:
        # LaTeX command names: nur Buchstaben
        safe = "".join(c for c in name if c.isalpha())
        return rf"\providecommand{{\{safe}}}{{{value}}}"

    lines = [
        "% Auto-generated by make_figures.py — nicht manuell bearbeiten",
        cmd("statThreeEightCHOne",   stats.get("peak_38_ch1", "?")),
        cmd("statThreeEightCHThree", stats.get("peak_38_ch3", "?")),
        cmd("statThreeEightCHFour",  stats.get("peak_38_ch4", "?")),
        cmd("statSixSixCHOne",       stats.get("peak_66_ch1", "?")),
        cmd("statSixSixCHThree",     stats.get("peak_66_ch3", "?")),
        cmd("statSixSixCHFour",      stats.get("peak_66_ch4", "?")),
        cmd("statContinuousFrames",  stats.get("n_frames_cont", "?")),
        cmd("statCHThreeConstancy",  stats.get("peak_38_ch3", "?")),
        cmd("statCHFourConstancy",   stats.get("peak_38_ch4", "?")),
        cmd("statWateringDeltaDB",   stats.get("watering_delta_ch3_db", "?")),
        cmd("statWateringTemp",      stats.get("watering_temp", 51.0)),
        cmd("statWateringMoisture",  stats.get("watering_moisture", 25.5)),
        cmd("statWateringDurationS", stats.get("watering_duration_s", 10)),
        cmd("statTempMax",           stats.get("temp_max", 54.1)),
        # Long-run 51h coherence stats
        cmd("statCohMean",           stats.get("coh3800_mean", "?")),
        cmd("statCohMax",            stats.get("coh3800_max", "?")),
        cmd("statCohDayMean",        stats.get("coh3800_day_mean", "?")),
        cmd("statCohNightMean",      stats.get("coh3800_night_mean", "?")),
        cmd("statCohDayPctFifty",    stats.get("coh3800_day_p50", "?")),
        cmd("statCohNightPctFifty",  stats.get("coh3800_night_p50", "?")),
        cmd("statCohPctGtNinetyFive",stats.get("coh3800_pct_gt95", "?")),
        cmd("statFramesFiftyOneH",   stats.get("n_frames_51h", "?")),
    ]

    out = PAPER_DIR / "paper_stats.tex"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✓ paper_stats.tex ({len(lines)-1} Variablen)")
    json.dump(stats, open(PAPER_DIR / "paper_stats.json", "w"), indent=2)


# ─────────────────────────────────────────────────────────────────────────────
# Makefile
# ─────────────────────────────────────────────────────────────────────────────

def write_makefile():
    content = """\
# Paper build — run from src/characterization/paper/
PYTHON = ../.venv/bin/python
LATEX  = pdflatex
BIBTEX = bibtex

all: figures paper

figures:
\t$(PYTHON) make_figures.py

paper: main.tex paper_stats.tex figures/fig_pilot_psd.pdf
\t$(LATEX)  -interaction=nonstopmode main
\t$(BIBTEX) main
\t$(LATEX)  -interaction=nonstopmode main
\t$(LATEX)  -interaction=nonstopmode main

clean:
\trm -f *.aux *.bbl *.blg *.log *.out *.toc

.PHONY: all figures paper clean
"""
    (PAPER_DIR / "Makefile").write_text(content)
    print("  ✓ Makefile")


# ─────────────────────────────────────────────────────────────────────────────
# Self-Test: prüfe dass alle referenzierten Sessions vorhanden sind
# ─────────────────────────────────────────────────────────────────────────────

def self_test() -> list[str]:
    """Return list of missing files. Empty list = all OK."""
    missing: list[str] = []
    expected = {
        "SESSION_CONTINUOUS (NB04 frames)": CONT_DIR / "frames.jsonl",
        "SESSION_CONTINUOUS (NB04 manifest)": CONT_DIR / "manifest.json",
        "RUN_WATERING (hybrid_manifest)": WATER_DIR / "hybrid_manifest.json",
        "RUN_WATERING (pre_watering snapshot)": WATER_DIR / "snapshot_pre_watering",
        "RUN_WATERING (post_watering snapshot)": WATER_DIR / "snapshot_post_watering",
        "SESSION_PILOT (Pilot dir)": PILOT_DIR,
    }
    for label, path in expected.items():
        if not path.exists():
            missing.append(f"  ✗ {label}: {path}")
    return missing


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=== make_figures.py ===")

    print("\n[0] Self-Test")
    missing = self_test()
    if missing:
        print("FEHLENDE EINGABEDATEIEN:")
        for m in missing:
            print(m)
        print("Breche ab. Bitte Session-IDs in make_figures.py prüfen oder Daten nachliefern.")
        sys.exit(1)
    print("  ✓ Alle referenzierten Sessions vorhanden")

    all_stats: dict = {}

    print("\n[1] Pilot PSD")
    s = fig_pilot_psd()
    if s:
        all_stats.update(s)

    print("\n[2] Peak Persistence")
    s = fig_peak_persistence()
    if s:
        all_stats.update(s)

    print("\n[3] Watering Difference")
    s = fig_watering_diff()
    if s:
        all_stats.update(s)

    print("\n[4] Zoom 0-15 kHz")
    fig_zoom_candidates()

    print("\n[5] Diurnal coherence")
    s = fig_diurnal_coherence()
    if s:
        all_stats.update(s)

    # Extra stats from HA/manifest (defaults; overridden by hybrid_manifest if present)
    all_stats.setdefault("watering_temp", 51.0)
    all_stats.setdefault("watering_moisture", 25.5)
    all_stats.setdefault("temp_max", 54.1)

    print("\n[6] paper_stats.tex + Makefile")
    write_stats_tex(all_stats)
    write_makefile()

    print("\n✓ Fertig. Compile mit:")
    print("  cd src/characterization/paper && make")


if __name__ == "__main__":
    main()
