#!/usr/bin/env python3
"""Acquire a short, repeatable Phase-3 sensor sanity test."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

from plant_ae.deep_acquisition import (
    acquire_deep_memory_frame,
    configure_deep_memory_scope,
)
from plant_ae.rolling import extract_frame_features
from scope.config import load_config
from scope.instrument import InstrumentConnection


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment_piezo_mems.yaml"
OUTPUT_ROOT = ROOT / "data" / "test_measurements_phase3"
CHANNELS = (1, 3, 4)
CHANNEL_LABELS = {
    1: "Piezo + LM amplifier",
    3: "MEMS A + LM amplifier",
    4: "MEMS B + LM amplifier",
}


def channel_metrics(capture) -> dict:
    voltage = np.asarray(capture.voltage_vector, dtype=float)
    centered = signal.detrend(voltage, type="constant")
    raw = np.frombuffer(bytes(capture.raw_bytes), dtype=np.uint8)
    return {
        "mean_v": float(np.mean(voltage)),
        "rms_ac_v": float(np.sqrt(np.mean(centered**2))),
        "peak_to_peak_v": float(np.ptp(voltage)),
        "max_abs_ac_v": float(np.max(np.abs(centered))),
        "raw_min": int(raw.min()),
        "raw_max": int(raw.max()),
        "rail_fraction": float(np.mean((raw <= 1) | (raw >= 254))),
    }


def acquire_run(*, captures_target: int, power_supply: str) -> Path:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    config = load_config(CONFIG_PATH)
    frames = []
    records = []
    errors = []
    attempts = 0
    instrument_id = ""
    scope_profile = None

    try:
        with InstrumentConnection(config) as conn:
            instrument_id = conn.query("*IDN?")
            scope_profile = configure_deep_memory_scope(conn)
            print(f"Instrument: {instrument_id}", flush=True)
            print(f"Scope profile: {scope_profile}", flush=True)
            try:
                while len(frames) < captures_target and attempts < captures_target * 3:
                    attempts += 1
                    try:
                        channel_captures = acquire_deep_memory_frame(
                            conn, config, sequence=len(frames)
                        )
                        frame = extract_frame_features(len(frames), channel_captures)
                    except Exception as exc:
                        message = f"attempt {attempts}: {type(exc).__name__}: {exc}"
                        errors.append(message)
                        print(f"Skipped {message}", flush=True)
                        configure_deep_memory_scope(conn)
                        continue

                    np.savez_compressed(
                        output_dir / f"capture_{len(frames) + 1:03d}.npz",
                        channels=np.asarray(CHANNELS, dtype=np.int16),
                        sample_rate_hz=np.asarray(frame.sample_rate_hz),
                        timestamp_utc=np.asarray(frame.timestamp_utc),
                        voltages=frame.voltages.astype(np.float32),
                    )
                    per_channel = {
                        str(capture.metadata.channel): {
                            **channel_metrics(capture),
                            "dominant_peaks": frame.peaks.get(
                                int(capture.metadata.channel), []
                            )[:10],
                        }
                        for capture in channel_captures
                    }
                    records.append(
                        {
                            "capture": len(frames) + 1,
                            "timestamp_utc": frame.timestamp_utc,
                            "channels": per_channel,
                        }
                    )
                    frames.append(frame)
                    print(
                        f"Valid frame {len(frames)}/{captures_target}: "
                        + ", ".join(
                            f"CH{channel} RMS="
                            f"{per_channel[str(channel)]['rms_ac_v'] * 1e3:.3f} mV "
                            f"pp={per_channel[str(channel)]['peak_to_peak_v'] * 1e3:.3f} mV"
                            for channel in CHANNELS
                        ),
                        flush=True,
                    )
            finally:
                conn.write(":RUN")
    except Exception as exc:
        errors.append(f"fatal: {type(exc).__name__}: {exc}")
        (output_dir / "FAILED.txt").write_text(
            "\n".join(errors) + "\n", encoding="utf-8"
        )
        raise

    if len(frames) != captures_target:
        raise RuntimeError(f"Only {len(frames)}/{captures_target} valid frames")

    aggregates = {}
    for channel in CHANNELS:
        values = [record["channels"][str(channel)] for record in records]
        rms = np.asarray([value["rms_ac_v"] for value in values])
        peak_to_peak = np.asarray([value["peak_to_peak_v"] for value in values])
        rail_fraction = np.asarray([value["rail_fraction"] for value in values])
        aggregates[str(channel)] = {
            "label": CHANNEL_LABELS[channel],
            "rms_ac_mean_v": float(np.mean(rms)),
            "rms_ac_std_v": float(np.std(rms)),
            "peak_to_peak_max_v": float(np.max(peak_to_peak)),
            "rail_fraction_max": float(np.max(rail_fraction)),
            "not_rail_clipped": bool(np.max(rail_fraction) == 0.0),
        }

    frequencies = frames[0].frequencies.astype(float)
    mean_psd = np.mean(np.stack([frame.psd for frame in frames]), axis=0)
    search = (frequencies >= 4_500) & (frequencies <= 6_500)
    interference = {}
    for channel_index, channel in enumerate(CHANNELS):
        local_index = int(np.argmax(mean_psd[channel_index, search]))
        frequency = float(frequencies[search][local_index])
        psd = float(mean_psd[channel_index, search][local_index])
        interference[str(channel)] = {
            "frequency_hz": frequency,
            "psd_v2_per_hz": psd,
            "psd_db_v2_per_hz": float(10 * np.log10(max(psd, 1e-30))),
        }

    line_frequency = interference["3"]["frequency_hz"]
    line_coherence = []
    for frame in frames:
        f_coh, coherence = signal.coherence(
            frame.voltages[1],
            frame.voltages[2],
            fs=frame.sample_rate_hz,
            nperseg=16_384,
        )
        index = int(np.argmin(np.abs(f_coh - line_frequency)))
        line_coherence.append(float(coherence[index]))

    summary = {
        "run_id": run_id,
        "phase": 3,
        "location": "soil next to the new plant at Julian's setup",
        "power_supply": power_supply,
        "instrument_idn": instrument_id,
        "utc_finished": datetime.now(timezone.utc).isoformat(),
        "scope_profile": scope_profile,
        "captures_valid": len(frames),
        "attempts": attempts,
        "transfer_errors": errors,
        "home_assistant_available": False,
        "automatic_watering": False,
        "temperature_recording": False,
        "channels": aggregates,
        "interference_line_near_5_39_khz": interference,
        "ch3_ch4_line_coherence": {
            "mean": float(np.mean(line_coherence)),
            "min": float(np.min(line_coherence)),
        },
        "records": records,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )

    fig, ax = plt.subplots(figsize=(12, 6), constrained_layout=True)
    mask = (frequencies >= 20) & (frequencies <= 100_000)
    for channel_index, channel in enumerate(CHANNELS):
        ax.plot(
            frequencies[mask] / 1_000,
            10 * np.log10(np.maximum(mean_psd[channel_index, mask], 1e-30)),
            linewidth=0.8,
            label=f"CH{channel} {CHANNEL_LABELS[channel]}",
        )
    ax.set_xlabel("Frequency (kHz)")
    ax.set_ylabel("PSD (dB V²/Hz)")
    ax.set_title(f"Phase-3 soil test — {power_supply}")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.savefig(output_dir / "test_measurement.png", dpi=160)
    plt.close(fig)
    print(f"Completed: {output_dir}", flush=True)
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=int, default=3)
    parser.add_argument("--power-supply", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    acquire_run(captures_target=args.captures, power_supply=args.power_supply)
