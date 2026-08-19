"""Tests for the reusable plant experiment modules."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from plant_ae.deep_acquisition import timebase_for
from plant_ae.rolling import (
    ContinuousFrequencyMonitor,
    CrossChannelPeakDetector,
    PeakTracker,
    RamFrameRing,
    RollingBandDetector,
    SweepFrame,
    classify_light_phase,
)
from plant_ae.watering import configure_scope, detect_condition_peaks


def test_legacy_osc_vib_source_package_is_gone() -> None:
    characterization_root = Path(__file__).resolve().parents[1]
    assert not (characterization_root / "src" / "osc_vib").exists()


def test_ram_ring_evicts_oldest_frame() -> None:
    def frame(sequence: int) -> SweepFrame:
        return SweepFrame(
            sequence=sequence,
            timestamp_utc="2026-06-22T12:00:00+00:00",
            voltages=np.zeros((3, 8), dtype=np.float32),
            band_energy=np.zeros((3, 20), dtype=np.float32),
            frequencies=np.zeros(5, dtype=np.float32),
            psd=np.zeros((3, 5), dtype=np.float32),
            peaks={1: [], 2: [], 3: []},
        )

    first = frame(1)
    ring = RamFrameRing(max_bytes=first.nbytes)
    ring.append(first)
    ring.append(frame(2))

    assert [item.sequence for item in ring.frames] == [2]
    assert ring.evicted_frames == 1


def test_workflow_notebooks_do_not_execute_other_notebooks() -> None:
    notebook_dir = Path(__file__).resolve().parents[1] / "notebooks"
    forbidden = ("exec(compile", "execute_notebook_code", "__globals__", "osc_vib")

    for name in (
        "03_watering_experiment.ipynb",
        "04_continuous_frequency_sweep.ipynb",
        "05_automated_hybrid_experiment.ipynb",
    ):
        notebook = json.loads((notebook_dir / name).read_text(encoding="utf-8"))
        source = "\n".join(
            "".join(cell.get("source", []))
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code"
        )
        assert not any(pattern in source for pattern in forbidden)


def test_scope_configuration_resets_stale_memory_depth(monkeypatch) -> None:
    class Connection:
        def __init__(self) -> None:
            self.commands: list[str] = []

        def write(self, command: str) -> None:
            self.commands.append(command)

        def query(self, command: str) -> str:
            responses = {
                ":ACQ:SRAT?": "25000000",
                ":ACQ:MDEP?": "AUTO",
                ":TIM:SCAL?": "0.01",
                ":TRIG:MODE?": "EDGE",
                ":TRIG:EDGE:SOUR?": "CHAN1",
                ":TRIG:EDGE:LEV?": "0.02",
            }
            return responses[command]

    monkeypatch.setattr("plant_ae.watering.time.sleep", lambda _: None)
    connection = Connection()
    settings = configure_scope(connection)

    assert connection.commands.index(":RUN") < connection.commands.index(":ACQ:MDEP AUTO")
    assert ":ACQ:MDEP 100000" not in connection.commands
    assert settings["sample_rate_hz"] == 25_000_000


def test_deep_profile_resolution() -> None:
    assert timebase_for(500_000, 300_000) == 0.05
    assert 300_000 / 500_000 == 0.6
    assert 500_000 / 300_000 == 5 / 3


def test_light_phase_uses_berlin_local_time() -> None:
    local_time, phase = classify_light_phase("2026-06-22T22:30:00+00:00")
    assert local_time.startswith("2026-06-23T00:30:00+02:00")
    assert phase == "night"


def test_frequency_drift_is_measured_per_second() -> None:
    tracker = PeakTracker(
        min_points_for_drift=4,
        min_displacement_hz=500,
        min_slope_hz_per_second=1,
        min_r_squared=0.99,
        event_cooldown_frames=1,
    )
    events = []
    for sequence in range(4):
        events = tracker.update(
            sequence,
            timestamp_s=sequence * 10.0,
            peaks_by_channel={
                1: [
                    {
                        "frequency_hz": 10_000 + sequence * 200,
                        "psd_db": -30,
                        "prominence_db": 12,
                    }
                ],
                2: [],
                3: [],
            },
        )
    assert events[0]["slope_hz_per_second"] == 20


def test_persistent_peak_requires_two_channels() -> None:
    detector = CrossChannelPeakDetector(
        tolerance_hz=100,
        persistence_frames=3,
        cooldown_frames=10,
        bin_width_hz=50,
    )
    single_channel = {
        1: [{"frequency_hz": 10_000, "prominence_db": 12}],
        2: [],
        3: [],
    }
    assert detector.update(0, single_channel) == []
    peaks = {
        1: [{"frequency_hz": 10_000, "prominence_db": 12}],
        2: [{"frequency_hz": 10_050, "prominence_db": 11}],
        3: [],
    }
    assert detector.update(1, peaks) == []
    assert detector.update(2, peaks) == []
    event = detector.update(3, peaks)[0]
    assert event["type"] == "persistent_cross_channel_peak"
    assert event["channels"] == [1, 2]


def test_band_change_requires_two_channels() -> None:
    """RollingBandDetector flags a band change only when ≥2 active channels
    exceed the threshold persistently.

    Note: CHANNELS = (1, 3, 4) since the 2026-06-22 CH2 hardware fault
    (see experiment_continuous_plant_ae_20260622/HARDWARE_CHANGELOG.md).
    Changing array indices [0:2] therefore modifies CH1 and CH3, not
    CH1 and CH2. The expected channels in the event reflect this."""
    detector = RollingBandDetector(
        history_frames=4,
        min_reference_frames=2,
        threshold_db=3,
        persistence_frames=2,
        cooldown_frames=10,
    )
    baseline = np.ones((3, 20), dtype=np.float32)
    detector.update(0, baseline)
    detector.update(1, baseline)
    changed = baseline.copy()
    changed[0:2, 0] *= 10  # CH1 (index 0) and CH3 (index 1) in CHANNELS=(1,3,4)
    assert detector.update(2, changed) == []
    event = detector.update(3, changed)[0]
    assert event["type"] == "cross_channel_band_energy_change"
    assert event["channels"] == [1, 3]  # CH1 and CH3, NOT CH1 and CH2 (CH2 is disabled)


def test_mains_harmonics_can_be_excluded_from_peaks() -> None:
    frequencies = np.arange(0, 2001, dtype=float)
    psd = np.ones_like(frequencies)
    psd[50] = 1e6
    psd[550] = 1e5
    psd[1234] = 1e4

    peaks = detect_condition_peaks(
        frequencies,
        psd,
        prominence_db=3,
        min_distance_hz=10,
        ignore_frequency_bands_hz=((45, 55), (545, 555)),
    )

    assert all(abs(peak["frequency_hz"] - 50) > 5 for peak in peaks)
    assert all(abs(peak["frequency_hz"] - 550) > 5 for peak in peaks)
    assert any(abs(peak["frequency_hz"] - 1234) < 2 for peak in peaks)


def test_drift_requires_parallel_channels_and_direction() -> None:
    same_direction = [
        {
            "sequence": 20,
            "channel": 1,
            "start_frequency_hz": 10_000,
            "end_frequency_hz": 10_700,
            "displacement_hz": 700,
            "slope_hz_per_second": 2.0,
            "r_squared": 0.9,
        },
        {
            "sequence": 20,
            "channel": 2,
            "start_frequency_hz": 10_100,
            "end_frequency_hz": 10_750,
            "displacement_hz": 650,
            "slope_hz_per_second": 1.8,
            "r_squared": 0.85,
        },
    ]
    event = ContinuousFrequencyMonitor._merge_cross_channel_drifts(same_direction)[0]
    assert event["type"] == "cross_channel_frequency_drift"
    assert event["channels"] == [1, 2]

    opposite_direction = [same_direction[0], {**same_direction[1], "slope_hz_per_second": -1.8}]
    assert ContinuousFrequencyMonitor._merge_cross_channel_drifts(opposite_direction) == []
