"""RAM-backed continuous spectral monitoring for plant acoustic emissions."""

from __future__ import annotations

import csv
import json
import os
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal, stats
from scipy.optimize import linear_sum_assignment

from .watering import (
    CHANNELS,
    detect_condition_peaks,
    utc_now,
)

CHARACTERIZATION_ROOT = Path(__file__).resolve().parents[2]
REPORT_ROOT = (
    CHARACTERIZATION_ROOT / "data" / "reports" / "notebooks" / "04_continuous_frequency_sweep"
)


def summarize_monitor_sessions(report_root: Path = REPORT_ROOT) -> dict:
    """Rank slow frequency and amplitude trends across restarted monitor sessions."""
    band_values: dict[tuple[datetime, int, int], list[float]] = {}
    peak_values: dict[tuple[datetime, int, int], list[tuple[float, float]]] = {}
    phase_frames: dict[str, int] = {}
    event_counts: dict[str, dict[str, int]] = {}
    sessions = 0
    for frames_path in sorted(report_root.glob("*/frames.jsonl")):
        sessions += 1
        with frames_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                record = json.loads(line)
                phase = record.get("light_phase", "unknown")
                phase_frames[phase] = phase_frames.get(phase, 0) + 1
                timestamp = datetime.fromisoformat(record["timestamp_local"])
                hour = timestamp.replace(minute=0, second=0, microsecond=0)
                for event_type in record.get("event_types", []):
                    event_counts.setdefault(event_type, {})
                    event_counts[event_type][phase] = (
                        event_counts[event_type].get(phase, 0) + 1
                    )
                for channel_index, energies in enumerate(record["band_energy"], 1):
                    for band_index, energy in enumerate(energies):
                        key = (hour, channel_index, band_index)
                        band_values.setdefault(key, []).append(
                            float(10 * np.log10(max(float(energy), 1e-30)))
                        )
                for channel_text, peaks in record.get("peaks", {}).items():
                    channel = int(channel_text)
                    for peak in peaks:
                        frequency = float(peak["frequency_hz"])
                        frequency_bin = int(round(frequency / 500.0))
                        amplitude = float(peak.get("psd_db", peak.get("prominence_db", 0.0)))
                        peak_values.setdefault(
                            (hour, channel, frequency_bin), []
                        ).append((frequency, amplitude))

    trends = []

    def add_trend(
        *,
        kind: str,
        channel: int,
        label: str,
        unit: str,
        hourly_points: list[tuple[datetime, float]],
    ) -> None:
        if len(hourly_points) < 3:
            return
        hourly_points.sort()
        start = hourly_points[0][0]
        x = np.array(
            [(timestamp - start).total_seconds() / 3600 for timestamp, _ in hourly_points]
        )
        y = np.array([value for _, value in hourly_points])
        if np.ptp(x) < 2:
            return
        regression = stats.linregress(x, y)
        total_change = float(y[-1] - y[0])
        r_squared = float(regression.rvalue**2)
        trends.append(
            {
                "score": abs(total_change) * r_squared * np.log1p(len(y)),
                "kind": kind,
                "channel": channel,
                "label": label,
                "unit": unit,
                "hourly_points": len(y),
                "start_local": hourly_points[0][0].isoformat(),
                "end_local": hourly_points[-1][0].isoformat(),
                "start_value": float(y[0]),
                "end_value": float(y[-1]),
                "total_change": total_change,
                "slope_per_hour": float(regression.slope),
                "r_squared": r_squared,
            }
        )

    band_series: dict[tuple[int, int], list[tuple[datetime, float]]] = {}
    for (hour, channel, band_index), values in band_values.items():
        band_series.setdefault((channel, band_index), []).append(
            (hour, float(np.median(values)))
        )
    for (channel, band_index), points in band_series.items():
        add_trend(
            kind="band_energy",
            channel=channel,
            label=f"{BAND_EDGES_HZ[band_index]/1000:g}-{BAND_EDGES_HZ[band_index+1]/1000:g} kHz",
            unit="dB V²",
            hourly_points=points,
        )

    peak_series: dict[tuple[int, int], list[tuple[datetime, float]]] = {}
    amplitude_series: dict[tuple[int, int], list[tuple[datetime, float]]] = {}
    for (hour, channel, frequency_bin), values in peak_values.items():
        peak_series.setdefault((channel, frequency_bin), []).append(
            (hour, float(np.median([value[0] for value in values])))
        )
        amplitude_series.setdefault((channel, frequency_bin), []).append(
            (hour, float(np.median([value[1] for value in values])))
        )
    for (channel, frequency_bin), points in peak_series.items():
        label = f"peak near {frequency_bin * 0.5:g} kHz"
        add_trend(
            kind="peak_frequency",
            channel=channel,
            label=label,
            unit="Hz",
            hourly_points=points,
        )
        add_trend(
            kind="peak_amplitude",
            channel=channel,
            label=label,
            unit="dB",
            hourly_points=amplitude_series[(channel, frequency_bin)],
        )

    trends.sort(key=lambda row: row["score"], reverse=True)
    top_trends = trends[:200]
    summary = {
        "generated_utc": utc_now(),
        "sessions": sessions,
        "phase_frames": phase_frames,
        "event_counts_by_phase": event_counts,
        "candidate_definition": (
            "Restart-tolerant ranking of hourly-median frequency and amplitude trends. "
            "At least three hourly points spanning two hours are required. Trends are "
            "candidates, not proof of biological origin."
        ),
        "top_trends": top_trends,
    }
    report_root.mkdir(parents=True, exist_ok=True)
    (report_root / "candidate_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    if top_trends:
        with (report_root / "candidate_summary.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.DictWriter(handle, fieldnames=list(top_trends[0]))
            writer.writeheader()
            writer.writerows(top_trends)
    return summary


def linux_memory_bytes() -> tuple[int, int]:
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        values[key] = int(value.strip().split()[0]) * 1024
    return (values["MemTotal"], values["MemAvailable"])


def calculate_ram_budget(memory_fraction: float = 0.90, reserve_gib: float = 2.0) -> int:
    """Dynamisch: RAM-Budget = verfügbar − 10 % des Gesamtspeichers.

    Ziel: System-RAM nie über 90 % auslasten. Wird bei jedem Neustart
    des Monitors neu berechnet; der RamFrameRing passt sein Limit bei
    jedem Append dynamisch an (siehe RamFrameRing.dynamic_max_bytes).
    """
    if not 0 < memory_fraction < 1:
        raise ValueError("memory_fraction must be between 0 and 1")
    total, available = linux_memory_bytes()
    reserve = int(reserve_gib * 1024**3)
    # Erlaubte Ring-Größe = verfügbar − Reserve (kein fester total-Anteil)
    budget = max(0, available - reserve)
    if budget < 512 * 1024**2:
        raise MemoryError("Less than 512 MiB safely available for monitoring")
    return budget


def classify_light_phase(
    timestamp_utc: str,
    *,
    timezone_name: str = "Europe/Berlin",
    day_start_hour: int = 6,
    night_start_hour: int = 22,
) -> tuple[str, str]:
    local_time = datetime.fromisoformat(timestamp_utc).astimezone(ZoneInfo(timezone_name))
    hour = local_time.hour
    if day_start_hour < night_start_hour:
        phase = "day" if day_start_hour <= hour < night_start_hour else "night"
    else:
        phase = "day" if hour >= day_start_hour or hour < night_start_hour else "night"
    return local_time.isoformat(), phase


@dataclass
class SweepFrame:
    sequence: int
    timestamp_utc: str
    voltages: np.ndarray
    band_energy: np.ndarray
    frequencies: np.ndarray
    psd: np.ndarray
    peaks: dict[int, list[dict]]
    sample_rate_hz: float = 0.0
    n_samples: int = 0

    @property
    def nbytes(self) -> int:
        return (
            self.voltages.nbytes
            + self.band_energy.nbytes
            + self.frequencies.nbytes
            + self.psd.nbytes
        )

    def free_voltages(self) -> None:
        """Gibt den Rohdaten-Array frei. Aufruf nach _track_candidates()."""
        self.voltages = np.empty((0, 0), dtype=np.float32)


class RamFrameRing:
    """RAM-Ring mit dynamischem Budget: hält Ring-Größe unter 90 % RAM-Auslastung."""

    _RECHECK_INTERVAL = 10  # Jede N Appends Budget neu berechnen

    def __init__(self, initial_max_bytes: int, snapshot_dir: Path | None = None):
        self.max_bytes = int(initial_max_bytes)
        self.current_bytes = 0
        self.frames: deque[SweepFrame] = deque()
        self.evicted_frames = 0
        self.snapshot_dir = snapshot_dir
        self._append_count = 0
        self._snapshot_psd_buffer: list[np.ndarray] = []
        self._snapshot_last_hour: int = -1

    def _update_budget(self) -> None:
        """Reberechnet Budget aus aktuellem /proc/meminfo (max 90 % RAM)."""
        try:
            self.max_bytes = calculate_ram_budget()
        except MemoryError:
            pass  # Behalte letztes Budget, evict weiter

    def _maybe_save_snapshot(self, frame: SweepFrame) -> None:
        """Speichert stündlichen PSD-Snapshot auf Platte (Rohdaten-Archiv)."""
        if self.snapshot_dir is None:
            return
        local_dt = datetime.fromisoformat(frame.timestamp_utc).astimezone()
        hour = local_dt.hour
        self._snapshot_psd_buffer.append(frame.psd.copy())
        if hour != self._snapshot_last_hour and len(self._snapshot_psd_buffer) >= 1:
            self._snapshot_last_hour = hour
            mean_psd = np.mean(np.stack(self._snapshot_psd_buffer), axis=0).astype(np.float32)
            ts_str = local_dt.strftime("%Y-%m-%dT%H-%M-%S")
            out = self.snapshot_dir / f"psd_snapshot_{ts_str}_seq{frame.sequence:06d}.npz"
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            np.savez_compressed(
                out,
                frequencies=frame.frequencies,
                mean_psd=mean_psd,
                band_energy=frame.band_energy,
                n_frames=np.array(len(self._snapshot_psd_buffer)),
            )
            self._snapshot_psd_buffer.clear()

    def append(self, frame: SweepFrame) -> None:
        self._append_count += 1
        if self._append_count % self._RECHECK_INTERVAL == 0:
            self._update_budget()

        self._maybe_save_snapshot(frame)

        while self.frames and self.current_bytes + frame.nbytes > self.max_bytes:
            removed = self.frames.popleft()
            self.current_bytes -= removed.nbytes
            self.evicted_frames += 1
        self.frames.append(frame)
        self.current_bytes += frame.nbytes

    def __len__(self) -> int:
        return len(self.frames)

    def usage_gib(self) -> float:
        return self.current_bytes / 1024**3


BAND_EDGES_HZ = np.arange(0, 250000 + 5000, 5000, dtype=float)  # 0-250 kHz, 50 Bänder à 5 kHz
MAINS_HARMONIC_BANDS_HZ = tuple(
    (harmonic - 5.0, harmonic + 5.0) for harmonic in np.arange(50.0, 1000.1, 50.0)
)


def extract_frame_features(
    sequence: int,
    captures,
    *,
    max_frequency_hz: float = 250_000.0,
    ignore_frequency_bands_hz: tuple[tuple[float, float], ...] = (MAINS_HARMONIC_BANDS_HZ),
) -> SweepFrame:
    if not captures:
        raise ValueError("At least one capture is required")
    voltages = np.stack([capture.voltage_vector for capture in captures]).astype(np.float32)
    expected_samples = len(captures[0].voltage_vector)
    expected_rate = float(captures[0].metadata.sample_rate_sa_per_s)
    frequencies = None
    spectra = []
    band_energy = []
    peaks = {}
    for capture in captures:
        sample_rate = float(capture.metadata.sample_rate_sa_per_s)
        voltage = np.asarray(capture.voltage_vector, dtype=float)
        if len(voltage) != expected_samples or not np.isclose(sample_rate, expected_rate):
            raise ValueError("Acquisition signatures differ between channels")
        cleaned = signal.detrend(voltage, type="linear")
        current_frequencies, current_psd = signal.periodogram(
            cleaned, fs=sample_rate, window="hann", scaling="density"
        )
        if frequencies is None:
            frequencies = current_frequencies
        elif not np.array_equal(frequencies, current_frequencies):
            raise ValueError("Frequency axes differ between channels")
        spectra.append(current_psd.astype(np.float32))
        energies = []
        for low, high in zip(BAND_EDGES_HZ[:-1], BAND_EDGES_HZ[1:], strict=True):
            mask = (frequencies >= low) & (frequencies < high)
            energies.append(np.trapezoid(current_psd[mask], frequencies[mask]))
        band_energy.append(energies)
        channel = int(capture.metadata.channel)
        peaks[channel] = detect_condition_peaks(
            frequencies,
            current_psd,
            max_frequency_hz=max_frequency_hz,
            ignore_frequency_bands_hz=ignore_frequency_bands_hz,
        )
    return SweepFrame(
        sequence=sequence,
        timestamp_utc=utc_now(),
        voltages=voltages,
        band_energy=np.asarray(band_energy, dtype=np.float32),
        frequencies=np.asarray(frequencies, dtype=np.float32),
        psd=np.asarray(spectra, dtype=np.float32),
        peaks=peaks,
        sample_rate_hz=expected_rate,
        n_samples=expected_samples,
    )


@dataclass
class PeakTrack:
    track_id: int
    channel: int
    observations: deque = field(default_factory=lambda: deque(maxlen=30))
    missed: int = 0
    last_event_sequence: int = -10000

    def add(self, sequence: int, timestamp_s: float, peak: dict) -> None:
        self.observations.append((sequence, timestamp_s, peak["frequency_hz"], peak["psd_db"]))
        self.missed = 0

    @property
    def frequency_hz(self) -> float:
        return float(self.observations[-1][2])


class PeakTracker:
    def __init__(
        self,
        match_tolerance_hz: float = 500.0,
        max_missed: int = 5,
        min_points_for_drift: int = 12,
        min_displacement_hz: float = 500.0,
        min_slope_hz_per_second: float = 0.5,
        min_r_squared: float = 0.8,
        event_cooldown_frames: int = 30,
    ):
        self.match_tolerance_hz = match_tolerance_hz
        self.max_missed = max_missed
        self.min_points_for_drift = min_points_for_drift
        self.min_displacement_hz = min_displacement_hz
        self.min_slope_hz_per_second = min_slope_hz_per_second
        self.min_r_squared = min_r_squared
        self.event_cooldown_frames = event_cooldown_frames
        self.next_track_id = 1
        self.tracks: dict[int, PeakTrack] = {}
        self.initialized_channels = set()

    def _new_track(self, channel: int, sequence: int, timestamp_s: float, peak: dict) -> None:
        track = PeakTrack(self.next_track_id, channel)
        track.add(sequence, timestamp_s, peak)
        self.tracks[track.track_id] = track
        self.next_track_id += 1

    def update(self, sequence: int, timestamp_s: float, peaks_by_channel: dict) -> list[dict]:
        events = []
        for channel in CHANNELS:
            peaks = peaks_by_channel.get(channel, [])
            tracks = [track for track in self.tracks.values() if track.channel == channel]
            matched_track_ids = set()
            matched_peak_indices = set()
            if tracks and peaks:
                cost = np.abs(
                    np.subtract.outer(
                        [track.frequency_hz for track in tracks],
                        [peak["frequency_hz"] for peak in peaks],
                    )
                )
                rows, columns = linear_sum_assignment(cost)
                for row, column in zip(rows, columns, strict=True):
                    if cost[row, column] <= self.match_tolerance_hz:
                        tracks[row].add(sequence, timestamp_s, peaks[column])
                        matched_track_ids.add(tracks[row].track_id)
                        matched_peak_indices.add(int(column))
            for track in tracks:
                if track.track_id not in matched_track_ids:
                    track.missed += 1
            for peak_index, peak in enumerate(peaks):
                if peak_index not in matched_peak_indices:
                    self._new_track(channel, sequence, timestamp_s, peak)
            self.initialized_channels.add(channel)
        for track_id in list(self.tracks):
            track = self.tracks[track_id]
            if track.missed > self.max_missed:
                del self.tracks[track_id]
                continue
            if len(track.observations) < self.min_points_for_drift:
                continue
            observations = list(track.observations)[-self.min_points_for_drift :]
            x = np.asarray([item[1] for item in observations], dtype=float)
            x -= x[0]
            y = np.asarray([item[2] for item in observations], dtype=float)
            regression = stats.linregress(x, y)
            displacement = float(y[-1] - y[0])
            if (
                abs(displacement) >= self.min_displacement_hz
                and abs(regression.slope) >= self.min_slope_hz_per_second
                and (regression.rvalue**2 >= self.min_r_squared)
                and (sequence - track.last_event_sequence >= self.event_cooldown_frames)
            ):
                events.append(
                    {
                        "type": "wandering_frequency",
                        "sequence": sequence,
                        "channel": track.channel,
                        "track_id": track.track_id,
                        "start_frequency_hz": float(y[0]),
                        "end_frequency_hz": float(y[-1]),
                        "displacement_hz": displacement,
                        "slope_hz_per_second": float(regression.slope),
                        "r_squared": float(regression.rvalue**2),
                    }
                )
                track.last_event_sequence = sequence
        return events


class CrossChannelPeakDetector:
    """Report only peaks persisting on at least two independent channels."""

    def __init__(
        self,
        *,
        tolerance_hz: float = 500.0,
        persistence_frames: int = 12,
        cooldown_frames: int = 60,
        bin_width_hz: float = 250.0,
    ):
        self.tolerance_hz = tolerance_hz
        self.persistence_frames = persistence_frames
        self.cooldown_frames = cooldown_frames
        self.bin_width_hz = bin_width_hz
        self.pending: dict[int, int] = {}
        self.last_event: dict[int, int] = {}

    def update(self, sequence: int, peaks_by_channel: dict) -> list[dict]:
        candidates: dict[int, dict] = {}
        for peaks in peaks_by_channel.values():
            for peak in peaks:
                frequency = float(peak["frequency_hz"])
                supporting = {
                    other_channel: min(
                        (
                            other_peak
                            for other_peak in other_peaks
                            if abs(float(other_peak["frequency_hz"]) - frequency)
                            <= self.tolerance_hz
                        ),
                        key=lambda item: abs(float(item["frequency_hz"]) - frequency),
                        default=None,
                    )
                    for other_channel, other_peaks in peaks_by_channel.items()
                }
                supporting = {
                    support_channel: support_peak
                    for support_channel, support_peak in supporting.items()
                    if support_peak is not None
                }
                if len(supporting) < 2:
                    continue
                mean_frequency = float(
                    np.mean(
                        [
                            float(support_peak["frequency_hz"])
                            for support_peak in supporting.values()
                        ]
                    )
                )
                key = int(round(mean_frequency / self.bin_width_hz))
                candidates[key] = {
                    "frequency_hz": mean_frequency,
                    "channels": sorted(int(value) for value in supporting),
                    "prominence_db": {
                        str(support_channel): float(support_peak["prominence_db"])
                        for support_channel, support_peak in supporting.items()
                    },
                }

        active_keys = set(candidates)
        for key in list(self.pending):
            if key not in active_keys:
                self.pending[key] = 0
        events = []
        for key, candidate in candidates.items():
            self.pending[key] = self.pending.get(key, 0) + 1
            if self.pending[key] < self.persistence_frames:
                continue
            if sequence - self.last_event.get(key, -10000) < self.cooldown_frames:
                continue
            events.append(
                {
                    "type": "persistent_cross_channel_peak",
                    "sequence": sequence,
                    "persistence_frames": self.pending[key],
                    **candidate,
                }
            )
            self.last_event[key] = sequence
        return events


class RollingBandDetector:
    def __init__(
        self,
        history_frames: int = 30,
        min_reference_frames: int = 10,
        threshold_db: float = 3.0,
        persistence_frames: int = 3,
        cooldown_frames: int = 10,
    ):
        self.history = deque(maxlen=history_frames)
        self.min_reference_frames = min_reference_frames
        self.threshold_db = threshold_db
        self.persistence_frames = persistence_frames
        self.cooldown_frames = cooldown_frames
        self.pending: np.ndarray | None = None    # lazy-init on first band_energy
        self.last_event: np.ndarray | None = None

    def update(self, sequence: int, band_energy: np.ndarray) -> list[dict]:
        events = []
        # Lazy initialisation: shape adapts to whatever band_energy arrives first
        if self.pending is None or self.pending.shape != band_energy.shape:
            self.pending = np.zeros_like(band_energy, dtype=int)
            self.last_event = np.full(band_energy.shape[1], -10000, dtype=int)
        if len(self.history) >= self.min_reference_frames:
            reference = np.median(np.stack(self.history), axis=0)
            change_db = 10 * np.log10(np.maximum(band_energy, 1e-30) / np.maximum(reference, 1e-30))
            active = np.abs(change_db) >= self.threshold_db
            self.pending = np.where(active, self.pending + 1, 0)
            for band_index in range(self.pending.shape[1]):
                channel_indices = np.flatnonzero(
                    self.pending[:, band_index] >= self.persistence_frames
                )
                if len(channel_indices) < 2:
                    continue
                if sequence - self.last_event[band_index] < self.cooldown_frames:
                    continue
                events.append(
                    {
                        "type": "cross_channel_band_energy_change",
                        "sequence": sequence,
                        "channels": [
                            int(CHANNELS[channel_index]) for channel_index in channel_indices
                        ],
                        "band_low_hz": float(BAND_EDGES_HZ[band_index]),
                        "band_high_hz": float(BAND_EDGES_HZ[band_index + 1]),
                        "change_db": {
                            str(CHANNELS[channel_index]): float(
                                change_db[channel_index, band_index]
                            )
                            for channel_index in channel_indices
                        },
                    }
                )
                self.last_event[band_index] = sequence
                self.pending[channel_indices, band_index] = 0
        self.history.append(np.asarray(band_energy, dtype=np.float32))
        return events


class ContinuousFrequencyMonitor:
    def __init__(
        self,
        *,
        memory_fraction: float = 0.90,
        reserve_gib: float = 2.0,
        persist_events: bool = True,
        save_event_raw: bool = False,
        dashboard_history: int = 200,
        peak_average_frames: int = 5,
        peak_tracker_options: dict | None = None,
        persistent_peak_options: dict | None = None,
        band_detector_options: dict | None = None,
        persist_frames: bool = False,
        timezone_name: str = "Europe/Berlin",
        day_start_hour: int = 6,
        night_start_hour: int = 22,
        temperature_poller: Callable[[], float | None] | None = None,
        candidate_freqs_hz: tuple[float, ...] = (3800.0, 6600.0),
        candidate_search_hz: float = 300.0,
        candidate_coherence_nperseg: int = 16384,
        save_psd_snapshots: bool = True,
        known_artifact_harmonics_hz: tuple[float, ...] | None = None,
    ):
        self._save_psd_snapshots = save_psd_snapshots
        # 750 Hz Gebäudestruktur-Harmonische als bekannte Artefakte (HVAC/Heizungspumpe)
        if known_artifact_harmonics_hz is None:
            known_artifact_harmonics_hz = tuple(float(h) for h in range(750, 250_001, 750))
        self._known_artifacts = np.asarray(known_artifact_harmonics_hz, dtype=np.float64)
        self.ring = RamFrameRing(calculate_ram_budget(memory_fraction, reserve_gib))
        self.peak_tracker = PeakTracker(**(peak_tracker_options or {}))
        self.persistent_peak_detector = CrossChannelPeakDetector(**(persistent_peak_options or {}))
        self.band_detector = RollingBandDetector(**(band_detector_options or {}))
        self.persist_events = persist_events
        self.save_event_raw = save_event_raw
        self.persist_frames = persist_frames
        self.timezone_name = timezone_name
        self.day_start_hour = day_start_hour
        self.night_start_hour = night_start_hour
        self.candidate_freqs_hz = candidate_freqs_hz
        self.candidate_search_hz = candidate_search_hz
        self.candidate_coherence_nperseg = candidate_coherence_nperseg
        self.temperature_poller = temperature_poller
        self.dashboard_history = dashboard_history
        self.peak_psd_history = deque(maxlen=peak_average_frames)
        self.events = []
        self.frames_processed = 0
        self.feature_history = deque(maxlen=dashboard_history)
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = REPORT_ROOT / self.run_id
        if persist_events or save_event_raw:
            self.output_dir.mkdir(parents=True, exist_ok=False)
        if persist_frames:
            self.output_dir.mkdir(parents=True, exist_ok=True)
        if persist_events or save_event_raw or persist_frames:
            self._write_manifest("running", started_utc=utc_now())
        # Stündliche PSD-Snapshots auf Platte statt in Swap
        snapshot_dir = (self.output_dir / "psd_snapshots") if save_psd_snapshots else None
        self.ring.snapshot_dir = snapshot_dir

    def _write_manifest(self, status: str, **details) -> None:
        manifest_path = self.output_dir / "manifest.json"
        manifest = {
            "run_id": self.run_id,
            "status": status,
            "timezone": self.timezone_name,
            "day_start_hour": self.day_start_hour,
            "night_start_hour": self.night_start_hour,
            "sample_window_note": (
                "Frames are 0.6 s snapshots separated by instrument/LAN transfer time; "
                "this is not gapless acquisition."
            ),
            **details,
        }
        if manifest_path.exists():
            manifest = {**json.loads(manifest_path.read_text(encoding="utf-8")), **manifest}
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def finish(self, status: str = "finished") -> None:
        self._write_manifest(
            status,
            finished_utc=utc_now(),
            frames_processed=self.frames_processed,
            monitor_status=self.status(),
        )

    def _track_candidates(self, frame: SweepFrame) -> dict:
        """Fine-frequency + cross-channel coherence at each candidate frequency.

        Uses full-resolution FFT (1.67 Hz/bin at 500 kSa/s / 300 k points) with
        parabolic interpolation for sub-bin centre-frequency accuracy, and
        Welch-based coherence between every channel pair at the candidate bin.
        All computation is lightweight CPU only (~5 ms per frame).
        """
        fs = frame.sample_rate_hz
        voltages = frame.voltages          # shape (n_ch, n_samples)
        n_ch, n_samp = voltages.shape
        df = fs / n_samp                   # native resolution ≈ 1.67 Hz
        # Anzahl Welch-Segmente für Kohärenz-Bias-Abschätzung (Bias ≈ 1/n_seg)
        n_coh_seg = max(1, n_samp // self.candidate_coherence_nperseg)

        # Map channel number → voltages row index
        ch_idx = {ch: i for i, ch in enumerate(CHANNELS) if i < n_ch}

        # Pre-compute full-resolution FFT magnitudes once per channel
        full_fft: dict[int, np.ndarray] = {}
        full_fax = np.fft.rfftfreq(n_samp, 1.0 / fs)
        for ch, idx in ch_idx.items():
            v = voltages[idx]
            full_fft[ch] = np.abs(np.fft.rfft(v - v.mean()))

        result: dict[str, dict] = {}
        for f_cand in self.candidate_freqs_hz:
            # Nächste bekannte Artefakt-Harmonische und Abstand
            diffs = np.abs(self._known_artifacts - f_cand)
            nearest_i = int(np.argmin(diffs))
            nearest_artifact = float(self._known_artifacts[nearest_i])

            entry: dict = {
                "nearest_artifact_hz": nearest_artifact,
                "artifact_offset_hz": round(float(f_cand - nearest_artifact), 1),
                "coherence_n_segments": n_coh_seg,
                "coherence_bias_floor": round(1.0 / n_coh_seg, 4),
            }
            win_lo = f_cand - self.candidate_search_hz
            win_hi = f_cand + self.candidate_search_hz
            freq_mask = (full_fax >= win_lo) & (full_fax <= win_hi)
            freq_win = full_fax[freq_mask]
            if freq_win.size < 3:
                result[str(int(f_cand))] = entry
                continue

            # Per-channel: centre frequency (parabolic interp) + amplitude + SNR
            amps_sq: dict[int, float] = {}
            tracked_freqs: list[float] = []
            for ch, idx in ch_idx.items():
                mag = full_fft[ch][freq_mask]
                pk = int(np.argmax(mag))
                # Parabolic sub-bin interpolation
                if 0 < pk < len(mag) - 1:
                    a, b, c = mag[pk - 1], mag[pk], mag[pk + 1]
                    d = 0.5 * (a - c) / (a - 2 * b + c + 1e-30)
                    f_fine = freq_win[pk] + d * df
                else:
                    f_fine = freq_win[pk]
                amp_db = 20.0 * np.log10(mag[pk] + 1e-30)
                # SNR: Peak vs. Median-Hintergrund im Fenster (ohne ±3 Bins um Peak)
                bg_mask = np.ones(len(mag), dtype=bool)
                bg_mask[max(0, pk - 3) : min(len(mag), pk + 4)] = False
                bg_med = np.median(mag[bg_mask]) if bg_mask.any() else 1e-30
                snr_db = 20.0 * np.log10((mag[pk] + 1e-30) / (bg_med + 1e-30))
                entry[f"ch{ch}_freq_hz"] = round(float(f_fine), 2)
                entry[f"ch{ch}_amp_db"] = round(float(amp_db), 2)
                entry[f"ch{ch}_snr_db"] = round(float(snr_db), 2)
                amps_sq[ch] = float(mag[pk]) ** 2
                tracked_freqs.append(float(f_fine))

            # Artefakt-Abstand zur tatsächlich getrackten (gemittelten) Frequenz
            if tracked_freqs:
                mean_tracked = float(np.mean(tracked_freqs))
                diffs2 = np.abs(self._known_artifacts - mean_tracked)
                nearest_i2 = int(np.argmin(diffs2))
                entry["tracked_freq_hz"] = round(mean_tracked, 1)
                entry["tracked_artifact_offset_hz"] = round(
                    float(mean_tracked - float(self._known_artifacts[nearest_i2])), 1
                )

            # Cross-channel coherence at f_cand (Welch, nperseg=candidate_coherence_nperseg)
            pairs = [(3, 4, "ch3_ch4"), (1, 3, "ch1_ch3"), (1, 4, "ch1_ch4")]
            for ca, cb, label in pairs:
                if ca not in ch_idx or cb not in ch_idx:
                    continue
                try:
                    f_coh, coh = signal.coherence(
                        voltages[ch_idx[ca]],
                        voltages[ch_idx[cb]],
                        fs=fs,
                        nperseg=self.candidate_coherence_nperseg,
                    )
                    bin_i = int(np.argmin(np.abs(f_coh - f_cand)))
                    entry[f"coherence_{label}"] = round(float(coh[bin_i]), 4)
                except Exception:
                    pass

            result[str(int(f_cand))] = entry
        return result

    def _frame_record(
        self,
        frame: SweepFrame,
        events: list[dict],
        *,
        _timestamp_local: str | None = None,
        _light_phase: str | None = None,
    ) -> dict:
        if _timestamp_local is None or _light_phase is None:
            _timestamp_local, _light_phase = classify_light_phase(
                frame.timestamp_utc,
                timezone_name=self.timezone_name,
                day_start_hour=self.day_start_hour,
                night_start_hour=self.night_start_hour,
            )
        temperature_c = None
        if self.temperature_poller is not None:
            try:
                temperature_c = self.temperature_poller()
            except Exception:
                pass
        sample_count = frame.n_samples or int(frame.voltages.shape[1])
        return {
            "sequence": frame.sequence,
            "timestamp_utc": frame.timestamp_utc,
            "timestamp_local": _timestamp_local,
            "light_phase": _light_phase,
            "sample_rate_hz": frame.sample_rate_hz,
            "sample_count": sample_count,
            "sample_duration_s": float(sample_count / frame.sample_rate_hz),
            "temperature_c": temperature_c,
            "band_energy": frame.band_energy.tolist(),
            "peaks": frame.peaks,
            "event_types": [event["type"] for event in events],
            "candidate_analysis": self._track_candidates(frame),
        }

    @staticmethod
    def _merge_cross_channel_drifts(
        drift_events: list[dict],
        tolerance_hz: float = 500.0,
    ) -> list[dict]:
        merged = []
        consumed: set[int] = set()
        for index, event in enumerate(drift_events):
            if index in consumed:
                continue
            group = [event]
            for other_index, other in enumerate(drift_events[index + 1 :], index + 1):
                same_region = (
                    abs(float(other["end_frequency_hz"]) - float(event["end_frequency_hz"]))
                    <= tolerance_hz
                )
                same_direction = np.sign(other["slope_hz_per_second"]) == np.sign(
                    event["slope_hz_per_second"]
                )
                if other["channel"] != event["channel"] and same_region and same_direction:
                    group.append(other)
                    consumed.add(other_index)
            channels = sorted({int(item["channel"]) for item in group})
            if len(channels) < 2:
                continue
            merged.append(
                {
                    "type": "cross_channel_frequency_drift",
                    "sequence": int(event["sequence"]),
                    "channels": channels,
                    "start_frequency_hz": float(
                        np.mean([item["start_frequency_hz"] for item in group])
                    ),
                    "end_frequency_hz": float(
                        np.mean([item["end_frequency_hz"] for item in group])
                    ),
                    "displacement_hz": float(np.mean([item["displacement_hz"] for item in group])),
                    "slope_hz_per_second": float(
                        np.mean([item["slope_hz_per_second"] for item in group])
                    ),
                    "minimum_r_squared": float(min(item["r_squared"] for item in group)),
                }
            )
        return merged

    def _record_events(
        self,
        frame: SweepFrame,
        events: list[dict],
        *,
        _timestamp_local: str | None = None,
        _light_phase: str | None = None,
    ) -> None:
        if _timestamp_local is None or _light_phase is None:
            _timestamp_local, _light_phase = classify_light_phase(
                frame.timestamp_utc,
                timezone_name=self.timezone_name,
                day_start_hour=self.day_start_hour,
                night_start_hour=self.night_start_hour,
            )
        timestamp_local, light_phase = _timestamp_local, _light_phase
        for event in events:
            event = {
                "timestamp_utc": frame.timestamp_utc,
                "timestamp_local": timestamp_local,
                "light_phase": light_phase,
                **event,
            }
            self.events.append(event)
            if self.persist_events:
                with (self.output_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event) + "\n")
        if events and self.save_event_raw:
            np.savez_compressed(
                self.output_dir / f"event_frame_{frame.sequence:06d}.npz",
                voltages=frame.voltages,
                band_energy=frame.band_energy,
                frequencies=frame.frequencies,
                psd=frame.psd,
            )

    def process_frame(self, frame: SweepFrame) -> list[dict]:
        timestamp_s = datetime.fromisoformat(frame.timestamp_utc).timestamp()
        # classify_light_phase einmal berechnen und an alle Unterroutinen weitergeben
        timestamp_local, light_phase = classify_light_phase(
            frame.timestamp_utc,
            timezone_name=self.timezone_name,
            day_start_hour=self.day_start_hour,
            night_start_hour=self.night_start_hour,
        )
        self.peak_psd_history.append(frame.psd)
        events = []
        if len(self.peak_psd_history) == self.peak_psd_history.maxlen:
            averaged_psd = np.mean(np.stack(self.peak_psd_history), axis=0)
            averaged_peaks = {
                channel: detect_condition_peaks(
                    frame.frequencies,
                    averaged_psd[index],
                    ignore_frequency_bands_hz=MAINS_HARMONIC_BANDS_HZ,
                )
                for index, channel in enumerate(CHANNELS)
            }
            drift_events = self.peak_tracker.update(frame.sequence, timestamp_s, averaged_peaks)
            events.extend(self._merge_cross_channel_drifts(drift_events))
            events.extend(self.persistent_peak_detector.update(frame.sequence, averaged_peaks))
        events.extend(self.band_detector.update(frame.sequence, frame.band_energy))
        self._record_events(frame, events, _timestamp_local=timestamp_local, _light_phase=light_phase)
        if self.persist_frames:
            with (self.output_dir / "frames.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(
                    json.dumps(
                        self._frame_record(
                            frame, events,
                            _timestamp_local=timestamp_local,
                            _light_phase=light_phase,
                        )
                    ) + "\n"
                )
        # Voltages freigeben BEVOR ring.append, damit current_bytes korrekt bleibt
        frame.free_voltages()
        self.ring.append(frame)
        self.feature_history.append(
            {
                "sequence": frame.sequence,
                "timestamp_utc": frame.timestamp_utc,
                "timestamp_local": timestamp_local,
                "band_energy": frame.band_energy.copy(),
            }
        )
        self.frames_processed += 1
        # Atomic heartbeat write — lets measurement.py status detect a frozen process
        _hb = {
            "last_frame_utc": frame.timestamp_utc,
            "sequence": frame.sequence,
            "frames_processed": self.frames_processed,
            "pid": os.getpid(),
        }
        _hb_path = self.output_dir / "heartbeat.json"
        _hb_tmp = _hb_path.with_suffix(".tmp")
        _hb_tmp.write_text(json.dumps(_hb))
        _hb_tmp.replace(_hb_path)
        return events

    def status(self) -> dict:
        total, available = linux_memory_bytes()
        return {
            "frames_in_ram": len(self.ring),
            "evicted_frames": self.ring.evicted_frames,
            "ring_usage_gib": self.ring.usage_gib(),
            "ring_budget_gib": self.ring.max_bytes / 1024**3,
            "system_available_gib": available / 1024**3,
            "active_peak_tracks": len(self.peak_tracker.tracks),
            "events": len(self.events),
        }

    def plot_dashboard(self, frame: SweepFrame):
        fig, axes = plt.subplots(3, 1, figsize=(15, 12))
        mask = (frame.frequencies >= 20) & (frame.frequencies <= 250000)
        for channel_index, channel in enumerate(CHANNELS):
            axes[0].plot(
                frame.frequencies[mask] / 1000,
                10 * np.log10(np.maximum(frame.psd[channel_index, mask], 1e-30)),
                label=f"CH{channel}",
                linewidth=0.8,
            )
        axes[0].set_xlim(0, 100)
        axes[0].set_ylabel("PSD (dB V²/Hz)")
        timestamp_local, light_phase = classify_light_phase(
            frame.timestamp_utc,
            timezone_name=self.timezone_name,
            day_start_hour=self.day_start_hour,
            night_start_hour=self.night_start_hour,
        )
        axes[0].set_title(
            f"Current spectrum — frame {frame.sequence} — {light_phase} — "
            f"{timestamp_local[:19]}"
        )
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        if len(self.feature_history) >= 2:
            history = list(self.feature_history)
            sequences = [item["sequence"] for item in history]
            matrix = np.stack([item["band_energy"][0] for item in history]).T
            image = axes[1].imshow(
                10 * np.log10(np.maximum(matrix, 1e-30)),
                aspect="auto",
                origin="lower",
                interpolation="nearest",
                extent=[sequences[0], sequences[-1], 0, 100],
                cmap="viridis",
            )
            axes[1].set_ylabel("CH1 band frequency (kHz)")
            axes[1].set_title("20-band energy history")
            fig.colorbar(image, ax=axes[1], label="Band energy (dB V²)")
        for track in self.peak_tracker.tracks.values():
            if len(track.observations) < 2:
                continue
            x = [item[0] for item in track.observations]
            y = [item[2] / 1000 for item in track.observations]
            axes[2].plot(
                x, y, marker=".", linewidth=0.8, label=f"CH{track.channel}/T{track.track_id}"
            )
        axes[2].set_ylabel("Tracked peak (kHz)")
        axes[2].set_xlabel("Frame sequence")
        axes[2].set_title("Peak trajectories")
        axes[2].grid(alpha=0.3)
        handles, labels = axes[2].get_legend_handles_labels()
        if handles and len(self.peak_tracker.tracks) <= 12:
            axes[2].legend(fontsize=7, ncol=3)
        fig.tight_layout()
        return fig
