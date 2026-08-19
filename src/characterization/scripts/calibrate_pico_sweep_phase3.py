#!/usr/bin/env python3
"""Phase-3 Pico sweep calibration for the MEMS channels CH3 and CH4.

This is the executable counterpart of archived notebook NB11. During the
calibration CH1 is temporarily used for the Pico GP14 band-transition marker;
CH3 and CH4 record the amplified MEMS microphone signals. The normal Phase-3
scope channel state is restored when the program exits.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from scope.config import load_config
from scope.instrument import InstrumentConnection, parse_preamble


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "configs" / "experiment_piezo_mems.yaml"
OUTPUT_ROOT = ROOT / "data" / "pico_sweep_calibration_phase3"

BANDS_HZ = list(range(5_000, 101_000, 5_000))
TIM_SCALE_S = 1e-4
FS_MIN_HZ = 900_000
BAND_INTERVAL_S = 1.5
TRIGGER_CHANNEL = 1
SENSOR_CHANNELS = (3, 4)


def configure_calibration_scope(conn: InstrumentConnection) -> None:
    """Configure NB11-compatible Pico marker and MEMS acquisition channels."""
    conn.write(":STOP")
    for command in (
        ":CHAN1:DISP ON",
        ":CHAN1:COUP DC",
        ":CHAN1:SCAL 1.0",
        ":CHAN1:PROB 10",
        ":CHAN1:OFFS 0",
        ":CHAN2:DISP OFF",
    ):
        conn.write(command)
    for channel in SENSOR_CHANNELS:
        for command in (
            f":CHAN{channel}:DISP ON",
            f":CHAN{channel}:COUP AC",
            f":CHAN{channel}:SCAL 0.5",
            f":CHAN{channel}:PROB 10",
            f":CHAN{channel}:OFFS 0",
        ):
            conn.write(command)
    for command in (
        f":TIM:SCAL {TIM_SCALE_S}",
        ":TIM:OFFS 0",
        ":ACQ:TYPE NORM",
        ":ACQ:MDEP AUTO",
        ":TRIG:MODE EDGE",
        f":TRIG:EDGE:SOUR CHAN{TRIGGER_CHANNEL}",
        ":TRIG:EDGE:SLOP POS",
        ":TRIG:EDGE:LEV 1.0",
        ":TRIG:SWE NORM",
    ):
        conn.write(command)


def restore_phase3_scope(conn: InstrumentConnection) -> None:
    """Restore the normal CH1 Piezo / CH3+CH4 MEMS display and trigger state."""
    conn.write(":STOP")
    conn.write(":CHAN2:DISP OFF")
    for channel in (1, 3, 4):
        for command in (
            f":CHAN{channel}:DISP ON",
            f":CHAN{channel}:COUP AC",
            f":CHAN{channel}:PROB 10",
            f":CHAN{channel}:SCAL 0.5",
            f":CHAN{channel}:OFFS 0",
        ):
            conn.write(command)
    for command in (
        ":TIM:SCAL 0.05",
        ":TIM:OFFS 0",
        ":TRIG:MODE EDGE",
        ":TRIG:EDGE:SOUR CHAN3",
        ":TRIG:EDGE:SLOP POS",
        ":TRIG:EDGE:LEV 0.02",
        ":TRIG:SWE AUTO",
        ":RUN",
    ):
        conn.write(command)
    time.sleep(0.5)
    conn.write(":ACQ:MDEP 300000")
    time.sleep(1.5)


def per_frame_metrics(v3: np.ndarray, v4: np.ndarray, fs: float, band_hz: int) -> dict:
    """Compute the NB11 amplitude, SNR, THD, phase and repeatability inputs."""
    sample_count = min(len(v3), len(v4))
    v3, v4 = v3[:sample_count], v4[:sample_count]
    window = np.hanning(sample_count)
    norm = window.sum()
    frequencies = np.fft.rfftfreq(sample_count, 1.0 / fs)
    fft3 = np.fft.rfft(v3 * window)
    fft4 = np.fft.rfft(v4 * window)
    amp3_spectrum = 2 * np.abs(fft3) / norm
    amp4_spectrum = 2 * np.abs(fft4) / norm
    target_bin = int(round(band_hz * sample_count / fs))
    target_bin = max(2, min(target_bin, len(amp3_spectrum) - 3))

    def peak_amplitude(spectrum: np.ndarray, center: int, half_width: int = 2) -> float:
        return float(spectrum[max(0, center - half_width) : center + half_width + 1].max())

    amp3 = peak_amplitude(amp3_spectrum, target_bin)
    amp4 = peak_amplitude(amp4_spectrum, target_bin)
    exclusion_width = max(3, int(0.10 * target_bin))
    off_band = np.ones(len(amp3_spectrum), dtype=bool)
    off_band[max(0, target_bin - exclusion_width) : target_bin + exclusion_width + 1] = False
    off_band[:2] = False
    noise3 = float(amp3_spectrum[off_band].mean()) if off_band.any() else 1e-12
    noise4 = float(amp4_spectrum[off_band].mean()) if off_band.any() else 1e-12
    snr3 = amp3 / (noise3 + 1e-12)
    snr4 = amp4 / (noise4 + 1e-12)

    def thd(spectrum: np.ndarray, snr: float) -> float:
        if snr < 3.0:
            return float("nan")
        fundamental = peak_amplitude(spectrum, target_bin)
        harmonic_power = 0.0
        for harmonic in range(2, 6):
            if harmonic * band_hz > 0.95 * fs / 2:
                break
            harmonic_bin = min(
                int(round(harmonic * band_hz * sample_count / fs)), len(spectrum) - 1
            )
            harmonic_power += peak_amplitude(spectrum, harmonic_bin) ** 2
        return float(np.sqrt(harmonic_power) / (fundamental + 1e-12))

    def peak_frequency(spectrum: np.ndarray) -> float:
        region = (frequencies >= 0.8 * band_hz) & (frequencies <= 1.2 * band_hz)
        return float(frequencies[region][np.argmax(spectrum[region])])

    def crest_factor(voltage: np.ndarray) -> float:
        rms = np.sqrt(np.mean(voltage**2))
        return float(np.max(np.abs(voltage)) / (rms + 1e-12))

    return {
        "amp3": amp3,
        "amp4": amp4,
        "snr3": snr3,
        "snr4": snr4,
        "thd3": thd(amp3_spectrum, snr3),
        "thd4": thd(amp4_spectrum, snr4),
        "peak_f3": peak_frequency(amp3_spectrum),
        "peak_f4": peak_frequency(amp4_spectrum),
        "cf3": crest_factor(v3),
        "cf4": crest_factor(v4),
        "fft3_bin": complex(fft3[target_bin]),
        "fft4_bin": complex(fft4[target_bin]),
        "fs": float(fs),
        "sample_count": int(sample_count),
    }


def read_channel(conn: InstrumentConnection, channel: int) -> tuple[np.ndarray, float]:
    last_length = 0
    for _attempt in range(3):
        conn.write(f":WAV:SOUR CHAN{channel}")
        conn.write(":WAV:MODE NORM")
        conn.write(":WAV:FORM BYTE")
        preamble = parse_preamble(conn.query(":WAV:PRE?"))
        raw = conn.query_binary_values(":WAV:DATA?", datatype="B", is_big_endian=False)
        last_length = len(raw)
        if last_length >= 100 and preamble.xincrement > 0:
            sample_rate = 1.0 / preamble.xincrement
            voltage = (
                (np.asarray(raw, dtype=np.float32) - preamble.yorigin - preamble.yreference)
                * preamble.yincrement
            )
            return voltage, sample_rate
        time.sleep(0.08)
    raise RuntimeError(f"CH{channel}: invalid waveform ({last_length} samples)")


def detect_sync_band(v3: np.ndarray, v4: np.ndarray, fs: float) -> tuple[int | None, float]:
    """Return strongest expected band above 12 kHz and its spectral SNR."""
    sample_count = min(len(v3), len(v4))
    window = np.hanning(sample_count)
    spectrum = 2 * np.abs(np.fft.rfft(v4[:sample_count] * window)) / window.sum()
    frequencies = np.fft.rfftfreq(sample_count, 1.0 / fs)
    region = (frequencies > 12_000) & (frequencies < 105_000)
    if not region.any():
        return None, 0.0
    baseline = float(np.median(spectrum[region]))
    strongest_band, strongest_snr = None, 0.0
    for band_hz in BANDS_HZ:
        if band_hz < 12_000:
            continue
        index = int(round(band_hz * sample_count / fs))
        amplitude = spectrum[max(0, index - 2) : index + 3].max()
        snr = float(amplitude / (baseline + 1e-12))
        if snr > strongest_snr:
            strongest_band, strongest_snr = band_hz, snr
    return strongest_band, strongest_snr


def save_results(
    output_dir: Path,
    records: list[dict],
    frame_count: dict[int, int],
    cross_spectrum: dict[int, complex],
    auto3: dict[int, float],
    auto4: dict[int, float],
) -> dict:
    scalar_keys = (
        "amp3_V",
        "amp4_V",
        "snr3",
        "snr4",
        "thd3",
        "thd4",
        "peak_f3_hz",
        "peak_f4_hz",
        "cf3",
        "cf4",
    )
    grouped = {key: defaultdict(list) for key in scalar_keys}
    for record in records:
        for key in scalar_keys:
            if record.get(key) is not None:
                grouped[key][record["band_hz"]].append(float(record[key]))

    def statistic(key: str, band_hz: int, function) -> float:
        values = grouped[key][band_hz]
        return float(function(values)) if values else float("nan")

    def finite_or_none(value: float) -> float | None:
        return float(value) if np.isfinite(value) else None

    bands = sorted({record["band_hz"] for record in records})
    results = []
    for band_hz in bands:
        g34 = cross_spectrum[band_hz]
        coherence = float(
            abs(g34) ** 2 / (auto3[band_hz] * auto4[band_hz] + 1e-60)
        )
        tau_us = float(-np.angle(g34) / (2 * np.pi * band_hz) * 1e6)
        amp3_mean = statistic("amp3_V", band_hz, np.mean)
        amp4_mean = statistic("amp4_V", band_hz, np.mean)
        amp3_std = statistic("amp3_V", band_hz, np.std)
        amp4_std = statistic("amp4_V", band_hz, np.std)
        thd3_percent = statistic("thd3", band_hz, np.median) * 100
        thd4_percent = statistic("thd4", band_hz, np.median) * 100
        peak_deviation3 = statistic("peak_f3_hz", band_hz, np.median) - band_hz
        peak_deviation4 = statistic("peak_f4_hz", band_hz, np.median) - band_hz
        results.append(
            {
                "band_hz": band_hz,
                "frames": frame_count[band_hz],
                "amp3_mean_mV": amp3_mean * 1e3,
                "amp3_std_mV": amp3_std * 1e3,
                "amp4_mean_mV": amp4_mean * 1e3,
                "amp4_std_mV": amp4_std * 1e3,
                "snr3_mean": statistic("snr3", band_hz, np.mean),
                "snr4_mean": statistic("snr4", band_hz, np.mean),
                "coherence_mf": coherence,
                "tau_mle_us": tau_us,
                "thd3_median_percent": finite_or_none(thd3_percent),
                "thd4_median_percent": finite_or_none(thd4_percent),
                "cv3_percent": amp3_std / (amp3_mean + 1e-12) * 100,
                "cv4_percent": amp4_std / (amp4_mean + 1e-12) * 100,
                "peak_deviation3_hz": finite_or_none(peak_deviation3),
                "peak_deviation4_hz": finite_or_none(peak_deviation4),
            }
        )

    reliable = [
        item["band_hz"]
        for item in results
        if item["frames"] >= 3
        and item["coherence_mf"] >= 0.9
        and item["snr3_mean"] >= 3
        and item["snr4_mean"] >= 3
    ]
    summary = {
        "phase": 3,
        "sensor_configuration": {
            "CH1": "Pico GP14 trigger marker during calibration; normally Piezo + LM amplifier",
            "CH3": "MEMS microphone + existing LM amplifier",
            "CH4": "MEMS microphone + existing LM amplifier",
        },
        "bands": results,
        "reliable_bands_hz": reliable,
    }
    (output_dir / "calibration_summary.json").write_text(
        json.dumps(summary, indent=2, allow_nan=False), encoding="utf-8"
    )

    x = np.asarray([item["band_hz"] / 1e3 for item in results])
    fig, axes = plt.subplots(3, 1, figsize=(12, 12), constrained_layout=True)
    axes[0].errorbar(
        x,
        [item["amp3_mean_mV"] for item in results],
        yerr=[item["amp3_std_mV"] for item in results],
        fmt="o-",
        label="CH3 MEMS + LM amplifier",
    )
    axes[0].errorbar(
        x,
        [item["amp4_mean_mV"] for item in results],
        yerr=[item["amp4_std_mV"] for item in results],
        fmt="s-",
        label="CH4 MEMS + LM amplifier",
    )
    axes[0].set_ylabel("Amplitude at drive frequency (mV)")
    axes[0].set_title("Phase-3 Pico sweep transfer response")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(x, [item["snr3_mean"] for item in results], "o-", label="CH3")
    axes[1].plot(x, [item["snr4_mean"] for item in results], "s-", label="CH4")
    axes[1].axhline(3, color="red", linestyle="--", label="SNR threshold")
    axes[1].set_ylabel("SNR")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    axes[2].plot(x, [item["coherence_mf"] for item in results], "o-")
    axes[2].axhline(0.9, color="green", linestyle="--", label="coherence threshold")
    axes[2].set_ylim(0, 1.05)
    axes[2].set_xlabel("Pico drive frequency (kHz)")
    axes[2].set_ylabel("CH3–CH4 coherence")
    axes[2].legend()
    axes[2].grid(alpha=0.3)
    fig.savefig(output_dir / "calibration_report.png", dpi=160)
    plt.close(fig)
    return summary


def run_calibration(captures: int, trigger_timeout_s: float) -> Path:
    run_local = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = OUTPUT_ROOT / run_local
    output_dir.mkdir(parents=True, exist_ok=False)
    config = load_config(CONFIG_PATH)

    cross_spectrum: dict[int, complex] = defaultdict(complex)
    auto3: dict[int, float] = defaultdict(float)
    auto4: dict[int, float] = defaultdict(float)
    frame_count: dict[int, int] = defaultdict(int)
    records: list[dict] = []
    meta = {
        "run_id": run_local,
        "phase": 3,
        "utc_start": datetime.now(timezone.utc).isoformat(),
        "config_path": str(CONFIG_PATH),
        "bands_hz": BANDS_HZ,
        "captures_target": captures,
        "trigger": "Pico GP14 -> CH1, 10x probe, positive edge, 1.0 V displayed",
        "excitation": "Pico GP15 sweep, 5–100 kHz, 5 kHz step, 1.5 s per band",
        "channels": {
            "CH3": "MEMS microphone + existing LM amplifier, AC, 10x, 0.5 V/div",
            "CH4": "MEMS microphone + existing LM amplifier, AC, 10x, 0.5 V/div",
        },
        "home_assistant_available": False,
        "automatic_watering": False,
        "temperature_recording": False,
    }

    with InstrumentConnection(config) as conn:
        meta["instrument_idn"] = conn.query("*IDN?")
        configure_calibration_scope(conn)
        time.sleep(0.3)
        print(f"Output: {output_dir}", flush=True)
        print(f"Instrument: {meta['instrument_idn']}", flush=True)
        print(f"Starting {captures} Pico-triggered captures ...", flush=True)
        band_start_index: int | None = None
        previous_trigger_time: float | None = None
        absolute_frame = 0
        consecutive_timeouts = 0
        attempt_count = 0
        transfer_errors = 0
        try:
            while len(records) < captures:
                attempt_count += 1
                if attempt_count > captures * 3:
                    raise RuntimeError(
                        f"Only {len(records)}/{captures} valid frames after {attempt_count} attempts"
                    )
                conn.write(f":TIM:SCAL {TIM_SCALE_S}")
                conn.write(":SING")
                time.sleep(0.1)
                wait_start = time.monotonic()
                while time.monotonic() - wait_start < trigger_timeout_s:
                    if conn.query(":TRIG:STAT?").strip().upper() == "STOP":
                        break
                    time.sleep(0.008)
                else:
                    consecutive_timeouts += 1
                    print(
                        f"[attempt {attempt_count:03d}] no GP14 trigger "
                        f"({consecutive_timeouts}/3)",
                        flush=True,
                    )
                    if consecutive_timeouts >= 3:
                        raise RuntimeError(
                            "No Pico GP14 transition marker detected on CH1. "
                            "Connect GP14 to CH1 and ensure pico_rust_sweep is running."
                        )
                    configure_calibration_scope(conn)
                    continue

                consecutive_timeouts = 0
                trigger_time = time.monotonic()
                if previous_trigger_time is not None:
                    delta = trigger_time - previous_trigger_time
                    missed = max(0, round(delta / BAND_INTERVAL_S) - 1)
                    absolute_frame += missed
                previous_trigger_time = trigger_time
                time.sleep(0.03)

                try:
                    v3, fs3 = read_channel(conn, 3)
                    v4, fs4 = read_channel(conn, 4)
                except Exception as exc:
                    transfer_errors += 1
                    print(
                        f"[attempt {attempt_count:03d}] waveform transfer skipped: {exc}",
                        flush=True,
                    )
                    absolute_frame += 1
                    configure_calibration_scope(conn)
                    continue
                if min(fs3, fs4) < FS_MIN_HZ:
                    raise RuntimeError(f"Sample rate too low: CH3={fs3:g}, CH4={fs4:g} Sa/s")
                fs = fs4

                if band_start_index is None:
                    sync_band, sync_snr = detect_sync_band(v3, v4, fs)
                    if sync_band is not None and sync_snr > 4.0:
                        band_start_index = (
                            BANDS_HZ.index(sync_band) - absolute_frame
                        ) % len(BANDS_HZ)
                        print(
                            f"Band sync: {sync_band / 1e3:.0f} kHz "
                            f"(spectral SNR={sync_snr:.1f})",
                            flush=True,
                        )
                    elif attempt_count >= 10:
                        raise RuntimeError(
                            "Pico GP15 sweep not detected on CH4 with spectral SNR > 4 "
                            "during the first ten frames."
                        )

                band_hz = BANDS_HZ[
                    (absolute_frame + (band_start_index or 0)) % len(BANDS_HZ)
                ]
                metrics = per_frame_metrics(v3, v4, fs, band_hz)
                cross_spectrum[band_hz] += (
                    metrics["fft3_bin"] * metrics["fft4_bin"].conjugate()
                )
                auto3[band_hz] += abs(metrics["fft3_bin"]) ** 2
                auto4[band_hz] += abs(metrics["fft4_bin"]) ** 2
                frame_count[band_hz] += 1

                record = {
                    "capture": len(records) + 1,
                    "attempt": attempt_count,
                    "absolute_frame": absolute_frame,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "band_hz": band_hz,
                    "amp3_V": float(metrics["amp3"]),
                    "amp4_V": float(metrics["amp4"]),
                    "snr3": float(metrics["snr3"]),
                    "snr4": float(metrics["snr4"]),
                    "thd3": None if np.isnan(metrics["thd3"]) else float(metrics["thd3"]),
                    "thd4": None if np.isnan(metrics["thd4"]) else float(metrics["thd4"]),
                    "peak_f3_hz": float(metrics["peak_f3"]),
                    "peak_f4_hz": float(metrics["peak_f4"]),
                    "cf3": float(metrics["cf3"]),
                    "cf4": float(metrics["cf4"]),
                    "fs_hz": float(metrics["fs"]),
                    "sample_count": int(metrics["sample_count"]),
                    "fft3_bin_real": float(metrics["fft3_bin"].real),
                    "fft3_bin_imag": float(metrics["fft3_bin"].imag),
                    "fft4_bin_real": float(metrics["fft4_bin"].real),
                    "fft4_bin_imag": float(metrics["fft4_bin"].imag),
                }
                records.append(record)
                with (output_dir / "records.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(record, allow_nan=False) + "\n")
                print(
                    f"[{len(records):03d}/{captures:03d}] {band_hz / 1e3:5.1f} kHz  "
                    f"CH3={metrics['amp3'] * 1e3:8.3f} mV "
                    f"CH4={metrics['amp4'] * 1e3:8.3f} mV "
                    f"SNR=({metrics['snr3']:.1f}, {metrics['snr4']:.1f})",
                    flush=True,
                )
                absolute_frame += 1
        finally:
            restore_phase3_scope(conn)

    if band_start_index is None:
        raise RuntimeError("Calibration ended without sweep-band synchronisation")
    meta["utc_end"] = datetime.now(timezone.utc).isoformat()
    meta["captures_valid"] = len(records)
    meta["attempts"] = attempt_count
    meta["transfer_errors"] = transfer_errors
    (output_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, allow_nan=False), encoding="utf-8"
    )
    summary = save_results(output_dir, records, frame_count, cross_spectrum, auto3, auto4)
    print(f"Reliable bands: {[f / 1e3 for f in summary['reliable_bands_hz']]} kHz")
    print(f"Calibration complete: {output_dir}")
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=int, default=80)
    parser.add_argument("--trigger-timeout", type=float, default=3.5)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    run_calibration(arguments.captures, arguments.trigger_timeout)
