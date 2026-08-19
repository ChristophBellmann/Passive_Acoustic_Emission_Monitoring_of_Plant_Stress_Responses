# Raspberry Pi power-supply intervention

## Motivation

The Phase-3 measurement system now runs on a Raspberry Pi instead of the
previous workstation. This host change, including the Raspberry Pi power
supply, is new relative to the earlier experimental phases and is a plausible
source of the common 5.39 kHz harmonic comb observed on CH1, CH3 and CH4.

This is a hypothesis to be tested, not an established cause.

## Before state

- Date: 2026-07-14
- Reference run: `20260714_215434`
- Host: Raspberry Pi
- Power supply: original Raspberry Pi power supply (exact model/rating not yet
  recorded)
- Sensors: in soil next to the new plant at Julian's setup
- Channels: CH1 Piezo + LM amplifier; CH3/CH4 MEMS + LM amplifiers
- Oscilloscope profile: AC coupling, 10x probes, 0.5 V/div, 500 kSa/s,
  300,000 points, CH3 auto trigger at 20 mV
- Observation: a common line near 5.39 kHz and harmonics near 10.78, 16.17,
  21.56 and 26.95 kHz; coherence at the actual lines is approximately 1.0
  across the sensor channels
- Auxiliary data: no Home Assistant, automatic watering or temperature record

The reference run is the baseline **before** changing the Raspberry Pi power
supply. The earlier run `20260714_215154` is not a suitable baseline because
CH3 and CH4 were not powered.

## Planned intervention

Julian will shut the Raspberry Pi down cleanly and replace only its power
supply. The intention is to determine whether the 5.39 kHz line and its
harmonic comb originate from the current Raspberry Pi power supply.

For a controlled comparison, keep the following unchanged:

- sensor positions and soil contact;
- LM amplifier wiring and supply arrangement, except where inseparable from
  the Raspberry Pi supply under test;
- oscilloscope probes, channel settings and trigger profile;
- nearby actuator/Pico state and other electrical equipment;
- acquisition length and analysis method.

After the replacement, repeat three synchronized 0.6 s frames using the same
Phase-3 test procedure. Record the replacement power-supply manufacturer,
model and rating if available.

## Decision criteria

Compare the before and after runs using:

1. frequency and PSD amplitude of the line near 5.39 kHz;
2. amplitudes of its harmonics;
3. CH3--CH4 and CH1--CH3 coherence at the actual line frequencies;
4. broadband RMS and clipping state of all three channels.

A substantial disappearance or reduction of the line and harmonics after the
single power-supply change supports the power-supply hypothesis. An unchanged
comb argues against it. A frequency shift that follows the replacement supply
also supports a supply-related origin. One before/after pair is diagnostic but
should be repeated before making a strong causal claim.

## After state

Power-supply replacement confirmed after the Raspberry Pi restart on
2026-07-14 at approximately 22:08 CEST.

- Shutdown/restart time: completed before 2026-07-14 22:08 CEST
- Replacement power supply: laptop power supply (exact manufacturer/model/rating
  not yet recorded)
- Post-change run ID: `20260714_221000`
- Common-line frequency: 5393.3 Hz before; 5358.3 Hz after (-35.0 Hz)
- Common-line amplitude: approximately 0.9 dB stronger after the replacement on
  all three channels
- Harmonic-comb result: remained present, shifted with the fundamental, and did
  not decrease
- Coherence result: remained approximately 1.0 across all channel pairs at the
  actual line frequency
- Conclusion: the original Raspberry Pi power supply is not the sole source.
  The common frequency shift indicates that the power-delivery condition
  influences the artifact, but the exact coupling source is not yet isolated.
  See `POWER_SUPPLY_COMPARISON.md` for the numerical comparison.

## Restored operating state

After the A/B measurement, the laptop power supply was removed and the
original Raspberry Pi power supply was restored. The plant was then watered
manually immediately before starting the Phase-3 continuous long run. The
watering event is recorded separately under `../phase3_events/` and the
long-run session uses the restored original-supply state.
