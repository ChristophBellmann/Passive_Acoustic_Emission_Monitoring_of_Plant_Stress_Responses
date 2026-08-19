"""Tests for the notebook process controller."""

from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("measurement", ROOT / "measurement.py")
assert SPEC and SPEC.loader
measurement = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measurement)


def test_default_workflow_is_the_continuous_notebook() -> None:
    assert measurement.DEFAULT_NOTEBOOK.name == "04_continuous_frequency_sweep.ipynb"
    assert measurement.DEFAULT_NOTEBOOK.is_file()


def test_process_identity_rejects_reused_or_missing_pid() -> None:
    assert not measurement.state_process_is_alive(None)
    assert not measurement.state_process_is_alive({"pid": 999_999_999})
    assert not measurement.state_process_is_alive(
        {"pid": 999_999_999, "process_start_ticks": 1}
    )


def test_notebook_runner_executes_code_cells(tmp_path: Path) -> None:
    marker = tmp_path / "executed.txt"
    notebook = tmp_path / "workflow.ipynb"
    notebook.write_text(
        json.dumps(
            {
                "cells": [
                    {"cell_type": "markdown", "metadata": {}, "source": ["ignored"]},
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "execution_count": None,
                        "outputs": [],
                        "source": [
                            "%matplotlib inline\n",
                            "from pathlib import Path\n"
                            f"Path({str(marker)!r}).write_text('ok')"
                        ],
                    },
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )

    assert measurement.run_notebook(str(notebook), auto_push=False) == 0
    assert marker.read_text(encoding="utf-8") == "ok"


def test_start_status_stop_lifecycle(tmp_path: Path, monkeypatch) -> None:
    control_dir = tmp_path / "control"
    notebook = tmp_path / "long-running.ipynb"
    notebook.write_text(
        json.dumps(
            {
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "execution_count": None,
                        "outputs": [],
                        "source": [
                            "import time\n",
                            "try:\n",
                            "    while True:\n",
                            "        time.sleep(0.1)\n",
                            "except KeyboardInterrupt:\n",
                            "    print('stopped')\n",
                        ],
                    }
                ],
                "metadata": {},
                "nbformat": 4,
                "nbformat_minor": 5,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("MEASUREMENT_CONTROL_DIR", str(control_dir))
    monkeypatch.setattr(measurement, "CONTROL_DIR", control_dir)
    monkeypatch.setattr(measurement, "STATE_PATH", control_dir / "state.json")
    monkeypatch.setattr(measurement, "LOG_DIR", control_dir / "logs")

    try:
        assert measurement.start(str(notebook), auto_push=False) == 0
        state = measurement.read_state()
        assert measurement.state_process_is_alive(state)
        time.sleep(0.3)
        assert measurement.stop(timeout=3) == 0
        assert not measurement.state_process_is_alive(measurement.read_state())
    finally:
        state = measurement.read_state()
        if measurement.state_process_is_alive(state):
            measurement.stop(timeout=1)


def test_runner_command_controls_automatic_push(tmp_path: Path) -> None:
    notebook = tmp_path / "workflow.ipynb"
    without_push = measurement.runner_command(notebook, auto_push=False)
    with_push = measurement.runner_command(notebook, auto_push=True)

    assert "--no-push" in without_push
    assert "--no-push" not in with_push
