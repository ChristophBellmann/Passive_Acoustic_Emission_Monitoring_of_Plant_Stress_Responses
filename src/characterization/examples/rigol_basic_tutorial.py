"""
Minimal Rigol oscilloscope automation example.

This script follows the steps described in:
https://testflowinc.com/blog/automate-rigol-oscilloscope-python-scpi-pyvisa-guide

It shows the basic PyVISA/SCPI workflow without the full analysis pipeline:
1. List VISA resources
2. Connect to the scope
3. Query identity
4. Run automated measurements
5. Capture waveform data
6. Convert raw bytes to voltage and plot/save the result

Requirements:
    pip install pyvisa pyvisa-py pyusb numpy matplotlib

Usage:
    python examples/rigol_basic_tutorial.py

The default VISA resource is for a Rigol DS1104Z over LAN. Adjust
VISA_RESOURCE below for USB or for your scope's IP address.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Try to import the project package so the example can reuse the Rigol parser.
PROJECT_SRC = Path(__file__).resolve().parent.parent / "instrument_control"
if PROJECT_SRC.exists():
    sys.path.insert(0, str(PROJECT_SRC))
    from scope.instrument import (
        InstrumentConnection,
        acquire_waveform_bytes,
        bytes_to_voltage,
        build_time_vector,
        parse_preamble,
    )
    USE_PROJECT_HELPERS = True
else:
    USE_PROJECT_HELPERS = False  # type: ignore[assignment]

import pyvisa

# ---------------------------------------------------------------------------
# User settings
# ---------------------------------------------------------------------------

# For LAN connection use: "TCPIP0::192.168.178.70::INSTR"
# For USB connection use the string reported by rm.list_resources(), e.g.:
# "USB0::0x1AB1::0x04CE::DS1ZA201607099::INSTR"
VISA_RESOURCE = "TCPIP0::192.168.178.70::INSTR"

TIMEOUT_MS = 10_000
CHANNEL = 1


def measure(scope: pyvisa.resources.Resource, item: str, channel: str = "CHANnel1") -> float:
    """Query a single :MEASure:ITEM from the scope."""
    return float(scope.query(f":MEASure:ITEM? {item},{channel}"))


def main() -> None:
    # ------------------------------------------------------------------
    # Step 1: Find and connect to the scope
    # ------------------------------------------------------------------
    rm = pyvisa.ResourceManager("@py")
    resources = rm.list_resources()
    print("VISA resources found:")
    for r in resources:
        print(f"  {r}")

    if VISA_RESOURCE not in resources:
        print(f"\nRequested resource '{VISA_RESOURCE}' not in list.")
        print("If connecting over USB, copy the correct USB resource string above.")
        print("If connecting over LAN, ensure the IP address is correct.")
        # For LAN the resource is often not discovered by list_resources(),
        # so we still try to open it directly.

    print(f"\nOpening {VISA_RESOURCE} ...")
    scope = rm.open_resource(VISA_RESOURCE, timeout=TIMEOUT_MS)

    idn = scope.query("*IDN?").strip()
    print(f"IDN: {idn}")
    if "RIGOL" not in idn.upper():
        raise ConnectionError(f"Expected a Rigol instrument, got: {idn}")

    # ------------------------------------------------------------------
    # Step 2: Automated measurements
    # ------------------------------------------------------------------
    scope.write(":AUToscale")
    # Give the scope a moment to settle.
    import time

    time.sleep(1.0)

    vpp = measure(scope, "VPP", f"CHANnel{CHANNEL}")
    freq = measure(scope, "FREQuency", f"CHANnel{CHANNEL}")
    vavg = measure(scope, "VAVG", f"CHANnel{CHANNEL}")

    # Rigol returns 9.9e37 when a measurement is invalid.
    INVALID = 9.9e37
    print("\nAutomated measurements:")
    print(f"  Vpp   = {vpp:.3f} V" if vpp < INVALID else "  Vpp   = invalid")
    print(f"  f     = {freq:.1f} Hz" if freq < INVALID else "  f     = invalid")
    print(f"  Vavg  = {vavg:.3f} V" if vavg < INVALID else "  Vavg  = invalid")

    # ------------------------------------------------------------------
    # Step 3: Capture the waveform itself
    # ------------------------------------------------------------------
    print(f"\nCapturing waveform from CH{CHANNEL} ...")

    if USE_PROJECT_HELPERS:
        # Reuse the project's Rigol parser (cleaner and tested).
        conn = InstrumentConnection.__new__(InstrumentConnection)
        conn._inst = scope
        preamble, raw = acquire_waveform_bytes(
            conn, channel=CHANNEL, mode="NORMal", fmt="BYTE"
        )
        volts = np.array(bytes_to_voltage(raw, preamble), dtype=np.float64)
        time_s = np.array(build_time_vector(preamble), dtype=np.float64)
    else:
        # Stand-alone version matching the blog article exactly.
        scope.write(f":WAVeform:SOURce CHANnel{CHANNEL}")
        scope.write(":WAVeform:MODE NORMal")
        scope.write(":WAVeform:FORMat BYTE")

        xinc = float(scope.query(":WAVeform:XINCrement?"))
        yinc = float(scope.query(":WAVeform:YINCrement?"))
        yorig = float(scope.query(":WAVeform:YORigin?"))
        yref = float(scope.query(":WAVeform:YREFerence?"))

        raw = scope.query_binary_values(":WAVeform:DATA?", datatype="B", container=np.array)
        volts = (raw - yorig - yref) * yinc
        time_s = np.arange(len(volts)) * xinc

    print(f"  Captured {len(volts)} points over {time_s[-1] - time_s[0]:.6f} s")
    print(f"  Sample interval: {time_s[1] - time_s[0]:.3e} s")

    # ------------------------------------------------------------------
    # Step 4: Plot and save
    # ------------------------------------------------------------------
    import matplotlib.pyplot as plt

    plt.figure(figsize=(10, 5))
    plt.plot(time_s * 1e3, volts)
    plt.xlabel("Time (ms)")
    plt.ylabel("Voltage (V)")
    plt.title(f"Rigol capture - {idn}")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    out_dir = Path(__file__).resolve().parent / "output"
    out_dir.mkdir(exist_ok=True)
    png_path = out_dir / "capture.png"
    csv_path = out_dir / "capture.csv"

    plt.savefig(png_path, dpi=150)
    np.savetxt(
        csv_path,
        np.column_stack([time_s, volts]),
        delimiter=",",
        header="time_s,volts",
        comments="",
    )

    print(f"\nSaved plot to {png_path}")
    print(f"Saved CSV to {csv_path}")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------
    scope.close()
    rm.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
