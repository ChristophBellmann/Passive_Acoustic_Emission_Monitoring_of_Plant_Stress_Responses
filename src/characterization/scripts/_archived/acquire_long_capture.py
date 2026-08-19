#!/usr/bin/env python3
"""
Long-window plant AE acquisition at 500 kSa/s (Nyquist 250 kHz).

Background
----------
The Rigol DS1104Z couples the sample rate to memory depth and time-base:

    sample_rate = memory_depth / (TIM:SCAL × 12_divisions)

Two facts, both verified live with scripts/probe_scope.py, drive this script:

1. ``:ACQ:MDEP AUTO`` does NOT select deep memory at slow time-bases — the
   scope stays at 25 MSa/s. The memory depth must be set EXPLICITLY (and while
   the scope is running). With 3 channels active, MDEP and TIM:SCAL are chosen
   so the rate lands on 500 kSa/s.

2. A bare ``:WAV:DATA?`` in RAW mode returns only ~100 bytes, and a single
   request is hard-capped at 250 000 points. The full record must be paged out
   in ≤250 k chunks via ``:WAV:STAR`` / ``:WAV:STOP`` (see
   ``scope.instrument.acquire_waveform_full``).

Readout over LAN (pyvisa-py) is bandwidth-limited to ~25 kB/s (~10 s per
250 k chunk), so read time scales with point count. The default 300 000-point
depth (0.6 s window, 1.67 Hz resolution) is the practical sweet spot for
kHz-scale plant AE and reads in ~12 s/channel. 500 kSa/s already covers the
full 0–100 kHz AE band, so no software decimation is used.

Per-channel output (default 300 k depth):
  * 300 000 float32 samples
  * duration   : 0.6 s
  * Nyquist    : 250 kHz
  * freq. res. : 1.67 Hz (Welch coarser, depending on nperseg)
  * file size  : ≈ 0.3 MB compressed NPZ (LFS-tracked)

Usage
-----
  python scripts/acquire_long_capture.py                       # single capture
  python scripts/acquire_long_capture.py --captures 20         # baseline series
  python scripts/acquire_long_capture.py --memory-depth 3000000  # 0.17 Hz, slow
  python scripts/acquire_long_capture.py --dry-run             # check only
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent.parent
INSTRUMENT_CONTROL = SCRIPT_DIR / "instrument_control"
sys.path.insert(0, str(INSTRUMENT_CONTROL))

from scope.config import load_config
from scope.instrument import (
    InstrumentConnection,
    acquire_waveform_full,
)

# ---------------------------------------------------------------------------
# Acquisition parameters
# ---------------------------------------------------------------------------
CONFIG_PATH = SCRIPT_DIR / "experiment_plant_acoustic_emissions_20260621" / "config.yaml"
DATA_ROOT = SCRIPT_DIR / "data" / "long_captures"
CHANNELS = (1, 2, 3)
TIMEZONE = ZoneInfo("Europe/Berlin")

# The DS1104Z couples sample rate to memory depth and time-base:
#     sample_rate = memory_depth / (12 * TIM:SCAL)
# We fix the rate at 500 kSa/s (Nyquist 250 kHz, covers the 0-100 kHz AE band)
# and derive the time-base from the chosen memory depth.
#
# Deep-memory RAW readout over LAN (pyvisa-py) is bandwidth-limited to
# ~25 kB/s and hard-capped at 250 000 points per :WAV:DATA? request, so the
# read time scales with point count (~10 s per 250 k chunk). 300 k points
# (0.6 s window, 1.67 Hz resolution) read in ~12 s/channel — the practical
# sweet spot for kHz-scale plant AE. 3 M points (0.17 Hz) take ~6 min/capture;
# pass --memory-depth 3000000 only for a deliberate high-resolution run.
EXPECTED_RATE_HZ = 500_000.0       # 500 kSa/s; Nyquist 250 kHz
DEFAULT_MEMORY_DEPTH = 300_000     # 0.6 s window, 1.67 Hz resolution
VALID_MEMORY_DEPTHS = (30_000, 300_000, 3_000_000, 6_000_000)
READ_CHUNK_POINTS = 250_000        # hard per-request limit on the DS1000Z
VISA_TIMEOUT_MS = 30_000           # one 250 k chunk takes ~10 s; 10 s is too tight

# Maximum allowed deviation from expected rate before aborting
RATE_TOLERANCE = 0.10              # ±10 %


def timebase_for(memory_depth: int) -> float:
    """TIM:SCAL (s/div) that yields EXPECTED_RATE_HZ for *memory_depth*."""
    return memory_depth / (12.0 * EXPECTED_RATE_HZ)


def configure_scope_long(conn: InstrumentConnection, memory_depth: int) -> dict:
    """
    Configure the scope for a *memory_depth*-point / 500 kSa/s acquisition.

    Sets the time-base so that the resulting sample rate equals
    EXPECTED_RATE_HZ, sets the memory depth explicitly (AUTO does not select
    deep memory), and verifies the rate live. Does NOT trigger an acquisition —
    every capture does its own :SING.
    """
    timebase = timebase_for(memory_depth)
    conn.write(":STOP")
    time.sleep(0.3)

    for ch, probe, scale in ((1, 10, 0.2), (2, 1, 0.01), (3, 1, 0.01)):
        conn.write(f":CHAN{ch}:DISP ON")
        conn.write(f":CHAN{ch}:COUP AC")
        conn.write(f":CHAN{ch}:PROB {probe}")
        conn.write(f":CHAN{ch}:SCAL {scale}")
        conn.write(f":CHAN{ch}:OFFS 0")
    conn.write(":CHAN4:DISP OFF")

    conn.write(f":TIM:SCAL {timebase}")
    conn.write(":TIM:OFFS 0")
    conn.write(":TRIG:MODE EDGE")
    conn.write(":TRIG:EDGE:SOUR CHAN1")
    conn.write(":TRIG:EDGE:LEV 0.02")
    conn.write(":TRIG:SWE AUTO")
    conn.write(":RUN")
    time.sleep(0.5)

    # Memory depth MUST be set explicitly and while running. ":ACQ:MDEP AUTO"
    # keeps the scope at 25 MSa/s even at slow time-bases (verified via
    # probe_scope.py); only an explicit depth couples the rate down to 500 kSa/s.
    conn.write(f":ACQ:MDEP {memory_depth}")
    time.sleep(1.5)   # let scope apply settings

    actual_timescale = float(conn.query(":TIM:SCAL?"))
    if abs(actual_timescale - timebase) / timebase > 0.05:
        raise RuntimeError(
            f"Scope rejected TIM:SCAL={timebase}, got {actual_timescale}"
        )

    # Verify the deep-memory sample rate actually took effect.
    actual_rate = float(conn.query(":ACQ:SRAT?"))
    if abs(actual_rate - EXPECTED_RATE_HZ) / EXPECTED_RATE_HZ > RATE_TOLERANCE:
        raise RuntimeError(
            f"Scope SRAT={actual_rate/1e3:.1f} kSa/s after :ACQ:MDEP {memory_depth}, "
            f"expected {EXPECTED_RATE_HZ/1e3:.1f} kSa/s ±{RATE_TOLERANCE:.0%}. "
            "Memory depth did not apply — check channel count / time-base."
        )
    actual_mdep = conn.query(":ACQ:MDEP?")

    capture_duration_s = memory_depth / EXPECTED_RATE_HZ
    return {
        "sample_rate_hz": actual_rate,
        "memory_depth": actual_mdep,
        "timebase_s_per_div": actual_timescale,
        "expected_points": memory_depth,
        "capture_duration_s": capture_duration_s,
    }


def trigger_and_wait(conn: InstrumentConnection, duration_s: float) -> None:
    """Trigger a single acquisition and wait for it to complete."""
    conn.write(":SING")
    time.sleep(duration_s + 1.5)   # full window + download headroom


def acquire_channel(
    conn: InstrumentConnection, channel: int, expected_points: int
) -> tuple[np.ndarray, float]:
    """
    Download one channel's full RAW waveform from the last completed acquisition.

    Uses chunked WAV:STAR/STOP paging (a single :WAV:DATA? returns only ~100
    bytes in RAW mode). The scope must already be stopped. Voltage conversion is
    vectorised: (raw - yorigin - yreference) * yincrement.
    Returns (voltage_float32, sample_rate_hz).
    """
    preamble, raw_bytes = acquire_waveform_full(
        conn, channel, chunk_size=READ_CHUNK_POINTS, expected_points=expected_points,
    )
    raw = np.frombuffer(bytes(raw_bytes), dtype=np.uint8).astype(np.float32)
    voltage = (
        (raw - preamble.yorigin - preamble.yreference) * preamble.yincrement
    ).astype(np.float32)
    sample_rate = 1.0 / preamble.xincrement if preamble.xincrement > 0 else EXPECTED_RATE_HZ
    return voltage, sample_rate


def save_capture(
    out_dir: Path,
    channel: int,
    voltage: np.ndarray,
    sample_rate: float,
    capture_ts: str,
    metadata: dict,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{capture_ts}_ch{channel}.npz"
    np.savez_compressed(
        path,
        voltage=voltage,
        sample_rate=np.float32(sample_rate),
        metadata=np.array([metadata]),
    )
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG_PATH)
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument("--captures", type=int, default=1,
                        help="Number of capture sets (default: 1)")
    parser.add_argument("--delay-s", type=float, default=2.0,
                        help="Delay between captures in seconds (default: 2)")
    parser.add_argument("--memory-depth", type=int, default=DEFAULT_MEMORY_DEPTH,
                        choices=VALID_MEMORY_DEPTHS,
                        help=f"Points per capture (default: {DEFAULT_MEMORY_DEPTH}). "
                             "300000 → 1.67 Hz res, ~12 s/ch; 3000000 → 0.17 Hz, ~2 min/ch.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Connect and verify scope, then exit without capturing")
    args = parser.parse_args(argv)

    config = load_config(str(args.config))
    mdep = args.memory_depth
    timebase = timebase_for(mdep)

    run_ts = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
    run_dir = (args.out_dir or DATA_ROOT) / run_ts
    raw_dir = run_dir / "raw"

    print("=" * 70)
    print("LONG-CAPTURE PLANT AE ACQUISITION")
    print("=" * 70)
    print(f"  Config    : {args.config}")
    print(f"  Output    : {run_dir}")
    print(f"  Timebase  : {timebase*1e3:.1f} ms/div  → {timebase*12:.2f} s total")
    print(f"  Target    : {EXPECTED_RATE_HZ/1e3:.0f} kSa/s, Nyquist {EXPECTED_RATE_HZ/2/1e3:.0f} kHz")
    print(f"  Points    : {mdep:,} pts → {mdep/EXPECTED_RATE_HZ:.2f} s window")
    print(f"  Freq. res.: {EXPECTED_RATE_HZ/mdep:.2f} Hz")
    print()

    with InstrumentConnection(config) as conn:
        # Deep-memory chunk reads take ~10 s each; the config's 10 s VISA
        # timeout is too tight and causes truncated/empty reads.
        conn._inst.timeout = VISA_TIMEOUT_MS
        print("Configuring scope for long-window acquisition...")
        scope_settings = configure_scope_long(conn, mdep)
        actual_rate = scope_settings["sample_rate_hz"]
        print(f"  Sample rate  : {scope_settings['sample_rate_hz']/1e3:.0f} kSa/s")
        print(f"  Points       : {scope_settings['expected_points']:,}")
        print(f"  Duration     : {scope_settings['capture_duration_s']:.3f} s")
        print()

        if args.dry_run:
            print("Dry run complete — scope is ready.")
            return 0

        cap_dur = scope_settings["capture_duration_s"]
        actual_rate = scope_settings["sample_rate_hz"]
        rate_verified = False

        for cap_num in range(1, args.captures + 1):
            cap_ts = datetime.now(TIMEZONE).strftime("%Y%m%d_%H%M%S")
            print(f"Capture {cap_num}/{args.captures}  [{cap_ts}]")

            # Trigger a fresh single acquisition for every capture.
            trigger_and_wait(conn, cap_dur)

            metadata_base = {
                "timestamp": cap_ts,
                "run_id": run_ts,
                "capture_number": cap_num,
                "scope_sample_rate_hz": actual_rate,
                "expected_points": scope_settings["expected_points"],
                "timebase_s_per_div": scope_settings["timebase_s_per_div"],
            }

            for ch in CHANNELS:
                voltage, ch_rate = acquire_channel(conn, ch, scope_settings["expected_points"])
                dur_s = len(voltage) / ch_rate if ch_rate > 0 else 0

                # First channel of first capture: verify actual sample rate
                if not rate_verified and ch == CHANNELS[0] and len(voltage) > 0:
                    rate_err = abs(ch_rate - EXPECTED_RATE_HZ) / EXPECTED_RATE_HZ
                    if rate_err > RATE_TOLERANCE:
                        raise RuntimeError(
                            f"RAW preamble: {ch_rate/1e3:.1f} kSa/s, expected "
                            f"{EXPECTED_RATE_HZ/1e3:.1f} kSa/s ±{RATE_TOLERANCE:.0%}"
                        )
                    actual_rate = ch_rate
                    rate_verified = True
                    print(f"  Rate verified: {actual_rate/1e3:.0f} kSa/s from preamble")

                print(f"  CH{ch}: {len(voltage):,} pts @ {ch_rate/1e3:.0f} kSa/s "
                      f"({dur_s:.3f} s)")

                metadata = {**metadata_base, "channel": ch}
                raw_path = save_capture(raw_dir, ch, voltage, ch_rate, cap_ts, metadata)
                size_kb = raw_path.stat().st_size / 1024
                print(f"    → {raw_path.name}  ({len(voltage):,} pts, {size_kb:.0f} kB)")

            if cap_num < args.captures:
                print(f"  Waiting {args.delay_s:.1f} s before next SING...")
                time.sleep(args.delay_s)

    print()
    print("=" * 70)
    print(f"Done. Output in: {run_dir}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
