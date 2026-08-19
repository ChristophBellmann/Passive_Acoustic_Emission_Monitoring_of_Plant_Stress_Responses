# Phase-3 MEMS characterisation (lettuce-plant setup)

Raw data evaluated directly: frequency sweep `20260714_175557` (records.jsonl) and passive noise run `20260714_221000` (3 deep-memory frames). Coherence and MLE time-delay recomputed from the raw complex FFT bins with the same estimators as the piezo characterisation.

## Frequency sweep (CH3/CH4 MEMS)

| f (kHz) | N | CH3 (mV) | CH4 (mV) | SNR3 | SNR4 | coherence | TDE (us) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 4 | 15.18 | 13.98 | 5.1 | 5.0 | 0.9783 | +3.378 |
| 10 | 5 | 99.03 | 91.65 | 38.3 | 38.2 | 0.9997 | +0.357 |
| 15 | 4 | 7.28 | 6.44 | 2.7 | 2.5 | 0.9606 | -1.024 |
| 20 | 4 | 27.43 | 25.41 | 9.5 | 9.7 | 0.9797 | +0.202 |
| 25 | 4 | 15.94 | 15.11 | 5.3 | 5.5 | 0.9623 | +1.178 |
| 30 | 4 | 74.05 | 69.52 | 26.7 | 27.1 | 0.9972 | -0.012 |
| 35 | 3 | 10.42 | 9.95 | 3.5 | 3.6 | 0.9970 | -0.163 |
| 40 | 4 | 6.56 | 6.28 | 2.1 | 2.2 | 0.9812 | -0.411 |
| 45 | 4 | 5.71 | 5.47 | 1.9 | 1.9 | 0.9721 | -0.059 |
| 50 | 5 | 3.43 | 3.65 | 1.1 | 1.3 | 0.8629 | +0.727 |
| 55 | 5 | 4.60 | 4.57 | 1.5 | 1.6 | 0.9702 | -0.167 |
| 60 | 4 | 5.63 | 5.50 | 2.0 | 2.1 | 0.9824 | +0.042 |
| 65 | 4 | 4.95 | 4.13 | 1.6 | 1.5 | 0.9253 | +0.067 |
| 70 | 4 | 1.86 | 1.89 | 0.6 | 0.6 | 0.2760 | -1.055 |
| 75 | 3 | 2.24 | 2.11 | 0.8 | 0.8 | 0.7469 | +0.610 |
| 80 | 4 | 1.29 | 1.40 | 0.5 | 0.5 | 0.0330 | -2.163 |
| 85 | 4 | 1.76 | 1.74 | 0.6 | 0.6 | 0.7058 | -0.824 |
| 90 | 3 | 1.42 | 1.57 | 0.5 | 0.5 | 0.4576 | +0.583 |
| 95 | 4 | 1.38 | 2.00 | 0.5 | 0.7 | 0.6432 | -0.194 |
| 100 | 4 | 1.48 | 1.65 | 0.5 | 0.6 | 0.1402 | +0.618 |

Calibrated band (coherence >= 0.9, SNR >= 3.0 on both): **5, 10, 20, 25, 30, 35 kHz**, i.e. up to ~35 kHz. Time-delay across the reliable bands: -0.16 to +3.38 us (mean +0.82 us), consistent with near-equidistant MEMS placement.

## Passive noise floor (per 5 kHz band, mV RMS)

| Band (kHz) | CH1 piezo | CH3 MEMS A | CH4 MEMS B |
|---:|---:|---:|---:|
| 0-5 | 1.22 | 13.51 | 11.87 |
| 5-10 | 29.58 | 65.03 | 60.09 |
| 10-15 | 16.23 | 33.02 | 30.70 |
| 15-20 | 10.36 | 20.23 | 19.11 |
| 20-25 | 7.93 | 13.60 | 13.02 |
| 25-30 | 5.59 | 9.86 | 9.33 |
| 30-35 | 4.47 | 7.49 | 7.15 |
| 35-40 | 3.34 | 5.97 | 5.72 |
| 40-45 | 3.30 | 4.92 | 4.78 |
| 45-50 | 3.11 | 4.24 | 4.14 |
| 50-55 | 2.66 | 3.67 | 3.61 |
| 55-60 | 2.26 | 3.25 | 3.10 |

Total AC RMS: CH1 39.1 mV, CH3 80.9 mV, CH4 75.1 mV. The MEMS channels are dominated by a common-mode harmonic comb (fundamental ~5.36 kHz) in the 5-10 kHz band, coherent across all channel pairs (line coherence > 0.999). A controlled power-supply A/B swap shifted the comb by -35 Hz (5393->5358 Hz) but did not remove it: the original Raspberry Pi supply is thus not the sole source, yet the supply-tracking frequency shift shows the power-delivery path influences the artefact. The exact coupling source is not yet isolated. It is an instrumentation artefact, not a biological signal.
