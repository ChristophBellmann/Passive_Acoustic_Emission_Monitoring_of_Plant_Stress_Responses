"""Jupyter widget controls for notebook-defined measurement workflows."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CHARACTERIZATION_ROOT = Path(__file__).resolve().parents[2]
NOTEBOOK_ROOT = CHARACTERIZATION_ROOT / "notebooks"
MEASUREMENT_PY = CHARACTERIZATION_ROOT / "measurement.py"
CONTROL_PANEL_NOTEBOOK = NOTEBOOK_ROOT / "00_control_panel.ipynb"
LONGRUN_NOTEBOOK = NOTEBOOK_ROOT / "04_continuous_frequency_sweep.ipynb"


@dataclass(frozen=True)
class NotebookEntry:
    label: str
    path: Path


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(CHARACTERIZATION_ROOT))
    except ValueError:
        return str(path)


def list_notebooks(*, include_archived: bool = False) -> list[NotebookEntry]:
    notebooks = sorted(NOTEBOOK_ROOT.glob("*.ipynb"))
    if include_archived:
        notebooks.extend(sorted((NOTEBOOK_ROOT / "archive").glob("*.ipynb")))
        notebooks.extend(sorted((NOTEBOOK_ROOT / "_archived").glob("*.ipynb")))

    entries = []
    for notebook in notebooks:
        if notebook.name.startswith(".ipynb_checkpoints"):
            continue
        if notebook.resolve() == CONTROL_PANEL_NOTEBOOK.resolve():
            continue
        entries.append(NotebookEntry(_relative(notebook), notebook.resolve()))
    return entries


def _command_environment() -> dict[str, str]:
    environment = os.environ.copy()
    python_paths = [str(CHARACTERIZATION_ROOT / "instrument_control"), str(CHARACTERIZATION_ROOT)]
    existing = environment.get("PYTHONPATH")
    if existing:
        python_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    environment["PYTHONUNBUFFERED"] = "1"
    return environment


def run_measurement_command(*args: str, timeout: float | None = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MEASUREMENT_PY), *args],
        cwd=CHARACTERIZATION_ROOT,
        env=_command_environment(),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def measurement_status() -> dict[str, object]:
    result = run_measurement_command("status", "--json", timeout=10)
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        payload = {"active": False, "status": "unknown", "raw": result.stdout + result.stderr}
    payload["returncode"] = result.returncode
    return payload


def latest_log_tail(lines: int = 80) -> str:
    state = measurement_status()
    log_path = state.get("log")
    if not log_path:
        return "Kein Logpfad im aktuellen Messstatus."
    path = Path(str(log_path))
    if not path.is_absolute():
        path = CHARACTERIZATION_ROOT / path
    if not path.is_file():
        return f"Logdatei nicht gefunden: {path}"
    content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(content[-lines:]) if content else "(Log ist leer.)"


def show_control_panel():
    """Render the notebook control panel in the current Jupyter output cell."""
    try:
        import ipywidgets as widgets
        from IPython.display import Markdown, clear_output, display
    except ImportError as exc:  # pragma: no cover - only relevant in notebooks
        raise RuntimeError(
            "ipywidgets fehlt. Bitte `./setup_jupyter.sh` in src/characterization ausführen."
        ) from exc

    include_archived = widgets.Checkbox(value=False, description="Archive anzeigen")
    notebook_dropdown = widgets.Dropdown(description="Notebook", layout=widgets.Layout(width="100%"))
    auto_push = widgets.Checkbox(value=False, description="Nach Hintergrundlauf auto-push")
    start_button = widgets.Button(
        description="Start Longrun (NB04)", button_style="success", icon="play"
    )
    stop_button = widgets.Button(description="Stop", button_style="danger", icon="stop")
    status_button = widgets.Button(description="Status", icon="info")
    log_button = widgets.Button(description="Log", icon="file-text")
    run_button = widgets.Button(description="Run Once", button_style="warning", icon="step-forward")
    refresh_button = widgets.Button(description="Refresh", icon="refresh")
    output = widgets.Output(layout=widgets.Layout(border="1px solid #ddd", padding="8px"))

    def refresh_options() -> None:
        entries = list_notebooks(include_archived=include_archived.value)
        notebook_dropdown.options = [(entry.label, str(entry.path)) for entry in entries]
        longrun_value = str(LONGRUN_NOTEBOOK.resolve())
        option_values = {str(entry.path) for entry in entries}
        if longrun_value in option_values:
            notebook_dropdown.value = longrun_value
        elif entries and notebook_dropdown.value is None:
            notebook_dropdown.value = str(entries[0].path)

    def write_result(title: str, result: subprocess.CompletedProcess[str]) -> None:
        with output:
            clear_output()
            print(title)
            print(f"Exit-Code: {result.returncode}")
            text = (result.stdout or "") + (result.stderr or "")
            print(text.strip() or "(keine Ausgabe)")

    def selected_notebook() -> str:
        value = notebook_dropdown.value
        if not value:
            raise RuntimeError("Kein Notebook ausgewählt.")
        return str(value)

    def on_refresh(_button) -> None:
        refresh_options()
        on_status(_button)

    def on_status(_button) -> None:
        result = run_measurement_command("status", timeout=10)
        write_result("Messstatus", result)

    def on_start(_button) -> None:
        args = ["start", "--notebook", str(LONGRUN_NOTEBOOK.resolve())]
        if not auto_push.value:
            args.append("--no-push")
        result = run_measurement_command(*args, timeout=20)
        write_result("Hintergrundlauf starten", result)

    def on_stop(_button) -> None:
        result = run_measurement_command("stop", "--timeout", "900", timeout=930)
        write_result("Hintergrundlauf stoppen", result)

    def on_log(_button) -> None:
        with output:
            clear_output()
            print(latest_log_tail())

    def on_run(_button) -> None:
        run_button.disabled = True
        try:
            result = run_measurement_command(
                "run",
                "--notebook",
                selected_notebook(),
                timeout=None,
            )
            write_result("Notebook einmalig ausführen", result)
        finally:
            run_button.disabled = False

    include_archived.observe(lambda change: refresh_options(), names="value")
    refresh_button.on_click(on_refresh)
    status_button.on_click(on_status)
    start_button.on_click(on_start)
    stop_button.on_click(on_stop)
    log_button.on_click(on_log)
    run_button.on_click(on_run)

    refresh_options()
    controls = widgets.VBox(
        [
            widgets.HTML("<h3>Plant AE Notebook Control</h3>"),
            widgets.HTML(
                "<p><b>Single Source of Truth:</b> NB00 ist der Bedien-Einstieg; "
                "<code>04_continuous_frequency_sweep.ipynb</code> definiert den Longrun; "
                "<code>measurement.py</code> führt ihn nur im Hintergrund aus. "
                "Das Dropdown gilt für <i>Run Once</i>, nicht für den Longrun-Start.</p>"
            ),
            widgets.HBox([include_archived, auto_push]),
            notebook_dropdown,
            widgets.HBox([start_button, stop_button, status_button, log_button, run_button, refresh_button]),
            output,
        ]
    )
    display(controls)
    with output:
        display(
            Markdown(
                "Bereit. `Start Longrun (NB04)` nutzt `measurement.py start`; `Run Once` "
                "führt das Notebook aus dem Dropdown im Vordergrund aus. Der Longrun-Start "
                "ist fest an NB04 gebunden. In Phase 3 sind Home Assistant, automatische "
                "Bewässerung und Temperaturmessung nicht verfügbar."
            )
        )
