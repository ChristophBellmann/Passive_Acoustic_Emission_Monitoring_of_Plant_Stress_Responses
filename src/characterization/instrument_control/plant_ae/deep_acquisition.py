"""Synchronized deep-memory acquisition for long-running plant AE experiments."""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any

import numpy as np
from scope.acquisition import Capture, CaptureMetadata
from scope.config import ExperimentConfig
from scope.instrument import InstrumentConnection, acquire_waveform_full

DEFAULT_SAMPLE_RATE_HZ = 500_000.0
DEFAULT_MEMORY_DEPTH = 300_000
DEFAULT_CHUNK_POINTS = 250_000

# Single source of truth for current channel hardware configuration.
# (channel, probe_ratio, volts_per_div)
# CH2 is disabled (hardware fault).
CHANNEL_HW_CONFIG: tuple[tuple[int, int, float], ...] = (
    (1, 10, 0.5),    # CH1: amplifier + 820 kΩ + piezo
    (3, 10, 0.5),    # CH3: amplifier + MEMS microphone
    (4, 10, 0.5),    # CH4: amplifier + MEMS microphone
)


def timebase_for(sample_rate_hz: float, memory_depth: int) -> float:
    """Return seconds/division for the DS1104Z twelve-division acquisition."""
    if sample_rate_hz <= 0 or memory_depth <= 0:
        raise ValueError("sample rate and memory depth must be positive")
    return memory_depth / (12.0 * sample_rate_hz)


def configure_deep_memory_scope(
    conn: InstrumentConnection,
    *,
    sample_rate_hz: float = DEFAULT_SAMPLE_RATE_HZ,
    memory_depth: int = DEFAULT_MEMORY_DEPTH,
    verify_timebase: bool = True,
) -> dict[str, Any]:
    """Configure and verify a synchronized multi-channel deep-memory profile.

    Active channels (CH2 disabled — hardware defect):
      CH1: amplifier + 820 kΩ + piezo
      CH3: amplifier + MEMS microphone
      CH4: amplifier + MEMS microphone
    """
    timebase = timebase_for(sample_rate_hz, memory_depth)
    conn.write(":STOP")
    time.sleep(0.3)
    for channel, probe, scale in CHANNEL_HW_CONFIG:
        conn.write(f":CHAN{channel}:DISP ON")
        conn.write(f":CHAN{channel}:COUP AC")
        conn.write(f":CHAN{channel}:PROB {probe}")
        conn.write(f":CHAN{channel}:SCAL {scale}")
        conn.write(f":CHAN{channel}:OFFS 0")
    conn.write(":CHAN2:DISP OFF")  # CH2 defekt
    conn.write(f":TIM:SCAL {timebase}")
    conn.write(":TIM:OFFS 0")
    conn.write(":TRIG:MODE EDGE")
    conn.write(":TRIG:EDGE:SOUR CHAN3")  # CH3 = amplified MEMS microphone
    conn.write(":TRIG:EDGE:LEV 0.02")
    conn.write(":TRIG:SWE AUTO")
    conn.write(":RUN")
    time.sleep(0.5)
    conn.write(f":ACQ:MDEP {memory_depth}")
    time.sleep(1.5)

    actual_rate = float(conn.query(":ACQ:SRAT?"))
    actual_timebase = float(conn.query(":TIM:SCAL?"))
    actual_depth = int(float(conn.query(":ACQ:MDEP?")))
    if not np.isclose(actual_rate, sample_rate_hz, rtol=0.1):
        raise RuntimeError(
            f"Rigol sample rate is {actual_rate:g} Sa/s, expected {sample_rate_hz:g}"
        )
    if verify_timebase and not np.isclose(actual_timebase, timebase, rtol=0.05):
        raise RuntimeError(f"Rigol timebase is {actual_timebase:g} s/div, expected {timebase:g}")
    if actual_depth != memory_depth:
        raise RuntimeError(f"Rigol memory depth is {actual_depth}, expected {memory_depth}")
    return {
        "profile": "deep_memory_500k",
        "sample_rate_hz": actual_rate,
        "memory_depth": actual_depth,
        "horizontal_scale_s_per_div": actual_timebase,
        "capture_duration_s": memory_depth / actual_rate,
        "frequency_resolution_hz": actual_rate / memory_depth,
        "nyquist_hz": actual_rate / 2,
        "trigger_mode": conn.query(":TRIG:MODE?"),
        "trigger_source": conn.query(":TRIG:EDGE:SOUR?"),
        "trigger_level_v": float(conn.query(":TRIG:EDGE:LEV?")),
    }


def trigger_deep_memory_frame(
    conn: InstrumentConnection,
    *,
    capture_duration_s: float,
    timeout_s: float = 10.0,
) -> None:
    """Trigger one frame and wait until the frozen RAW memory is readable."""
    conn.write(":SING")
    deadline = time.monotonic() + capture_duration_s + timeout_s
    time.sleep(capture_duration_s + 0.5)
    while time.monotonic() < deadline:
        if conn.query(":TRIG:STAT?").strip().upper() == "STOP":
            return
        time.sleep(0.1)
    raise TimeoutError("Deep-memory acquisition did not complete")


def acquire_deep_memory_frame(
    conn: InstrumentConnection,
    config: ExperimentConfig,
    *,
    sequence: int,
    sample_rate_hz: float = DEFAULT_SAMPLE_RATE_HZ,
    memory_depth: int = DEFAULT_MEMORY_DEPTH,
    chunk_points: int = DEFAULT_CHUNK_POINTS,
    channels: tuple[int, ...] = (1, 3, 4),
) -> list[Capture]:
    """Acquire one synchronized frame and download every channel in chunks."""
    trigger_deep_memory_frame(
        conn,
        capture_duration_s=memory_depth / sample_rate_hz,
    )
    instrument_id = conn.query("*IDN?")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    captures: list[Capture] = []
    for channel in channels:
        preamble, raw_bytes = acquire_waveform_full(
            conn,
            channel,
            chunk_size=chunk_points,
            expected_points=memory_depth,
        )
        if len(raw_bytes) != memory_depth:
            raise RuntimeError(
                f"CH{channel}: received {len(raw_bytes)} points, expected {memory_depth}"
            )
        actual_rate = 1.0 / preamble.xincrement
        if not np.isclose(actual_rate, sample_rate_hz, rtol=0.1):
            raise RuntimeError(
                f"CH{channel}: RAW rate {actual_rate:g}, expected {sample_rate_hz:g}"
            )
        raw = np.frombuffer(bytes(raw_bytes), dtype=np.uint8).astype(np.float32)
        voltage = ((raw - preamble.yorigin - preamble.yreference) * preamble.yincrement).astype(
            np.float32
        )
        time_vector = (
            np.arange(len(voltage), dtype=np.float64) - preamble.xreference
        ) * preamble.xincrement + preamble.xorigin
        channel_config = config.oscilloscope.channel_settings.get(channel)
        captures.append(
            Capture(
                metadata=CaptureMetadata(
                    timestamp=timestamp,
                    instrument_idn=instrument_id,
                    channel=channel,
                    channel_label=(channel_config.label if channel_config else f"ch{channel}"),
                    probe_ratio=(channel_config.probe_ratio if channel_config else 1.0),
                    sample_interval_s=preamble.xincrement,
                    sample_rate_sa_per_s=actual_rate,
                    record_length=len(voltage),
                    vertical_scale_v_per_div=(
                        channel_config.vertical_scale_v_per_div
                        if channel_config and channel_config.vertical_scale_v_per_div is not None
                        else 0.0
                    ),
                    vertical_offset_v=(
                        channel_config.offset_v
                        if channel_config and channel_config.offset_v is not None
                        else 0.0
                    ),
                    horizontal_scale_s_per_div=timebase_for(sample_rate_hz, memory_depth),
                    trigger_mode="EDGE",
                    trigger_source="CHAN3",
                    trigger_level_v=0.02,
                ),
                time_vector=time_vector,
                voltage_vector=voltage,
                raw_bytes=raw_bytes,
            )
        )
    return captures
