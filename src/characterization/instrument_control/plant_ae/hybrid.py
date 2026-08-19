"""Automated hybrid rolling-window and snapshot watering experiment."""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import numpy as np
from scope.config import load_config
from scope.instrument import InstrumentConnection

from .deep_acquisition import (
    DEFAULT_MEMORY_DEPTH,
    DEFAULT_SAMPLE_RATE_HZ,
    acquire_deep_memory_frame,
    configure_deep_memory_scope,
)
from .rolling import ContinuousFrequencyMonitor, extract_frame_features
from .watering import (
    CHANNELS,
    CONFIG_PATH,
    analyze_condition,
    create_comparison_plots,
    create_condition_plots,
    utc_now,
    write_json,
)

CHARACTERIZATION_ROOT = Path(__file__).resolve().parents[2]
HYBRID_DATA_ROOT = CHARACTERIZATION_ROOT / "data" / "hybrid_watering_experiment"
HYBRID_REPORT_ROOT = (
    CHARACTERIZATION_ROOT / "data" / "reports" / "notebooks" / "05_automated_hybrid_experiment"
)


def persist_snapshot_frames(frames, output_dir: Path, condition: str, notes: str) -> Path:
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "condition": condition,
        "notes": notes,
        "created_utc": utc_now(),
        "cycles_accepted": len(frames),
        "captures": [],
        "source": "continuous RAM ring",
    }
    for cycle, frame in enumerate(frames):
        rate = frame.sample_rate_hz if frame.sample_rate_hz > 0 else DEFAULT_SAMPLE_RATE_HZ
        for channel_index, channel in enumerate(CHANNELS):
            voltage = np.asarray(frame.voltages[channel_index], dtype=np.float64)
            time_vector = np.arange(len(voltage), dtype=np.float64) / rate
            metadata = {
                "timestamp": frame.timestamp_utc,
                "channel": channel,
                "channel_label": f"hybrid_ch{channel}",
                "sample_interval_s": 1 / rate,
                "sample_rate_sa_per_s": rate,
                "record_length": len(voltage),
                "cycle": cycle,
                "source_sequence": frame.sequence,
                "condition": condition,
            }
            filename = f"cycle_{cycle:03d}_ch{channel}.npz"
            np.savez(
                raw_dir / filename,
                time_vector=time_vector,
                voltage_vector=voltage,
                metadata=np.array([metadata]),
            )
            manifest["captures"].append(
                {
                    "cycle": cycle,
                    "channel": channel,
                    "source_sequence": frame.sequence,
                    "file": filename,
                }
            )
    write_json(output_dir / "manifest.json", manifest)
    return output_dir


class AutomatedHybridExperiment:
    def __init__(
        self,
        actuator,
        *,
        warmup_frames: int = 10,
        pre_snapshot_frames: int = 20,
        settle_frames: int = 5,
        post_snapshot_frames: int = 20,
        memory_fraction: float = 0.75,
        reserve_gib: float = 4.0,
        persist_rolling_events: bool = True,
    ):
        self.actuator = actuator
        self.warmup_frames = warmup_frames
        self.pre_snapshot_frames = pre_snapshot_frames
        self.settle_frames = settle_frames
        self.post_snapshot_frames = post_snapshot_frames
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = HYBRID_DATA_ROOT / self.run_id
        self.report_dir = HYBRID_REPORT_ROOT / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)
        self.report_dir.mkdir(parents=True, exist_ok=False)
        self.monitor = ContinuousFrequencyMonitor(
            memory_fraction=memory_fraction,
            reserve_gib=reserve_gib,
            persist_events=False,
            save_event_raw=False,
        )
        self.monitor.persist_events = persist_rolling_events
        self.monitor.output_dir = self.run_dir / "rolling_events"
        if persist_rolling_events:
            self.monitor.output_dir.mkdir(parents=True, exist_ok=False)
        self.manifest = {
            "run_id": self.run_id,
            "started_utc": utc_now(),
            "parameters": {
                "warmup_frames": warmup_frames,
                "pre_snapshot_frames": pre_snapshot_frames,
                "settle_frames": settle_frames,
                "post_snapshot_frames": post_snapshot_frames,
                "memory_fraction": memory_fraction,
                "reserve_gib": reserve_gib,
                "persist_rolling_events": persist_rolling_events,
            },
            "rolling_event_dir": str(self.monitor.output_dir),
            "events": [],
            "snapshots": {},
        }
        self._write_manifest()

    def _write_manifest(self) -> None:
        write_json(self.run_dir / "hybrid_manifest.json", self.manifest)

    def _event(self, name: str, **details) -> None:
        self.manifest["events"].append({"timestamp_utc": utc_now(), "event": name, **details})
        self._write_manifest()

    def _acquire_frame(self, conn, config, sequence: int):
        captures = acquire_deep_memory_frame(
            conn,
            config,
            sequence=sequence,
            sample_rate_hz=DEFAULT_SAMPLE_RATE_HZ,
            memory_depth=DEFAULT_MEMORY_DEPTH,
        )
        frame = extract_frame_features(sequence, captures)
        events = self.monitor.process_frame(frame)
        if events:
            self._event("rolling_events", sequence=sequence, detections=events)
        return frame

    def run(self) -> dict[str, Path]:
        self.actuator.assert_ready()
        config = load_config(CONFIG_PATH)
        sequence = 0
        watering_frames = []
        post_frames = []
        with InstrumentConnection(config) as conn:
            settings = configure_deep_memory_scope(conn)
            self.manifest["verified_scope_settings"] = settings
            self._write_manifest()
            required_reference_frames = self.warmup_frames + self.pre_snapshot_frames
            self._event("rolling_reference_start", required_frames=required_reference_frames)
            while sequence < required_reference_frames:
                self._acquire_frame(conn, config, sequence)
                sequence += 1
                print(f"Reference/rolling frame {sequence}/{required_reference_frames}")
            pre_frames = list(self.monitor.ring.frames)[-self.pre_snapshot_frames :]
            pre_dir = persist_snapshot_frames(
                pre_frames,
                self.run_dir / "snapshot_pre_watering",
                "mcu_on_idle",
                "Automatically selected from the RAM ring immediately before watering",
            )
            self.manifest["snapshots"]["pre_watering"] = str(pre_dir)
            self._event(
                "pre_snapshot_materialized",
                first_sequence=pre_frames[0].sequence,
                last_sequence=pre_frames[-1].sequence,
            )
            watering_duration_s = float(self.actuator.module.GIESSZEIT_SEKUNDEN)
            self._event("watering_trigger_requested", duration_s=watering_duration_s)
            self.actuator.water()
            self._event("watering_started")
            watering_deadline = time.monotonic() + watering_duration_s
            while time.monotonic() < watering_deadline or not watering_frames:
                frame = self._acquire_frame(conn, config, sequence)
                watering_frames.append(frame)
                sequence += 1
                print(f"Watering/rolling frame {len(watering_frames)}")
            self.actuator.wait_until_ready(timeout_s=120.0, poll_s=1.0)
            self._event("watering_confirmed_complete", frames=len(watering_frames))
            for index in range(self.settle_frames):
                self._acquire_frame(conn, config, sequence)
                sequence += 1
                print(f"Settle/rolling frame {index + 1}/{self.settle_frames}")
            for index in range(self.post_snapshot_frames):
                post_frames.append(self._acquire_frame(conn, config, sequence))
                sequence += 1
                print(f"Post/rolling frame {index + 1}/{self.post_snapshot_frames}")
        watering_dir = persist_snapshot_frames(
            watering_frames,
            self.run_dir / "snapshot_watering_event",
            "watering",
            "Frames acquired while the Home Assistant watering script was active",
        )
        post_dir = persist_snapshot_frames(
            post_frames,
            self.run_dir / "snapshot_post_watering",
            "post_watering",
            "Automatically selected post-watering frames from the same rolling stream",
        )
        self.manifest["snapshots"].update(
            {"watering_event": str(watering_dir), "post_watering": str(post_dir)}
        )
        self.manifest["finished_utc"] = utc_now()
        self.manifest["rolling_status"] = self.monitor.status()
        self._write_manifest()
        for snapshot_dir in (pre_dir, watering_dir, post_dir):
            analyze_condition(snapshot_dir)
            create_condition_plots(snapshot_dir)
        create_comparison_plots(
            pre_dir, watering_dir, "watering_event_vs_pre", report_root=self.report_dir
        )
        create_comparison_plots(
            pre_dir, post_dir, "post_watering_vs_pre", report_root=self.report_dir
        )
        self._event("analysis_complete", report_dir=str(self.report_dir))
        return {
            "pre_watering": pre_dir,
            "watering_event": watering_dir,
            "post_watering": post_dir,
            "report_dir": self.report_dir,
        }
