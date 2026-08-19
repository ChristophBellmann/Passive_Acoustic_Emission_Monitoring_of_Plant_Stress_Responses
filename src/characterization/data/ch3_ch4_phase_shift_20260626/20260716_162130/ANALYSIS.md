# CH3/CH4 MEMS TDE analysis — run 20260716_162130

## Measurement context

- CH3 and CH4: MEMS microphones outside the soil, in air, just above the soil surface.
- Role: air/environment reference near the plant; this run does not measure propagation through soil or plant tissue.
- Acquisition: 20 synchronized frames, 500 kSa/s, 300,000 samples per channel, 0.6 s per frame.
- Analysis band: 20–100 kHz. Positive delay means CH4 lags CH3.

## Results

| Metric | Result |
|---|---:|
| Completed frames | 20/20 |
| Frames within ±1 µs | 17/20 (85%) |
| High-confidence frames (GCC confidence ≥ 5) | 17/20 |
| High-confidence delay median | 0.000 µs |
| High-confidence delay mean | −0.088 µs |
| High-confidence delay standard deviation | 0.147 µs |
| High-confidence delay range | −0.500 to 0.000 µs |
| Low-confidence outliers | −200.00, −43.75, +195.25 µs |
| Frames with phase-band candidates | 9/20 |
| Total phase-band candidates | 13 |

The three large GCC-PHAT delays all have low confidence (3.19–3.96); one hits the configured −200 µs search boundary. They are treated as ambiguous correlation peaks rather than physical propagation estimates.

The phase-band candidates occur predominantly near the upper analysis boundary (roughly 90–100 kHz). Their per-band delay uncertainties are about 196–322 µs, far larger than their fitted delays (mostly within ±2 µs, with one 3.19 µs result). They therefore do not provide a stable phase-slope TDE estimate.

## Interpretation

This air-reference run shows nearly simultaneous signals on CH3 and CH4 in the reliable frames. It does **not** provide evidence for a reproducible inter-MEMS propagation delay attributable to plant acoustic emission. The near-zero delay is consistent with common-mode pickup, a distant airborne source, or signals arriving almost simultaneously at the two closely spaced microphones.

For a plant-AE claim, compare this reference against a controlled geometry with one sensor mechanically coupled to the plant/soil and a time-locked event or impulse. A repeatable delay inside the physically expected window (6.25–100 µs for the configured 10 mm and 100–1600 m/s assumptions), absent from this air reference, would be stronger evidence.
