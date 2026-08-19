#!/usr/bin/env python3
"""Start, stop, and inspect notebook-defined measurement workflows."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_NOTEBOOK = ROOT / "notebooks" / "04_continuous_frequency_sweep.ipynb"
REPORT_ROOT = ROOT / "data" / "reports" / "notebooks" / "04_continuous_frequency_sweep"
CONTROL_DIR = Path(
    os.environ.get("MEASUREMENT_CONTROL_DIR", ROOT / ".measurement-control")
).resolve()
STATE_PATH = CONTROL_DIR / "state.json"
LOG_DIR = CONTROL_DIR / "logs"
DATA_DIR = ROOT / "data"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_state() -> dict[str, Any] | None:
    try:
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None


def write_state(state: dict[str, Any]) -> None:
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(STATE_PATH)


def process_start_ticks(pid: int) -> int | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8").split()
        if fields[2] == "Z":
            return None
        return int(fields[21])
    except (FileNotFoundError, IndexError, OSError, ValueError):
        return None


def state_process_is_alive(state: dict[str, Any] | None) -> bool:
    if not state:
        return False
    try:
        pid = int(state["pid"])
        expected_ticks = int(state["process_start_ticks"])
    except (KeyError, TypeError, ValueError):
        return False
    return process_start_ticks(pid) == expected_ticks


def resolve_notebook(value: str | None) -> Path:
    notebook = DEFAULT_NOTEBOOK if value is None else Path(value).expanduser()
    if not notebook.is_absolute():
        notebook = (Path.cwd() / notebook).resolve()
    else:
        notebook = notebook.resolve()
    if notebook.suffix != ".ipynb" or not notebook.is_file():
        raise ValueError(f"Notebook nicht gefunden: {notebook}")
    return notebook


def display_path(path: Path) -> Path:
    return path.relative_to(ROOT) if path.is_relative_to(ROOT) else path


def runner_command(notebook: Path, *, auto_push: bool) -> list[str]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "_run",
        "--notebook",
        str(notebook),
    ]
    if not auto_push:
        command.append("--no-push")
    return command


def notebook_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["PYTHONUNBUFFERED"] = "1"
    python_paths = [str(ROOT / "instrument_control"), str(ROOT)]
    existing = environment.get("PYTHONPATH")
    if existing:
        python_paths.append(existing)
    environment["PYTHONPATH"] = os.pathsep.join(python_paths)
    return environment


def start(notebook_value: str | None, *, auto_push: bool) -> int:
    existing = read_state()
    if state_process_is_alive(existing):
        print(f"Erfassung läuft bereits (PID {existing['pid']}).")
        return 1

    try:
        notebook = resolve_notebook(notebook_value)
    except ValueError as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 2

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{notebook.stem}_{stamp}.log"
    environment = notebook_environment()

    with log_path.open("ab", buffering=0) as log_handle:
        process = subprocess.Popen(
            runner_command(notebook, auto_push=auto_push),
            cwd=notebook.parent,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            env=environment,
            start_new_session=True,
        )

    ticks = None
    for _ in range(50):
        ticks = process_start_ticks(process.pid)
        if ticks is not None:
            break
        time.sleep(0.01)
    if ticks is None:
        print("Fehler: Messprozess konnte nicht gestartet werden.", file=sys.stderr)
        return 1

    write_state(
        {
            "status": "running",
            "pid": process.pid,
            "process_start_ticks": ticks,
            "notebook": str(notebook),
            "log": str(log_path),
            "started_utc": utc_now(),
            "auto_push": auto_push,
        }
    )

    # Catch immediate notebook/bootstrap failures before claiming a successful
    # start. Hardware errors that happen later remain visible through status/log.
    time.sleep(1)
    state = read_state()
    if not state_process_is_alive(state):
        print("Fehler: Die Erfassung wurde direkt wieder beendet.", file=sys.stderr)
        print(f"Log: {display_path(log_path)}", file=sys.stderr)
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            lines = []
        if lines:
            print("\n".join(lines[-12:]), file=sys.stderr)
        return 1

    print(f"Erfassung gestartet (PID {process.pid}).")
    print(f"Notebook: {display_path(notebook)}")
    print(f"Log: {display_path(log_path)}")
    print(f"Daten-Push: {'automatisch' if auto_push else 'deaktiviert'}")
    return 0


def wait_until_stopped(state: dict[str, Any], timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    publishing_deadline_extended = False
    while time.monotonic() < deadline:
        if not state_process_is_alive(state):
            return True
        current = read_state()
        if (
            current
            and current.get("status") == "publishing"
            and not publishing_deadline_extended
        ):
            deadline = max(deadline, time.monotonic() + 600)
            publishing_deadline_extended = True
        time.sleep(0.2)
    return not state_process_is_alive(state)


def stop(timeout: float) -> int:
    state = read_state()
    if not state_process_is_alive(state):
        print("Keine Erfassung aktiv.")
        return 0

    pid = int(state["pid"])
    print(f"Stoppe Erfassung (PID {pid}) …")
    with suppress(ProcessLookupError):
        os.killpg(pid, signal.SIGINT)

    if not wait_until_stopped(state, timeout):
        print(f"Kein sauberer Abbruch nach {timeout:g} s; sende SIGTERM.")
        with suppress(ProcessLookupError):
            os.killpg(pid, signal.SIGTERM)
        if not wait_until_stopped(state, 5):
            print("Prozess reagiert nicht; sende SIGKILL.", file=sys.stderr)
            with suppress(ProcessLookupError):
                os.killpg(pid, signal.SIGKILL)
            wait_until_stopped(state, 2)

    current = read_state() or state
    current.update({"status": "stopped", "stopped_utc": utc_now()})
    write_state(current)
    print("Erfassung gestoppt.")
    return 0


def format_age(timestamp: str | None) -> str:
    if not timestamp:
        return "unbekannt"
    try:
        started = datetime.fromisoformat(timestamp)
        seconds = max(0, int((datetime.now(timezone.utc) - started).total_seconds()))
    except ValueError:
        return "unbekannt"
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def status(as_json: bool) -> int:
    state = read_state()
    alive = state_process_is_alive(state)
    if not state:
        payload = {"active": False, "status": "not_started"}
    else:
        payload = dict(state)
        payload["active"] = alive
        if not alive and payload.get("status") == "running":
            payload["status"] = "stale"

    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if alive else 1

    if not state:
        print("Status: noch nie gestartet")
        return 1

    print(f"Status: {'ERFASSUNG AKTIV' if alive else 'nicht aktiv'}")
    print(f"PID: {state.get('pid', '–')}")
    print(f"Laufzeit: {format_age(state.get('started_utc'))}")
    print(f"Notebook: {state.get('notebook', '–')}")
    print(f"Log: {state.get('log', '–')}")
    if not alive:
        print(f"Letzter Zustand: {payload.get('status', 'unbekannt')}")
        if "exit_code" in state:
            print(f"Exit-Code: {state['exit_code']}")
    if state.get("publish_commit"):
        print(f"Daten-Commit: {state['publish_commit']}")
    if state.get("publish_error"):
        print(f"Push-Fehler: {state['publish_error']}")
    # Heartbeat-Prüfung: letzte Frame-Zeit aus der neuesten Session
    if REPORT_ROOT.exists():
        hb_files = sorted(REPORT_ROOT.glob("*/heartbeat.json"))
        if hb_files:
            try:
                hb = json.loads(hb_files[-1].read_text())
                last_ts = datetime.fromisoformat(hb["last_frame_utc"]).timestamp()
                age_min = (datetime.now(timezone.utc).timestamp() - last_ts) / 60
                seq = hb.get("sequence", "?")
                total = hb.get("frames_processed", "?")
                if alive and age_min > 10:
                    print(f"WARNUNG: letztes Frame vor {age_min:.0f} min "
                          f"(Seq {seq}, {total} Frames gesamt) — Prozess hängt möglicherweise!")
                elif alive:
                    print(f"Letztes Frame: vor {age_min:.1f} min "
                          f"(Seq {seq}, {total} Frames gesamt)")
                else:
                    print(f"Letztes Frame: {hb['last_frame_utc'][:19]} UTC "
                          f"(Seq {seq}, {total} Frames gesamt)")
            except Exception:
                pass
    return 0 if alive else 1


def git_command(
    arguments: list[str], *, check: bool = True, capture_output: bool = False
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def publish_measurement_data() -> dict[str, Any]:
    """Commit data only and push it; LFS is applied by repository attributes."""
    repository_root = Path(
        git_command(["rev-parse", "--show-toplevel"], capture_output=True).stdout.strip()
    )
    data_relative = str(DATA_DIR.relative_to(repository_root))
    data_pathspec = f":(top){data_relative}"

    git_command(["add", "-A", "--", data_pathspec])
    npz_files = [
        f":(top){path.relative_to(repository_root)}" for path in DATA_DIR.rglob("*.npz")
    ]
    for offset in range(0, len(npz_files), 100):
        git_command(["add", "-f", "--", *npz_files[offset : offset + 100]])

    changed = git_command(
        ["diff", "--cached", "--quiet", "--", data_pathspec],
        check=False,
    ).returncode
    if changed == 0:
        print("Keine neuen Messdaten zum Pushen.", flush=True)
        return {"published": False}
    if changed != 1:
        raise RuntimeError("Git konnte die gestagten Messdaten nicht prüfen.")

    message = f"Add measurement data {datetime.now().strftime('%Y-%m-%dT%H:%M')}"
    git_command(["commit", "-m", message, "--", data_pathspec])
    commit = git_command(["rev-parse", "HEAD"], capture_output=True).stdout.strip()
    branch = git_command(
        ["branch", "--show-current"], capture_output=True
    ).stdout.strip()
    if not branch:
        raise RuntimeError("Automatischer Push ist im detached-HEAD-Zustand nicht möglich.")
    git_command(["push", "origin", branch])
    print(f"Messdaten gepusht: {commit[:12]}", flush=True)
    return {"published": True, "commit": commit, "branch": branch}


def run_notebook(
    notebook_value: str,
    *,
    auto_push: bool,
    update_state: bool = False,
) -> int:
    """Execute code cells in-process so SIGINT reaches the active notebook cell."""
    try:
        from IPython.terminal.interactiveshell import TerminalInteractiveShell
    except ImportError:
        print(
            "IPython fehlt. Installiere die Notebook-Abhängigkeiten mit "
            "'pip install -e \".[notebooks]\"'.",
            file=sys.stderr,
        )
        return 2

    notebook = resolve_notebook(notebook_value)
    if update_state:
        # The parent writes the PID record immediately after spawning us.
        # Waiting briefly avoids a fast notebook finishing before that record
        # exists.
        for _ in range(200):
            state = read_state()
            if state and int(state.get("pid", -1)) == os.getpid():
                break
            time.sleep(0.01)

    document = json.loads(notebook.read_text(encoding="utf-8"))
    shell = TerminalInteractiveShell.instance()
    shell.user_ns.setdefault("CHARACTERIZATION_ROOT", ROOT)
    shell.user_ns.setdefault("NOTEBOOK_PATH", notebook)
    exit_code = 0
    previous_cwd = Path.cwd()
    try:
        os.chdir(notebook.parent)
        for index, cell in enumerate(document.get("cells", [])):
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            if not source.strip():
                continue
            print(f"\n--- Notebook-Zelle {index} ---", flush=True)
            result = shell.run_cell(source, store_history=False)
            error = result.error_before_exec or result.error_in_exec
            if error is not None:
                exit_code = 1
                break
    except KeyboardInterrupt:
        print("\nNotebook-Ausführung abgebrochen.", flush=True)
        exit_code = 130
    finally:
        os.chdir(previous_cwd)
        state = read_state()
        if update_state and state and int(state.get("pid", -1)) == os.getpid():
            state.update(
                {
                    "status": "publishing" if auto_push else (
                        "finished" if exit_code == 0 else "failed"
                    ),
                    "finished_utc": utc_now(),
                    "exit_code": exit_code,
                }
            )
            write_state(state)
        if auto_push:
            try:
                result = publish_measurement_data()
                state = read_state() or {}
                if result.get("commit"):
                    state["publish_commit"] = result["commit"]
                state["publish_status"] = (
                    "pushed" if result.get("published") else "no_changes"
                )
            except Exception as exc:
                print(f"Automatischer Daten-Push fehlgeschlagen: {exc}", file=sys.stderr)
                state = read_state() or {}
                state["publish_status"] = "failed"
                state["publish_error"] = str(exc)
            if update_state:
                state["status"] = "finished" if exit_code == 0 else "failed"
                write_state(state)
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Notebook-basierte Messung starten, stoppen und prüfen."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    start_parser = subparsers.add_parser("start", help="Messung im Hintergrund starten")
    start_parser.add_argument(
        "--notebook",
        help=f"Auszuführendes Notebook (Standard: {DEFAULT_NOTEBOOK.relative_to(ROOT)})",
    )
    start_parser.add_argument(
        "--no-push",
        action="store_true",
        help="Messdaten nach dem Lauf nicht automatisch committen und pushen",
    )

    stop_parser = subparsers.add_parser("stop", help="Laufende Messung sauber stoppen")
    stop_parser.add_argument(
        "--timeout",
        type=float,
        default=40,
        help="Sekunden bis zum erzwungenen Abbruch (Standard: 40)",
    )

    status_parser = subparsers.add_parser("status", help="Messstatus anzeigen")
    status_parser.add_argument("--json", action="store_true", help="JSON ausgeben")

    run_parser = subparsers.add_parser(
        "run",
        help="Notebook im Vordergrund ausführen",
    )
    run_parser.add_argument(
        "--notebook",
        required=True,
        help="Auszuführendes Notebook",
    )
    run_parser.add_argument(
        "--push",
        action="store_true",
        help="Messdaten nach erfolgreichem Lauf committen und pushen",
    )

    subparsers.add_parser(
        "publish",
        help="Vorhandene Messdaten jetzt über Git/LFS committen und pushen",
    )

    return parser


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "_run":
        runner_parser = argparse.ArgumentParser(add_help=False)
        runner_parser.add_argument("_run")
        runner_parser.add_argument("--notebook", required=True)
        runner_parser.add_argument("--no-push", action="store_true")
        runner_args = runner_parser.parse_args()
        return run_notebook(
            runner_args.notebook,
            auto_push=not runner_args.no_push,
            update_state=True,
        )

    args = build_parser().parse_args()
    if args.command == "start":
        return start(args.notebook, auto_push=not args.no_push)
    if args.command == "stop":
        return stop(args.timeout)
    if args.command == "status":
        return status(args.json)
    if args.command == "run":
        return run_notebook(args.notebook, auto_push=args.push, update_state=False)
    if args.command == "publish":
        try:
            publish_measurement_data()
        except Exception as exc:
            print(f"Daten-Push fehlgeschlagen: {exc}", file=sys.stderr)
            return 1
        return 0
    return 2


if __name__ == "__main__":
    project_venv = ROOT / ".venv"
    project_python = project_venv / "bin" / "python3"
    if project_python.is_file() and Path(sys.prefix).resolve() != project_venv.resolve():
        os.execv(str(project_python), [str(project_python), *sys.argv])
    raise SystemExit(main())
