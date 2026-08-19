# CH3/CH4 Pump Arrival Phase-Shift Result
Run: `20260626_220641`

## Physical Target
- Sensor spacing: 10 mm.
- Expected delay for granular soil / plant coupling at 100-1600 m/s: 6.25-100 us.
- Amplifier bandwidth on CH3/CH4: usable only up to about 700 kHz. Frequencies above 700 kHz are not considered physically reliable for phase/TDE interpretation because amplifier roll-off and phase shift can dominate.
- Search bands used in this run: 20-100 kHz, 100-300 kHz, 300 kHz-1 MHz. The last band is therefore only valid up to 700 kHz and should be treated as a methodological overreach in this run.
- Capture: 250 MSa/s, 300000 samples, 1.2 ms per frame; pump pulse requested 3 ms via Home Assistant REST.

## Result
- No physically plausible CH3/CH4 propagation delay was found.
- Stable high-band delays are mostly sub-microsecond; interpreted as electrical/common-mode or very fast structural coupling, not propagation through the granular substrate between sensors.

## Per-Band Summary
- 20-100 kHz: delay median -0.774 us, range -0.951..-0.426 us, confidence median 13.03.
- 100-300 kHz: delay median 0.361 us, range 0.322..0.419 us, confidence median 17.40.
- 300-1000 kHz: delay median -0.038 us, range -0.782..0.027 us, confidence median 24.99. Note: only the 300-700 kHz part is within the stated amplifier bandwidth; content above 700 kHz should not be interpreted.

## Interpretation
A true 10 mm propagation path through Bims/granular soil should not produce an apparent velocity above several km/s. Most estimates imply >10 km/s, and coherent phase-band estimates also cluster near 0 us. Therefore this pump excitation did not reveal a measurable plant/substrate transit delay between CH3 and CH4.

## Method Correction
Future CH3/CH4 TDE runs should cap the analysis at 600-700 kHz, preferably using explicit bands such as 20-100 kHz, 100-300 kHz and 300-600 kHz. The 300 kHz-1 MHz band from this run is retained in the raw analysis record for transparency but should not be used as evidence above 700 kHz.
