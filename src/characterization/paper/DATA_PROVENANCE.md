# Data Provenance for Paper Figures

> **Single source of truth** for which data file feeds which paper number/figure.
> When you regenerate `paper_stats.json` via `make_figures.py`, cross-check the
> Session-IDs at the top of that script against the entries below. They must
> match; otherwise the paper renders stale numbers.

## Paper numbers (LaTeX `\statXxx` commands in `main.tex`)

| LaTeX macro | paper_stats.json key | Source data | Generator | Git-Commit |
|-------------|----------------------|-------------|-----------|-----------|
| `\statContinuousFrames` | `n_frames_cont` | `data/reports/notebooks/04_continuous_frequency_sweep/20260623_233855/frames.jsonl` | NB04, `summarize_monitor_sessions()` | 3189310 |
| `\statThreeEightCHOne` | `peak_38_ch1` | same frames.jsonl, persistence bin near 3.8 kHz | NB04 | 3189310 |
| `\statThreeEightCHThree` | `peak_38_ch3` | same | NB04 | 3189310 |
| `\statThreeEightCHFour` | `peak_38_ch4` | same | NB04 | 3189310 |
| `\statSixSixCHOne` | `peak_66_ch1` | same | NB04 | 3189310 |
| `\statSixSixCHThree` | `peak_66_ch3` | same | NB04 | 3189310 |
| `\statSixSixCHFour` | `peak_66_ch4` | same | NB04 | 3189310 |
| `\statCHThreeConstancy` | `peak_38_ch3` (alias) | same | NB04 | 3189310 |
| `\statCHFourConstancy` | `peak_38_ch4` (alias) | same | NB04 | 3189310 |
| `\statWateringDeltaDB` | `watering_delta_ch3_db` | `data/hybrid_watering_experiment/20260623_232016/snapshot_pre_watering/*.npz` vs `snapshot_post_watering/*.npz` | NB05 + `plant_ae.watering.compare_conditions` | 5089e50 |
| `\statWateringTemp` | `watering_temp` | `hybrid_manifest.json` (default 51.0 °C) | NB05 | 5089e50 |
| `\statWateringMoisture` | `watering_moisture` | `hybrid_manifest.json` (default 25.5 %) | NB05 | 5089e50 |
| `\statWateringDurationS` | `watering_duration_s` | `hybrid_manifest.json` (default 10 s) | NB05 | 5089e50 |
| `\statTempMax` | `temp_max` | Operator logbook (54.1 °C during 23.06. afternoon) | manual | — |

## Paper figures (`paper/figures/*.pdf`)

| File | Source data | Generator |
|------|-------------|-----------|
| `fig_pilot_psd.pdf` | `data/snapshot_sweeps/20260623_223349/*.npz` (5 frames) | `make_figures.py:fig_pilot_psd()` |
| `fig_peak_persistence.pdf` | `data/reports/notebooks/04_continuous_frequency_sweep/20260623_233855/frames.jsonl` | `make_figures.py:fig_peak_persistence()` |
| `fig_watering_diff.pdf` | pre+post watering snapshots | `make_figures.py:fig_watering_diff()` |
| `fig_zoom_candidates.pdf` | same pre+post snapshots, 0–15 kHz zoom | `make_figures.py:fig_zoom_candidates()` |

## Phase-3 MEMS follow-up

| Paper item | Source data | Generator / analysis |
|------------|-------------|----------------------|
| Air-reference RMS, GCC-PHAT and phase-candidate uncertainty | `data/ch3_ch4_phase_shift_20260626/20260716_162130/{summary.json,phase_candidates.csv,raw/*.npz}` | `experiment_ch3_ch4_phase_shift_20260626/ch3_ch4_phase_shift_experiment.py`; run-local `ANALYSIS.md` |
| MEMS-in-soil RMS, peaks, coherence, TDE, transients and statistics | `data/ch3_ch4_phase_shift_20260626/20260716_165231/{summary.json,methods_analysis.json,raw/*.npz}` | same acquisition script; run-local `METHODS_ANALYSIS.md` |
| `methods_overview.png` (Fig. `fig:mems`) | run `20260716_165231`, 20 synchronized CH3/CH4 raw frames | Phase-3 method-suite analysis stored with the run |
| `frame_0013_transient_detail.png` | run `20260716_165231`, raw frame 13 | run-local saturation/plausibility analysis; diagnostic, not included as a paper figure |

The Phase-3 soil geometry is intentionally reported as incomplete metadata: the
operator recorded that one MEMS was nearer and one farther from the presumed
source region, but did not record the channel mapping or distances. Consequently,
the paper uses TDE only as a rejection test for the observed zero-delay
common-mode signal, not for source localization.

## Reproducibility check

```bash
cd src/characterization
.venv/bin/python paper/make_figures.py
# Should print:
#   [0] Self-Test
#     ✓ Alle referenzierten Sessions vorhanden
#   [1] Pilot PSD
#     ✓ fig_pilot_psd.pdf
#   [2] Peak Persistence
#     ✓ fig_peak_persistence.pdf
#   [3] Watering Difference
#     ✓ fig_watering_diff.pdf
#   [4] Zoom 0-15 kHz
#     ✓ fig_zoom_candidates.pdf
#   [5] paper_stats.tex + Makefile
#     ✓ paper_stats.tex (14 Variablen)
#     ✓ Makefile
```

Then `cd paper && make` to compile the LaTeX.

## Historical ongoing-campaign items not yet included (Stand 27.06.2026)

The paper is based on the 23.06.2026 session (~70 frames). The ongoing campaign
(NB04, `measurement.py start`, Sessions 22.06.–27.06.) has produced ~4 800 frames
across 25 sessions with the following confirmed findings not yet in the paper text:

| Finding | Status | Data source |
|---------|--------|-------------|
| **Diurnales Kohärenzmuster 3 800 Hz** (Tag 0,27 / Nacht 0,80, σ=0,22) | 3+ unabhängige Nächte bestätigt | `data/reports/notebooks/04_continuous_frequency_sweep/*/frames.jsonl`, Feld `candidate_analysis.3800.coherence_ch3_ch4` |
| **6 747 Hz = strukturelles Artefakt** (9×750 Hz Gebäudepumpe) | Kohärenz MW 0,124, kein Frame >0,5 | selbe frames.jsonl, `candidate_analysis.6600.*` |
| **Tagesdrift 3 800 Hz** (+140 Hz, 14 bis 02 Uhr) | parabole Sub-Bin-Interpolation, `tracked_freq_hz` | selbe |
| **Bewässerungs-Δcoh 27.06.** (−0,104 nach 10 s) | 1 automatisches Experiment | `data/watering_experiments/20260627_*/analysis.json` |

Wenn die Kampagne n≥20 Frames pro Tages-/Nachtphase aus ≥5 unabhängigen Tagen
liefert, können die LaTeX-Makros oben durch Updates von `SESSION_CONTINUOUS`
in `make_figures.py` auf die Dauerläufe umgestellt werden.

> `continuous_characterization.py` ist seit 2026-06-26 **superseded** — neue Sessions
> laufen ausschließlich über NB04 (`measurement.py start`). Die letzten Runs via
> `continuous_characterization.py` endeten am 24.06.2026.
