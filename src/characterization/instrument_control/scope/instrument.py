"""Instrument connection and SCPI communication for Rigol DS1104Z."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Optional

import pyvisa

from .config import ExperimentConfig


@dataclass
class OscilloscopeSettings:
    channel: int
    enabled: bool = True
    coupling: str = "AC"
    probe_ratio: float = 1.0
    vertical_scale_v_per_div: float = 0.0
    vertical_offset_v: float = 0.0
    horizontal_scale_s_per_div: float = 0.0
    horizontal_offset_s: float = 0.0
    sample_rate_sa_per_s: float = 0.0
    memory_depth: int = 0
    trigger_mode: str = ""
    trigger_source: str = ""
    trigger_level_v: float = 0.0


@dataclass
class WaveformPreamble:
    format: str = ""
    type: str = ""
    points: int = 0
    count: int = 1
    xincrement: float = 0.0
    xorigin: float = 0.0
    xreference: float = 0.0
    yincrement: float = 0.0
    yorigin: float = 0.0
    yreference: float = 0.0


class InstrumentConnection:
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self._rm: Optional[pyvisa.ResourceManager] = None
        self._inst: Optional[pyvisa.resources.Resource] = None

    def open(self) -> str:
        self._rm = pyvisa.ResourceManager("@py")
        self._inst = self._rm.open_resource(
            self.config.instrument.visa_resource,
            timeout=self.config.instrument.timeout_ms,
        )
        idn = self.query("*IDN?")
        self._verify_idn(idn)
        if self.config.instrument.disable_beep:
            try:
                self.write(":SYST:BEEP OFF")
            except Exception:
                pass
        return idn

    def close(self) -> None:
        if self._inst is not None:
            try:
                self._inst.close()
            except Exception:
                pass
        if self._rm is not None:
            try:
                self._rm.close()
            except Exception:
                pass

    def query(self, command: str) -> str:
        assert self._inst is not None, "Instrument not connected"
        return self._inst.query(command).strip()

    def write(self, command: str) -> None:
        assert self._inst is not None, "Instrument not connected"
        self._inst.write(command)

    def query_binary_values(self, command: str, **kwargs) -> bytearray:
        assert self._inst is not None, "Instrument not connected"
        if 'datatype' not in kwargs:
            kwargs['datatype'] = "B"
        if 'container' not in kwargs:
            kwargs['container'] = bytearray
        return self._inst.query_binary_values(command, **kwargs)

    def query_raw(self, command: str) -> bytes:
        assert self._inst is not None, "Instrument not connected"
        return self._inst.query_raw(command)

    def _verify_idn(self, idn: str) -> None:
        for expected in self.config.instrument.idn_expected_contains:
            if expected.upper() not in idn.upper():
                raise ConnectionError(
                    f"IDN mismatch: expected '{expected}' in '{idn}'"
                )

    def __enter__(self) -> "InstrumentConnection":
        self.open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


def parse_preamble(preamble_str: str) -> WaveformPreamble:
    parts = preamble_str.split(",")
    if len(parts) < 10:
        raise ValueError(f"Preamble has only {len(parts)} fields, expected 10: {preamble_str}")
    fmt_map = {0: "BYTE", 1: "WORD", 2: "ASC"}
    type_map = {0: "NORMAL", 1: "PEAK", 2: "AVERAGE"}
    return WaveformPreamble(
        format=fmt_map.get(int(parts[0]), parts[0]),
        type=type_map.get(int(parts[1]), parts[1]),
        points=int(parts[2]),
        count=int(parts[3]),
        xincrement=float(parts[4]),
        xorigin=float(parts[5]),
        xreference=float(parts[6]),
        yincrement=float(parts[7]),
        yorigin=float(parts[8]),
        yreference=float(parts[9]),
    )


def read_oscilloscope_settings(
    conn: InstrumentConnection, channel: int
) -> OscilloscopeSettings:
    ch_str = f"CHAN{channel}"
    enabled = conn.query(f":{ch_str}:DISP?") == "1"
    coupling = conn.query(f":{ch_str}:COUP?")
    probe_ratio = float(conn.query(f":{ch_str}:PROB?"))
    vert_scale = float(conn.query(f":{ch_str}:SCAL?"))
    vert_offset = float(conn.query(f":{ch_str}:OFFS?"))
    horiz_scale = float(conn.query(":TIM:SCAL?"))
    horiz_offset = float(conn.query(":TIM:OFFS?"))
    sample_rate = float(conn.query(":ACQ:SRAT?"))
    memory_depth_str = conn.query(":ACQ:MDEP?")
    try:
        memory_depth = int(float(memory_depth_str))
    except ValueError:
        memory_depth = 0
    trigger_mode = conn.query(":TRIG:MODE?")
    trigger_source = ""
    trigger_level = 0.0
    try:
        trigger_source = conn.query(":TRIG:EDGE:SOUR?")
        trigger_level = float(conn.query(":TRIG:EDGE:LEV?"))
    except Exception:
        pass
    return OscilloscopeSettings(
        channel=channel,
        enabled=enabled,
        coupling=coupling,
        probe_ratio=probe_ratio,
        vertical_scale_v_per_div=vert_scale,
        vertical_offset_v=vert_offset,
        horizontal_scale_s_per_div=horiz_scale,
        horizontal_offset_s=horiz_offset,
        sample_rate_sa_per_s=sample_rate,
        memory_depth=memory_depth,
        trigger_mode=trigger_mode,
        trigger_source=trigger_source,
        trigger_level_v=trigger_level,
    )


def write_oscilloscope_settings(
    conn: InstrumentConnection, settings: OscilloscopeSettings
) -> None:
    ch_str = f"CHAN{settings.channel}"
    conn.write(f":{ch_str}:DISP {'ON' if settings.enabled else 'OFF'}")
    conn.write(f":{ch_str}:COUP {settings.coupling}")
    conn.write(f":{ch_str}:PROB {settings.probe_ratio}")
    if settings.vertical_scale_v_per_div > 0:
        conn.write(f":{ch_str}:SCAL {settings.vertical_scale_v_per_div}")
    if settings.vertical_offset_v != 0:
        conn.write(f":{ch_str}:OFFS {settings.vertical_offset_v}")
    if settings.horizontal_scale_s_per_div > 0:
        conn.write(f":TIM:SCAL {settings.horizontal_scale_s_per_div}")
    if settings.horizontal_offset_s != 0:
        conn.write(f":TIM:OFFS {settings.horizontal_offset_s}")


def get_preamble(conn: InstrumentConnection, channel: int) -> WaveformPreamble:
    ch_str = f"CHAN{channel}"
    conn.write(f":WAV:SOUR {ch_str}")
    raw = conn.query(":WAV:PRE?")
    return parse_preamble(raw)


def acquire_waveform_bytes(
    conn: InstrumentConnection,
    channel: int,
    mode: str = "RAW",
    fmt: str = "BYTE",
    max_points: int = 100000,
) -> tuple[WaveformPreamble, bytearray]:
    ch_str = f"CHAN{channel}"
    conn.write(f":WAV:SOUR {ch_str}")
    conn.write(f":WAV:MODE {mode}")
    conn.write(f":WAV:FORM {fmt}")
    
    # Begrenze Punkte für schnelleren Transfer
    preamble = get_preamble(conn, channel)
    if preamble.points > max_points:
        conn.write(f":WAV:POIN {max_points}")
        preamble = get_preamble(conn, channel)
    
    # BYTE-Format: datatype='B' (unsigned char)
    datatype = 'B' if fmt == "BYTE" else 'H'
    raw_data = conn.query_binary_values(
        ":WAV:DATA?", datatype=datatype, container=bytearray
    )
    return preamble, raw_data


def acquire_waveform_full(
    conn: InstrumentConnection,
    channel: int,
    chunk_size: int = 250_000,
    expected_points: int | None = None,
) -> tuple[WaveformPreamble, bytearray]:
    """
    Read the FULL deep-memory RAW waveform for *channel* via chunked paging.

    The Rigol DS1000Z series returns at most ~250 000 points per ``:WAV:DATA?``
    request in RAW mode, and a bare ``:WAV:DATA?`` without an explicit
    ``:WAV:STAR`` / ``:WAV:STOP`` window returns almost nothing (≈100 bytes).
    The full record must therefore be paged out in chunks.

    Preconditions (caller's responsibility):
    * The scope must be STOPPED (e.g. after ``:SING`` completes) so the deep
      acquisition memory is frozen and readable.
    * Memory depth must already be set explicitly via ``:ACQ:MDEP`` — ``AUTO``
      does not select deep memory at slow time-bases.

    Returns ``(preamble, raw_bytes)`` with ``len(raw_bytes)`` equal to the
    record length (``preamble.points``) on success.
    """
    ch_str = f"CHAN{channel}"
    conn.write(f":WAV:SOUR {ch_str}")
    conn.write(":WAV:MODE RAW")
    conn.write(":WAV:FORM BYTE")
    preamble = get_preamble(conn, channel)

    total = preamble.points
    if expected_points is not None and total != expected_points:
        # Trust the preamble (ground truth) but warn via the returned value.
        total = preamble.points or expected_points

    data = bytearray()
    start = 1
    while start <= total:
        stop = min(start + chunk_size - 1, total)
        conn.write(f":WAV:STAR {start}")
        conn.write(f":WAV:STOP {stop}")
        chunk = conn.query_binary_values(
            ":WAV:DATA?", datatype="B", container=bytearray
        )
        if not chunk:
            break
        data.extend(chunk)
        start += len(chunk)  # advance by what we actually received
    return preamble, data


def bytes_to_voltage(
    raw_data: bytearray, preamble: WaveformPreamble
) -> list[float]:
    yincr = preamble.yincrement
    yorig = preamble.yorigin
    yref = preamble.yreference
    return [(b - yorig - yref) * yincr for b in raw_data]


def build_time_vector(preamble: WaveformPreamble) -> list[float]:
    xincr = preamble.xincrement
    xorig = preamble.xorigin
    xref = preamble.xreference
    return [(i - xref) * xincr + xorig for i in range(preamble.points)]
