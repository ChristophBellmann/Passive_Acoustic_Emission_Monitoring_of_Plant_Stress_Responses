# Phase-3 soil sensor test after power-supply replacement

- Run: `20260714_221000`
- Host: Raspberry Pi
- Power supply: laptop power supply
- Previous state: original Raspberry Pi power supply
- Acquisition: three valid synchronized 0.6 s frames at 500 kSa/s
- Transfer errors: none
- Rail clipping: none on CH1, CH3 or CH4
- No Home Assistant, automatic watering or temperature record

## Mean signal levels

| Channel | Sensor | Mean AC RMS (mV) | Maximum peak-to-peak (mV) |
|---:|---|---:|---:|
| CH1 | Piezo + LM amplifier | 39.128 | 265.332 |
| CH3 | MEMS A + LM amplifier | 80.941 | 628.672 |
| CH4 | MEMS B + LM amplifier | 75.061 | 551.641 |

## Interference observation

The common line and its harmonic comb remain present. The fundamental is now
at 5358.3 Hz on all three channels, compared with 5393.3 Hz using the original
Raspberry Pi power supply. CH3--CH4 coherence at the line is 0.99995; the other
channel pairs are similarly coherent. This remains a common artifact and must
not be interpreted as a biological signal.

See `../POWER_SUPPLY_COMPARISON.md` for the controlled before/after comparison.
