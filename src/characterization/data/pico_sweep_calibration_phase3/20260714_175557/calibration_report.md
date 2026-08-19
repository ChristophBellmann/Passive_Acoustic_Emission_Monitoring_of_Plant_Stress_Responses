# Phase-3 Pico sweep calibration

- Run: `20260714_175557`
- Instrument: Rigol DS1104Z, serial `DS1ZA201607099`
- Sensors: CH3 and CH4 MEMS microphones through the existing LM amplifier stages
- Excitation: Pico GP15, 5--100 kHz in 5 kHz steps
- Synchronisation: Pico GP14 on CH1, 10x probe
- Acquisition: 80 valid frames from 86 attempts; 6 empty waveform transfers rejected
- No Home Assistant, automatic watering, or temperature data

## Results

| f (kHz) | N | CH3 (mV) | CH4 (mV) | SNR CH3 | SNR CH4 | Coherence | TDE (us) | CV CH3 (%) | CV CH4 (%) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 | 4 | 15.178 | 13.982 | 5.1 | 5.0 | 0.9783 | +3.378 | 34.0 | 34.6 |
| 10 | 5 | 99.034 | 91.652 | 38.3 | 38.2 | 0.9997 | +0.357 | 4.1 | 4.1 |
| 15 | 4 | 7.278 | 6.437 | 2.7 | 2.5 | 0.9606 | -1.024 | 34.8 | 34.8 |
| 20 | 4 | 27.428 | 25.409 | 9.5 | 9.7 | 0.9797 | +0.202 | 22.3 | 20.3 |
| 25 | 4 | 15.945 | 15.107 | 5.3 | 5.5 | 0.9623 | +1.178 | 67.5 | 67.1 |
| 30 | 4 | 74.051 | 69.524 | 26.7 | 27.1 | 0.9972 | -0.012 | 19.8 | 19.5 |
| 35 | 3 | 10.425 | 9.953 | 3.5 | 3.6 | 0.9970 | -0.163 | 9.4 | 11.3 |
| 40 | 4 | 6.558 | 6.282 | 2.1 | 2.2 | 0.9812 | -0.411 | 48.3 | 46.1 |
| 45 | 4 | 5.706 | 5.473 | 1.9 | 1.9 | 0.9721 | -0.059 | 15.0 | 17.5 |
| 50 | 5 | 3.428 | 3.649 | 1.1 | 1.3 | 0.8629 | +0.727 | 49.3 | 45.1 |
| 55 | 5 | 4.598 | 4.570 | 1.5 | 1.6 | 0.9702 | -0.167 | 37.1 | 34.2 |
| 60 | 4 | 5.627 | 5.502 | 2.0 | 2.1 | 0.9824 | +0.042 | 35.9 | 36.0 |
| 65 | 4 | 4.949 | 4.134 | 1.6 | 1.5 | 0.9253 | +0.067 | 9.5 | 19.1 |
| 70 | 4 | 1.860 | 1.890 | 0.6 | 0.6 | 0.2760 | -1.055 | 33.6 | 37.7 |
| 75 | 3 | 2.236 | 2.112 | 0.8 | 0.8 | 0.7469 | +0.610 | 8.2 | 12.4 |
| 80 | 4 | 1.287 | 1.403 | 0.5 | 0.5 | 0.0330 | -2.163 | 40.3 | 33.6 |
| 85 | 4 | 1.763 | 1.737 | 0.6 | 0.6 | 0.7058 | -0.824 | 11.8 | 10.0 |
| 90 | 3 | 1.416 | 1.571 | 0.5 | 0.5 | 0.4576 | +0.583 | 22.4 | 10.3 |
| 95 | 4 | 1.383 | 1.995 | 0.5 | 0.7 | 0.6432 | -0.194 | 29.4 | 15.3 |
| 100 | 4 | 1.480 | 1.654 | 0.5 | 0.6 | 0.1402 | +0.618 | 29.2 | 29.8 |

## Interpretation

The automated acceptance rule (at least three frames, SNR >= 3 on both
channels, and coherence >= 0.9) accepts 5, 10, 20, 25, 30, and 35 kHz. The
15 kHz point is coherent but remains below the SNR threshold. The 40 kHz point
is also coherent but noise-limited. Frequencies above 40 kHz are not supported
as a calibrated measurement range by this run.

CH3 and CH4 show closely matching transfer responses. The strongest responses
occur at 10 and 30 kHz. Repeatability is best at 10 kHz; the large coefficients
of variation at 5, 20, 25, and 30 kHz must be retained as an uncertainty caveat
in quantitative comparisons.
