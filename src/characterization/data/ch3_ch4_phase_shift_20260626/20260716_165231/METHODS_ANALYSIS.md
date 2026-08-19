# MEMS-in-soil AE method suite — run 20260716_165231

## Setup

Both CH3 and CH4 MEMS microphones were inserted into soil. One was reported closer and one farther from the presumed source region, but the channel mapping and exact distances were not recorded. This was a passive run without a time-locked excitation event.

## Results

- 20/20 synchronized raw frames passed acquisition.
- Median RMS: CH3 306.79 mV; CH4 298.71 mV; CH4/CH3 -0.23 dB.
- Mean CH3–CH4 coherence in 20–100 kHz: 0.603; maximum 0.997 at 32.59 kHz.
- GCC-PHAT: median 0.000 µs across 20 frames.
- Phase-MLE bands with coherence >= 0.7: 14/16.
- First-half/second-half tests significant after FDR: 0/32.
- RMS trend: CH3 Kendall tau -0.253 (p=0.128); CH4 -0.358 (p=0.0283).
- Robust transient screening: CH3 10879 candidates, CH4 10883, 10392 CH3 candidates with a CH4 match within 200 µs.
- The roughly 544 detections per channel and frame are periodic and predominantly coincident; they are rejected as the existing line-comb/common-mode interference rather than isolated AE clicks.
- Frame 13 contains an additional CH3-only step from about +1.4 V to -2.54 V with no CH4 counterpart. Its discontinuity, sustained rail-level plateau, and filtering ring-down identify it as saturation/overflow or a channel fault, not plant AE.

## Decision

A plant acoustic-emission event is not established by this passive series. The frame-wise zero-delay result, the highly coherent 32.59 kHz line, the periodic transient count, and the rejected CH3 step all fail the AE validation gates. A positive claim requires a transient that is absent from baseline, repeats under a controlled event, appears plausibly on both sensors, and shows a physically plausible non-zero delay consistent with the recorded channel geometry.
