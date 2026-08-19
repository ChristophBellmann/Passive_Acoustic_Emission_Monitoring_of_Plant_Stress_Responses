# Phase-3 soil sensor test

- Run: `20260714_215434`
- Location: sensors in soil next to the new plant at Julian's setup
- Acquisition: 3 synchronized frames, 0.6 s each, 500 kSa/s
- Attempts: 3; transfer errors: 0
- No Home Assistant, automatic watering or temperature record

## Electrical sanity check

| Channel | Sensor | Mean AC RMS (mV) | RMS SD (mV) | Max pp (mV) | Rail clipping |
|---:|---|---:|---:|---:|---:|
| CH1 | Piezo + LM amplifier | 38.943 | 0.065 | 265.332 | no |
| CH3 | MEMS A + LM amplifier | 90.843 | 10.497 | 967.188 | no |
| CH4 | MEMS B + LM amplifier | 82.093 | 7.931 | 839.453 | no |

## CH3/CH4 coherence at calibrated points

| Frequency (kHz) | Mean coherence | Minimum coherence |
|---:|---:|---:|
| 5 | 0.5429 | 0.4592 |
| 10 | 0.2484 | 0.1148 |
| 20 | 0.4004 | 0.3605 |
| 25 | 0.1249 | 0.0751 |
| 30 | 0.0654 | 0.0168 |
| 35 | 0.4281 | 0.4005 |

This short baseline verifies acquisition and electrical plausibility only. It cannot establish biological origin; that requires repeated measurements and controls over a longer observation period.

## Interpretation

All three channels acquired complete records without ADC-rail clipping. CH3 and
CH4 have comparable signal levels, and the Piezo signal on CH1 is stable across
the three frames. The sensor and acquisition chains are therefore operational.

The recording is not yet a clean soil baseline. All three channels contain a
strong line near 5.39 kHz and a harmonic comb at approximately 10.78, 16.17,
21.56 and 26.95 kHz. Coherence at these actual line frequencies is approximately
1.0 for both CH3--CH4 and CH1--CH3. Such nearly perfect synchronization across
the Piezo and both MEMS channels is evidence of a common electrical or
mechanical excitation, not evidence of a biological event.

Before interpreting plant signals, switch off or disconnect possible shared
sources one at a time (especially a still-running Pico/actuator, switching power
supply or shared-ground interference) and repeat this short test. A useful
baseline should substantially reduce the harmonic comb while retaining
non-clipped, plausible noise on all three channels.

## Planned Raspberry Pi power-supply test

Unlike the earlier setup on a workstation, Phase 3 now runs on a Raspberry Pi.
The run documented here is the **before measurement with the original
Raspberry Pi power supply connected**. Julian subsequently shut the Raspberry
Pi down cleanly and replaced it with a laptop power supply, with the specific
intention of testing whether the original supply causes the 5.39 kHz signal.
The full controlled-comparison protocol is documented in
`../POWER_SUPPLY_INTERVENTION.md`.
