# Phase-3 Pico sweep calibration

This directory preserves the calibration of the two amplified MEMS microphone
channels after the measurement setup was relocated. The procedure follows the
frequency-sweep method from archived notebook NB11, but is implemented as the
repeatable command-line script `scripts/calibrate_pico_sweep_phase3.py`.

## Wiring and acquisition

During calibration, oscilloscope CH1 is temporarily disconnected from the
Piezo amplifier and connected to Pico GP14 (physical pin 19). GP14 supplies the
positive transition marker used to trigger each capture. Pico GP15 (physical
pin 20) drives the actuator. Pico and oscilloscope grounds must be connected.

| Oscilloscope channel | Calibration signal | Probe/configuration |
|---|---|---|
| CH1 | Pico GP14 transition marker | DC, 10x, 1 V/div, +1 V trigger |
| CH3 | MEMS microphone through existing LM amplifier | AC, 10x, 0.5 V/div |
| CH4 | MEMS microphone through existing LM amplifier | AC, 10x, 0.5 V/div |

The Pico firmware sweeps 5--100 kHz in 5 kHz steps and holds each band for
1.5 s. Run the acquisition from the repository root with:

```bash
.venv/bin/python scripts/calibrate_pico_sweep_phase3.py --captures 80
```

The script detects the current sweep position spectrally, rejects invalid
waveform transfers, calculates amplitude, SNR, CH3--CH4 coherence and time-delay
estimates, and restores the normal Phase-3 oscilloscope state even when an error
occurs. Afterward, physically remove GP14 from CH1 and reconnect the CH1 Piezo
amplifier; software restoration cannot restore this cable connection.

Phase 3 has no Home Assistant connection. Consequently, this calibration has
no temperature record, automatic watering event or associated environmental
metadata.

## Valid run: 2026-07-14 17:55 local time

Run `20260714_175557` acquired 80 valid frames in 86 attempts. Six attempts
were skipped because the Rigol returned an empty waveform over its LAN
connection. The complete numerical results and interpretation are in
`20260714_175557/calibration_report.md`; the raw per-frame values remain in
`records.jsonl`.

The acceptance rule requires at least three frames, mean SNR >= 3 on both MEMS
channels and CH3--CH4 coherence >= 0.9. It accepts the following **discrete
measurement points**:

- 5, 10, 20, 25, 30 and 35 kHz

This must not be reported as one continuous 5--35 kHz calibrated band: 15 kHz
fails the SNR threshold. The 40 kHz point is coherent but noise-limited, and
frequencies above 40 kHz are not supported as a calibrated range by this run.
The most robust responses are at 10 and 30 kHz. The high coefficients of
variation at 5, 20, 25 and 30 kHz remain an uncertainty limitation for
quantitative comparisons.

## Lessons learned

- The physical oscilloscope probe on CH1 is 10x. Configuring CH1 as 1x makes
  the displayed GP14 marker and trigger level inconsistent and prevents stable
  triggering after the first transition.
- The Rigol DS1104Z can intermittently return an empty waveform via LAN even
  though acquisition completed. Each channel transfer therefore needs retries,
  and an invalid frame must not advance the count of valid captures.
- Scalar JSON records alone are insufficient to reconstruct the implemented
  coherence and phase aggregation. A run is complete only after
  `calibration_summary.json` has been generated from the accumulated complex
  cross spectra.
- Sweep-band assignment must be synchronized from the microphone spectrum;
  assuming that acquisition begins at 5 kHz can label every later frame with
  the wrong frequency.
- The oscilloscope memory depth is restored explicitly to 300,000 points after
  calibration. With the normal 50 ms/div timebase this gives 500 kSa/s in the
  restored Phase-3 setup.
- CH3 and CH4 track one another closely, which supports their use as a paired
  MEMS measurement. High coherence alone is not enough: SNR and repeatability
  must be checked independently.

## Diagnostic runs

The earlier timestamped directories are retained as troubleshooting
provenance and are marked with `INCOMPLETE.txt`. They must not be mixed with
the valid calibration:

- `20260714_174949`: incorrect 1x marker-probe configuration;
- `20260714_175140`: stopped on an empty CH3 waveform transfer;
- `20260714_175238`: 80 scalar frames acquired, but complex spectral
  aggregation was not preserved, so phase and coherence are invalid.
