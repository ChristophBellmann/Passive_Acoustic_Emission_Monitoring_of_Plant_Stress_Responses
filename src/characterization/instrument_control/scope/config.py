"""Configuration loading and validation."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field


class InstrumentConfig(BaseModel):
    visa_resource: str = "TCPIP::192.168.178.70::INSTR"
    idn_expected_contains: list[str] = Field(default_factory=lambda: ["RIGOL", "DS1104Z"])
    timeout_ms: int = 10000
    disable_beep: bool = True


class ChannelSetting(BaseModel):
    enabled: bool = True
    label: str = ""
    probe_ratio: float = 1.0
    coupling: str = "AC"
    vertical_scale_v_per_div: Optional[float] = None
    offset_v: Optional[float] = None
    amplitude_calibrated: bool = False
    notes: str = ""


class OscilloscopeConfig(BaseModel):
    channels: list[int] = Field(default_factory=lambda: [1, 2])
    channel_settings: dict[int, ChannelSetting] = Field(default_factory=dict)


class AcquisitionConfig(BaseModel):
    captures: int = 20
    delay_between_captures_s: float = 1.0
    memory_depth: str = "AUTO"
    waveform_mode: str = "RAW"
    waveform_format: str = "BYTE"
    auto_setup_allowed: bool = False
    stop_before_read: bool = True
    restore_run_after_read: bool = True


class WelchConfig(BaseModel):
    enabled: bool = True
    nperseg: int = 4096
    overlap: float = 0.5


class StftConfig(BaseModel):
    enabled: bool = True
    nperseg: int = 2048
    overlap: float = 0.75


class ProcessingConfig(BaseModel):
    remove_dc: bool = True
    detrend: bool = True
    window: str = "hann"
    min_frequency_hz: float = 5.0
    max_frequency_hz: Optional[float] = None
    welch: WelchConfig = Field(default_factory=WelchConfig)
    stft: StftConfig = Field(default_factory=StftConfig)


class PeakDetectionConfig(BaseModel):
    prominence_db: float = 8.0
    min_distance_hz: float = 20.0
    max_peaks: int = 20
    ignore_frequency_bands_hz: list[list[float]] = Field(
        default_factory=lambda: [[48, 52], [98, 102], [148, 152], [198, 202]]
    )


class PlausibilityConfig(BaseModel):
    clipping_threshold_fraction: float = 0.98
    min_snr_db: float = 6.0
    repeatability_min_fraction: float = 0.4
    mains_frequencies_hz: list[float] = Field(
        default_factory=lambda: [50.0, 100.0, 150.0, 200.0]
    )
    switching_noise_check: bool = True
    aliasing_check: bool = True


class OutputConfig(BaseModel):
    save_raw_csv: bool = True
    save_npz: bool = True
    save_plots: bool = True
    save_report_markdown: bool = True
    plot_format: str = "png"


class ExperimentConfig(BaseModel):
    instrument: InstrumentConfig = Field(default_factory=InstrumentConfig)
    oscilloscope: OscilloscopeConfig = Field(default_factory=OscilloscopeConfig)
    acquisition: AcquisitionConfig = Field(default_factory=AcquisitionConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    peak_detection: PeakDetectionConfig = Field(default_factory=PeakDetectionConfig)
    plausibility: PlausibilityConfig = Field(default_factory=PlausibilityConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_config(path: str | Path) -> ExperimentConfig:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r") as f:
        raw: dict[str, Any] = yaml.safe_load(f)
    if raw is None:
        raw = {}
    if "oscilloscope" in raw and "channel_settings" in raw["oscilloscope"]:
        cs = raw["oscilloscope"]["channel_settings"]
        raw["oscilloscope"]["channel_settings"] = {
            int(k): v for k, v in cs.items()
        }
    return ExperimentConfig(**raw)


def get_git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"
