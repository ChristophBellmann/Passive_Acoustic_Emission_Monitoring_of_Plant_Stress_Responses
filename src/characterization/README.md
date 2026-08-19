# scope - Oscilloscope Vibration Characterization

Scientific, config-driven Python tool for characterizing vibrations measured with a
Rigol DS1104Z oscilloscope. Acquires waveforms from piezo and MEMS sensors, performs spectral
analysis, detects peaks, runs plausibility checks, and generates Markdown reports.

The install provides two direct Python packages:

- `scope` for generic oscilloscope control and signal processing;
- `plant_ae` for current rolling-window measurements and historical watering/hybrid experiments.

The Jupyter notebooks under `notebooks/` are thin experiment frontends and do
not execute each other or depend on legacy import shims.

## Installation

```bash
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Portable Jupyter Setup

Use the setup script on each workstation. It creates `src/characterization/.venv`,
installs the project in editable mode and registers the stable Jupyter kernel
`plant-ae`.

```bash
cd src/characterization
./setup_jupyter.sh
.venv/bin/jupyter lab notebooks/00_control_panel.ipynb
```

The control panel notebook provides buttons for `measurement.py start`, `stop`,
`status`, log viewing and one-shot execution of any notebook under
`notebooks/`. The experiment logic stays in the selected notebooks; the panel is
only the operator UI.

For normal operation, always enter through `notebooks/00_control_panel.ipynb`.
Its **Start Longrun (NB04)** button is fixed to
`notebooks/04_continuous_frequency_sweep.ipynb`, the single source of truth for
continuous acquisition. `measurement.py` is only the shared background runner;
the notebook dropdown is used solely by **Run Once**.

Phase 3 has no Home Assistant connection at the relocated setup. Automatic
watering and Home-Assistant temperature acquisition are therefore unavailable;
the control panel starts measurement notebooks without either function. The
Home Assistant integrations remain in the repository solely to reproduce the
historical Phase-1/2 workflows.

## Quick Start

### Minimal PyVISA/SCPI example

If you want to see the low-level Rigol control first, run the standalone tutorial that matches the TestFlow blog post:

```bash
python examples/rigol_basic_tutorial.py
```

A Jupyter notebook version is also available in `examples/rigol_basic_tutorial.ipynb`.

### 1. Check oscilloscope connection

```bash
python -m scope.cli check-connection --config configs/experiment_piezo_mems.yaml
```

### 2. Acquire data

```bash
python -m scope.cli acquire --config configs/experiment_piezo_mems.yaml --captures 20
```

### 3. Analyze data

```bash
python -m scope.cli analyze --config configs/experiment_piezo_mems.yaml --input data/raw
```

### 4. Full pipeline (acquire + analyze)

```bash
python -m scope.cli run --config configs/experiment_piezo_mems.yaml --captures 20
```

## Configuration

All experiment parameters are in YAML config files under `configs/`:

- `default.yaml` - Full default configuration
- `rigol_ds1104z.yaml` - Instrument-specific settings
- `experiment_piezo_stainless.yaml` - Complete experiment config for piezo + stainless steel setup
- `experiment_piezo_mems.yaml` - Current CH1 Piezo / CH3+CH4 MEMS configuration (since 2026-07-14)

## Measurement Setup

> **Channel history:** CH2 (Piezo on 0.8mm stainless-steel plate, 1:1 probe) suffered a hardware fault and was disabled. It was replaced by CH4. After relocation of the setup in July 2026, the Piezo sensors on CH3 and CH4 were replaced by MEMS microphones; the existing LM amplifier stages remain in use. Active channels are **CH1, CH3, CH4** (see `instrument_control/plant_ae/deep_acquisition.py:CHANNEL_HW_CONFIG`). Reports based on earlier captures retain their historical sensor descriptions.

- **CH1**: Piezo + existing LM amplifier — oscilloscope (10:1 probe)
- **CH3**: MEMS microphone + existing LM amplifier — oscilloscope (10:1 probe)
- **CH4**: MEMS microphone + existing LM amplifier — oscilloscope (10:1 probe)
- **CH2**: **disabled** (hardware defect)
- **Oscilloscope**: Rigol DS1104Z at 192.168.178.70 (TCP/IP VISA)
- **Auxiliary data**: no automatic watering and no temperature measurement in Phase 3

## Output

- Raw data: `data/raw/*.npz` and `data/raw/*.csv`
- Processed plots: `data/processed/*.png`
- Reports: `data/reports/*_report.md`
- Phase-3 MEMS sweep calibration, accepted frequencies and operational lessons:
  `data/pico_sweep_calibration_phase3/README.md`

## Running Tests

```bash
pytest tests/
```

## Dependencies

numpy, scipy, matplotlib, pandas, pyyaml, pyvisa, pyvisa-py, tqdm, rich, typer, pydantic
