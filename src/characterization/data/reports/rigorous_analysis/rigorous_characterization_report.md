
# Rigorous Plant Acoustic Emission Frequency Characterization

**Date of measurement:** 2026-06-21  
**Analysis date:** 2026-06-22 12:53:36  
**Script:** `rigorous_frequency_analysis.py`


## Data and Method

Raw captures: `data/plant_ae_optimized/20260621_200339/raw/`  
Channels: CH1 (amplified, LM358), CH2 (820 kΩ), CH3 (direct piezo)  
Captures per channel: 19 × 3  
Sample rate: 25.0 MSa/s  
Capture window: 4.0 ms  
**Frequency resolution: 250 Hz (bin spacing of the periodogram)**  
Analysis bandwidth: 20 Hz – 100 kHz  


Peak validity requires ALL three criteria:
1. **Repeatability** ≥40% of captures per channel.
2. **Cross-channel coherence**: frequency within ±1.0 kHz on ≥ 2 channels.
3. **Impulse-response exclusion**: NOT matching a dominant peak in the free-decay spectrum of the same sensor chain (sensor resonance test).


## Sensor Resonances (from impulse response)

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


**CH1** (CH1 (amplified, LM358))  
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

**CH2** (CH2 (820 kΩ))  
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

**CH3** (CH3 (direct))  
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

The three-step validation procedure (repeatability, cross-channel coherence, impulse-response exclusion) yields two categories of peaks:

**Category A – Sensor resonances:** Peaks that appear reproducibly in both the plant measurements AND the free-decay impulse response of the sensor chain.  The strongest example is the **71 kHz peak** (SNR = 33 dB, all three channels, 100 % repeatability), which was incorrectly labelled a 'novel plant AE finding' in earlier characterization reports.  It is a mechanical resonance of the piezoelectric element.  The plant IS generating acoustic activity – it excites the sensor resonance – but 71 kHz is a property of the sensor, not of the plant emission.

**Category B – Tentative plant AE candidates:** Peaks that pass all criteria and are NOT matched by a known sensor resonance.  The most prominent is the **4.3 kHz peak** (SNR = 28 dB, 89 % repeatability, CH1 + CH3).  However, this peak is absent on CH2 (820 kΩ), which shares neither the LM358 amplifier (CH1) nor the direct-connection topology (CH3).  A common electrical path or ground loop between CH1 and CH3 cannot be excluded from the current data; the peak should be regarded as *tentative* until a CH2-positive observation or a spatial correlation measurement confirms its mechanical origin.  Weaker multi-channel candidates exist in the 10–25 kHz range, consistent with xylem cavitation literature (1–50 kHz).

**Critical limitation:** The 4 ms capture window (250 Hz frequency resolution) makes it impossible to separate slowly modulated plant signals from transient environmental vibration.  Confirmed plant AE characterization requires captures of at least 1 s duration at a reduced sample rate.


## Validated Peaks (all three criteria met)

| Rank | Frequency (kHz) | SNR (dB) | Repeatability | Channels | Resonance? |
|---|---|---|---|---|---|
| 1 | 70.92 ± 0.25 | 33.1 | 100% | CH1, CH2, CH3 | YES (sensor) |
| 2 | 4.29 ± 0.25 | 27.6 | 89% | CH1, CH3 | no |
| 3 | 9.03 ± 0.25 | 19.1 | 68% | CH1, CH2, CH3 | YES (sensor) |
| 4 | 14.05 ± 0.25 | 12.4 | 68% | CH1, CH2 | YES (sensor) |
| 5 | 13.07 ± 0.25 | 11.8 | 47% | CH1, CH3 | YES (sensor) |
| 6 | 7.52 ± 0.25 | 11.0 | 47% | CH2, CH3 | YES (sensor) |
| 7 | 10.11 ± 0.25 | 10.4 | 47% | CH2, CH3 | no |
| 8 | 66.50 ± 0.25 | 10.0 | 63% | CH1, CH2 | no |
| 9 | 16.01 ± 0.25 | 8.4 | 63% | CH1, CH2 | no |
| 10 | 75.79 ± 0.25 | 7.8 | 58% | CH1, CH3 | no |
| 11 | 17.63 ± 0.25 | 7.0 | 63% | CH1, CH2, CH3 | YES (sensor) |
| 12 | 74.72 ± 0.25 | 6.6 | 63% | CH2, CH3 | no |
| 13 | 20.32 ± 0.25 | 5.6 | 58% | CH1, CH2 | no |
| 14 | 21.39 ± 0.25 | 5.5 | 63% | CH2, CH3 | no |

## Methodological Notes

**Frequency resolution constraint:**  
The oscilloscope was configured at 25 MSa/s with 100 000 points, yielding a
4 ms capture window.  The resulting periodogram bin spacing is **250 Hz**.  
All frequency estimates carry a systematic uncertainty of ±250 Hz;
sub-bin quadratic interpolation reduces the random centroid error but cannot
improve the fundamental resolution limit.

**Recommended future configuration:**  
Set the oscilloscope to 250 kSa/s with ≥250 000 points (≥1 s window).  
This achieves 1 Hz frequency resolution while keeping Nyquist at 125 kHz,
covering the full plant AE range.  File size per capture: ≈ 2 MB (float32),
reduced from ≈ 1.6 MB at 25 MSa/s for the same information content.

**Anti-aliasing:**  
Do not downsample by striding; use `scipy.signal.decimate` or `resample_poly`
to avoid aliasing of high-frequency noise into the analysis band.
