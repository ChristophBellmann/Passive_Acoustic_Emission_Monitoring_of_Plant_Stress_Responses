# Rigol Oscilloscope Examples

This folder contains short, self-contained examples that follow the PyVISA/SCPI workflow described in the TestFlow blog post:
[How to Automate a Rigol Oscilloscope with Python](https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide)

They are intended as a gentle introduction before using the full `scope` pipeline.

## Files

- `rigol_basic_tutorial.py` — Standalone script that lists VISA resources, connects to a Rigol scope, runs `:MEASure:ITEM?` queries, captures a waveform in `NORMal` mode, converts the raw bytes to voltage, and plots/saves the result.
- `rigol_basic_tutorial.ipynb` — Jupyter notebook version of the same tutorial.
- `generate_notebook.py` — Helper script that regenerates the `.ipynb` file from a Python dict.

## Quick start

1. Install the minimal dependencies:

   ```bash
   pip install pyvisa pyvisa-py pyusb numpy matplotlib
   ```

2. Edit the `VISA_RESOURCE` string at the top of `rigol_basic_tutorial.py`:

   - LAN: `TCPIP0::192.168.178.70::INSTR`
   - USB: `USB0::0x1AB1::0x04CE::<serial>::INSTR` (copy the exact string from `rm.list_resources()`)

3. Run the example:

   ```bash
   python examples/rigol_basic_tutorial.py
   ```

Output is written to `examples/output/capture.png` and `examples/output/capture.csv`.

## Relationship to the main package

The full `scope` package (`instrument_control/scope/`) wraps the same PyVISA/SCPI calls into a config-driven acquisition, analysis, and reporting pipeline. Use these examples to understand the low-level instrument communication, then switch to the CLI for real experiments.
