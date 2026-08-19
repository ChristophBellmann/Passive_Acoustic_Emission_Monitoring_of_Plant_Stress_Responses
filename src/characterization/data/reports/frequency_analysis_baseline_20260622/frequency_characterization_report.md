
# Plant Acoustic Emission Frequency Characterization

> **⚠ Phase 1 report (pre-CH2-defect).** This analysis was performed on 2026-06-22 16:59 using the **Phase 1 setup: CH1 + CH2 + CH3** (CH2 = Piezo on 0.8 mm stainless-steel plate, 1:1 probe). On 2026-06-22 CH2 suffered a hardware fault and was replaced by CH4. **Cross-channel conclusions from this report are not directly applicable to current Phase 2 (CH1+CH3+CH4) measurements.** See `experiment_continuous_plant_ae_20260622/HARDWARE_CHANGELOG.md` for the full setup history.

**Analysis date:** 2026-06-22 16:59:22  
**Raw data:** `data/long_captures/20260622_163645/raw`  
**Impulse reference:** `data/impulse_response/20260621_182730/raw`  
**Script:** `frequency_analysis.py`


## Data and Method

Channels: CH1 (piezo + LM358 amplifier + 820 kΩ, 10:1 probe, uncalibrated gain), CH2 (piezo + 820 kΩ, 1:1 probe), CH3 (piezo direct, 1:1 probe)  [Phase 1 setup, pre-CH2-defect]
Captures per channel: 20  
Sample rate: 500 kSa/s (Nyquist 250 kHz)  
Capture window: 600 ms  
**Frequency resolution: 1.67 Hz** (periodogram bin spacing)  
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
Repeatable peaks (≥40%, excl. mains): 36
| Frequency (kHz) | Repeatability | Mean Prominence (dB) |
|---|---|---|
| 26.94 | 85% | 76.3 |
| 4.61 | 100% | 66.5 |
| 54.11 | 50% | 62.7 |
| 53.04 | 60% | 59.4 |
| 81.12 | 55% | 59.1 |
| 26.05 | 75% | 52.4 |
| 9.30 | 100% | 51.8 |
| 0.90 | 100% | 50.0 |

**CH2 (820 kΩ)**  
Repeatable peaks (≥40%, excl. mains): 30
| Frequency (kHz) | Repeatability | Mean Prominence (dB) |
|---|---|---|
| 26.97 | 100% | 81.7 |
| 81.17 | 50% | 77.5 |
| 54.11 | 50% | 75.4 |
| 53.04 | 55% | 70.5 |
| 1.98 | 100% | 63.7 |
| 0.90 | 100% | 60.1 |
| 2.91 | 100% | 59.6 |
| 3.92 | 100% | 56.1 |

**CH3 (direct)**  
Repeatable peaks (≥40%, excl. mains): 27
| Frequency (kHz) | Repeatability | Mean Prominence (dB) |
|---|---|---|
| 0.81 | 100% | 69.8 |
| 26.91 | 80% | 66.0 |
| 3.03 | 100% | 60.8 |
| 1.90 | 100% | 59.6 |
| 3.92 | 95% | 55.4 |
| 5.07 | 100% | 51.9 |
| 6.07 | 100% | 51.4 |
| 7.97 | 100% | 50.4 |

## Key Findings

Across 20 captures per channel, **8 peak(s)** met all criteria without matching a known sensor resonance, and **2 peak(s)** met the criteria but coincide with a sensor resonance.


**None of these peaks can be attributed to the plant from this passive measurement.** Two reasons:

1. *Cross-channel agreement is ambiguous in a passive baseline.* The coherence criterion rules out sensor-*specific* artefacts, but a tone shared by several channels is equally the signature of common-mode pickup (mains-adjacent, switching-supply, or environmental vibration) conducted into every channel.
2. *The peaks have the wrong morphology for cavitation.* They are sharp, persistent tones reproduced at up to 100 % across 20 captures spanning minutes — the opposite of the sparse, broadband, transient bursts expected from xylem-cavitation acoustic emission.

The parsimonious interpretation is that these peaks characterise the **measurement chain plus environment**, not plant emission. They are listed below as reproducible spectral features — useful as a reference floor to subtract in a later excitation contrast.


**Reproducible cross-channel peaks** (passed all criteria; not attributed to the plant):

- 0.87 kHz — SNR 26.7 dB, repeatability 100%, CH1+CH2+CH3
- 4.15 kHz — SNR 24.1 dB, repeatability 100%, CH1+CH2+CH3
- 2.19 kHz — SNR 23.9 dB, repeatability 100%, CH1+CH2+CH3
- 26.59 kHz — SNR 16.8 dB, repeatability 100%, CH1+CH2+CH3
- 54.11 kHz — SNR 11.1 dB, repeatability 50%, CH1+CH2
- 9.55 kHz — SNR 10.9 dB, repeatability 100%, CH1+CH2+CH3
- 53.04 kHz — SNR 9.2 dB, repeatability 60%, CH1+CH2+CH3
- 81.14 kHz — SNR 6.9 dB, repeatability 55%, CH1+CH2

**Update to the prior characterisation:** the 4.15 kHz peak now appears on all three channels at 100 % repeatability. The previous session reported a “4.3 kHz plant-AE candidate” visible only on CH1+CH3 (absent on CH2) and already flagged as a possible CH1–CH3 ground loop. Its presence on three electrically distinct channels strengthens a common-mode origin and **supersedes the earlier tentative plant-AE attribution**.


**Sensor resonances present in the signal** (excluded from the list above):

- 14.18 kHz — SNR 8.3 dB, CH1+CH2+CH3
- 8.25 kHz — SNR 6.2 dB, CH2+CH3

These are properties of the piezo sensor (confirmed by the free-decay impulse response), not of the plant.


## Validated Peaks (all criteria met)

| Rank | Frequency (kHz) | SNR (dB) | Repeatability | Channels | Sensor resonance? |
|---|---|---|---|---|---|
| 1 | 0.87 ± 0.002 | 26.7 | 100% | CH1, CH2, CH3 | no |
| 2 | 4.15 ± 0.002 | 24.1 | 100% | CH1, CH2, CH3 | no |
| 3 | 2.19 ± 0.002 | 23.9 | 100% | CH1, CH2, CH3 | no |
| 4 | 26.59 ± 0.002 | 16.8 | 100% | CH1, CH2, CH3 | no |
| 5 | 54.11 ± 0.002 | 11.1 | 50% | CH1, CH2 | no |
| 6 | 9.55 ± 0.002 | 10.9 | 100% | CH1, CH2, CH3 | no |
| 7 | 53.04 ± 0.002 | 9.2 | 60% | CH1, CH2, CH3 | no |
| 8 | 14.18 ± 0.002 | 8.3 | 95% | CH1, CH2, CH3 | YES (sensor) |
| 9 | 81.14 ± 0.002 | 6.9 | 55% | CH1, CH2 | no |
| 10 | 8.25 ± 0.002 | 6.2 | 100% | CH2, CH3 | YES (sensor) |

## Limitations

- **CH1 amplitude is not calibrated**: LM358 gain, bias, and supply quality are unknown, so CH1 amplitudes are not physical voltages at the piezo.
- **Cross-channel amplitudes are not directly comparable**: the sensors differ in mechanical coupling (steel rod vs. 0.8 mm plate) and electronics.
- **Frequency estimates are valid only within the acquired bandwidth** (20 Hz – 100 kHz) at the stated 1.67 Hz resolution.
- **Passive baseline**: no deliberate mechanical or physiological excitation was applied; this characterizes the resting spectral content of the measurement chain plus environment, not stimulus-evoked plant emission.


## Methodological Notes

500 kSa/s with 300,000 points gives a 600 ms window and 1.67 Hz periodogram bin spacing. The Nyquist frequency (250 kHz) covers the full plant AE band (literature: ~1–100 kHz for xylem cavitation), so no software decimation is applied.

Deep-memory readout from the DS1104Z is bandwidth-limited (~25 kB/s) and capped at 250 000 points per request; the waveform is paged out in chunks (see `scope.instrument.acquire_waveform_full`). For finer resolution at the cost of readout time, re-acquire with `--memory-depth 3000000` (6 s window, 0.17 Hz, ~6 min/capture).

Anti-aliasing: never downsample by striding; use `scipy.signal.decimate` or `resample_poly`.


## Recommended Next Measurement

1. **Controlled-excitation contrast** — repeat this acquisition while applying a light tap to the steel rod / plate and compare against the quiet baseline to separate stimulus-evoked peaks from continuous background.
2. **Drought / watering contrast** — acquire over a dry-down vs. watered cycle to test whether candidate peaks track the plant's water status.
