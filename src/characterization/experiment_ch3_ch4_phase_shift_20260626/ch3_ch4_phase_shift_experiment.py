#!/usr/bin/env python3
"""Dedicated CH3/CH4 phase-delay search experiment."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

CHARACTERIZATION_ROOT = Path(__file__).resolve().parents[1]
INSTRUMENT_CONTROL = CHARACTERIZATION_ROOT / "instrument_control"
if str(INSTRUMENT_CONTROL) not in sys.path:
    sys.path.insert(0, str(INSTRUMENT_CONTROL))

from plant_ae.deep_acquisition import (  # noqa: E402
    acquire_deep_memory_frame,
    configure_deep_memory_scope,
)
from plant_ae.phase_shift import (  # noqa: E402
    candidate_to_dict,
    cross_spectral_phase_candidates,
    delay_to_dict,
    gcc_phat_delay,
)
from plant_ae.watering import (  # noqa: E402
    CONFIG_PATH as SCOPE_CONFIG_PATH,
    HOMEASSISTANT_ENABLED_ENV,
    require_homeassistant_enabled,
)
from scope.acquisition import Capture, CaptureMetadata  # noqa: E402
from scope.config import load_config  # noqa: E402
from scope.instrument import InstrumentConnection, acquire_waveform_full  # noqa: E402

DATA_ROOT = CHARACTERIZATION_ROOT / "data" / "ch3_ch4_phase_shift_20260626"
CHANNELS = (3, 4)
ACTUATOR_PATH = CHARACTERIZATION_ROOT.parent / "actuator" / "giessen_pflanze1.py"
MIN_HA_PUMP_PULSE_S = 0.001


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def expected_delay_window(args: argparse.Namespace) -> dict[str, float]:
    distance_m = float(args.sensor_distance_mm) * 1e-3
    min_speed = float(args.min_speed_m_per_s)
    max_speed = float(args.max_speed_m_per_s)
    if distance_m <= 0 or min_speed <= 0 or max_speed <= 0 or min_speed >= max_speed:
        raise ValueError("sensor distance and speed bounds must be positive and ordered")
    return {
        "sensor_distance_mm": float(args.sensor_distance_mm),
        "min_speed_m_per_s": min_speed,
        "max_speed_m_per_s": max_speed,
        "max_expected_delay_us": distance_m / min_speed * 1e6,
        "min_expected_delay_us": distance_m / max_speed * 1e6,
    }


def load_actuator_module() -> Any:
    spec = importlib.util.spec_from_file_location("plant1_actuator", ACTUATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load actuator module: {ACTUATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build_homeassistant_client(args: argparse.Namespace) -> tuple[Any, Any]:
    require_homeassistant_enabled()
    actuator = load_actuator_module()
    sync_dir = Path(args.ha_sync_dir or actuator.DEFAULT_SYNC_DIR)
    sync_module = actuator.load_homeassistant_sync(sync_dir)
    url, token = actuator.load_connection_settings(
        sync_module,
        sync_dir,
        ha_url=args.ha_url,
        token=args.ha_token,
    )
    return actuator, sync_module.HomeAssistantRestClient(url, token, timeout=12.0)


def assert_pump_ready(actuator: Any, client: Any) -> None:
    script_state = actuator.entity_state(client, actuator.GIESS_SCRIPT_ENTITY)
    pump_state = actuator.entity_state(client, actuator.PUMPE_ENTITY)
    if script_state in {"unavailable", "unknown", ""}:
        raise RuntimeError(f"{actuator.GIESS_SCRIPT_ENTITY} is unavailable")
    if script_state == "on":
        raise RuntimeError("watering script is already running")
    if pump_state in {"unavailable", "unknown", ""}:
        raise RuntimeError(f"{actuator.PUMPE_ENTITY} is unavailable")
    if pump_state == "on":
        raise RuntimeError("pump is already on")


def homeassistant_pump_pulse(actuator: Any, client: Any, duration_s: float) -> dict[str, Any]:
    if duration_s < MIN_HA_PUMP_PULSE_S:
        raise ValueError(
            f"Refusing HA pump pulse of {duration_s * 1000:.1f} ms. "
            f"Use at least {MIN_HA_PUMP_PULSE_S * 1000:.0f} ms."
        )
    assert_pump_ready(actuator, client)
    started = time.monotonic()
    on_returned_s = None
    client.post("/api/services/switch/turn_on", {"entity_id": actuator.PUMPE_ENTITY})
    on_returned_s = time.monotonic() - started
    time.sleep(duration_s)
    client.post("/api/services/switch/turn_off", {"entity_id": actuator.PUMPE_ENTITY})
    elapsed = time.monotonic() - started
    return {
        "requested_duration_s": duration_s,
        "turn_on_returned_after_s": on_returned_s,
        "software_elapsed_s": elapsed,
        "entity_id": actuator.PUMPE_ENTITY,
        "timing_note": "Best effort via Home Assistant REST; mechanical/electrical pulse width is not calibrated.",
    }


def acquire_impulse_frame(
    conn: InstrumentConnection,
    scope_config: Any,
    *,
    sequence: int,
    sample_rate_hz: float,
    memory_depth: int,
    chunk_points: int,
    action: Any,
    action_delay_s: float,
) -> tuple[list[Capture], dict[str, Any]]:
    """Arm one acquisition, run an impulse action, then read frozen CH3/CH4 memory."""
    capture_duration_s = memory_depth / sample_rate_hz
    conn.write(":SING")
    time.sleep(max(0.0, action_delay_s))
    action_result = action()
    deadline = time.monotonic() + capture_duration_s + 10.0
    time.sleep(capture_duration_s + 0.2)
    while time.monotonic() < deadline:
        if conn.query(":TRIG:STAT?").strip().upper() == "STOP":
            break
        time.sleep(0.05)
    else:
        raise TimeoutError("Impulse acquisition did not complete")

    instrument_id = conn.query("*IDN?")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    captures: list[Capture] = []
    for channel in CHANNELS:
        preamble, raw_bytes = acquire_waveform_full(
            conn,
            channel,
            chunk_size=chunk_points,
            expected_points=memory_depth,
        )
        if len(raw_bytes) != memory_depth:
            raise RuntimeError(f"CH{channel}: received {len(raw_bytes)} points")
        actual_rate = 1.0 / preamble.xincrement
        raw = np.frombuffer(bytes(raw_bytes), dtype=np.uint8).astype(np.float32)
        voltage = ((raw - preamble.yorigin - preamble.yreference) * preamble.yincrement).astype(
            np.float32
        )
        time_vector = (
            np.arange(len(voltage), dtype=np.float64) - preamble.xreference
        ) * preamble.xincrement + preamble.xorigin
        captures.append(
            Capture(
                metadata=CaptureMetadata(
                    timestamp=timestamp,
                    instrument_idn=instrument_id,
                    channel=channel,
                    channel_label=f"ch{channel}",
                    probe_ratio=10.0,
                    sample_interval_s=preamble.xincrement,
                    sample_rate_sa_per_s=actual_rate,
                    record_length=len(voltage),
                    vertical_scale_v_per_div=0.0,
                    vertical_offset_v=0.0,
                    horizontal_scale_s_per_div=memory_depth / (12.0 * sample_rate_hz),
                    trigger_mode="EDGE",
                    trigger_source="CHAN3",
                    trigger_level_v=0.02,
                ),
                time_vector=time_vector,
                voltage_vector=voltage,
                raw_bytes=raw_bytes,
            )
        )
    return captures, action_result


def plot_phase_frame(
    path: Path,
    frequencies: np.ndarray,
    coherence: np.ndarray,
    phase: np.ndarray,
    candidates: list[Any],
    *,
    title: str,
) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(frequencies / 1000.0, coherence, linewidth=0.8)
    axes[0].set_ylabel("Coherence")
    axes[0].set_ylim(-0.02, 1.02)
    axes[0].grid(alpha=0.3)
    axes[0].set_title(title)

    axes[1].plot(frequencies / 1000.0, phase, linewidth=0.8)
    axes[1].set_xlabel("Frequency (kHz)")
    axes[1].set_ylabel("Unwrapped cross phase (rad)")
    axes[1].grid(alpha=0.3)
    for candidate in candidates[:5]:
        for ax in axes:
            ax.axvspan(
                candidate.f_low_hz / 1000.0,
                candidate.f_high_hz / 1000.0,
                color="tab:orange",
                alpha=0.15,
            )
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def save_raw_frame(path: Path, sequence: int, captures: list[Any]) -> None:
    ch3, ch4 = captures
    np.savez_compressed(
        path,
        sequence=np.array(sequence, dtype=np.int32),
        timestamp=np.array(ch3.metadata.timestamp),
        sample_rate_hz=np.array(ch3.metadata.sample_rate_sa_per_s, dtype=np.float64),
        ch3_voltage=np.asarray(ch3.voltage_vector, dtype=np.float32),
        ch4_voltage=np.asarray(ch4.voltage_vector, dtype=np.float32),
        ch3_time=np.asarray(ch3.time_vector, dtype=np.float64),
        ch4_time=np.asarray(ch4.time_vector, dtype=np.float64),
    )


def summarize_delays(frame_results: list[dict[str, Any]]) -> dict[str, Any]:
    delays = np.array(
        [
            frame["gcc_phat"]["delay_us"]
            for frame in frame_results
            if np.isfinite(frame["gcc_phat"]["delay_us"])
        ],
        dtype=float,
    )
    if delays.size == 0:
        return {}
    return {
        "gcc_phat_delay_us_median": float(np.median(delays)),
        "gcc_phat_delay_us_mean": float(np.mean(delays)),
        "gcc_phat_delay_us_std": float(np.std(delays)),
        "gcc_phat_delay_us_min": float(np.min(delays)),
        "gcc_phat_delay_us_max": float(np.max(delays)),
        "frames": int(delays.size),
    }


def run(args: argparse.Namespace) -> Path:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = DATA_ROOT / run_id
    raw_dir = run_dir / "raw"
    run_dir.mkdir(parents=True, exist_ok=False)
    if args.save_raw:
        raw_dir.mkdir()

    scope_config = load_config(SCOPE_CONFIG_PATH)
    scope_config.instrument.timeout_ms = int(args.visa_timeout_ms)

    manifest = {
        "run_id": run_id,
        "started": utc_now(),
        "channels": CHANNELS,
        "positive_delay_definition": "CH4 lags CH3",
        "parameters": vars(args),
        "expected_delay_window": expected_delay_window(args),
        "scope_config_path": str(SCOPE_CONFIG_PATH),
    }
    write_json(run_dir / "manifest.json", manifest)

    frame_results: list[dict[str, Any]] = []
    all_candidate_rows: list[dict[str, Any]] = []
    actuator = None
    ha_client = None
    if args.impulse_source == "ha-pump":
        actuator, ha_client = build_homeassistant_client(args)
        assert_pump_ready(actuator, ha_client)

    with InstrumentConnection(scope_config) as connection:
        settings = configure_deep_memory_scope(
            connection,
            sample_rate_hz=float(args.sample_rate_hz),
            memory_depth=int(args.memory_depth),
            verify_timebase=not bool(args.allow_quantized_timebase),
        )
        connection.write(":TRIG:EDGE:SOUR CHAN3")
        connection.write(f":TRIG:EDGE:LEV {float(args.trigger_level_v)}")
        connection.write(f":TRIG:SWE {args.trigger_sweep}")
        settings["trigger_source"] = connection.query(":TRIG:EDGE:SOUR?")
        settings["trigger_level_v"] = float(connection.query(":TRIG:EDGE:LEV?"))
        settings["trigger_sweep"] = connection.query(":TRIG:SWE?")
        manifest["verified_scope_settings"] = settings
        write_json(run_dir / "manifest.json", manifest)

        for sequence in range(int(args.frames)):
            action_result = None
            if args.impulse_source == "ha-pump":
                assert actuator is not None and ha_client is not None

                def action() -> dict[str, Any]:
                    return homeassistant_pump_pulse(
                        actuator,
                        ha_client,
                        float(args.pump_pulse_s),
                    )

                captures, action_result = acquire_impulse_frame(
                    connection,
                    scope_config,
                    sequence=sequence,
                    sample_rate_hz=float(args.sample_rate_hz),
                    memory_depth=int(args.memory_depth),
                    chunk_points=int(args.chunk_points),
                    action=action,
                    action_delay_s=float(args.impulse_delay_s),
                )
            else:
                captures = acquire_deep_memory_frame(
                    connection,
                    scope_config,
                    sequence=sequence,
                    sample_rate_hz=float(args.sample_rate_hz),
                    memory_depth=int(args.memory_depth),
                    chunk_points=int(args.chunk_points),
                    channels=CHANNELS,
                )
            if [capture.metadata.channel for capture in captures] != [3, 4]:
                raise RuntimeError("Unexpected channel order")

            ch3 = np.asarray(captures[0].voltage_vector, dtype=np.float64)
            ch4 = np.asarray(captures[1].voltage_vector, dtype=np.float64)
            sample_rate = float(captures[0].metadata.sample_rate_sa_per_s)

            delay = gcc_phat_delay(
                ch3,
                ch4,
                sample_rate,
                max_delay_s=float(args.max_delay_us) * 1e-6,
                interpolation=int(args.interpolation),
                min_frequency_hz=float(args.min_frequency_hz),
                max_frequency_hz=float(args.max_frequency_hz),
            )
            frequencies, coherence, phase, candidates = cross_spectral_phase_candidates(
                ch3,
                ch4,
                sample_rate,
                min_frequency_hz=float(args.min_frequency_hz),
                max_frequency_hz=float(args.max_frequency_hz),
                nperseg=int(args.nperseg),
                coherence_threshold=float(args.coherence_threshold),
                min_bandwidth_hz=float(args.min_bandwidth_hz),
                max_abs_delay_s=float(args.max_delay_us) * 1e-6,
            )

            if args.save_raw:
                save_raw_frame(raw_dir / f"frame_{sequence:04d}_ch3_ch4.npz", sequence, captures)

            plot_phase_frame(
                run_dir / f"frame_{sequence:04d}_phase.png",
                frequencies,
                coherence,
                phase,
                candidates,
                title=(
                    f"CH3->CH4 phase search frame {sequence:04d}; "
                    f"GCC-PHAT delay {delay.delay_s * 1e6:.2f} us"
                ),
            )

            candidate_dicts = [candidate_to_dict(candidate) for candidate in candidates]
            for rank, row in enumerate(candidate_dicts, start=1):
                all_candidate_rows.append({"sequence": sequence, "rank": rank, **row})

            frame_result = {
                "sequence": sequence,
                "timestamp": captures[0].metadata.timestamp,
                "sample_rate_hz": sample_rate,
                "impulse_source": args.impulse_source,
                "impulse_result": action_result,
                "gcc_phat": delay_to_dict(delay),
                "top_phase_candidates": candidate_dicts[:10],
            }
            frame_results.append(frame_result)
            print(
                f"frame={sequence:04d} gcc_delay_us={delay.delay_s * 1e6:.2f} "
                f"gcc_conf={delay.confidence:.2f} phase_candidates={len(candidates)}",
                flush=True,
            )

    if all_candidate_rows:
        with (run_dir / "phase_candidates.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(all_candidate_rows[0]))
            writer.writeheader()
            writer.writerows(all_candidate_rows)

    summary = {
        "run_id": run_id,
        "finished": utc_now(),
        "parameters": vars(args),
        "delay_summary": summarize_delays(frame_results),
        "frames": frame_results,
    }
    write_json(run_dir / "summary.json", summary)
    manifest["status"] = "finished"
    manifest["finished"] = summary["finished"]
    write_json(run_dir / "manifest.json", manifest)
    return run_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dedicated synchronized CH3/CH4 phase-delay search experiment."
    )
    parser.add_argument("--frames", type=int, default=20)
    parser.add_argument("--sample-rate-hz", type=float, default=500_000.0)
    parser.add_argument("--memory-depth", type=int, default=300_000)
    parser.add_argument("--chunk-points", type=int, default=250_000)
    parser.add_argument("--visa-timeout-ms", type=int, default=30_000)
    parser.add_argument("--save-raw", action="store_true")
    parser.add_argument("--max-delay-us", type=float, default=200.0)
    parser.add_argument("--interpolation", type=int, default=8)
    parser.add_argument("--min-frequency-hz", type=float, default=20_000.0)
    parser.add_argument("--max-frequency-hz", type=float, default=100_000.0)
    parser.add_argument("--nperseg", type=int, default=16_384)
    parser.add_argument("--coherence-threshold", type=float, default=0.7)
    parser.add_argument("--min-bandwidth-hz", type=float, default=2_000.0)
    parser.add_argument("--sensor-distance-mm", type=float, default=10.0)
    parser.add_argument("--min-speed-m-per-s", type=float, default=100.0)
    parser.add_argument("--max-speed-m-per-s", type=float, default=1600.0)
    parser.add_argument(
        "--impulse-source",
        choices=("none", "ha-pump"),
        default="none",
        help="Optional impulse source fired after the oscilloscope is armed.",
    )
    parser.add_argument("--impulse-delay-s", type=float, default=0.05)
    parser.add_argument("--pump-pulse-s", type=float, default=0.001)
    parser.add_argument("--ha-url")
    parser.add_argument("--ha-token")
    parser.add_argument("--ha-sync-dir")
    parser.add_argument(
        "--enable-homeassistant",
        action="store_true",
        help=f"Allow Home Assistant access for this run ({HOMEASSISTANT_ENABLED_ENV}=1).",
    )
    parser.add_argument("--trigger-level-v", type=float, default=0.005)
    parser.add_argument("--trigger-sweep", choices=("AUTO", "NORM"), default="NORM")
    parser.add_argument("--allow-quantized-timebase", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.enable_homeassistant:
        import os

        os.environ[HOMEASSISTANT_ENABLED_ENV] = "1"
    try:
        run_dir = run(args)
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1
    print(f"Experiment beendet. Ergebnisse: {run_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
