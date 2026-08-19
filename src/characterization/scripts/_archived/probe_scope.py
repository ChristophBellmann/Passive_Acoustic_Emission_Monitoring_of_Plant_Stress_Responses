#!/usr/bin/env python3
"""
Diagnostic probe for the Rigol DS1104Z long-capture memory-depth problem.

Determines WHY long captures return only 100k (or 0) points instead of 3M:
  * Does :ACQ:MDEP AUTO actually select a deep memory at 0.5 s/div?
  * Does explicit :ACQ:MDEP 3000000 stick with 3 channels enabled?
  * How many points does a SINGLE :WAV:DATA? return (chunk-size limit)?
  * Does chunked WAV:STAR / WAV:STOP paging work?

Read-only w.r.t. data: it triggers ONE acquisition and reads back metadata
plus small byte counts. Does not save any waveform.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPT_DIR / "instrument_control"))

from scope.config import load_config
from scope.instrument import InstrumentConnection, get_preamble

CONFIG_PATH = SCRIPT_DIR / "experiment_plant_acoustic_emissions_20260621" / "config.yaml"


def q(conn, cmd):
    try:
        return conn.query(cmd)
    except Exception as exc:  # noqa: BLE001
        return f"<ERR {exc}>"


def main() -> int:
    config = load_config(str(CONFIG_PATH))
    print("=" * 70)
    print("DS1104Z LONG-CAPTURE DIAGNOSTIC PROBE")
    print("=" * 70)

    with InstrumentConnection(config) as conn:
        print("IDN:", q(conn, "*IDN?"))

        print("\n--- current state (before reconfigure) ---")
        for cmd in (":TIM:SCAL?", ":ACQ:MDEP?", ":ACQ:SRAT?", ":ACQ:TYPE?",
                    ":CHAN1:DISP?", ":CHAN2:DISP?", ":CHAN3:DISP?", ":CHAN4:DISP?"):
            print(f"  {cmd:14s} {q(conn, cmd)}")

        print("\n--- configure 3 ch, 0.5 s/div, MDEP AUTO (as long-capture script) ---")
        conn.write(":STOP")
        time.sleep(0.3)
        for ch, probe, scale in ((1, 10, 0.2), (2, 1, 0.01), (3, 1, 0.01)):
            conn.write(f":CHAN{ch}:DISP ON")
            conn.write(f":CHAN{ch}:COUP AC")
            conn.write(f":CHAN{ch}:PROB {probe}")
            conn.write(f":CHAN{ch}:SCAL {scale}")
        conn.write(":CHAN4:DISP OFF")
        conn.write(":TIM:SCAL 0.5")
        conn.write(":TIM:OFFS 0")
        conn.write(":ACQ:MDEP AUTO")
        conn.write(":RUN")
        time.sleep(1.5)
        print(f"  TIM:SCAL  -> {q(conn, ':TIM:SCAL?')}")
        print(f"  ACQ:MDEP  -> {q(conn, ':ACQ:MDEP?')}   (AUTO)")
        print(f"  ACQ:SRAT  -> {q(conn, ':ACQ:SRAT?')}")

        print("\n--- try EXPLICIT :ACQ:MDEP 3000000 ---")
        conn.write(":RUN")
        time.sleep(0.3)
        for depth in ("3000000", "6000000", "1200000"):
            conn.write(f":ACQ:MDEP {depth}")
            time.sleep(0.4)
            got = q(conn, ":ACQ:MDEP?")
            print(f"  set {depth:>9s} -> ACQ:MDEP={got}   SRAT={q(conn, ':ACQ:SRAT?')}")

        # Pick the deepest that stuck
        conn.write(":ACQ:MDEP 3000000")
        time.sleep(0.4)
        mdep = q(conn, ":ACQ:MDEP?")
        print(f"\n  using MDEP={mdep}")

        print("\n--- trigger ONE acquisition, then STOP for deep-memory read ---")
        conn.write(":SING")
        time.sleep(7.5)  # 6 s window + headroom
        conn.write(":STOP")
        time.sleep(0.5)
        print(f"  TRIG:STAT -> {q(conn, ':TRIG:STAT?')}")
        print(f"  ACQ:MDEP  -> {q(conn, ':ACQ:MDEP?')}")
        print(f"  ACQ:SRAT  -> {q(conn, ':ACQ:SRAT?')}")

        print("\n--- RAW preamble for CH1 ---")
        conn.write(":WAV:SOUR CHAN1")
        conn.write(":WAV:MODE RAW")
        conn.write(":WAV:FORM BYTE")
        time.sleep(0.2)
        try:
            pre = get_preamble(conn, 1)
            print(f"  preamble.points = {pre.points:,}")
            print(f"  xincrement      = {pre.xincrement:g}  -> rate {1/pre.xincrement/1e3:.1f} kSa/s"
                  if pre.xincrement > 0 else "  xincrement = 0")
        except Exception as exc:  # noqa: BLE001
            print("  preamble ERR:", exc)

        print("\n--- single :WAV:DATA? (no STAR/STOP) byte count ---")
        try:
            data = conn.query_binary_values(":WAV:DATA?", datatype="B", container=bytearray)
            print(f"  single read returned {len(data):,} bytes")
        except Exception as exc:  # noqa: BLE001
            print("  single read ERR:", exc)

        print("\n--- chunked read test: STAR/STOP paging ---")
        chunk = 250000
        try:
            total = int(float(q(conn, ":ACQ:MDEP?")))
        except Exception:
            total = 3000000
        got_total = 0
        n_chunks = 0
        try:
            start = 1
            while start <= total and n_chunks < 4:  # test first 4 chunks only
                stop = min(start + chunk - 1, total)
                conn.write(f":WAV:STAR {start}")
                conn.write(f":WAV:STOP {stop}")
                d = conn.query_binary_values(":WAV:DATA?", datatype="B", container=bytearray)
                print(f"    chunk [{start:>8,}..{stop:>8,}] -> {len(d):,} bytes")
                got_total += len(d)
                n_chunks += 1
                start = stop + 1
            print(f"  {n_chunks} chunks OK, {got_total:,} bytes "
                  f"(would need {-(-total // chunk)} chunks for full {total:,} pts)")
        except Exception as exc:  # noqa: BLE001
            print("  chunked read ERR:", exc)

        conn.write(":RUN")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
