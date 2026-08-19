from __future__ import annotations

import importlib.util
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


MODULE_PATH = Path(__file__).with_name("continuous_characterization.py")
SPEC = importlib.util.spec_from_file_location("continuous_characterization", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def local(hour: int) -> datetime:
    return datetime(2026, 6, 22, hour, tzinfo=ZoneInfo("Europe/Berlin"))


def test_day_night_classification() -> None:
    assert MODULE.classify_light_phase(local(6), 6, 22) == "day"
    assert MODULE.classify_light_phase(local(21), 6, 22) == "day"
    assert MODULE.classify_light_phase(local(22), 6, 22) == "night"
    assert MODULE.classify_light_phase(local(5), 6, 22) == "night"


def test_wrapped_day_interval() -> None:
    assert MODULE.classify_light_phase(local(23), 22, 6) == "day"
    assert MODULE.classify_light_phase(local(4), 22, 6) == "day"
    assert MODULE.classify_light_phase(local(12), 22, 6) == "night"


def test_equal_boundaries_are_rejected() -> None:
    try:
        MODULE.classify_light_phase(local(12), 6, 6)
    except ValueError:
        pass
    else:
        raise AssertionError("Identical boundaries must fail")


def test_watering_requires_explicit_runtime_permission() -> None:
    class Sampler:
        def __init__(self) -> None:
            self.calls = 0

        def assert_watering_ready(self) -> None:
            pass

        def water_once(self) -> None:
            self.calls += 1

    sampler = Sampler()
    experiment = MODULE.ContinuousCharacterizationExperiment.__new__(
        MODULE.ContinuousCharacterizationExperiment
    )
    experiment.config = {
        "watering": {
            "enabled": True,
            "once_after_baseline_minutes": 0,
            "only_below_soil_moisture_percent": None,
        }
    }
    experiment.hardware = {"environment_sampler": sampler}
    experiment.latest_environment = {"soil_moisture_percent": 40.0}
    experiment.watering_triggered = False
    experiment.event = lambda *args, **kwargs: None

    experiment.enable_watering = False
    experiment.maybe_water(time.monotonic())
    assert sampler.calls == 0

    experiment.enable_watering = True
    experiment.maybe_water(time.monotonic())
    experiment.maybe_water(time.monotonic())
    assert sampler.calls == 1
