# Phase-3 soil sensor test

- Run: `20260714_215154`
- Location: sensors in soil next to the new plant at Julian's setup
- Acquisition: 3 synchronized frames, 0.6 s each, 500 kSa/s
- Attempts: 3; transfer errors: 0
- No Home Assistant, automatic watering or temperature record

## Electrical sanity check

| Channel | Sensor | Mean AC RMS (mV) | RMS SD (mV) | Max pp (mV) | Rail clipping |
|---:|---|---:|---:|---:|---:|
| CH1 | Piezo + LM amplifier | 83.060 | 0.528 | 554.785 | no |
| CH3 | MEMS A + LM amplifier | 1356.180 | 6.434 | 4255.625 | YES |
| CH4 | MEMS B + LM amplifier | 1137.887 | 44.757 | 4341.171 | YES |

## CH3/CH4 coherence at calibrated points

| Frequency (kHz) | Mean coherence | Minimum coherence |
|---:|---:|---:|
| 5 | 0.2775 | 0.1269 |
| 10 | 0.4493 | 0.3972 |
| 20 | 0.2916 | 0.1408 |
| 25 | 0.3633 | 0.3191 |
| 30 | 0.2130 | 0.0541 |
| 35 | 0.3020 | 0.1984 |

This short baseline verifies acquisition and electrical plausibility only. It cannot establish biological origin; that requires repeated measurements and controls over a longer observation period.
