# Instruction for Codex / Claude / OpenChat: Oscilloscope-Based Vibration Characterization Program

## Goal

Create a clean, scientific, config-driven Python program to characterize vibrations measured with a Rigol DS1104Z oscilloscope.

The program shall acquire waveform data from the oscilloscope, process two piezo-based measurement channels, identify physically plausible dominant frequencies, generate plots, run plausibility checks, and save reproducible analysis results.

The final result should be a maintainable repository that can be extended for later experiments on acoustic or vibration emissions from plants, soil, stainless-steel coupling structures, and piezo sensors.

---

## Measurement Setup

### Oscilloscope

Instrument:

```text
Model: Rigol DS1104Z
Manufacturer: RIGOL TECHNOLOGIES
Series: DS1000Z
Firmware: 00.04.04.SP3
IP address: 192.168.178.70
VISA TCP/IP string: TCPIP::192.168.178.70::INSTR
USB VISA string: USB0::0x1AB1::0x4CE::DS1ZA201607099::INSTR
Serial number: DS1ZA201607099
```

The program should primarily connect via LAN/VISA using:

```text
TCPIP::192.168.178.70::INSTR
```

Use `pyvisa` with a suitable VISA backend.

---

## Sensor Channels

### Channel 1

```text
Oscilloscope channel: CH1
Probe setting: 10:1
Sensor: Piezo attached to a stainless-steel rod
Signal chain:
    piezo
    → Millig LM358 amplifier board
    → oscilloscope probe CH1
```

Important uncertainties:

```text
LM358 gain: unknown
LM358 bias: unknown
LM358 supply voltage: unknown
Switching power supply quality: unknown
```

Known observation:

```text
The LM358 board visibly amplifies the piezo signal on CH1.
```

The software must therefore not assume calibrated amplitude on CH1. Frequency analysis is more important than absolute amplitude.

### Channel 2

> **STATUS (since 2026-06-22):** CH2 is **disabled** due to a hardware fault. It was replaced by **CH4** (see `plant_ae/watering.py:CHANNELS = (1, 3, 4)`). All current measurements use CH1, CH3, CH4. The original CH2 specification is kept below for historical reference only.

```text
Oscilloscope channel: CH2
Probe setting: 1:1
Sensor: Piezo directly connected
Mechanical coupling:
    piezo glued to a stainless-steel plate
    plate approximately business-card sized
    thickness approximately 0.8 mm
```

CH2 was a direct piezo measurement without amplifier. It had lower amplitude but less unknown electronic gain/bias.

### Channel 4 (replacement for CH2 since 2026-06-22)

```text
Oscilloscope channel: CH4
Probe setting: 10:1
Sensor: Piezo with amplifier + 820 kΩ
Mechanical coupling:
    piezo glued to a stainless-steel rod
    rod placed next to the plant
```

CH4 is the post-fault replacement for CH2. Both use the same amplifier topology but a different mechanical coupling (rod vs. plate), so resonances and amplitudes are not directly comparable to historical CH2 data.

---

## Scientific Objectives

The program shall answer:

```text
Which frequencies are present in each channel?
Which peaks are stable and physically plausible?
Which peaks are likely artifacts from electronics, mains noise, aliasing, clipping, or poor acquisition settings?
How do CH1 and CH3 compare? (Phase 2: CH1+CH3+CH4, CH2 disabled — see HARDWARE_CHANGELOG.md)
Are detected frequencies repeatable over multiple captures?
```

The program must generate evidence, not just one FFT plot.

---

## Required Repository Structure

Create a repository similar to:

```text
scoperation-characterization/
├── README.md
├── pyproject.toml
├── requirements.txt
├── configs/
│   ├── default.yaml
│   ├── rigol_ds1104z.yaml
│   └── experiment_piezo_stainless.yaml
├── src/
│   └── scope/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── instrument.py
│       ├── acquisition.py
│       ├── preprocessing.py
│       ├── spectral.py
│       ├── peak_detection.py
│       ├── plausibility.py
│       ├── plotting.py
│       ├── reporting.py
│       └── utils.py
├── scripts/
│   ├── acquire_once.py
│   ├── acquire_series.py
│   └── analyze_directory.py
├── data/
│   ├── raw/
│   ├── processed/
│   └── reports/
├── notebooks/
│   └── exploratory_analysis.ipynb
└── tests/
    ├── test_spectral.py
    ├── test_peak_detection.py
    └── test_plausibility.py
```

---

## Configuration-Driven Design

All experimental assumptions must be stored in YAML config files.

Example config fields:

```yaml
instrument:
  visa_resource: "TCPIP::192.168.178.70::INSTR"
  idn_expected_contains: "RIGOL"
  timeout_ms: 10000

oscilloscope:
  channels: [1, 2]
  channel_settings:
    1:
      enabled: true
      label: "piezo_rod_lm358"
      probe_ratio: 10
      coupling: "AC"
      vertical_scale_v_per_div: null
      offset_v: null
      amplitude_calibrated: false
      notes: "Piezo on stainless-steel rod through unknown LM358 amplifier board."
    2:
      enabled: true
      label: "piezo_plate_direct"
      probe_ratio: 1
      coupling: "AC"
      vertical_scale_v_per_div: null
      offset_v: null
      amplitude_calibrated: false
      notes: "Direct piezo on 0.8 mm stainless-steel plate."

acquisition:
  captures: 20
  delay_between_captures_s: 1.0
  memory_depth: "AUTO"
  waveform_mode: "RAW"
  waveform_format: "BYTE"
  auto_setup_allowed: false
  stop_before_read: true
  restore_run_after_read: true

processing:
  remove_dc: true
  detrend: true
  window: "hann"
  min_frequency_hz: 5
  max_frequency_hz: null
  welch:
    enabled: true
    nperseg: 4096
    overlap: 0.5
  stft:
    enabled: true
    nperseg: 2048
    overlap: 0.75

peak_detection:
  prominence_db: 8
  min_distance_hz: 20
  max_peaks: 20
  ignore_frequency_bands_hz:
    - [48, 52]
    - [98, 102]
    - [148, 152]
    - [198, 202]

plausibility:
  clipping_threshold_fraction: 0.98
  min_snr_db: 6
  repeatability_min_fraction: 0.4
  mains_frequencies_hz: [50, 100, 150, 200]
  switching_noise_check: true
  aliasing_check: true

output:
  save_raw_csv: true
  save_npz: true
  save_plots: true
  save_report_markdown: true
  plot_format: "png"
```

---

## Required Features

### 1. Instrument Connection

Implement robust connection handling:

```text
- Connect via pyvisa.
- Query *IDN?.
- Verify that the returned identity contains RIGOL and DS1104Z if possible.
- Print connection metadata.
- Fail cleanly if the oscilloscope is unreachable.
```

The program should support:

```bash
python -m scope.cli check-connection --config configs/experiment_piezo_stainless.yaml
```

---

### 2. Waveform Acquisition

Acquire waveform data from the active channel set (Phase 2: CH1, CH3, CH4 — CH2 disabled).

Important requirements:

```text
- Correctly read Rigol DS1000Z waveform preamble.
- Convert ADC byte values to real voltage values using the scope preamble.
- Save time vector and voltage vector.
- Store metadata with every capture.
- Support repeated captures.
- Do not rely on screenshots.
```

For each capture, save:

```text
timestamp
instrument IDN
channel number
channel label
probe ratio
sample interval
sample rate
record length
vertical scale
vertical offset
time scale
trigger settings if available
raw waveform
converted voltage waveform
```

Preferred storage:

```text
data/raw/YYYY-MM-DD_HH-MM-SS_capture_0001_ch1.npz
data/raw/YYYY-MM-DD_HH-MM-SS_capture_0001_ch2.npz
```

Also create optional CSV export for inspection.

---

### 3. Preprocessing

Implement preprocessing functions:

```text
- remove DC offset
- detrend signal
- optional high-pass filtering
- optional low-pass filtering
- windowing before FFT
- clipping detection
- flatline detection
- NaN/Inf checks
```

Do not permanently alter raw data. Save processed data separately.

---

### 4. Spectral Analysis

Implement at least:

```text
- single-shot FFT
- amplitude spectrum
- power spectral density
- Welch spectrum
- optional STFT/spectrogram
```

Frequency axis must be correct from actual sample interval, not guessed.

Use `scipy.signal` where appropriate.

Required plots:

```text
- time-domain signal per channel
- zoomed time-domain signal around strongest event
- FFT amplitude spectrum
- Welch PSD
- spectrogram if enabled
- peak summary plot with labeled detected frequencies
- CH1 vs CH3 comparison plot (Phase 2: CH1+CH3+CH4)
```

---

### 5. Peak Detection

Implement robust peak detection:

```text
- Detect local spectral peaks.
- Rank peaks by prominence and power.
- Ignore configured noise bands, especially 50 Hz mains harmonics.
- Report peak frequency, amplitude, prominence, bandwidth, Q estimate if possible.
- Compare peaks across repeated captures.
```

Peak output table:

```text
channel
capture_id
frequency_hz
amplitude
prominence_db
bandwidth_hz
q_factor
snr_db
is_mains_related
is_repeatable
plausibility_label
notes
```

---

### 6. Plausibility Tests

The software must not blindly accept FFT peaks.

Implement tests for:

```text
1. Clipping
   - Check whether signal reaches near ADC or scope vertical limits.

2. DC bias
   - Especially relevant for CH1 because the LM358 board may add unknown bias.

3. Saturation
   - Check whether signal is stuck near upper or lower range.

4. Mains noise
   - Mark peaks close to 50 Hz and harmonics.

5. Switching power supply noise
   - Detect stable narrow peaks that appear only on amplified CH1 but not CH2.

6. Aliasing risk
   - Check whether sample rate is high enough for the maximum reported frequency.

7. Repeatability
   - A frequency is more plausible if it appears in multiple captures.

8. Cross-channel support
   - A frequency is more plausible if it appears on at least two of the three active channels (CH1, CH3, CH4), but CH1-only frequencies are not automatically invalid because the sensors are mechanically different.
   - *Historical note:* until 2026-06-22 the active set was CH1+CH2+CH3. CH2 was disabled after a hardware fault and replaced by CH4. Cross-channel support statements from sessions that reference CH2 predate this change.

9. Mechanical plausibility
   - CH4 is mounted on a stainless-steel rod next to the plant; resonances may differ strongly from CH1 (also a rod, but with different coupling location) and CH3 (soil near plant).

10. Event-based plausibility
   - If a peak exists only during a transient event, mark it differently from continuous background noise.
```

Possible labels:

```text
plausible_mechanical
possible_mechanical
likely_mains_noise
likely_switching_noise
likely_electronic_artifact
likely_clipping_artifact
uncertain
```

---

### 7. Reporting

Generate a Markdown report automatically for each acquisition series:

```text
data/reports/YYYY-MM-DD_HH-MM-SS_report.md
```

The report should include:

```text
- experiment metadata
- oscilloscope settings
- sensor descriptions
- acquisition parameters
- time-domain summary
- spectral summary
- detected frequency table
- plausibility table
- comparison of CH1 and CH3 (Phase 2: CH1+CH3+CH4)
- plots linked as images
- warnings and limitations
- next recommended measurement settings
```

The report must clearly state:

```text
CH1 amplitude is not calibrated because the LM358 gain and bias are unknown.
CH2 amplitude is not necessarily directly comparable to CH1 because sensor geometry and coupling differ.
Frequency estimates are valid only within the acquired bandwidth and sample-rate limits.
```

---

## Command-Line Interface

Provide a CLI with commands:

```bash
python -m scope.cli check-connection --config configs/experiment_piezo_stainless.yaml

python -m scope.cli acquire \
  --config configs/experiment_piezo_stainless.yaml \
  --captures 20

python -m scope.cli analyze \
  --config configs/experiment_piezo_stainless.yaml \
  --input data/raw/latest

python -m scope.cli report \
  --config configs/experiment_piezo_stainless.yaml \
  --input data/processed/latest
```

A combined command is also useful:

```bash
python -m scope.cli run \
  --config configs/experiment_piezo_stainless.yaml \
  --captures 20
```

---

## Python Dependencies

Use common scientific Python packages:

```text
numpy
scipy
matplotlib
pandas
pyyaml
pyvisa
pyvisa-py
tqdm
rich
```

Optional:

```text
h5py
plotly
typer
pydantic
```

Prefer simple, reliable dependencies.

---

## Data Integrity Requirements

Every analysis result must be traceable to raw data.

For each generated plot or report table, store:

```text
input file names
config file used
processing parameters
timestamp
software version or git commit if available
```

Never overwrite raw data.

---

## Rigol DS1104Z Notes

Implement acquisition carefully for Rigol DS1000Z.

Typical SCPI commands may include:

```text
*IDN?
:STOP
:WAV:SOUR CHAN1
:WAV:MODE RAW
:WAV:FORM BYTE
:WAV:PRE?
:WAV:DATA?
:RUN
```

The exact parser should be tested with the actual preamble returned by the instrument.

The software must handle binary block waveform responses correctly.

---

## Suggested Analysis Workflow

1. Check connection.

```bash
python -m scope.cli check-connection --config configs/experiment_piezo_stainless.yaml
```

2. Acquire baseline with no deliberate excitation.

```bash
python -m scope.cli run --config configs/experiment_piezo_stainless.yaml --captures 20
```

3. Acquire controlled mechanical excitation.

Examples:

```text
- light tap on stainless-steel rod
- light tap on stainless-steel plate
- rubbing or bending test
- soil-contact test
- dry/wet comparison
```

4. Compare reports.

Important comparison questions:

```text
Which frequencies occur during baseline?
Which frequencies appear only after mechanical excitation?
Which frequencies are present on both channels?
Which peaks are stable on CH1 only?
Which peaks are likely caused by the LM358 board or its power supply?
```

---

## Code Quality Expectations

The code should be:

```text
- clean
- typed where reasonable
- modular
- documented
- testable
- not notebook-only
- suitable for repeated measurements
- suitable for later publication-quality analysis
```

Avoid hard-coded constants except safe defaults.

All experiment-specific values should be configurable.

---

## Acceptance Criteria

The implementation is successful when:

```text
1. The program connects to the Rigol DS1104Z at 192.168.178.70.
2. It acquires CH1 and CH3 waveforms (Phase 2 active set: CH1, CH3, CH4; CH2 disabled).
3. It saves raw data with metadata.
4. It computes correct frequency spectra from actual timebase data.
5. It identifies dominant frequencies.
6. It flags likely artifacts.
7. It creates plots.
8. It creates a Markdown report.
9. It can repeat acquisition and compare peak repeatability.
10. It can be extended without rewriting the core logic.
```

---

## Important Interpretation Rules

Do not overclaim.

The program should distinguish between:

```text
measured spectral peak
likely mechanical resonance
possible electronic artifact
environmental noise
uncertain result
```

Especially for this setup:

```text
CH1 is amplified by an unknown LM358 board.
CH1 may contain amplifier noise, bias, saturation, or switching-supply artifacts.
CH3 and CH4 are also amplified (amplifier + 820 kΩ), with different mechanical coupling.
Therefore, frequency agreement between any pair of active channels is useful but not mandatory.
Amplitude comparison between channels is not scientifically valid without calibration.
```

---

## Final Deliverables

Please create:

```text
- complete Python package
- README with installation and usage
- YAML configs
- CLI
- acquisition module for Rigol DS1104Z
- spectral analysis module
- peak detection module
- plausibility checks
- plotting module
- automatic Markdown report generation
- tests for non-hardware analysis functions
```

The project should be usable by running:

```bash
pip install -e .
python -m scope.cli check-connection --config configs/experiment_piezo_stainless.yaml
python -m scope.cli run --config configs/experiment_piezo_stainless.yaml --captures 20
```
