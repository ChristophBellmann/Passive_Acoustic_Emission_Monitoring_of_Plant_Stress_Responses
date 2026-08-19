# Raspberry Pi power-supply A/B comparison

## Runs

| State | Power supply | Run |
|---|---|---|
| Before | Original Raspberry Pi power supply | `20260714_215434` |
| After | Laptop power supply | `20260714_221000` |

Both runs used three synchronized 0.6 s frames, 500 kSa/s, 300,000 points,
the same sensor positions and the same oscilloscope profile. No channel clipped
and neither run contains Home Assistant, watering or temperature data.

## Result at the common interference line

| Channel | Before frequency (Hz) | After frequency (Hz) | Shift (Hz) | PSD change (dB) | RMS change |
|---:|---:|---:|---:|---:|---:|
| CH1 Piezo | 5393.3 | 5358.3 | -35.0 | +0.96 | +0.5% |
| CH3 MEMS | 5393.3 | 5358.3 | -35.0 | +0.92 | -10.9% |
| CH4 MEMS | 5393.3 | 5358.3 | -35.0 | +0.94 | -8.6% |

The harmonic comb remained present after the replacement and shifted with the
fundamental. Its first five lines moved from approximately 5.393, 10.787,
16.180, 21.573 and 26.967 kHz to 5.358, 10.717, 16.075, 21.433 and 26.792 kHz.
The individual harmonic peaks did not decrease; they were roughly 1--2 dB
stronger in the after run.

Mean coherence at the actual fundamental remained essentially one:

| Pair | Original Raspberry Pi PSU | Laptop PSU |
|---|---:|---:|
| CH1--CH3 | 0.99998 | 0.99996 |
| CH1--CH4 | 0.99998 | 0.99996 |
| CH3--CH4 | 0.99998 | 0.99995 |

## Interpretation

Replacing the original Raspberry Pi power supply with the laptop power supply
did **not** remove or reduce the 5.39 kHz interference. The original supply is
therefore not the sole source of the comb.

The simultaneous 35 Hz frequency shift on all three channels after changing
only the power supply is evidence that the power-delivery path influences the
interference. It does not yet distinguish between the external supply, a
converter or load inside the Raspberry Pi, shared-ground coupling, or another
device whose operating point changes with the supply. One A/B pair is not
sufficient for a strong causal claim.

Useful next isolation steps are, one at a time:

1. repeat with a suitable battery/power bank, if it can power the Raspberry Pi
   safely and stably;
2. leave the Raspberry Pi supply unchanged and disable/disconnect the
   Pico/actuator;
3. isolate or separately power the sensor amplifier chain;
4. repeat each state to test whether the line frequency follows the power
   condition reproducibly.

The complete numerical comparison is stored in
`power_supply_comparison.json`.
