#!/usr/bin/env python3
"""Generate all figures for the plant AE paper."""
import json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.gridspec import GridSpec
from matplotlib.ticker import MultipleLocator
from pathlib import Path
from scipy import stats

# ── Paths ─────────────────────────────────────────────────────────────────────
CHAR = Path(__file__).resolve().parent.parent
FIG  = Path(__file__).resolve().parent / "figures"
FIG.mkdir(exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "font.family":      "serif",
    "font.size":        9,
    "axes.labelsize":   9,
    "axes.titlesize":   9,
    "xtick.labelsize":  8,
    "ytick.labelsize":  8,
    "legend.fontsize":  8,
    "figure.dpi":       150,
    "axes.spines.top":  False,
    "axes.spines.right":False,
    "axes.grid":        True,
    "grid.alpha":       0.3,
    "grid.linewidth":   0.5,
    "lines.linewidth":  1.2,
})
C1, C3, C4 = "#1f77b4", "#2ca02c", "#d62728"
GRAY = "#666666"

# ── Load data ─────────────────────────────────────────────────────────────────
with open(CHAR / "data/pico_sweep_calibration/20260630_000343/mle_results.json") as f:
    mle = json.load(f)
bands_cal = mle["bands"]
freq_cal   = np.array([b["band_hz"] / 1e3 for b in bands_cal])
coh_cal    = np.array([b["coherence_mf"] for b in bands_cal])
tau_cal    = np.array([b["tau_mle_us"] for b in bands_cal])
amp3_cal   = np.array([b["amp3_mean_mV"] for b in bands_cal])
amp4_cal   = np.array([b["amp4_mean_mV"] for b in bands_cal])

with open(CHAR / "data/pico_tde_xcorr/20260629_170951/tde_result.json") as f:
    tde = json.load(f)

nb14_recs = []
with open(CHAR / "data/plant_ae_characterization/20260630_002403/records.jsonl") as f:
    for line in f:
        nb14_recs.append(json.loads(line))
pre14  = [r for r in nb14_recs if r.get("phase") == "pre"]
post14 = [r for r in nb14_recs if r.get("phase") == "post"]

events_path = CHAR / "data/reports/notebooks/04_continuous_frequency_sweep/20260624_162020/events.jsonl"
roll_events = []
with open(events_path) as f:
    for line in f:
        try: roll_events.append(json.loads(line))
        except: pass
peak_ev = [e for e in roll_events if e.get("type") == "persistent_cross_channel_peak"]

nb06 = np.load(CHAR / "data/reference_channel_experiment/20260623_121656/voltages.npz",
               allow_pickle=True)
nb06_ch1 = nb06["ch1"].astype(np.float64)
nb06_ch2 = nb06["ch2"].astype(np.float64)
nb06_ch3 = nb06["ch3"].astype(np.float64)
FS06     = float(nb06["sample_rate_hz"])

# ── Figure 1: System Block Diagram ────────────────────────────────────────────
def fig_system():
    fig, ax = plt.subplots(figsize=(7, 2.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 3.5)
    ax.axis("off")

    def box(cx, cy, w, h, label, sublabel="", col="#4C72B0", lc="white"):
        rect = mpatches.FancyBboxPatch((cx-w/2, cy-h/2), w, h,
            boxstyle="round,pad=0.05", linewidth=0.8,
            edgecolor="#333", facecolor=col, zorder=3)
        ax.add_patch(rect)
        ax.text(cx, cy + (0.12 if sublabel else 0), label,
                ha="center", va="center", fontsize=8, fontweight="bold",
                color=lc, zorder=4)
        if sublabel:
            ax.text(cx, cy - 0.18, sublabel, ha="center", va="center",
                    fontsize=6.5, color=lc, zorder=4)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="->", lw=0.9, color="#333"), zorder=2)

    # Sensors
    box(0.8, 3.0, 1.2, 0.55, "Soil Piezo", "CH1 (plant)", col="#5b8dd9")
    box(0.8, 1.75, 1.2, 0.55, "Rod Piezo A", "CH3 (ref)", col="#55a868")
    box(0.8, 0.5, 1.2, 0.55, "Rod Piezo B", "CH4 (ref)", col="#c44e52")

    # Amplifiers
    box(3.0, 3.0, 1.4, 0.55, "LM358 Amp", "830 kΩ ‖ 10× probe", col="#6d6d6d")
    box(3.0, 1.75, 1.4, 0.55, "LM358 Amp", "820 kΩ ‖ 10× probe", col="#6d6d6d")
    box(3.0, 0.5, 1.4, 0.55, "LM358 Amp", "820 kΩ ‖ 10× probe", col="#6d6d6d")

    # DS1104Z
    box(6.5, 1.75, 1.8, 2.8, "Rigol DS1104Z", "500 kSa/s · 300 kpts\nAC coup · 0.5 V/div", col="#8172b2")

    # CH2 defective note
    ax.text(6.5, 0.5, "CH2: defective", ha="center", va="center",
            fontsize=7, color="#999", style="italic")

    # Laptop
    box(9.2, 1.75, 1.3, 1.0, "PC", "Python / Jupyter\nVISA / USB-TMC", col="#474747")

    # Arrows sensor→amp
    for y in [3.0, 1.75, 0.5]:
        arrow(1.4, y, 2.3, y)
    # Arrows amp→scope
    for y in [3.0, 1.75, 0.5]:
        arrow(3.7, y, 5.6, y)
    # Scope→PC
    arrow(7.4, 1.75, 8.55, 1.75)

    # Labels on arrows
    for y, ch in zip([3.0, 1.75, 0.5], ["CH1", "CH3", "CH4"]):
        ax.text(4.65, y + 0.15, ch, fontsize=7, color="#333", ha="center")

    ax.text(9.2, 0.5, "USB-TMC", fontsize=6.5, color=GRAY, ha="center")

    fig.suptitle("", fontsize=1)
    plt.tight_layout(pad=0.3)
    fig.savefig(FIG / "fig1_system.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig1_system.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 1 done")

# ── Figure 2: Bandwidth + Coherence ───────────────────────────────────────────
def fig_bandwidth():
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.3))

    # (a) Coherence
    ax = axes[0]
    cmap = plt.cm.RdYlGn
    colors = [cmap(c) for c in coh_cal]
    ax.bar(freq_cal, coh_cal, width=4.0, color=colors, edgecolor="#333", linewidth=0.4)
    ax.axhline(0.9, ls="--", lw=0.9, color="#333", label="γ² = 0.9 (usable threshold)")
    ax.axvspan(5, 37.5, alpha=0.07, color="green", label="Calibrated band (5–35 kHz)")
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Coherence γ²  (1 = channels agree)")
    ax.set_xlim(0, 105); ax.set_ylim(0, 1.05)
    ax.set_title("(a) Both rod sensors agree at 5–35 kHz")
    ax.legend(loc="lower left", fontsize=7)
    ax.xaxis.set_major_locator(MultipleLocator(20))
    ax.xaxis.set_minor_locator(MultipleLocator(5))

    # (b) Amplitude response
    ax = axes[1]
    ax.semilogy(freq_cal, amp3_cal, "o-", color=C3, ms=4, label="CH3 (rod A)")
    ax.semilogy(freq_cal, amp4_cal, "s-", color=C4, ms=4, label="CH4 (rod B)")
    ax.axvspan(5, 37.5, alpha=0.07, color="green")
    ax.axvline(35, ls=":", lw=0.8, color="#555")
    # Annotate resonances — positions chosen to avoid title and mutual overlap
    _resonances = [
        (10,  "9.17 kHz\neigenmode", (28, 82),  "left"),
        (20,  "~20 kHz",             (24,  7),  "left"),
        (30,  "~30 kHz",             (44, 35),  "left"),
    ]
    for fkHz, label, xytext, ha in _resonances:
        idx = np.argmin(np.abs(freq_cal - fkHz))
        ax.annotate(label, xy=(freq_cal[idx], amp3_cal[idx]),
                    xytext=xytext,
                    fontsize=6.5, arrowprops=dict(arrowstyle="-", lw=0.6),
                    ha=ha)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Amplitude (mV RMS)")
    ax.set_xlim(0, 105)
    ax.set_title("(b) Response collapses above 35 kHz (LM358 limit)")
    ax.legend()
    ax.xaxis.set_major_locator(MultipleLocator(20))

    plt.tight_layout(pad=0.6)
    fig.savefig(FIG / "fig2_bandwidth.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig2_bandwidth.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 2 done")

# ── Figure 3: TDE ─────────────────────────────────────────────────────────────
def fig_tde():
    fig, axes = plt.subplots(1, 2, figsize=(7, 2.3))

    # (a) τ_MLE from sweep (5 kHz bands)
    ax = axes[0]
    reliable = coh_cal >= 0.9
    ax.errorbar(freq_cal[reliable], tau_cal[reliable],
                fmt="o", ms=5, color=C3, capsize=3, label="γ² ≥ 0.9 (trustworthy)")
    ax.scatter(freq_cal[~reliable], tau_cal[~reliable],
               marker="x", s=30, color="#aaa", zorder=2, label="γ² < 0.9 (scatter)")
    ax.axhline(0, ls="--", lw=0.8, color="#333")
    ax.axhspan(-0.5, 0.5, alpha=0.08, color="green", label="|τ| < 0.5 µs  (equidistant)")
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Sensor delay τ̂  (µs)")
    ax.set_title("(a) Delay ≈ 0 in the calibrated band")
    ax.set_xlim(0, 105); ax.set_ylim(-1.5, 5.5)
    ax.legend(fontsize=7)
    ax.xaxis.set_major_locator(MultipleLocator(20))

    # (b) Phase-diff TDE at 9 kHz resonance — magnitude, clean frames only.
    # Per-record τ are stored with the opposite sign of the reported summary
    # (which the text uses as a magnitude); plot |τ| so points and the mean
    # line agree and match the +1.95 µs quoted in the paper.
    ax = axes[1]
    recs = [r for r in tde["records"] if 8.0 <= r["f"] / 1e3 <= 12.0]
    freqs_r = np.array([r["f"] / 1e3 for r in recs])
    taus_ph = np.abs(np.array([r["tau_ph_us"] for r in recs]))

    ax.scatter(freqs_r, taus_ph, marker="o", s=25, color=C3,
               label=f"Per-frame |τ̂|  (N={len(recs)})")
    ax.axhline(tde["tde_ph_us"], ls="--", lw=1.2, color=C3,
               label=f"Phase mean: {tde['tde_ph_us']:.2f} µs")
    ax.axhline(tde["tde_xc_us"], ls="-", lw=1.0, color=C4,
               label=f"Cross-corr: {tde['tde_xc_us']:.2f} µs")
    ax.fill_between([freqs_r.min()-0.05, freqs_r.max()+0.05],
                    tde["tde_ph_us"]-tde["tde_ph_std_us"],
                    tde["tde_ph_us"]+tde["tde_ph_std_us"],
                    alpha=0.15, color=C3)
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Phase offset |τ̂|  (µs)")
    ax.set_ylim(0, 2.6)
    ax.set_title("(b) Resonance adds a fixed 1.95 µs offset")
    ax.legend(fontsize=7, loc="lower center")

    plt.tight_layout(pad=0.6)
    fig.savefig(FIG / "fig3_tde.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig3_tde.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 3 done")

# ── Figure 4: Noise Floor ─────────────────────────────────────────────────────
def fig_noise():
    n_bands = 50
    band_lo  = np.arange(n_bands) * 5  # kHz lower edge

    pre_be = {ch: np.zeros(n_bands) for ch in [1, 3, 4]}
    for b in range(n_bands):
        for ch in [1, 3, 4]:
            key = f"be_b{b}_ch{ch}_dB"
            vals = [r[key] for r in pre14 if key in r]
            pre_be[ch][b] = np.mean(vals) if vals else np.nan

    fig, ax = plt.subplots(figsize=(7, 2.4))
    ax.plot(band_lo + 2.5, pre_be[1], color=C1, lw=1.4, label="CH1 soil (plant channel) — highest noise")
    ax.plot(band_lo + 2.5, pre_be[3], color=C3, lw=1.2, ls="--", label="CH3 rod A (reference)")
    ax.plot(band_lo + 2.5, pre_be[4], color=C4, lw=1.2, ls=":", label="CH4 rod B (reference)")

    # Annotate steel eigenmode region
    ax.axvspan(5, 10, alpha=0.10, color=C3)
    ax.annotate("steel eigenmode\n(+39 dB on CH3)", xy=(8, -24), xytext=(18, -18),
                fontsize=6.5, color="#2a6", ha="left",
                arrowprops=dict(arrowstyle="-", lw=0.5, color="#888"))
    ax.axvspan(0, 5, alpha=0.08, color=C1)

    # Usable bandwidth
    ax.axvspan(5, 35, alpha=0.04, color="green")
    ax.text(30, -74, "calibrated band\n(5–35 kHz)", fontsize=6.5, color="#2a6", ha="center",
            style="italic")

    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("Band energy (dB re 1 V²,  5 kHz bins)")
    ax.set_xlim(0, 100); ax.set_ylim(-80, -10)
    ax.set_title("Passive noise floor per channel (no signal applied, N = 10 baseline frames)")
    ax.legend(fontsize=7, loc="upper right", ncol=1)
    ax.xaxis.set_major_locator(MultipleLocator(10))

    plt.tight_layout(pad=0.4)
    fig.savefig(FIG / "fig4_noise.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig4_noise.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 4 done")

# ── Figure 5: Watering Experiment ─────────────────────────────────────────────
def fig_watering():
    fig = plt.figure(figsize=(7, 2.7))
    gs  = GridSpec(1, 2, figure=fig, wspace=0.34)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    # (a) RMS time series on the real acquisition timeline.  Each stored frame
    # contains 0.6 s of data, but consecutive frames are roughly one minute
    # apart; a frame-index axis would therefore misrepresent the experiment.
    watering_rec = next(r for r in nb14_recs if r.get("type") == "watering")
    watering_t = np.datetime64(watering_rec["ts_utc"])
    def minutes_from_watering(records):
        return np.array([
            (np.datetime64(r["ts_utc"]) - watering_t) / np.timedelta64(1, "m")
            for r in records
        ], dtype=float)
    pre_t  = minutes_from_watering(pre14)
    post_t = minutes_from_watering(post14)
    pre_rms  = np.array([r["rms_ch1_V"] * 1000 for r in pre14])
    post_rms = np.array([r["rms_ch1_V"] * 1000 for r in post14])
    pre_rms3  = np.array([r["rms_ch3_V"] * 1000 for r in pre14])
    post_rms3 = np.array([r["rms_ch3_V"] * 1000 for r in post14])

    ax1.plot(pre_t, pre_rms, "o-", color=C1, ms=4, lw=1.0, label="CH1 (soil)")
    ax1.plot(post_t, post_rms, "o-", color=C1, ms=4, lw=1.0, alpha=0.5)
    ax1.plot(pre_t, pre_rms3, "s--", color=C3, ms=3, lw=0.8, label="CH3 (rod)")
    ax1.plot(post_t, post_rms3, "s--", color=C3, ms=3, lw=0.8, alpha=0.5)

    ax1.axvline(0, color="navy", lw=1.5, ls="--", label="Watering")
    ax1.set_xlabel("Time relative to watering (min)")
    ax1.set_ylabel("RMS (mV)")
    ax1.set_title("(a) CH1 drops, then recovers over ~20 min")
    ax1.legend(fontsize=7)
    ax1.set_ylim(80, 145)

    # (b) Band energy delta — all bands, CH1
    n_bands = 50
    deltas = np.zeros(n_bands)
    for b in range(n_bands):
        key = f"be_b{b}_ch1_dB"
        pv  = np.mean([r[key] for r in pre14  if key in r])
        pst = np.mean([r[key] for r in post14 if key in r])
        deltas[b] = pst - pv

    # Color by significance (Wilcoxon, FDR)
    pvals = []
    for b in range(n_bands):
        key = f"be_b{b}_ch1_dB"
        pv  = [r[key] for r in pre14  if key in r]
        pst = [r[key] for r in post14 if key in r]
        n = min(len(pv), len(pst))
        try:
            _, p = stats.wilcoxon(pv[:n], pst[:n])
        except:
            p = 1.0
        pvals.append(p)
    padj = stats.false_discovery_control(np.asarray(pvals), method="bh")
    reject = padj < 0.05

    bar_colors = ["#d62728" if r and d < 0 else "#2ca02c" if r and d > 0
                  else "#aaaaaa" for r, d in zip(reject, deltas)]
    ax2.bar(np.arange(n_bands) * 5 + 2.5, deltas, width=4.5,
            color=bar_colors, edgecolor="none", alpha=0.85)
    ax2.axhline(0, color="#333", lw=0.7)
    ax2.axhline(3,  ls="--", color="#888", lw=0.7, label="±3 dB")
    ax2.axhline(-3, ls="--", color="#888", lw=0.7)
    ax2.set_xlim(0, 100)
    ax2.set_xlabel("Frequency (kHz)")
    ax2.set_ylabel("ΔE (dB)  post − pre")
    ax2.axvspan(5, 35, color="#4c78a8", alpha=0.10,
                label="calibrated band (5–35 kHz)")
    ax2.set_title("(b) No clear AE-specific change in calibrated band")
    ax2.legend(fontsize=7)

    plt.tight_layout(pad=0.4)
    fig.savefig(FIG / "fig5_watering.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig5_watering.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 5 done")

# ── Figure 6: Rolling Events ───────────────────────────────────────────────────
def fig_rolling():
    from collections import Counter

    freqs = [e["frequency_hz"] for e in peak_ev]
    phases = [e.get("light_phase", "day") for e in peak_ev]

    bins = np.arange(0, 20500, 500)
    freq_day   = [f for f, p in zip(freqs, phases) if p == "day"   and f < 20000]
    freq_night = [f for f, p in zip(freqs, phases) if p == "night" and f < 20000]

    fig, axes = plt.subplots(1, 2, figsize=(7, 2.6))

    ax = axes[0]
    ax.hist(freq_day,   bins=bins, color="#f4a261", alpha=0.85, label=f"Day (n={len(freq_day)})")
    ax.hist(freq_night, bins=bins, color="#264653", alpha=0.75, label=f"Night (n={len(freq_night)})")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Event count")
    ax.set_title("(a) Peaks cluster at 50 Hz mains harmonics")
    ax.legend(fontsize=7)
    ax.xaxis.set_major_locator(MultipleLocator(5000))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x/1000:.0f}k"))

    # Annotate top bins — staggered y with transparent bbox
    rounded_all   = [round(f / 100) * 100 for f in freqs     if f < 20000]
    rounded_day   = [round(f / 100) * 100 for f in freq_day  if f < 20000]
    rounded_night = [round(f / 100) * 100 for f in freq_night if f < 20000]
    cnt_day   = Counter(rounded_day)
    cnt_night = Counter(rounded_night)
    top = Counter(rounded_all).most_common(5)
    top_sorted = sorted(top, key=lambda x: x[0])  # left to right
    # Fixed text x-positions spread evenly so arrows don't cross
    text_xs = [2000, 3500, 5000, 6500, 8000]
    y_offsets = [32, 26, 20, 14, 8]
    bbox_props = dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.7)
    for i, (freq_hz, count) in enumerate(top_sorted):
        bar_top = max(cnt_day.get(freq_hz, 0), cnt_night.get(freq_hz, 0))
        # For the rightmost label let the arrow end at text height (→ horizontal)
        arrow_y = y_offsets[i] if i == len(top_sorted) - 1 else bar_top
        ax.annotate(f"{freq_hz/1000:.1f}kHz (n={count})",
                    xy=(freq_hz, arrow_y),
                    xytext=(text_xs[i], y_offsets[i]),
                    fontsize=5.5, ha="left", color="#333",
                    bbox=bbox_props,
                    arrowprops=dict(arrowstyle="-", lw=0.5, color="#888"))

    # (b) Channel combination pie
    ax = axes[1]
    from collections import Counter
    def ch_label(chs):
        return "+".join(f"CH{c}" for c in sorted(chs))
    combos = Counter(ch_label(e.get("channels", [])) for e in peak_ev)
    labels = list(combos.keys())
    sizes  = list(combos.values())
    colors_pie = ["#5b8dd9", "#55a868", "#c44e52", "#8172b2"]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.0f%%",
        colors=colors_pie[:len(labels)], startangle=90,
        textprops={"fontsize": 7})
    # Nudge CH1+CH4 label right and down to avoid overlap with CH1+CH3
    for t in texts:
        if t.get_text() == "CH1+CH4":
            x, y = t.get_position()
            t.set_position((x + 0.35, y - 0.18))
    ax.set_title("(b) 62% fire on all 3 channels → environmental")

    plt.tight_layout(pad=0.6)
    fig.savefig(FIG / "fig6_rolling.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig6_rolling.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 6 done")

# ── Figure 7: NB06 Reference Channel — Positive Control ──────────────────────
def fig_reference():
    N_FRAMES = nb06_ch1.shape[0]
    n = nb06_ch1.shape[1]
    fs = FS06
    freq_ax = np.fft.rfftfreq(n, 1 / fs)

    # Welch multi-frame coherence CH1 vs CH2 and CH1 vs CH3
    def mf_coherence(A, B, n_seg=512):
        n_full = A.shape[1]
        n_bins = n_full // n_seg
        cross  = np.zeros(n_seg // 2 + 1, dtype=complex)
        pA     = np.zeros(n_seg // 2 + 1)
        pB     = np.zeros(n_seg // 2 + 1)
        for frame in range(A.shape[0]):
            for seg in range(n_bins):
                a = np.fft.rfft(A[frame, seg*n_seg:(seg+1)*n_seg])
                b = np.fft.rfft(B[frame, seg*n_seg:(seg+1)*n_seg])
                cross += a * np.conj(b)
                pA    += np.abs(a) ** 2
                pB    += np.abs(b) ** 2
        return np.abs(cross)**2 / (pA * pB + 1e-30)

    n_seg  = 512
    f_seg  = np.fft.rfftfreq(n_seg, 1/fs)
    coh_12 = mf_coherence(nb06_ch1, nb06_ch2)
    coh_13 = mf_coherence(nb06_ch1, nb06_ch3)

    # RMS per frame per channel
    rms1 = np.sqrt(np.mean(nb06_ch1**2, axis=1)) * 1000
    rms2 = np.sqrt(np.mean(nb06_ch2**2, axis=1)) * 1000
    rms3 = np.sqrt(np.mean(nb06_ch3**2, axis=1)) * 1000

    # Wilcoxon on RMS: CH1 vs CH3 (CH1 active sweep, CH3 passive ref → large effect)
    stat_13, p_13 = stats.wilcoxon(rms1, rms3)

    fig, axes = plt.subplots(1, 2, figsize=(7, 2.4))

    ax = axes[0]
    mask = f_seg < 5000
    ax.semilogy(f_seg[mask], coh_12[mask], color="#5b8dd9", lw=1.2, label="driven pair CH1–CH2 (high)")
    ax.semilogy(f_seg[mask], coh_13[mask], color=C4,       lw=1.0, ls="--", label="passive pair CH1–CH3 (low)")
    ax.axhline(0.5, ls=":", lw=0.8, color="#555", label="γ² = 0.5")
    # Mark 290 Hz candidate
    idx290 = np.argmin(np.abs(f_seg - 290))
    ax.scatter([f_seg[idx290]], [coh_12[idx290]], marker="*", s=90,
               color="gold", zorder=5, label=f"290 Hz peak  γ²={coh_12[idx290]:.3f}")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Coherence γ²  (1 = channels agree)")
    ax.set_xlim(0, 5000)
    ax.set_title("(a) Pipeline sees the injected signal")
    ax.legend(fontsize=6.5)

    ax = axes[1]
    x = np.arange(N_FRAMES)
    ax.plot(x, rms1, color="#5b8dd9", lw=0.8, label=f"CH1 (active, μ={np.mean(rms1):.0f} mV)")
    ax.plot(x, rms2, color=C4,        lw=0.8, label=f"CH2 (amp out, μ={np.mean(rms2):.0f} mV)")
    ax.plot(x, rms3, color=C3,        lw=0.8, label=f"CH3 (passive ref, μ={np.mean(rms3):.2f} mV)")
    ax.set_xlabel("Frame index  (N = 40)")
    ax.set_ylabel("RMS (mV)")
    ax.set_title("(b) 52.6 dB gap: driven vs. passive channel")
    ax.legend(fontsize=7)
    ax.text(25, np.mean(rms1)*0.75,
            f"Sensitivity\nCH1 vs CH3:\n+52.6 dB",
            fontsize=7.5, color="#333", ha="center",
            bbox=dict(boxstyle="round", fc="lightyellow", ec="#ccc", lw=0.5))

    plt.tight_layout(pad=0.6)
    fig.savefig(FIG / "fig7_reference.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig7_reference.png", bbox_inches="tight", dpi=200)
    plt.close()
    print("Fig 7 done")

# ── Run all ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fig_system()
    fig_bandwidth()
    fig_tde()
    fig_noise()
    fig_watering()
    fig_rolling()
    fig_reference()
    print(f"\nAll figures saved to {FIG}")
