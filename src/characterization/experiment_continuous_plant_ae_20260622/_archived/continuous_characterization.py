#!/usr/bin/env python3
"""Continuous plant acoustic-emission characterization with environment logging.

ARCHIVIERT 2026-06-27. Letzte Produktionssession: 20260624_160540.
Ersetzt durch: notebooks/04_continuous_frequency_sweep.ipynb (NB04), gestartet
via ./measurement.py start. Dieses Skript ist für die Paper-Reproduzierbarkeit
erhalten, aber nicht mehr in Betrieb.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import signal
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import matplotlib
import numpy as np
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from plant_ae.deep_acquisition import (
    acquire_deep_memory_frame,
    configure_deep_memory_scope,
)
from plant_ae.rolling import ContinuousFrequencyMonitor, extract_frame_features
from plant_ae.watering import (
    CHANNELS,
    configure_scope,
    wait_for_single_frame,
)
from plant_ae.watering import (
    CONFIG_PATH as SCOPE_CONFIG_PATH,
)
from scope.acquisition import acquire_single_capture
from scope.config import load_config
from scope.instrument import InstrumentConnection

EXPERIMENT_DIR = Path(__file__).resolve().parent
CHARACTERIZATION_ROOT = EXPERIMENT_DIR.parent
PROJECT_SRC = CHARACTERIZATION_ROOT.parent
DEFAULT_CONFIG = EXPERIMENT_DIR / "config.yaml"
ACTUATOR_PATH = PROJECT_SRC / "actuator" / "giessen_pflanze1.py"
DATA_ROOT = CHARACTERIZATION_ROOT / "data" / "continuous_plant_ae_20260622"


def utc_now() -> str:
    return datetime.now(tz=ZoneInfo("UTC")).isoformat()


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_json(path: Path, value: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def load_actuator_module() -> Any:
    spec = importlib.util.spec_from_file_location("plant1_actuator", ACTUATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Aktormodul kann nicht geladen werden: {ACTUATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_configuration(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Ungültige Konfiguration: {path}")
    return config


def numeric_entity_state(client: Any, entity_id: str) -> float | None:
    response = client.get(f"/api/states/{entity_id}")
    if not isinstance(response, dict):
        raise RuntimeError(f"Ungültige Home-Assistant-Antwort für {entity_id}")
    state = str(response.get("state", ""))
    if state in {"", "unknown", "unavailable"}:
        return None
    return float(state)


def entity_state(client: Any, entity_id: str) -> str:
    response = client.get(f"/api/states/{entity_id}")
    if not isinstance(response, dict):
        raise RuntimeError(f"Ungültige Home-Assistant-Antwort für {entity_id}")
    return str(response.get("state", ""))


def classify_light_phase(local_time: datetime, day_start: int, night_start: int) -> str:
    if not 0 <= day_start <= 23 or not 0 <= night_start <= 23:
        raise ValueError("Tag- und Nachtbeginn müssen zwischen 0 und 23 liegen")
    if day_start == night_start:
        raise ValueError("Tag- und Nachtbeginn dürfen nicht identisch sein")
    hour = local_time.hour
    if day_start < night_start:
        return "day" if day_start <= hour < night_start else "night"
    return "day" if hour >= day_start or hour < night_start else "night"


class EnvironmentSampler:
    def __init__(self, config: dict[str, Any], actuator_module: Any):
        self.config = config
        self.module = actuator_module
        sync_dir = actuator_module.DEFAULT_SYNC_DIR
        sync_module = actuator_module.load_homeassistant_sync(sync_dir)
        url, token = actuator_module.load_connection_settings(
            sync_module, sync_dir, ha_url=None, token=None
        )
        self.client = sync_module.HomeAssistantRestClient(url, token, timeout=12.0)

    def sample(self) -> dict[str, Any]:
        environment = self.config["environment"]
        return {
            "soil_moisture_percent": numeric_entity_state(
                self.client, environment["soil_moisture_entity"]
            ),
            "pump_state": entity_state(self.client, environment["pump_entity"]),
            "watering_script_state": entity_state(
                self.client, environment["watering_script_entity"]
            ),
        }

    def assert_watering_ready(self) -> None:
        self.module.giessen(self.client, dry_run=True)

    def water_once(self) -> None:
        self.module.giessen(self.client, dry_run=False)


class ContinuousCharacterizationExperiment:
    def __init__(
        self,
        config: dict[str, Any],
        *,
        enable_watering: bool = False,
        duration_hours: float | None = None,
        max_frames: int | None = None,
        run_root: Path = DATA_ROOT,
        hardware: dict[str, Any] | None = None,
    ):
        self.config = config
        self.enable_watering = enable_watering
        self.duration_hours = duration_hours
        self.max_frames = max_frames
        self.stop_requested = False
        self.sequence = 0
        self.latest_environment: dict[str, Any] = {}
        self.soil_moisture_history: deque[float] = deque(
            maxlen=int(config["environment"].get("soil_moisture_median_samples", 10))
        )
        self.last_environment_poll = 0.0
        self.last_dashboard = 0.0
        self.last_phase: str | None = None
        self.watering_triggered = False
        self.history: deque[dict[str, Any]] = deque()

        self.timezone = ZoneInfo(config["experiment"]["timezone"])
        self.run_id = datetime.now(self.timezone).strftime("%Y%m%d_%H%M%S")
        self.run_dir = run_root / self.run_id
        self.dashboard_dir = self.run_dir / "dashboards"
        self.rolling_dir = self.run_dir / "rolling_events"
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.dashboard_dir.mkdir()

        if hardware is None:
            actuator_module = load_actuator_module()
            acquisition = config.get("acquisition", {})
            profile = acquisition.get("profile", "screen_25m")
            if profile == "deep_memory_500k":
                sample_rate_hz = float(acquisition["sample_rate_hz"])
                memory_depth = int(acquisition["memory_depth"])
                chunk_points = int(acquisition["chunk_points"])
                max_frequency_hz = float(acquisition["max_frequency_hz"])

                def configure(connection):
                    return configure_deep_memory_scope(
                        connection,
                        sample_rate_hz=sample_rate_hz,
                        memory_depth=memory_depth,
                    )

                def acquire_frame(connection, scope_config, sequence):
                    captures = acquire_deep_memory_frame(
                        connection,
                        scope_config,
                        sequence=sequence,
                        sample_rate_hz=sample_rate_hz,
                        memory_depth=memory_depth,
                        chunk_points=chunk_points,
                        channels=CHANNELS,
                    )
                    return extract_frame_features(
                        sequence,
                        captures,
                        max_frequency_hz=max_frequency_hz,
                    )

            elif profile == "screen_25m":
                configure = configure_scope
                acquire_frame = None
            else:
                raise ValueError(f"Unknown acquisition profile: {profile}")
            hardware = {
                "InstrumentConnection": InstrumentConnection,
                "load_config": load_config,
                "scope_config_path": SCOPE_CONFIG_PATH,
                "configure_scope": configure,
                "wait_for_single_frame": wait_for_single_frame,
                "acquire_single_capture": acquire_single_capture,
                "channels": CHANNELS,
                "extract_frame_features": extract_frame_features,
                "ContinuousFrequencyMonitor": ContinuousFrequencyMonitor,
                "environment_sampler": EnvironmentSampler(config, actuator_module),
                "acquire_frame": acquire_frame,
            }
        self.hardware = hardware
        monitor_config = config["monitor"]
        self.monitor = hardware["ContinuousFrequencyMonitor"](
            memory_fraction=float(monitor_config["memory_fraction"]),
            reserve_gib=float(monitor_config["reserve_gib"]),
            persist_events=False,
            save_event_raw=bool(monitor_config["save_event_raw"]),
            peak_average_frames=int(monitor_config.get("peak_average_frames", 8)),
            peak_tracker_options=monitor_config.get("peak_tracker"),
            persistent_peak_options=monitor_config.get("persistent_peaks"),
            band_detector_options=monitor_config.get("band_detector"),
        )
        self.monitor.persist_events = bool(monitor_config["persist_rolling_events"])
        self.monitor.output_dir = self.rolling_dir
        if self.monitor.persist_events or self.monitor.save_event_raw:
            self.rolling_dir.mkdir()

        self.frames_path = self.run_dir / "frame_characterization.jsonl"
        self.environment_path = self.run_dir / "environment.jsonl"
        self.events_path = self.run_dir / "experiment_events.jsonl"
        self.manifest_path = self.run_dir / "manifest.json"
        self.psd_snapshots_dir = self.run_dir / "psd_snapshots"
        self.psd_snapshots_dir.mkdir()
        self._snapshot_ring: deque[Any] = deque()
        self._last_psd_snapshot = 0.0
        self.manifest = {
            "experiment": config["experiment"],
            "run_id": self.run_id,
            "started_utc": utc_now(),
            "configuration": config,
            "watering_enabled_by_command_line": enable_watering,
            "paths": {
                "frame_characterization": str(self.frames_path),
                "environment": str(self.environment_path),
                "events": str(self.events_path),
                "rolling_events": str(self.rolling_dir),
            },
            "status": "initializing",
        }
        write_json(self.manifest_path, self.manifest)

    def request_stop(self, *_: Any) -> None:
        self.stop_requested = True

    def event(self, event: str, **details: Any) -> None:
        record = {"timestamp_utc": utc_now(), "event": event, **details}
        append_jsonl(self.events_path, record)

    def local_context(self) -> tuple[datetime, str]:
        local_time = datetime.now(self.timezone)
        experiment = self.config["experiment"]
        phase = classify_light_phase(
            local_time,
            int(experiment["day_start_hour"]),
            int(experiment["night_start_hour"]),
        )
        return local_time, phase

    def poll_environment(self, *, force: bool = False) -> None:
        now = time.monotonic()
        interval = float(self.config["environment"]["poll_interval_seconds"])
        if not force and now - self.last_environment_poll < interval:
            return
        local_time, phase = self.local_context()
        try:
            sample = self.hardware["environment_sampler"].sample()
            sample["error"] = None
        except Exception as exc:
            sample = {
                "soil_moisture_percent": None,
                "pump_state": "unknown",
                "watering_script_state": "unknown",
                "error": str(exc),
            }
            self.event("environment_read_failed", error=str(exc))
        sample.update(
            {
                "timestamp_utc": utc_now(),
                "timestamp_local": local_time.isoformat(),
                "light_phase": phase,
            }
        )
        moisture = sample.get("soil_moisture_percent")
        if moisture is not None:
            self.soil_moisture_history.append(float(moisture))
        sample["soil_moisture_median_percent"] = (
            float(np.median(self.soil_moisture_history)) if self.soil_moisture_history else None
        )
        self.latest_environment = sample
        self.last_environment_poll = now
        append_jsonl(self.environment_path, sample)
        if phase != self.last_phase:
            self.event("light_phase_changed", light_phase=phase)
            self.last_phase = phase

    def maybe_water(self, started_monotonic: float) -> None:
        watering = self.config["watering"]
        if self.watering_triggered or not self.enable_watering or not bool(watering["enabled"]):
            return
        baseline_seconds = float(watering["once_after_baseline_minutes"]) * 60
        if time.monotonic() - started_monotonic < baseline_seconds:
            return
        threshold = watering.get("only_below_soil_moisture_percent")
        moisture = self.latest_environment.get("soil_moisture_median_percent")
        if threshold is not None and (moisture is None or moisture >= float(threshold)):
            return
        sampler = self.hardware["environment_sampler"]
        sampler.assert_watering_ready()
        self.event(
            "watering_requested",
            soil_moisture_percent=moisture,
            baseline_minutes=watering["once_after_baseline_minutes"],
        )
        sampler.water_once()
        self.watering_triggered = True
        self.event("watering_triggered")

    def acquire_frame(self, connection: Any, scope_config: Any) -> Any:
        if self.hardware.get("acquire_frame") is not None:
            return self.hardware["acquire_frame"](connection, scope_config, self.sequence)
        self.hardware["wait_for_single_frame"](connection)
        captures = [
            self.hardware["acquire_single_capture"](
                connection, channel, scope_config, capture_id=self.sequence
            )
            for channel in self.hardware["channels"]
        ]
        return self.hardware["extract_frame_features"](self.sequence, captures)

    def _accumulate_snapshot_frame(self, frame: Any) -> None:
        """Append every frame to the rolling window used by PSD snapshots."""
        self._snapshot_ring.append(frame)
        window = int(self.config["monitor"].get("psd_snapshot_window_frames", 30))
        while len(self._snapshot_ring) > window:
            self._snapshot_ring.popleft()

    def maybe_save_psd_snapshot(self, frame: Any) -> None:
        """
        Periodically persist a compact, averaged Welch-PSD snapshot to disk.

        The raw waveform ring is in RAM only.  This method writes a compressed
        float32 NPZ with:
          - ``frequencies``: frequency axis in Hz (float32)
          - ``mean_psd``: mean PSD across all channels × recent frames (float32, V²/Hz)
          - ``n_frames``: number of frames averaged
          - ``timestamp_utc``: ISO-8601 string at snapshot time
          - ``band_energy``: mean 3-ch × 20-band energy matrix (float32)

        File size is ≈ 50–100 kB per snapshot regardless of capture length.

        NOTE: _accumulate_snapshot_frame must be called every frame so the ring
        holds consecutive frames; this method only writes to disk at intervals.
        """
        now = time.monotonic()
        interval_min = float(self.config["monitor"].get("psd_snapshot_interval_minutes", 60))
        if now - self._last_psd_snapshot < interval_min * 60:
            return

        if not hasattr(frame, "psd") or frame.psd is None:
            return

        frames_list = [f for f in self._snapshot_ring if hasattr(f, "psd") and f.psd is not None]
        try:
            # psd shape: (n_channels, n_freqs) per frame → stack to (n_frames, n_channels, n_freqs)
            psd_stack = np.stack([f.psd for f in frames_list], axis=0)  # (F, C, N)
            mean_psd = psd_stack.mean(axis=(0, 1)).astype(
                np.float32
            )  # (N,) mean over frames+channels
            band_energy_stack = np.stack([f.band_energy for f in frames_list], axis=0)
            mean_band_energy = band_energy_stack.mean(axis=0).astype(np.float32)
            frequencies = np.asarray(frame.frequencies, dtype=np.float32)

            ts = frame.timestamp_utc.replace(":", "-").replace("+", "p")[:19]
            snap_path = self.psd_snapshots_dir / f"psd_snapshot_{ts}_seq{frame.sequence:06d}.npz"
            np.savez_compressed(
                snap_path,
                frequencies=frequencies,
                mean_psd=mean_psd,
                band_energy=mean_band_energy,
                n_frames=np.array(len(frames_list), dtype=np.int32),
            )
            # Append a lightweight metadata record
            append_jsonl(
                self.events_path,
                {
                    "timestamp_utc": utc_now(),
                    "event": "psd_snapshot_saved",
                    "sequence": int(frame.sequence),
                    "n_frames_averaged": len(frames_list),
                    "path": str(snap_path),
                },
            )
        except Exception as exc:
            self.event("psd_snapshot_error", error=str(exc))
        finally:
            self._last_psd_snapshot = now

    def record_frame(self, frame: Any, rolling_events: list[dict[str, Any]]) -> None:
        local_time, phase = self.local_context()
        peaks = {
            str(channel): [
                {
                    "frequency_hz": float(peak["frequency_hz"]),
                    "prominence_db": float(peak["prominence_db"]),
                }
                for peak in channel_peaks
            ]
            for channel, channel_peaks in frame.peaks.items()
        }
        record = {
            "sequence": int(frame.sequence),
            "timestamp_utc": frame.timestamp_utc,
            "timestamp_local": local_time.isoformat(),
            "light_phase": phase,
            "soil_moisture_percent": self.latest_environment.get("soil_moisture_percent"),
            "soil_moisture_median_percent": self.latest_environment.get(
                "soil_moisture_median_percent"
            ),
            "pump_state": self.latest_environment.get("pump_state"),
            "watering_script_state": self.latest_environment.get("watering_script_state"),
            "band_energy": np.asarray(frame.band_energy).tolist(),
            "peaks": peaks,
            "rolling_event_count": len(rolling_events),
        }
        append_jsonl(self.frames_path, record)
        self.history.append(record)

    def save_dashboard(self, frame: Any, *, force: bool = False) -> None:
        now = time.monotonic()
        interval = float(self.config["monitor"]["dashboard_interval_minutes"]) * 60
        if not force and now - self.last_dashboard < interval:
            return
        figure = self.monitor.plot_dashboard(frame)
        figure.savefig(
            self.dashboard_dir / f"dashboard_{frame.sequence:06d}.png",
            dpi=140,
            bbox_inches="tight",
        )
        plt.close(figure)
        self.last_dashboard = now

    def save_summary(self) -> None:
        if not self.history:
            return
        records = list(self.history)
        sequences = np.array([record["sequence"] for record in records])
        energies = np.asarray([record["band_energy"] for record in records])
        phases = [record["light_phase"] for record in records]
        moisture = np.array(
            [
                np.nan
                if record["soil_moisture_percent"] is None
                else record["soil_moisture_percent"]
                for record in records
            ],
            dtype=float,
        )

        figure, axes = plt.subplots(3, 1, figsize=(16, 13), sharex=True)
        mean_energy = np.mean(energies, axis=1).T
        image = axes[0].imshow(
            10 * np.log10(np.maximum(mean_energy, 1e-30)),
            aspect="auto",
            origin="lower",
            interpolation="nearest",
            extent=[sequences[0], sequences[-1], 0, 100],
            cmap="viridis",
        )
        axes[0].set_ylabel("Frequency band (kHz)")
        axes[0].set_title("Mean 3-channel energy across all 20 bands")
        figure.colorbar(image, ax=axes[0], label="Band energy (dB V²)")

        axes[1].plot(sequences, moisture, color="tab:blue")
        axes[1].set_ylabel("Soil moisture (%)")
        axes[1].grid(alpha=0.3)

        phase_values = np.array([1 if phase == "day" else 0 for phase in phases])
        axes[2].step(sequences, phase_values, where="post", color="tab:orange")
        axes[2].set_yticks([0, 1], labels=["night", "day"])
        axes[2].set_ylabel("Clock phase")
        axes[2].set_xlabel("Frame sequence")
        axes[2].grid(alpha=0.3)
        figure.tight_layout()
        figure.savefig(self.run_dir / "continuous_summary.png", dpi=160)
        plt.close(figure)

        with (self.run_dir / "peak_tracks.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "track_id",
                    "channel",
                    "sequence",
                    "timestamp_s",
                    "frequency_hz",
                    "psd_db",
                ]
            )
            for track in self.monitor.peak_tracker.tracks.values():
                for observation in track.observations:
                    writer.writerow([track.track_id, track.channel, *observation])

    def run(self) -> Path:
        started = time.monotonic()
        duration_seconds = None if self.duration_hours is None else self.duration_hours * 3600
        self.poll_environment(force=True)
        if self.enable_watering:
            if not bool(self.config["watering"]["enabled"]):
                raise RuntimeError(
                    "--enable-watering wurde gesetzt, aber watering.enabled ist false"
                )
            self.hardware["environment_sampler"].assert_watering_ready()
        self.manifest["status"] = "running"
        write_json(self.manifest_path, self.manifest)
        self.event("experiment_started")
        latest_frame = None
        scope_config = self.hardware["load_config"](self.hardware["scope_config_path"])
        acquisition = self.config.get("acquisition", {})
        if "visa_timeout_ms" in acquisition:
            scope_config.instrument.timeout_ms = int(acquisition["visa_timeout_ms"])
        reconnect_delay = float(self.config["monitor"]["reconnect_delay_seconds"])

        try:
            while not self.stop_requested:
                if duration_seconds is not None and time.monotonic() - started >= duration_seconds:
                    break
                if self.max_frames is not None and self.sequence >= self.max_frames:
                    break
                try:
                    with self.hardware["InstrumentConnection"](scope_config) as connection:
                        settings = self.hardware["configure_scope"](connection)
                        self.manifest["verified_scope_settings"] = settings
                        write_json(self.manifest_path, self.manifest)
                        self.event("oscilloscope_connected", settings=settings)
                        while not self.stop_requested:
                            if (
                                duration_seconds is not None
                                and time.monotonic() - started >= duration_seconds
                            ):
                                break
                            if self.max_frames is not None and self.sequence >= self.max_frames:
                                break
                            self.poll_environment()
                            self.maybe_water(started)
                            frame = self.acquire_frame(connection, scope_config)
                            rolling_events = self.monitor.process_frame(frame)
                            self.record_frame(frame, rolling_events)
                            latest_frame = frame
                            self._accumulate_snapshot_frame(frame)
                            self.save_dashboard(frame)
                            self.maybe_save_psd_snapshot(frame)
                            if rolling_events:
                                self.event(
                                    "spectral_change",
                                    sequence=self.sequence,
                                    detections=rolling_events,
                                )
                            status_every = int(self.config["monitor"]["status_every_frames"])
                            if self.sequence % status_every == 0:
                                moisture = self.latest_environment.get("soil_moisture_percent")
                                _, phase = self.local_context()
                                print(
                                    f"frame={self.sequence} phase={phase} "
                                    f"soil={moisture} events={len(rolling_events)} "
                                    f"ram={self.monitor.status()['ring_usage_gib']:.2f} GiB",
                                    flush=True,
                                )
                            self.sequence += 1
                except KeyboardInterrupt:
                    self.stop_requested = True
                except Exception as exc:
                    self.event(
                        "oscilloscope_error",
                        sequence=self.sequence,
                        error=str(exc),
                    )
                    print(
                        f"Oszilloskopfehler bei Frame {self.sequence}: {exc}; "
                        f"neuer Versuch in {reconnect_delay:g} s",
                        file=sys.stderr,
                        flush=True,
                    )
                    time.sleep(reconnect_delay)
        finally:
            if latest_frame is not None:
                self.save_dashboard(latest_frame, force=True)
            self.save_summary()
            self.manifest.update(
                {
                    "status": "finished",
                    "finished_utc": utc_now(),
                    "frames": self.sequence,
                    "watering_triggered": self.watering_triggered,
                    "rolling_status": self.monitor.status(),
                }
            )
            write_json(self.manifest_path, self.manifest)
            self.event("experiment_finished", frames=self.sequence)
        return self.run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Kontinuierliche Pflanzen-AE-Charakterisierung mit Tag/Nacht- und "
            "Bodenfeuchteprotokoll. Beenden mit Ctrl+C."
        )
    )
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--duration-hours", type=float)
    parser.add_argument("--max-frames", type=int, help=argparse.SUPPRESS)
    parser.add_argument(
        "--enable-watering",
        action="store_true",
        help=(
            "Die in config.yaml konfigurierte einmalige automatische Bewässerung "
            "ausdrücklich freigeben."
        ),
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Nur Home Assistant und Oszilloskop prüfen; keine Messung und kein Gießen.",
    )
    return parser


def check_hardware(config: dict[str, Any]) -> None:
    actuator_module = load_actuator_module()
    environment = EnvironmentSampler(config, actuator_module)
    sample = environment.sample()
    environment.assert_watering_ready()
    scope_config = load_config(SCOPE_CONFIG_PATH)
    acquisition = config.get("acquisition", {})
    if "visa_timeout_ms" in acquisition:
        scope_config.instrument.timeout_ms = int(acquisition["visa_timeout_ms"])
    with InstrumentConnection(scope_config) as connection:
        if acquisition.get("profile", "screen_25m") == "deep_memory_500k":
            settings = configure_deep_memory_scope(
                connection,
                sample_rate_hz=float(acquisition["sample_rate_hz"]),
                memory_depth=int(acquisition["memory_depth"]),
            )
        else:
            settings = configure_scope(connection)
    print("Home Assistant:", json.dumps(sample, ensure_ascii=False))
    print("Oszilloskop:", json.dumps(settings, ensure_ascii=False))
    print("Prüfung erfolgreich; Pumpe wurde nicht gestartet.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = read_configuration(args.config)
        if args.check_only:
            check_hardware(config)
            return 0
        experiment = ContinuousCharacterizationExperiment(
            config,
            enable_watering=args.enable_watering,
            duration_hours=args.duration_hours,
            max_frames=args.max_frames,
        )
        signal.signal(signal.SIGTERM, experiment.request_stop)
        signal.signal(signal.SIGINT, experiment.request_stop)
        run_dir = experiment.run()
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(f"Experiment beendet. Ergebnisse: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
