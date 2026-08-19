# Plant Acoustic Emission Notebooks

This directory holds all Jupyter notebooks that drive measurement acquisition and analysis. The experimental campaign runs from 2026-06-21 (pilot) through the present.

## Portable Notebook Kernel

Run `../setup_jupyter.sh` once per workstation. It installs the Python
environment and registers the Jupyter kernel `plant-ae` (`Plant AE (Projekt I1)`).
All active notebooks are configured for that kernel name, so the kernel metadata
does not depend on an absolute `.venv` path.

For normal operation open:

```bash
cd src/characterization
.venv/bin/jupyter lab notebooks/00_control_panel.ipynb
```

The control panel is the canonical operator entry point. Its **Start Longrun
(NB04)** button always starts `04_continuous_frequency_sweep.ipynb`; the
dropdown applies only to **Run Once**. NB00 contains no experiment logic, NB04
is the continuous-experiment source of truth, and `measurement.py` is only the
shared background runner.

Phase 3 has no Home Assistant connection. Automatic watering and temperature
recording are disabled; manual watering events must be recorded as session
context.

## Single Source of Truth (SSOT)

| Tool | Sessions it produced | Status |
|------|----------------------|--------|
| `notebooks/04_continuous_frequency_sweep.ipynb` (NB04) via `measurement.py` | `data/reports/notebooks/04_continuous_frequency_sweep/20260622_*` … `20260627_*` (ongoing) | **Canonical — all continuous sessions** |
| `experiment_continuous_plant_ae_20260622/continuous_characterization.py` *(archiviert)* | `data/continuous_plant_ae_20260622/20260624_160540/` | **Archiviert 2026-06-27.** Letzte Session: 24.06.2026. Liegt jetzt unter `_archived/`. Nicht mehr starten — NB04 ist SSOT. |
| `notebooks/05_watering_experiment.ipynb` (NB05) | `data/hybrid_watering_experiment/20260623_232016/` | **Canonical watering experiment notebook** (archive/05_automated_hybrid_experiment.ipynb = superseded). |
| `notebooks/01..08` (other notebooks) | `data/<experiment>/<timestamp>/` | Canonical for their respective one-off experiments. |

**Architecture (current):** Operators open NB00 and use **Start Longrun
(NB04)**. NB00 invokes `measurement.py`, which executes NB04 as the canonical
background workflow. NB04 uses a `ContinuousFrequencyMonitor` with:
- RAM ring buffer (dynamic budget, ~90% RAM, 2 GiB reserve)
- Per-frame candidate-frequency tracking at 3 800 Hz and 6 750 Hz (fine-frequency via parabolic interpolation, Welch coherence, SNR, artifact-proximity metadata)
- Atomic heartbeat file per frame; `measurement.py status` detects frozen processes (>10 min without frame)
- Outer reconnect loop: after 5 consecutive frame errors, VISA connection is closed and reopened after 30 s; `monitor` state (ring, tracks, events) survives the reconnect

> **Do not delete `continuous_characterization.py` or NB05.** They are referenced in the paper (session 20260623_233855 via NB04, watering event via NB05). Deleting them would break paper reproducibility. For new continuous sessions, open NB00 and use **Start Longrun (NB04)**.

---

## Notebook Method Cards

Each notebook below lists its purpose, required inputs, generated outputs, hardware/software requirements, expected duration, and abort behaviour. All notebooks are JSON-valid and can be inspected without execution (`jupyter nbconvert --to script` or any text editor).

### NB01 — Channel Analysis

**File:** `01_channel_analysis.ipynb` **Purpose:** Three-channel comparison (time domain, spectra, cross-channel correlation) on the high-resolution baseline `data/long_captures/20260622_163645/`. **Inputs (read):** `data/long_captures/20260622_163645/raw/*.npz` (raw .npz, **Phase 1 setup CH1+CH2+CH3**). **Outputs (write):** `data/reports/notebooks/01_channel_analysis/<timestamp>/` (plots + summary). **Hardware:** None (offline analysis only). **Software:** `numpy`, `scipy`, `matplotlib`, `plant_ae`. **Duration:** <1 min. **Abort:** Safe to interrupt at any cell; pure read-only analysis.

### NB02 — Frequency Characterization

**File:** `02_frequency_characterization.ipynb` **Purpose:** Reproducible 0–100 kHz characterization with validation criteria (repeatability, cross-channel coherence, SNR, sensor-resonance flag). Reuses `frequency_analysis.py`. **Inputs (read):** User-specified `data_dir` of raw captures (typically `data/long_captures/<date>/raw`). **Outputs (write):** User-specified `output_dir` (typically `data/reports/frequency_analysis_baseline_20260622/`). **Hardware:** None. **Software:** as NB01. **Duration:** 1–3 min. **Abort:** Safe. **Note:** Output is the **canonical** `frequency_characterization_report.md` referenced in the paper.

### NB03 — Watering Experiment

**File:** `03_watering_experiment.ipynb` **Purpose:** Controlled comparison of MCU-off, MCU-on, pump and watering phases. **Inputs (read):** None (acquires its own data). **Outputs (write):** `data/plant_ae_3ch/<timestamp>/` with per-condition `oscilloscope_spectrum.png` and peak tables. **Hardware:** **Required** — Rigol DS1104Z @ 192.168.178.70, **Phase 1 setup CH1+CH2+CH3**. **Software:** `pyvisa`, `plant_ae.watering`. **Duration:** 15–30 min (depends on cycle count). **Abort:** Ctrl-C stops after current cycle; partial data is written to `manifest.json` with `status: interrupted`.

### NB04 — Continuous Frequency Sweep *(Paper-SSOT, primary ongoing tool)*

**File:** `04_continuous_frequency_sweep.ipynb` **Purpose:** RAM-backed continuous 0–100 kHz monitor for band changes and wandering frequencies. Source of the peak-persistence statistics in the paper and all ongoing sessions. **Inputs (read):** None (acquires its own data). **Outputs (write):** `data/reports/notebooks/04_continuous_frequency_sweep/<session_id>/` with `manifest.json`, `events.jsonl`, `frames.jsonl`, `heartbeat.json`. **Hardware:** **Required** — Rigol DS1104Z @ 192.168.178.70, **Phase 3 setup: CH1 Piezo + LM amplifier, CH3/CH4 MEMS microphones + LM amplifiers**, all with 10x probes; CH2 disabled. **Auxiliary data:** no Home Assistant, automatic watering or temperature measurement. **Software:** `pyvisa`, `plant_ae.rolling`, `plant_ae.deep_acquisition`. **Duration:** Unbounded. Frames are synchronized 0.6 s windows at 500 kSa/s and 300,000 points, separated by LAN transfer time. **Abort / Reconnect:** Outer reconnect loop handles VISA disconnect; Ctrl-C triggers safe finalization. **Start via:** NB00 **Start Longrun (NB04)**. Direct Cell-3 or terminal starts are diagnostic fallbacks only.

### NB05 — Automated Hybrid Experiment *(superseded for watering)*

**File:** `05_automated_hybrid_experiment.ipynb` **Purpose:** Was the primary automated workflow for the watering experiment (paper watering run 20260623_232016). **Superseded as of 2026-06-27** by `scripts/plant_in_loop_water.py` (cron, every 2 days, 20:13), which additionally stops/restarts the continuous measurement, captures N_PRE + N_POST frames with full candidate analysis, and runs 5 quantified hypothesis tests (H1–H5). **Inputs (read):** None. **Outputs (write):** `data/hybrid_watering_experiment/<timestamp>/`. **Hardware:** **Required** — Rigol DS1104Z + Home Assistant. **Note:** Kept for paper reproducibility (session 20260623_232016 = `\statWateringDeltaDB`). Do not start new watering experiments with NB05.

### NB06 — Reference Channel Experiment

**File:** `06_reference_channel_experiment.ipynb` **Purpose:** Reference channel comparison (plant-coupled vs external reference). **Inputs (read):** None. **Outputs (write):** `data/reference_channel_experiment/<timestamp>/`. **Hardware:** **Required** — Rigol DS1104Z, **uses CH2** for the reference comparison (not the main continuous path). **Duration:** 5–10 min. **Abort:** Safe.

### NB07 — Spatial Sensor Characterization

**File:** `07_spatial_sensor_characterization.ipynb` **Purpose:** Spatial variation of sensor placement (multiple positions, one stimulus). **Inputs (read):** None. **Outputs (write):** `data/spatial_sensor_experiment/<timestamp>/`. **Hardware:** **Required** — Rigol DS1104Z. **Duration:** 10–15 min. **Abort:** Safe.

### NB08 — Pump TDE Experiment

**File:** `08_pump_tde_experiment.ipynb` **Purpose:** Pump knock test for Time-Delay- Estimation (TDE) calibration between CH3 and CH4. **Inputs (read):** None. **Outputs (write):** `data/pump_tde_experiment/<timestamp>/` (TBD path). **Hardware:** **Required** — Rigol DS1104Z + pump actuator. **Duration:** 5–10 min. **Abort:** Safe.

---

## Data Schema (Phase 2, NB04 `frames.jsonl`)

```json
{
  "sequence": 17,
  "timestamp_utc": "2026-06-27T19:51:30+00:00",
  "timestamp_local": "2026-06-27T21:51:30+02:00",
  "light_phase": "day",
  "temperature_c": 23.4,
  "n_samples": 300000,
  "band_energy": [[...20 floats CH1...], [...CH3...], [...CH4...]],
  "peaks": {
    "1": [{"frequency_hz": 1250.1, "prominence_db": 31.4}, ...],
    "3": [{"frequency_hz": 3800.0, "prominence_db": 49.7}, ...],
    "4": [{"frequency_hz": 3800.0, "prominence_db": 48.5}, ...]
  },
  "candidate_analysis": {
    "3800": {
      "nearest_artifact_hz": 3750.0,
      "artifact_offset_hz": 50.0,
      "tracked_freq_hz": 3856.7,
      "tracked_artifact_offset_hz": 106.7,
      "coherence_ch3_ch4": 0.5252,
      "coherence_ch1_ch4": 0.018,
      "coherence_bias_floor": 0.0556,
      "coherence_n_segments": 18,
      "ch3_snr_db": 39.8,
      "ch4_snr_db": 38.1
    },
    "6600": {
      "nearest_artifact_hz": 6750.0,
      "artifact_offset_hz": -150.0,
      "tracked_freq_hz": 6747.3,
      "coherence_ch3_ch4": 0.124,
      "coherence_bias_floor": 0.0556
    }
  },
  "events": [...]
}
```

> Notes:
> - Channel keys in `peaks` are **strings** (`"1"`, `"3"`, `"4"`). CH2 absent by design.
> - `candidate_analysis` added 2026-06-26. Sessions before that date lack it.
> - `temperature_c` from Home Assistant sensor `sensor.satellite1_c412d0_temperature`; `null` if HA unreachable.
> - `coherence_bias_floor = 1/N_segments ≈ 0.056` (Welch, nperseg=16384, ~18 segments at 300k points). Values at or below the bias floor are not significant.

---

## Data Provenance

| Data file | Produced by | Git-Commit | Session date | Phase | |-----------|-------------|-----------|--------------|-------| | `data/plant_ae_optimized/20260621_200339/raw/` | NB04 / direct pyvisa | 3189310 | 2026-06-21 | Phase 1 (CH1+CH2+CH3) | | `data/long_captures/20260622_163645/raw/` | `scripts/acquire_long_capture.py` | 808ac18 | 2026-06-22 | Phase 1 | | `data/reports/frequency_analysis_baseline_20260622/` | `frequency_analysis.py` over long_captures | 808ac18 | 2026-06-22 16:59 | Phase 1 report | | `data/reports/frequency_analysis/` | `frequency_analysis.py` over plant_ae_optimized | 808ac18 | 2026-06-23 07:30 | Phase 1 report | | `data/snapshot_sweeps/20260623_223349/` | NB05 | bafbe6a | 2026-06-23 22:33 | Phase 2 (CH1+CH3+CH4) | | `data/hybrid_watering_experiment/20260623_232016/` | NB05 | 5089e50 | 2026-06-23 23:20 | Phase 2 | | `data/reports/notebooks/04_continuous_frequency_sweep/20260623_233855/` | NB04 | 3189310 | 2026-06-23 23:38 | Phase 2 (paper) | | `data/reports/notebooks/04_continuous_frequency_sweep/20260624_000840/` | continuous_characterization.py | 0fb1294 | 2026-06-24 00:08 | Phase 2 (overnight) | | `data/continuous_plant_ae_20260622/20260624_010136/` | continuous_characterization.py | (active) | 2026-06-24 01:01 | Phase 2 (overnight, active) |

> **Warnung:** `data/continuous_plant_ae_20260622/20260622_175202/` ist kompromittiert (83 Multi-Band-Drop-Events, Operator-Eingriff). Siehe `experiment_continuous_plant_ae_20260622/INCIDENT_REPORT.md`. Nur seq 0–11 sind nutzbar.

---

## Current Findings (Stand 27.06.2026, ~4 800 Frames, 25 Sessions)

Diese Befunde sind aus den Datendateien in `data/` reproduzierbar. Das Paper basiert noch auf der Pilotsession vom 23.06.; die folgenden Befunde stammen aus der laufenden Dauercharakterisierung.

### 1 · Diurnales Kohärenzmuster bei ~3 800 Hz

Die Kreuzkanal-Kohärenz CH3/CH4 bei ~3 800 Hz zeigt ein stabiles, sessionübergreifendes Tagesmuster (min. 3 unabhängige Nächte, 22.06.–27.06.):

| Phase | Kohärenz CH3/CH4 (Mittelwert) |
|-------|-------------------------------|
| Tag (06–22 Uhr) | 0,27 |
| Nacht (22–06 Uhr) | 0,80 |
| Natürliche Streuung (σ) | 0,22 |

- **CH1/CH4** bei 3 800 Hz: 0,002–0,04 — an/unter dem Kohärenz-Bias-Floor (1/N_seg = 1/18 ≈ 0,056).
- Die getrackte Frequenz liegt im Mittel ~15–70 Hz über dem 750-Hz-Gebäude-Harmonischen 5×750 = 3 750 Hz. Tagesdrift: +140 Hz von Minimum (14 Uhr) zu Maximum (02 Uhr).

### 2 · 6 750 Hz = strukturelles Artefakt

Der bisherige „6 600 Hz"-Kandidat ist die 9. Harmonische der Gebäude-Heizungspumpe (9 × 750 = 6 750 Hz):

- Mittlere getrackte Frequenz: **6 747 Hz** (2,7 Hz vom Sollwert)
- CH3/CH4-Kohärenz: Mittelwert **0,124**, kein Frame > 0,5
- Schluss: keine pflanzliche Quelle.

### 3 · Bewässerungs-Response

Erstes quantifiziertes Event (23.06.2026): 3 800 Hz Peak CH3 **+21,7 dB** nach 10 s Bewässerung (Bandenergie 0–5 kHz gesamt nur +0,2 dB, schmalbandig, keine Pumpeneinleitung).

Folge-Events (27.06.2026, automatisches Experiment `plant_in_loop_water.py`):

| Datum | pre coh | post coh | Δcoh |
|-------|---------|----------|------|
| 27.06. 20:13 | 0,631 | 0,527 | −0,104 |

Nächstes automatisches Experiment: 29.06.2026, 20:13 Uhr.

---

## Measurement Control (Terminal)

`measurement.py` (one level up) starts the code cells of a notebook as a background process, manages the PID, and writes state to `.measurement-control/state.json`. After completion it auto-commits and pushes new data to Git (LFS for .npz). Defaults to NB04.

```
./measurement.py start                            # NB04 (paper-continuous)
./measurement.py start --notebook notebooks/05_automated_hybrid_experiment.ipynb
./measurement.py status                           # PID + log path + start time
./measurement.py stop                             # SIGINT, graceful
./measurement.py publish                          # retry failed push
./measurement.py start --no-push                  # manual push later
```

The `.measurement-control/logs/` directory contains one `.log` per run; the state file records which notebook is running and the auto-push flag.

---

## Setup, Installation

```
python -m pip install -e src/characterization
```

Required Python packages: `numpy`, `scipy`, `matplotlib`, `pandas`, `pyvisa`, `typer`, `pydantic`, `ipython`, `jupyter`. The Rigol DS1104Z must be reachable at 192.168.178.70 via TCP/IP for any NB03–NB08 run.

---

## Cross-References

* Hardware setup history: `../experiment_continuous_plant_ae_20260622/HARDWARE_CHANGELOG.md`
* Methodology: `../experiment_continuous_plant_ae_20260622/METHODOLOGY.md`
* Paper figures generator: `../paper/generate_figures.py`
* Pilot experiment report: `../experiment_plant_acoustic_emissions_20260621/README.md`
* Automated workflow details: `AUTOMATED_WORKFLOW.md`
