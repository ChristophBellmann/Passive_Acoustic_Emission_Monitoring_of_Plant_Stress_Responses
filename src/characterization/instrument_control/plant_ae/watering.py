"""Controlled acquisition, watering and before/after analysis primitives."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import sys
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal, stats
from scipy.optimize import linear_sum_assignment
from scope.acquisition import acquire_single_capture
from scope.config import load_config
from scope.instrument import InstrumentConnection
from .deep_acquisition import CHANNEL_HW_CONFIG

HOMEASSISTANT_ENABLED_ENV = "PLANT_AE_HOMEASSISTANT_ENABLED"
_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}
CHARACTERIZATION_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SRC = CHARACTERIZATION_ROOT.parent
ACTUATOR_MODULE_PATH = PROJECT_SRC / "actuator" / "giessen_pflanze1.py"
CONFIG_PATH = CHARACTERIZATION_ROOT / "configs" / "experiment_piezo_mems.yaml"
DATA_ROOT = CHARACTERIZATION_ROOT / "data" / "watering_experiment"
REPORT_ROOT = CHARACTERIZATION_ROOT / "data" / "reports" / "notebooks" / "03_watering_experiment"


def homeassistant_enabled(*, default: bool = False) -> bool:
    value = os.environ.get(HOMEASSISTANT_ENABLED_ENV)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise RuntimeError(
        f"Invalid {HOMEASSISTANT_ENABLED_ENV}={value!r}; use 1/0, true/false, yes/no, on/off."
    )


def require_homeassistant_enabled() -> None:
    if not homeassistant_enabled(default=False):
        raise RuntimeError(
            "Home Assistant is disabled. Set "
            f"{HOMEASSISTANT_ENABLED_ENV}=1 or enable it in the control panel."
        )


def load_project_actuator():
    spec = importlib.util.spec_from_file_location("plant1_actuator", ACTUATOR_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load actuator module: {ACTUATOR_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class HomeAssistantPlant1Actuator:
    def __init__(
        self, *, ha_url: str | None = None, token: str | None = None, sync_dir: Path | None = None
    ):
        require_homeassistant_enabled()
        self.module = load_project_actuator()
        self.sync_dir = sync_dir or self.module.DEFAULT_SYNC_DIR
        sync_module = self.module.load_homeassistant_sync(self.sync_dir)
        resolved_url, resolved_token = self.module.load_connection_settings(
            sync_module, self.sync_dir, ha_url=ha_url, token=token
        )
        self.client = sync_module.HomeAssistantRestClient(
            resolved_url, resolved_token, timeout=12.0
        )

    def assert_ready(self) -> None:
        self.module.giessen(self.client, dry_run=True)

    def water(self) -> None:
        self.module.giessen(self.client, dry_run=False)

    def wait_until_ready(self, timeout_s: float = 300.0, poll_s: float = 2.0) -> None:
        deadline = time.monotonic() + timeout_s
        last_error = None
        while time.monotonic() < deadline:
            try:
                self.assert_ready()
                return
            except Exception as exc:
                last_error = exc
                time.sleep(poll_s)
        raise TimeoutError(f"Actuator did not become ready: {last_error}")


def run_homeassistant_watering_protocol(
    actuator: HomeAssistantPlant1Actuator,
    *,
    idle_cycles: int = 20,
    post_cycles: int = 20,
    settle_after_watering_s: float = 60.0,
) -> dict[str, Path]:
    protocol_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    protocol_dir = DATA_ROOT / f"{protocol_id}_ha_watering_protocol"
    protocol_dir.mkdir(parents=True, exist_ok=False)
    manifest = {"protocol_id": protocol_id, "started_utc": utc_now(), "events": [], "runs": {}}

    def event(name: str, **details) -> None:
        manifest["events"].append({"timestamp_utc": utc_now(), "event": name, **details})
        write_json(protocol_dir / "protocol_manifest.json", manifest)

    actuator.assert_ready()
    event("mcu_on_idle_reference_start")
    idle_dir = acquire_condition(
        "mcu_on_idle",
        notes=f"Protocol {protocol_id}: Home Assistant actuator ready, pump off",
        cycles=idle_cycles,
    )
    event("watering_triggered", duration_s=actuator.module.GIESSZEIT_SEKUNDEN)
    actuator.water()
    event("watering_script_started")
    time.sleep(actuator.module.GIESSZEIT_SEKUNDEN + settle_after_watering_s)
    event("post_watering_capture_start")
    post_dir = acquire_condition(
        "post_watering",
        notes=f"Protocol {protocol_id}: after Home Assistant watering script",
        cycles=post_cycles,
    )
    runs = {"mcu_on_idle_pre": idle_dir, "post_watering": post_dir}
    manifest["runs"] = {name: str(path) for name, path in runs.items()}
    manifest["finished_utc"] = utc_now()
    write_json(protocol_dir / "protocol_manifest.json", manifest)
    create_condition_plots(idle_dir)
    create_condition_plots(post_dir)
    create_comparison_plots(idle_dir, post_dir, f"{protocol_id}_post_watering_vs_idle")
    return runs


class SerialWateringController:
    def __init__(self, port: str, baudrate: int = 115200, timeout_s: float = 2.0):
        try:
            import serial
        except ImportError as exc:
            raise RuntimeError("Install pyserial before using the hardware controller") from exc
        self._serial = serial.Serial(port, baudrate=baudrate, timeout=timeout_s)
        time.sleep(2.0)
        self.command("PING")

    def command(self, text: str) -> str:
        self._serial.reset_input_buffer()
        self._serial.write((text.strip() + "\n").encode("ascii"))
        self._serial.flush()
        response = self._serial.readline().decode("ascii", errors="replace").strip()
        if response != "OK":
            raise RuntimeError(f"Controller rejected {text!r}: {response!r}")
        return response

    def pump(self, enabled: bool) -> None:
        self.command("PUMP ON" if enabled else "PUMP OFF")

    def route(self, target: str) -> None:
        target = target.upper()
        if target not in {"PLANT", "WASTE"}:
            raise ValueError(target)
        self.command(f"VALVE {target}")

    def close(self) -> None:
        try:
            self.pump(False)
        finally:
            self._serial.close()


class DryRunWateringController:
    def __init__(self):
        self.events = []

    def _record(self, command: str) -> None:
        self.events.append({"timestamp_utc": utc_now(), "command": command})
        print(f"[dry-run] {command}")

    def pump(self, enabled: bool) -> None:
        self._record("PUMP ON" if enabled else "PUMP OFF")

    def route(self, target: str) -> None:
        self._record(f"VALVE {target.upper()}")

    def close(self) -> None:
        self.pump(False)


def run_programmatic_protocol(
    controller,
    *,
    idle_cycles: int = 20,
    pump_control_cycles: int = 5,
    post_cycles: int = 20,
    watering_duration_s: float = 5.0,
    post_watering_delay_s: float = 60.0,
) -> dict[str, Path]:
    protocol_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    protocol_dir = DATA_ROOT / f"{protocol_id}_protocol"
    protocol_dir.mkdir(parents=True, exist_ok=False)
    protocol_manifest = {
        "protocol_id": protocol_id,
        "started_utc": utc_now(),
        "parameters": {
            "idle_cycles": idle_cycles,
            "pump_control_cycles": pump_control_cycles,
            "post_cycles": post_cycles,
            "watering_duration_s": watering_duration_s,
            "post_watering_delay_s": post_watering_delay_s,
        },
        "events": [],
        "runs": {},
    }

    def event(name: str, **details) -> None:
        protocol_manifest["events"].append({"timestamp_utc": utc_now(), "event": name, **details})
        write_json(protocol_dir / "protocol_manifest.json", protocol_manifest)

    runs: dict[str, Path] = {}
    try:
        controller.pump(False)
        controller.route("WASTE")
        event("reference_start", condition="mcu_on_idle_pre")
        runs["mcu_on_idle_pre"] = acquire_condition(
            "mcu_on_idle",
            notes=f"Protocol {protocol_id}: automatic pre-watering reference; pump OFF",
            cycles=idle_cycles,
        )
        event("pump_control_start", route="WASTE")
        controller.pump(True)
        runs["pump_control"] = acquire_condition(
            "pump_control",
            notes=f"Protocol {protocol_id}: pump ON, route WASTE",
            cycles=pump_control_cycles,
        )
        controller.pump(False)
        event("pump_control_stop")
        controller.route("PLANT")
        event("watering_start", duration_s=watering_duration_s)
        controller.pump(True)
        time.sleep(watering_duration_s)
        controller.pump(False)
        event("watering_stop")
        if post_watering_delay_s > 0:
            event("post_watering_wait_start", duration_s=post_watering_delay_s)
            time.sleep(post_watering_delay_s)
        event("post_watering_capture_start")
        runs["post_watering"] = acquire_condition(
            "post_watering",
            notes=f"Protocol {protocol_id}: pump OFF after programmatic watering",
            cycles=post_cycles,
        )
    finally:
        controller.pump(False)
    protocol_manifest["runs"] = {name: str(path) for name, path in runs.items()}
    protocol_manifest["finished_utc"] = utc_now()
    write_json(protocol_dir / "protocol_manifest.json", protocol_manifest)
    for run_dir in runs.values():
        create_condition_plots(run_dir)
    create_comparison_plots(
        runs["mcu_on_idle_pre"], runs["pump_control"], f"{protocol_id}_pump_vs_idle"
    )
    create_comparison_plots(
        runs["mcu_on_idle_pre"], runs["post_watering"], f"{protocol_id}_post_watering_vs_idle"
    )
    return runs


CHANNEL_COLORS = {1: "#aaaaaa", 2: "#ffff00", 3: "#00ff00", 4: "#00aaff"}

CHANNEL_LABELS = {
    1: "CH1 Verstärker + Piezo",
    3: "CH3 Verstärker + MEMS-Mikrofon",
    4: "CH4 Verstärker + MEMS-Mikrofon",
}


def load_condition_signals(run_dir: Path) -> dict[int, dict]:
    result = {channel: {"voltage": [], "psd": [], "metadata": []} for channel in CHANNELS}
    frequency_axis = None
    ref_samples: int | None = None
    ref_rate: float | None = None
    for path in sorted((run_dir / "raw").glob("*.npz")):
        voltage, metadata = load_capture(path)
        channel = int(metadata["channel"])
        sample_rate = float(metadata["sample_rate_sa_per_s"])
        if ref_samples is None:
            ref_samples, ref_rate = len(voltage), sample_rate
        if len(voltage) != ref_samples or sample_rate != ref_rate:
            continue
        cleaned = signal.detrend(voltage, type="linear")
        frequencies, psd = signal.periodogram(
            cleaned, fs=sample_rate, window="hann", scaling="density"
        )
        if frequency_axis is None:
            frequency_axis = frequencies
        elif not np.array_equal(frequency_axis, frequencies):
            raise ValueError("Frequency axes differ within condition")
        result[channel]["voltage"].append(voltage)
        result[channel]["psd"].append(psd)
        result[channel]["metadata"].append(metadata)
    for channel in CHANNELS:
        if not result[channel]["psd"]:
            raise ValueError(f"No valid CH{channel} data in {run_dir}")
        result[channel]["voltage"] = np.asarray(result[channel]["voltage"])
        result[channel]["psd"] = np.asarray(result[channel]["psd"])
        result[channel]["frequencies"] = frequency_axis
        result[channel]["mean_psd"] = result[channel]["psd"].mean(axis=0)
    return result


def _quadratic_peak_frequency(frequencies: np.ndarray, values_db: np.ndarray, index: int) -> float:
    if index <= 0 or index >= len(values_db) - 1:
        return float(frequencies[index])
    left, center, right = values_db[index - 1 : index + 2]
    denominator = left - 2 * center + right
    if denominator == 0:
        return float(frequencies[index])
    offset = np.clip(0.5 * (left - right) / denominator, -0.5, 0.5)
    return float(frequencies[index] + offset * (frequencies[1] - frequencies[0]))


def detect_condition_peaks(
    frequencies: np.ndarray,
    psd: np.ndarray,
    prominence_db: float = 6.0,
    min_distance_hz: float = 500.0,
    max_peaks: int = 20,
    max_frequency_hz: float = 100_000.0,
    ignore_frequency_bands_hz: tuple[tuple[float, float], ...] = (),
) -> list[dict]:
    mask = (frequencies >= 20.0) & (frequencies <= max_frequency_hz)
    selected_frequencies = frequencies[mask]
    selected_db = 10 * np.log10(np.maximum(psd[mask], 1e-30))
    resolution = selected_frequencies[1] - selected_frequencies[0]
    indices, properties = signal.find_peaks(
        selected_db,
        prominence=prominence_db,
        distance=max(1, int(round(min_distance_hz / resolution))),
    )
    order = np.argsort(properties["prominences"])[::-1][:max_peaks]
    peaks = []
    for order_index in order:
        index = int(indices[order_index])
        frequency_hz = _quadratic_peak_frequency(selected_frequencies, selected_db, index)
        if any(low_hz <= frequency_hz <= high_hz for low_hz, high_hz in ignore_frequency_bands_hz):
            continue
        peaks.append(
            {
                "frequency_hz": frequency_hz,
                "bin_frequency_hz": float(selected_frequencies[index]),
                "psd_db": float(selected_db[index]),
                "prominence_db": float(properties["prominences"][order_index]),
            }
        )
    return sorted(peaks, key=lambda peak: peak["frequency_hz"])


def representative_capture(voltages: np.ndarray) -> np.ndarray:
    rms = np.sqrt(np.mean(voltages**2, axis=1))
    return voltages[np.argmin(np.abs(rms - np.median(rms)))]


def create_condition_plots(run_dir: Path) -> dict[int, list[dict]]:
    data = load_condition_signals(run_dir)
    output_dir = run_dir / "plots"
    output_dir.mkdir(parents=True, exist_ok=True)
    condition = run_dir.name
    sample_rate = float(data[CHANNELS[0]]["metadata"][0]["sample_rate_sa_per_s"])
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor("#1a1a1a")
    ax.set_facecolor("#0a0a0a")
    for channel in CHANNELS:
        voltage = representative_capture(data[channel]["voltage"])
        time_ms = np.arange(len(voltage)) / sample_rate * 1000
        normalized = voltage / max(np.max(np.abs(voltage)), 1e-30)
        ax.plot(
            time_ms,
            normalized + (channel - 2) * 1.2,
            color=CHANNEL_COLORS[channel],
            linewidth=0.8,
            label=CHANNEL_LABELS[channel],
        )
    ax.set_xlabel("Time (ms)", color="white")
    ax.set_ylabel("Normalized amplitude + channel offset", color="white")
    ax.set_title(f"{condition}: representative synchronized waveforms", color="white")
    ax.tick_params(colors="white")
    ax.grid(True, color="gray", alpha=0.3)
    ax.legend(facecolor="#2a2a2a", labelcolor="white")
    fig.tight_layout()
    fig.savefig(output_dir / "oscilloscope_overlay.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    for channel in CHANNELS:
        voltage = representative_capture(data[channel]["voltage"])
        time_ms = np.arange(len(voltage)) / sample_rate * 1000
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor("#1a1a1a")
        ax.set_facecolor("#0a0a0a")
        ax.plot(time_ms, voltage * 1000, color=CHANNEL_COLORS[channel], linewidth=0.8)
        ax.set_xlabel("Time (ms)", color="white")
        ax.set_ylabel("Voltage (mV)", color="white")
        ax.set_title(f"{condition}: {CHANNEL_LABELS[channel]}", color="white")
        ax.tick_params(colors="white")
        ax.grid(True, color="gray", alpha=0.3)
        info = (
            f"Vpp: {np.ptp(voltage) * 1000:.2f} mV\n"
            f"RMS: {np.sqrt(np.mean(voltage**2)) * 1000:.2f} mV"
        )
        ax.text(
            0.02,
            0.97,
            info,
            transform=ax.transAxes,
            va="top",
            color="white",
            bbox={"boxstyle": "round", "facecolor": "#2a2a2a", "edgecolor": "white"},
        )
        fig.tight_layout()
        fig.savefig(output_dir / f"oscilloscope_ch{channel}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)
    detected = {}
    fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    fig.patch.set_facecolor("#1a1a1a")
    for axis, channel in zip(axes, CHANNELS, strict=True):
        axis.set_facecolor("#0a0a0a")
        frequencies = data[channel]["frequencies"]
        mean_psd = data[channel]["mean_psd"]
        mask = (frequencies >= 20) & (frequencies <= MAX_FREQUENCY_HZ)
        spectrum_db = 10 * np.log10(np.maximum(mean_psd, 1e-30))
        peaks = detect_condition_peaks(frequencies, mean_psd)
        detected[channel] = peaks
        axis.plot(
            frequencies[mask] / 1000,
            spectrum_db[mask],
            color=CHANNEL_COLORS[channel],
            linewidth=0.9,
        )
        for peak in sorted(peaks, key=lambda item: item["prominence_db"], reverse=True)[:8]:
            frequency_khz = peak["frequency_hz"] / 1000
            axis.axvline(frequency_khz, color="#ff5555", alpha=0.45, linestyle="--")
            axis.annotate(
                f"{frequency_khz:.2f} kHz",
                (frequency_khz, peak["psd_db"]),
                xytext=(4, 6),
                textcoords="offset points",
                color="yellow",
                fontsize=8,
                rotation=45,
            )
        axis.set_ylabel("PSD (dB V²/Hz)", color="white")
        axis.set_title(
            f"{CHANNEL_LABELS[channel]} — mean of {len(data[channel]['psd'])} captures",
            color="white",
        )
        axis.tick_params(colors="white")
        axis.grid(True, color="gray", alpha=0.3)
    axes[-1].set_xlabel("Frequency (kHz)", color="white")
    axes[-1].set_xlim(0, 100)
    fig.suptitle(f"{condition}: detected plant-emission candidates", color="white", fontsize=14)
    fig.tight_layout()
    fig.savefig(output_dir / "oscilloscope_spectrum.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    write_json(output_dir / "detected_peaks.json", {str(k): v for k, v in detected.items()})
    return detected


def _local_peak_distribution(
    frequencies: np.ndarray, spectra: np.ndarray, center_hz: float, radius_hz: float = 1000.0
) -> np.ndarray:
    mask = (frequencies >= center_hz - radius_hz) & (frequencies <= center_hz + radius_hz)
    local_frequencies = frequencies[mask]
    values = []
    for psd in spectra:
        local_db = 10 * np.log10(np.maximum(psd[mask], 1e-30))
        index = int(np.argmax(local_db))
        values.append(_quadratic_peak_frequency(local_frequencies, local_db, index))
    return np.asarray(values)


def match_condition_peaks(
    before_data: dict[int, dict], after_data: dict[int, dict], tolerance_hz: float = 2000.0
) -> list[dict]:
    matches = []
    for channel in CHANNELS:
        frequencies = before_data[channel]["frequencies"]
        if not np.array_equal(frequencies, after_data[channel]["frequencies"]):
            raise ValueError("Before and after frequency axes differ")
        before_peaks = detect_condition_peaks(frequencies, before_data[channel]["mean_psd"])
        after_peaks = detect_condition_peaks(frequencies, after_data[channel]["mean_psd"])
        if not before_peaks or not after_peaks:
            continue
        cost = np.abs(
            np.subtract.outer(
                [peak["frequency_hz"] for peak in before_peaks],
                [peak["frequency_hz"] for peak in after_peaks],
            )
        )
        rows, columns = linear_sum_assignment(cost)
        for row, column in zip(rows, columns, strict=True):
            if cost[row, column] > tolerance_hz:
                continue
            before_peak = before_peaks[row]
            after_peak = after_peaks[column]
            center = (before_peak["frequency_hz"] + after_peak["frequency_hz"]) / 2
            before_distribution = _local_peak_distribution(
                frequencies, before_data[channel]["psd"], center
            )
            after_distribution = _local_peak_distribution(
                frequencies, after_data[channel]["psd"], center
            )
            before_median = float(np.median(before_distribution))
            after_median = float(np.median(after_distribution))
            shift = after_median - before_median
            p_value = float(stats.mannwhitneyu(before_distribution, after_distribution).pvalue)
            matches.append(
                {
                    "channel": channel,
                    "before_frequency_hz": before_median,
                    "after_frequency_hz": after_median,
                    "shift_hz": shift,
                    "before_iqr_hz": float(np.ptp(np.percentile(before_distribution, [25, 75]))),
                    "after_iqr_hz": float(np.ptp(np.percentile(after_distribution, [25, 75]))),
                    "amplitude_change_db": after_peak["psd_db"] - before_peak["psd_db"],
                    "prominence_before_db": before_peak["prominence_db"],
                    "prominence_after_db": after_peak["prominence_db"],
                    "p_value_unadjusted": p_value,
                    "shift_exceeds_resolution": bool(
                        abs(shift) >= 2 * (frequencies[1] - frequencies[0])
                    ),
                }
            )
    if matches:
        p_values = np.asarray([match["p_value_unadjusted"] for match in matches])
        order = np.argsort(p_values)
        ranked = p_values[order] * len(p_values) / np.arange(1, len(p_values) + 1)
        adjusted_ranked = np.minimum.accumulate(ranked[::-1])[::-1]
        adjusted = np.empty_like(adjusted_ranked)
        adjusted[order] = np.clip(adjusted_ranked, 0, 1)
        for match, adjusted_p in zip(matches, adjusted, strict=True):
            match["p_value_fdr"] = float(adjusted_p)
    return matches


def create_comparison_plots(
    before_dir: Path,
    after_dir: Path,
    comparison_name: str,
    *,
    report_root: Path = REPORT_ROOT,
) -> list[dict]:
    before = load_condition_signals(before_dir)
    after = load_condition_signals(after_dir)
    output_dir = report_root / comparison_name
    output_dir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    for axis, channel in zip(axes, CHANNELS, strict=True):
        frequencies = before[channel]["frequencies"]
        mask = (frequencies >= 20) & (frequencies <= MAX_FREQUENCY_HZ)
        before_db = 10 * np.log10(np.maximum(before[channel]["mean_psd"], 1e-30))
        after_db = 10 * np.log10(np.maximum(after[channel]["mean_psd"], 1e-30))
        axis.plot(frequencies[mask] / 1000, before_db[mask], label=before_dir.name, linewidth=0.9)
        axis.plot(frequencies[mask] / 1000, after_db[mask], label=after_dir.name, linewidth=0.9)
        axis.set_ylabel("PSD (dB V²/Hz)")
        axis.set_title(CHANNEL_LABELS[channel])
        axis.grid(alpha=0.3)
        axis.legend()
    axes[-1].set_xlabel("Frequency (kHz)")
    axes[-1].set_xlim(0, 100)
    fig.suptitle(f"{comparison_name}: spectra before and after")
    fig.tight_layout()
    fig.savefig(output_dir / "spectrum_before_after.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    fig, axes = plt.subplots(3, 1, figsize=(14, 11), sharex=True)
    for axis, channel in zip(axes, CHANNELS, strict=True):
        frequencies = before[channel]["frequencies"]
        mask = (frequencies >= 20) & (frequencies <= MAX_FREQUENCY_HZ)
        difference_db = 10 * np.log10(
            np.maximum(after[channel]["mean_psd"], 1e-30)
            / np.maximum(before[channel]["mean_psd"], 1e-30)
        )
        axis.plot(frequencies[mask] / 1000, difference_db[mask], color="purple", linewidth=0.8)
        axis.axhline(0, color="black", linewidth=0.7)
        axis.set_ylabel("After / before (dB)")
        axis.set_title(CHANNEL_LABELS[channel])
        axis.grid(alpha=0.3)
    axes[-1].set_xlabel("Frequency (kHz)")
    axes[-1].set_xlim(0, 100)
    fig.suptitle(f"{comparison_name}: frequency-resolved spectral difference")
    fig.tight_layout()
    fig.savefig(output_dir / "spectrum_difference_db.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    matches = match_condition_peaks(before, after)
    with (output_dir / "peak_shifts.csv").open("w", newline="", encoding="utf-8") as handle:
        if matches:
            writer = csv.DictWriter(handle, fieldnames=list(matches[0]))
            writer.writeheader()
            writer.writerows(matches)
    write_json(output_dir / "peak_shifts.json", {"matches": matches})
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    for axis, channel in zip(axes, CHANNELS, strict=True):
        channel_matches = [match for match in matches if match["channel"] == channel]
        if channel_matches:
            x = np.array([match["before_frequency_hz"] for match in channel_matches]) / 1000
            y = np.array([match["shift_hz"] for match in channel_matches])
            colors = [
                "tab:red" if match["shift_exceeds_resolution"] else "tab:gray"
                for match in channel_matches
            ]
            axis.scatter(x, y, c=colors, s=55)
            for frequency, shift in zip(x, y, strict=True):
                axis.annotate(
                    f"{shift:+.0f} Hz",
                    (frequency, shift),
                    xytext=(4, 4),
                    textcoords="offset points",
                    fontsize=8,
                )
        axis.axhline(0, color="black", linewidth=0.7)
        axis.axhspan(-500, 500, color="gray", alpha=0.12, label="±2 bins")
        axis.set_ylabel("Peak shift (Hz)")
        axis.set_title(CHANNEL_LABELS[channel])
        axis.grid(alpha=0.3)
    axes[-1].set_xlabel("Peak frequency before condition (kHz)")
    fig.suptitle(f"{comparison_name}: matched frequency shifts")
    fig.tight_layout()
    fig.savefig(output_dir / "peak_frequency_shifts.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    before_rows = analyze_condition(before_dir)
    after_rows = analyze_condition(after_dir)
    band_figure, band_results = compare_conditions(before_rows, after_rows, comparison_name)
    band_figure.savefig(output_dir / "band_energy_change_db.png", dpi=160, bbox_inches="tight")
    plt.close(band_figure)
    write_json(output_dir / "band_energy_change.json", band_results)
    return matches


CHANNELS = (1, 3, 4)  # CH2 defekt (Hardware-Ausfall)

CYCLES_PER_CONDITION = 20

MAX_ATTEMPTS_PER_CONDITION = 40

EXPECTED_SAMPLE_RATE_HZ = 25000000.0

EXPECTED_SAMPLES = 100000

MAX_FREQUENCY_HZ = 250000.0

BAND_WIDTH_HZ = 5000.0

CONDITIONS = {
    "mcu_off": {"mcu": False, "pump": False, "water_to_plant": False},
    "mcu_on_idle": {"mcu": True, "pump": False, "water_to_plant": False},
    "pump_control": {"mcu": True, "pump": True, "water_to_plant": False},
    "watering": {"mcu": True, "pump": True, "water_to_plant": True},
    "post_watering": {"mcu": True, "pump": False, "water_to_plant": True},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def configure_scope(conn: InstrumentConnection) -> dict:
    """Configure scope channels from CHANNEL_HW_CONFIG (single source of truth)."""
    conn.write(":STOP")
    active_channels = {ch for ch, _, _ in CHANNEL_HW_CONFIG}
    for ch in (1, 2, 3, 4):
        if ch in active_channels:
            probe = next(p for c, p, _ in CHANNEL_HW_CONFIG if c == ch)
            scale = next(s for c, _, s in CHANNEL_HW_CONFIG if c == ch)
            conn.write(f":CHAN{ch}:DISP ON")
            conn.write(f":CHAN{ch}:COUP AC")
            conn.write(f":CHAN{ch}:PROB {probe}")
            conn.write(f":CHAN{ch}:SCAL {scale}")
            conn.write(f":CHAN{ch}:OFFS 0")
        else:
            conn.write(f":CHAN{ch}:DISP OFF")  # CH2 defekt
    conn.write(":TIM:SCAL 0.01")
    conn.write(":TIM:OFFS 0")
    conn.write(":TRIG:MODE EDGE")
    conn.write(":TRIG:EDGE:SOUR CHAN1")
    conn.write(":TRIG:EDGE:LEV 0.02")
    conn.write(":TRIG:SWE AUTO")

    # The Rigol applies memory-depth changes reliably only while running.
    # Reset AUTO explicitly so a previous deep-memory experiment cannot
    # silently leave this workflow at the wrong sample rate.
    conn.write(":RUN")
    time.sleep(0.3)
    conn.write(":ACQ:MDEP AUTO")
    time.sleep(1.2)

    settings = {
        "sample_rate_hz": float(conn.query(":ACQ:SRAT?")),
        "memory_depth": conn.query(":ACQ:MDEP?"),
        "horizontal_scale_s_per_div": float(conn.query(":TIM:SCAL?")),
        "trigger_mode": conn.query(":TRIG:MODE?"),
        "trigger_source": conn.query(":TRIG:EDGE:SOUR?"),
        "trigger_level_v": float(conn.query(":TRIG:EDGE:LEV?")),
    }
    if not np.isclose(settings["sample_rate_hz"], EXPECTED_SAMPLE_RATE_HZ):
        raise RuntimeError(f"Unexpected sample rate: {settings['sample_rate_hz']}")
    if not np.isclose(settings["horizontal_scale_s_per_div"], 0.01):
        raise RuntimeError(f"Unexpected time scale: {settings['horizontal_scale_s_per_div']}")
    return settings


def wait_for_single_frame(conn: InstrumentConnection, timeout_s: float = 5.0) -> None:
    conn.write(":STOP")
    time.sleep(0.1)
    conn.write(":SING")
    time.sleep(0.35)
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if conn.query(":TRIG:STAT?").strip().upper() == "STOP":
            return
        time.sleep(0.05)
    raise TimeoutError("Single acquisition did not complete")


def save_capture(path: Path, capture, cycle: int, condition: str) -> None:
    metadata = asdict(capture.metadata)
    metadata.update({"cycle": cycle, "condition": condition})
    np.savez(
        path,
        time_vector=capture.time_vector,
        voltage_vector=capture.voltage_vector,
        metadata=np.array([metadata]),
    )


def acquire_condition(condition: str, notes: str = "", cycles: int = CYCLES_PER_CONDITION) -> Path:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = DATA_ROOT / f"{run_id}_{condition}"
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "condition": condition,
        "condition_state": CONDITIONS[condition],
        "hardware_configuration": {
            "effective_from": "2026-07-14",
            "CH1": "Piezo + existing LM amplifier",
            "CH3": "MEMS microphone + existing LM amplifier",
            "CH4": "MEMS microphone + existing LM amplifier",
            "home_assistant_available": False,
            "automatic_watering": False,
            "temperature_recording": False,
        },
        "config_path": str(CONFIG_PATH),
        "notes": notes,
        "started_utc": utc_now(),
        "cycles_requested": cycles,
        "captures": [],
        "rejected_attempts": [],
        "events": [],
    }
    manifest_path = run_dir / "manifest.json"
    write_json(manifest_path, manifest)
    config = load_config(CONFIG_PATH)
    with InstrumentConnection(config) as conn:
        manifest["instrument_idn"] = conn.query("*IDN?")
        manifest["verified_settings"] = configure_scope(conn)
        write_json(manifest_path, manifest)
        accepted = 0
        attempts = 0
        while accepted < cycles and attempts < MAX_ATTEMPTS_PER_CONDITION:
            attempts += 1
            try:
                wait_for_single_frame(conn)
                captures = [
                    acquire_single_capture(conn, channel, config, capture_id=accepted)
                    for channel in CHANNELS
                ]
                lengths = [len(capture.voltage_vector) for capture in captures]
                rates = [capture.metadata.sample_rate_sa_per_s for capture in captures]
                if lengths != [EXPECTED_SAMPLES] * len(CHANNELS) or len(set(rates)) != 1:
                    raise ValueError(f"Invalid frame lengths={lengths}, rates={rates}")
                for capture in captures:
                    filename = f"cycle_{accepted:03d}_ch{capture.metadata.channel}.npz"
                    save_capture(raw_dir / filename, capture, accepted, condition)
                    manifest["captures"].append(
                        {
                            "cycle": accepted,
                            "channel": capture.metadata.channel,
                            "file": filename,
                            "samples": len(capture.voltage_vector),
                            "sample_rate_hz": capture.metadata.sample_rate_sa_per_s,
                        }
                    )
                accepted += 1
                print(f"{condition}: accepted cycle {accepted}/{cycles}")
            except Exception as exc:
                manifest["rejected_attempts"].append({"attempt": attempts, "reason": str(exc)})
                print(f"{condition}: rejected attempt {attempts}: {exc}")
            finally:
                manifest["cycles_accepted"] = accepted
                manifest["updated_utc"] = utc_now()
                write_json(manifest_path, manifest)
    manifest["finished_utc"] = utc_now()
    write_json(manifest_path, manifest)
    if accepted != cycles:
        raise RuntimeError(f"Only {accepted}/{cycles} cycles accepted; data retained in {run_dir}")
    return run_dir


BAND_COLUMNS = [f"energy_{low}_{low + 5}khz" for low in range(0, 100, 5)]


def load_capture(path: Path) -> tuple[np.ndarray, dict]:
    data = np.load(path, allow_pickle=True)
    return (np.asarray(data["voltage_vector"], dtype=float), data["metadata"][0])


def analyze_capture(path: Path) -> dict:
    voltage, metadata = load_capture(path)
    sample_rate = float(metadata["sample_rate_sa_per_s"])
    cleaned = signal.detrend(voltage, type="linear")
    frequencies, psd = signal.periodogram(cleaned, fs=sample_rate, window="hann", scaling="density")
    row = {
        "file": path.name,
        "condition": str(metadata.get("condition", "unknown")),
        "cycle": int(metadata.get("cycle", -1)),
        "channel": int(metadata["channel"]),
        "sample_rate_hz": sample_rate,
        "samples": len(voltage),
        "duration_s": len(voltage) / sample_rate,
        "frequency_resolution_hz": frequencies[1] - frequencies[0],
        "rms_v": float(np.sqrt(np.mean(cleaned**2))),
        "peak_to_peak_v": float(np.ptp(voltage)),
    }
    for low in range(0, 100, 5):
        mask = (frequencies >= low * 1000) & (frequencies < (low + 5) * 1000)
        row[f"energy_{low}_{low + 5}khz"] = float(np.trapezoid(psd[mask], frequencies[mask]))
    return row


def analyze_condition(run_dir: Path) -> list[dict]:
    rows = [analyze_capture(path) for path in sorted((run_dir / "raw").glob("*.npz"))]
    if not rows:
        raise ValueError(f"No captures in {run_dir}")
    signatures = {(r["sample_rate_hz"], r["samples"], r["duration_s"]) for r in rows}
    if len(signatures) != 1:
        raise ValueError(f"Mixed acquisition settings: {signatures}")
    output = run_dir / "capture_metrics.csv"
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def compare_conditions(before_rows: list[dict], after_rows: list[dict], title: str):
    before_signature = {(r["sample_rate_hz"], r["samples"], r["duration_s"]) for r in before_rows}
    after_signature = {(r["sample_rate_hz"], r["samples"], r["duration_s"]) for r in after_rows}
    if before_signature != after_signature or len(before_signature) != 1:
        raise ValueError(f"Acquisition settings differ: {before_signature} vs {after_signature}")
    channels = sorted({r["channel"] for r in before_rows} & {r["channel"] for r in after_rows})
    fig, axes = plt.subplots(len(channels), 1, figsize=(14, 4 * len(channels)), squeeze=False)
    results = {}
    x = np.arange(len(BAND_COLUMNS))
    for axis, channel in zip(axes[:, 0], channels, strict=True):
        before = np.array(
            [[r[column] for column in BAND_COLUMNS] for r in before_rows if r["channel"] == channel]
        )
        after = np.array(
            [[r[column] for column in BAND_COLUMNS] for r in after_rows if r["channel"] == channel]
        )
        before_mean = before.mean(axis=0)
        after_mean = after.mean(axis=0)
        change_db = 10 * np.log10(np.maximum(after_mean, 1e-30) / np.maximum(before_mean, 1e-30))
        p_values = [
            stats.mannwhitneyu(before[:, i], after[:, i]).pvalue for i in range(len(BAND_COLUMNS))
        ]
        axis.bar(x, change_db, color=np.where(change_db >= 0, "tab:red", "tab:blue"))
        axis.axhline(0, color="black", linewidth=0.8)
        axis.set_xticks(x)
        axis.set_xticklabels([c.removeprefix("energy_") for c in BAND_COLUMNS], rotation=45)
        axis.set_ylabel("Change (dB)")
        axis.set_title(f"CH{channel}: {title}")
        axis.grid(alpha=0.3, axis="y")
        results[str(channel)] = {
            column: {"change_db": float(change_db[i]), "p_value_unadjusted": float(p_values[i])}
            for i, column in enumerate(BAND_COLUMNS)
        }
    fig.tight_layout()
    return (fig, results)
