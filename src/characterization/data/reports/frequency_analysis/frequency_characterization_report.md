
# Plant Acoustic Emission Frequency Characterization

> **⚠ Phase 1 report (pre-CH2-defect).** This analysis was performed on 2026-06-23 07:30 using **raw data captured on 2026-06-21 (Phase 1 setup: CH1 + CH2 + CH3)**. CH2 = Piezo on 0.8 mm stainless-steel plate, 1:1 probe. On 2026-06-22 CH2 suffered a hardware fault and was replaced by CH4. **Cross-channel conclusions from this report are not directly applicable to current Phase 2 (CH1+CH3+CH4) measurements.** See `experiment_continuous_plant_ae_20260622/HARDWARE_CHANGELOG.md` for the full setup history.

**Analysis date:** 2026-06-23 07:30:07  
**Raw data:** `/media/christoph/some_space/Nextcloud/hs-augsburg/Semester_6/Projekt_I1/projekt_i1/src/characterization/data/plant_ae_optimized/20260621_200339/raw`  
**Impulse reference:** `/media/christoph/some_space/Nextcloud/hs-augsburg/Semester_6/Projekt_I1/projekt_i1/src/characterization/data/impulse_response/20260621_182730/raw`  
**Script:** `frequency_analysis.py`


## Data and Method

Channels: CH1 (piezo + LM358 amplifier + 820 kΩ, 10:1 probe, uncalibrated gain), CH2 (piezo + 820 kΩ, 1:1 probe), CH3 (piezo direct, 1:1 probe)  [Phase 1 setup, pre-CH2-defect]
Captures per channel: 19  
Sample rate: 25.00 MSa/s (Nyquist 12500 kHz)  
Capture window: 4 ms  
**Frequency resolution: 250.00 Hz** (periodogram bin spacing)  
Analysis bandwidth: 20 Hz – 100 kHz  


A spectral peak is accepted as a candidate only if it meets ALL of:
1. **Repeatability** ≥ 40% of captures per channel.
2. **Cross-channel coherence**: present within ±1.0 kHz on ≥ 2 channels.
3. **Minimum SNR** ≥ 5 dB above the per-channel median noise floor.
Peaks coinciding with a dominant resonance of the sensor chain's free-decay impulse response are additionally **flagged as sensor resonances** — a property of the piezo, not a plant emission.


## Sensor Resonances (from impulse response)

Dominant peaks in the free-decay spectrum of the sensor chain (±1.0 kHz tolerance used for exclusion):

- 5.46 kHz
- 8.26 kHz
- 13.49 kHz
- 17.58 kHz
- 25.05 kHz
- 28.91 kHz
- 35.16 kHz
- 37.36 kHz
- 38.70 kHz
- 41.69 kHz
- 50.01 kHz
- 71.35 kHz
- 82.52 kHz
- 88.80 kHz
- 91.63 kHz


## Repeatability Summary per Channel


**CH1 (amplified, LM358)**  
Repeatable peaks (≥40%, excl. mains): 48
| Frequency (kHz) | Repeatability | Mean Prominence (dB) |
|---|---|---|
| 70.92 | 100% | 47.0 |
| 4.66 | 89% | 31.6 |
| 9.18 | 68% | 23.7 |
| 66.20 | 63% | 23.3 |
| 56.92 | 47% | 20.6 |
| 80.16 | 42% | 19.2 |
| 93.11 | 42% | 18.9 |
| 30.84 | 47% | 18.4 |

**CH2 (820 kΩ)**  
Repeatable peaks (≥40%, excl. mains): 45
| Frequency (kHz) | Repeatability | Mean Prominence (dB) |
|---|---|---|
| 70.92 | 100% | 51.5 |
| 52.10 | 68% | 20.3 |
| 61.98 | 63% | 19.5 |
| 57.05 | 53% | 19.5 |
| 47.02 | 47% | 19.4 |
| 10.25 | 42% | 19.3 |
| 30.05 | 47% | 18.9 |
| 17.87 | 47% | 18.7 |

**CH3 (direct)**  
Repeatable peaks (≥40%, excl. mains): 55
| Frequency (kHz) | Repeatability | Mean Prominence (dB) |
|---|---|---|
| 70.91 | 100% | 39.2 |
| 25.01 | 47% | 18.9 |
| 17.07 | 42% | 18.5 |
| 86.99 | 53% | 18.5 |
| 42.05 | 42% | 17.7 |
| 38.84 | 42% | 17.7 |
| 21.06 | 63% | 17.3 |
| 33.83 | 47% | 17.2 |

## Key Findings

Across 19 captures per channel, **8 peak(s)** met all criteria without matching a known sensor resonance, and **6 peak(s)** met the criteria but coincide with a sensor resonance.


**None of these peaks can be attributed to the plant from this passive measurement.** Two reasons:

1. *Cross-channel agreement is ambiguous in a passive baseline.* The coherence criterion rules out sensor-*specific* artefacts, but a tone shared by several channels is equally the signature of common-mode pickup (mains-adjacent, switching-supply, or environmental vibration) conducted into every channel.
2. *The peaks have the wrong morphology for cavitation.* They are sharp, persistent tones reproduced at up to 100 % across 19 captures spanning minutes — the opposite of the sparse, broadband, transient bursts expected from xylem-cavitation acoustic emission.

The parsimonious interpretation is that these peaks characterise the **measurement chain plus environment**, not plant emission. They are listed below as reproducible spectral features — useful as a reference floor to subtract in a later excitation contrast.


**Reproducible cross-channel peaks** (passed all criteria; not attributed to the plant):

- 4.29 kHz — SNR 27.6 dB, repeatability 89%, CH1+CH3
- 10.11 kHz — SNR 10.4 dB, repeatability 47%, CH2+CH3
- 66.50 kHz — SNR 10.0 dB, repeatability 63%, CH1+CH2
- 16.01 kHz — SNR 8.4 dB, repeatability 63%, CH1+CH2
- 75.79 kHz — SNR 7.8 dB, repeatability 58%, CH1+CH3
- 74.72 kHz — SNR 6.6 dB, repeatability 63%, CH2+CH3
- 20.32 kHz — SNR 5.6 dB, repeatability 58%, CH1+CH2
- 21.39 kHz — SNR 5.5 dB, repeatability 63%, CH2+CH3

**Sensor resonances present in the signal** (excluded from the list above):

- 70.92 kHz — SNR 33.1 dB, CH1+CH2+CH3
- 9.03 kHz — SNR 19.1 dB, CH1+CH2+CH3
- 14.05 kHz — SNR 12.4 dB, CH1+CH2
- 13.07 kHz — SNR 11.8 dB, CH1+CH3
- 7.52 kHz — SNR 11.0 dB, CH2+CH3
- 17.63 kHz — SNR 7.0 dB, CH1+CH2+CH3

These are properties of the piezo sensor (confirmed by the free-decay impulse response), not of the plant.


## Validated Peaks (all criteria met)

| Rank | Frequency (kHz) | SNR (dB) | Repeatability | Channels | Sensor resonance? |
|---|---|---|---|---|---|
| 1 | 70.92 ± 0.250 | 33.1 | 100% | CH1, CH2, CH3 | YES (sensor) |
| 2 | 4.29 ± 0.250 | 27.6 | 89% | CH1, CH3 | no |
| 3 | 9.03 ± 0.250 | 19.1 | 68% | CH1, CH2, CH3 | YES (sensor) |
| 4 | 14.05 ± 0.250 | 12.4 | 68% | CH1, CH2 | YES (sensor) |
| 5 | 13.07 ± 0.250 | 11.8 | 47% | CH1, CH3 | YES (sensor) |
| 6 | 7.52 ± 0.250 | 11.0 | 47% | CH2, CH3 | YES (sensor) |
| 7 | 10.11 ± 0.250 | 10.4 | 47% | CH2, CH3 | no |
| 8 | 66.50 ± 0.250 | 10.0 | 63% | CH1, CH2 | no |
| 9 | 16.01 ± 0.250 | 8.4 | 63% | CH1, CH2 | no |
| 10 | 75.79 ± 0.250 | 7.8 | 58% | CH1, CH3 | no |
| 11 | 17.63 ± 0.250 | 7.0 | 63% | CH1, CH2, CH3 | YES (sensor) |
| 12 | 74.72 ± 0.250 | 6.6 | 63% | CH2, CH3 | no |
| 13 | 20.32 ± 0.250 | 5.6 | 58% | CH1, CH2 | no |
| 14 | 21.39 ± 0.250 | 5.5 | 63% | CH2, CH3 | no |

## Limitations

- **CH1 amplitude is not calibrated**: LM358 gain, bias, and supply quality are unknown, so CH1 amplitudes are not physical voltages at the piezo.
- **Cross-channel amplitudes are not directly comparable**: the sensors differ in mechanical coupling (steel rod vs. 0.8 mm plate) and electronics.
- **Frequency estimates are valid only within the acquired bandwidth** (20 Hz – 100 kHz) at the stated 250.00 Hz resolution.
- **Passive baseline**: no deliberate mechanical or physiological excitation was applied; this characterizes the resting spectral content of the measurement chain plus environment, not stimulus-evoked plant emission.


## Methodological Notes

25.00 MSa/s with 100,000 points gives a 4 ms window and 250.00 Hz periodogram bin spacing. The Nyquist frequency (12500 kHz) covers the full plant AE band (literature: ~1–100 kHz for xylem cavitation), so no software decimation is applied.

Deep-memory readout from the DS1104Z is bandwidth-limited (~25 kB/s) and capped at 250 000 points per request; the waveform is paged out in chunks (see `scope.instrument.acquire_waveform_full`). For finer resolution at the cost of readout time, re-acquire with `--memory-depth 3000000` (6 s window, 0.17 Hz, ~6 min/capture).

Anti-aliasing: never downsample by striding; use `scipy.signal.decimate` or `resample_poly`.


## Recommended Next Measurement

1. **Controlled-excitation contrast** — repeat this acquisition while applying a light tap to the steel rod / plate and compare against the quiet baseline to separate stimulus-evoked peaks from continuous background.
2. **Drought / watering contrast** — acquire over a dry-down vs. watered cycle to test whether candidate peaks track the plant's water status.
