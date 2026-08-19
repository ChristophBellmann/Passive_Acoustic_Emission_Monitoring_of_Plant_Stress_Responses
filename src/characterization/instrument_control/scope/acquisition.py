"""Waveform acquisition from Rigol DS1104Z."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

from .config import ExperimentConfig
from .instrument import (
    InstrumentConnection,
    OscilloscopeSettings,
    acquire_waveform_bytes,
    build_time_vector,
    bytes_to_voltage,
    read_oscilloscope_settings,
)


@dataclass
class CaptureMetadata:
    timestamp: str
    instrument_idn: str
    channel: int
    channel_label: str
    probe_ratio: float
    sample_interval_s: float
    sample_rate_sa_per_s: float
    record_length: int
    vertical_scale_v_per_div: float
    vertical_offset_v: float
    horizontal_scale_s_per_div: float
    trigger_mode: str = ""
    trigger_source: str = ""
    trigger_level_v: float = 0.0


@dataclass
class Capture:
    metadata: CaptureMetadata
    time_vector: np.ndarray
    voltage_vector: np.ndarray
    raw_bytes: bytearray


def acquire_single_capture(
    conn: InstrumentConnection,
    channel: int,
    config: ExperimentConfig,
    capture_id: int = 0,
    stop_before: bool = False,
    run_after: bool = False,
) -> Capture:
    ch_cfg = config.oscilloscope.channel_settings.get(channel)
    label = ch_cfg.label if ch_cfg else f"ch{channel}"
    probe_ratio = ch_cfg.probe_ratio if ch_cfg else 1.0

    osc_settings = read_oscilloscope_settings(conn, channel)

    if stop_before:
        try:
            conn.write(":STOP")
        except Exception:
            pass

    preamble, raw_data = acquire_waveform_bytes(
        conn,
        channel,
        mode=config.acquisition.waveform_mode,
        fmt="BYTE",  # BYTE funktioniert jetzt korrekt
        max_points=100000,
    )

    if run_after:
        try:
            conn.write(":RUN")
        except Exception:
            pass

    # Verwende die Preamble-Yincrement für die Spannungsberechnung
    # Die Preamble-Yincrement ist die tatsächliche Spannung pro Count am Oszilloskop-Eingang
    voltage = np.array(bytes_to_voltage(raw_data, preamble), dtype=np.float64)
    
    # Verwende tatsächliche Datenlänge statt Preamble
    actual_points = len(raw_data)
    time_vec = np.array(
        [(i - preamble.xreference) * preamble.xincrement + preamble.xorigin 
         for i in range(actual_points)],
        dtype=np.float64
    )

    # WICHTIG: Die probe_ratio ist bereits in der Preamble-Yincrement enthalten!
    # Wenn das Oszilloskop auf 10:1 Probe eingestellt ist, zeigt die Preamble-Yincrement
    # die Spannung am Messpunkt an, nicht die Spannung am Eingang.
    # Daher müssen wir die probe_ratio NICHT nochmal anwenden.

    idn = conn.query("*IDN?")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    metadata = CaptureMetadata(
        timestamp=timestamp,
        instrument_idn=idn,
        channel=channel,
        channel_label=label,
        probe_ratio=probe_ratio,
        sample_interval_s=preamble.xincrement,
        sample_rate_sa_per_s=1.0 / preamble.xincrement if preamble.xincrement != 0 else 0.0,
        record_length=preamble.points,
        vertical_scale_v_per_div=osc_settings.vertical_scale_v_per_div,
        vertical_offset_v=osc_settings.vertical_offset_v,
        horizontal_scale_s_per_div=osc_settings.horizontal_scale_s_per_div,
        trigger_mode=osc_settings.trigger_mode,
        trigger_source=osc_settings.trigger_source,
        trigger_level_v=osc_settings.trigger_level_v,
    )

    return Capture(
        metadata=metadata,
        time_vector=time_vec,
        voltage_vector=voltage,
        raw_bytes=raw_data,
    )


def acquire_series(
    conn: InstrumentConnection,
    config: ExperimentConfig,
    progress_callback: Optional[object] = None,
) -> list[Capture]:
    captures: list[Capture] = []
    channels = config.oscilloscope.channels
    n_captures = config.acquisition.captures
    delay = config.acquisition.delay_between_captures_s

    for i in range(n_captures):
        for ch in channels:
            ch_cfg = config.oscilloscope.channel_settings.get(ch)
            if ch_cfg and not ch_cfg.enabled:
                continue
            cap = acquire_single_capture(conn, ch, config, capture_id=i)
            captures.append(cap)
        if i < n_captures - 1 and delay > 0:
            time.sleep(delay)

    return captures


def save_capture_npz(capture: Capture, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{capture.metadata.timestamp}_capture_ch{capture.metadata.channel}.npz"
    path = output_dir / fname
    np.savez(
        path,
        time_vector=capture.time_vector,
        voltage_vector=capture.voltage_vector,
        metadata=np.array([_metadata_to_dict(capture.metadata)]),
    )
    return path


def save_capture_csv(capture: Capture, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{capture.metadata.timestamp}_capture_ch{capture.metadata.channel}.csv"
    path = output_dir / fname
    import pandas as pd

    df = pd.DataFrame({
        "time_s": capture.time_vector,
        "voltage_v": capture.voltage_vector,
    })
    df.to_csv(path, index=False)
    return path


def _metadata_to_dict(m: CaptureMetadata) -> dict:
    return {
        "timestamp": m.timestamp,
        "instrument_idn": m.instrument_idn,
        "channel": m.channel,
        "channel_label": m.channel_label,
        "probe_ratio": m.probe_ratio,
        "sample_interval_s": m.sample_interval_s,
        "sample_rate_sa_per_s": m.sample_rate_sa_per_s,
        "record_length": m.record_length,
        "vertical_scale_v_per_div": m.vertical_scale_v_per_div,
        "vertical_offset_v": m.vertical_offset_v,
        "horizontal_scale_s_per_div": m.horizontal_scale_s_per_div,
        "trigger_mode": m.trigger_mode,
        "trigger_source": m.trigger_source,
        "trigger_level_v": m.trigger_level_v,
    }
