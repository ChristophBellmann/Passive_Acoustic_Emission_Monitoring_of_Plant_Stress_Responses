# CH3/CH4 phase-shift experiment

Purpose: search for a coherent acoustic signal between the two amplified sensors
CH3 and CH4, which are about 10 mm apart with plant material between them.

The experiment is separate from the continuous characterization. It uses the same
synchronized Rigol deep-memory capture profile, but analyzes only CH3 and CH4:

- sample rate: 500 kSa/s by default, 2 us/sample
- memory depth: 300000 samples, 0.6 s per frame
- broadband delay: GCC-PHAT in a configurable lag window
- narrowband delay: cross-spectral phase slope in coherent frequency bands

Positive delay means CH4 lags CH3.

Run only when the continuous acquisition is stopped or when you intentionally want
this script to take over the oscilloscope configuration:

```bash
PYTHONPATH=instrument_control python experiment_ch3_ch4_phase_shift_20260626/ch3_ch4_phase_shift_experiment.py --frames 20
```

For auditability, save raw CH3/CH4 waveforms for each frame:

```bash
PYTHONPATH=instrument_control python experiment_ch3_ch4_phase_shift_20260626/ch3_ch4_phase_shift_experiment.py --frames 20 --save-raw
```

Outputs are written to `data/ch3_ch4_phase_shift_20260626/<run_id>/`:

- `summary.json`: run settings, per-frame delays, top phase-band candidates
- `phase_candidates.csv`: all coherent phase-band candidates
- `frame_XXXX_phase.png`: coherence and unwrapped phase plots per frame
- `raw/frame_XXXX_ch3_ch4.npz`: optional raw waveforms
