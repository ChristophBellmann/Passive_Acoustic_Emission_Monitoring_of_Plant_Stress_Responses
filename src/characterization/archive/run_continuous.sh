#!/usr/bin/env bash
# run_continuous.sh  –  Start (or restart) the continuous plant AE characterization.
#
# Usage:
#   ./run_continuous.sh                        # run indefinitely
#   ./run_continuous.sh --duration-hours 24    # stop after 24 h
#   ./run_continuous.sh --enable-watering      # also water once after baseline
#
# The script:
#   1. Activates the venv.
#   2. Launches continuous_characterization.py in the foreground (so Ctrl+C stops it).
#   3. On SIGTERM / SIGINT, the Python process writes summary, peak_tracks.csv
#      and manifest before exiting (built-in finaliser).
#
# For unattended background execution (tmux / screen recommended):
#   tmux new-session -d -s plant_ae \
#       './run_continuous.sh --duration-hours 72 2>&1 | tee logs/continuous.log'
#
# Systemd one-shot (copy to /etc/systemd/system/plant_ae.service and adjust paths):
#   [Unit]
#   Description=Plant acoustic emission continuous characterization
#   After=network.target
#
#   [Service]
#   Type=simple
#   WorkingDirectory=/path/to/projekt_i1/src/characterization
#   ExecStart=/path/to/projekt_i1/src/characterization/run_continuous.sh
#   Restart=on-failure
#   RestartSec=30
#
#   [Install]
#   WantedBy=multi-user.target

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PYTHON="$VENV/bin/python3"
EXPERIMENT="$SCRIPT_DIR/experiment_continuous_plant_ae_20260622/continuous_characterization.py"
LOG_DIR="$SCRIPT_DIR/data/continuous_plant_ae_20260622/logs"

if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: virtual environment not found at $VENV" >&2
    echo "       Run: python3 -m venv .venv && .venv/bin/pip install -e ." >&2
    exit 1
fi

mkdir -p "$LOG_DIR"
LOGFILE="$LOG_DIR/run_$(date +%Y%m%d_%H%M%S).log"

GIT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"

# On exit: commit and push any new PSD snapshots + summary files.
_git_push_on_exit() {
    if [[ -z "$GIT_ROOT" ]]; then return; fi
    echo ""
    echo "Einchecken neuer Daten nach Messende..."
    cd "$GIT_ROOT"
    # Compact snapshots (LFS), summary plots, manifest
    git add \
        "src/characterization/data/continuous_plant_ae_20260622/" \
        "src/characterization/data/long_captures/" \
        "src/characterization/data/reports/" \
        2>/dev/null || true
    if ! git diff --cached --quiet; then
        git commit -m "Messungs-Snapshot $(date +%Y-%m-%dT%H:%M)"
        git push origin main && echo "  → Gepusht." || echo "  → Push fehlgeschlagen (später: git push)."
    else
        echo "  → Keine neuen Daten."
    fi
}
trap _git_push_on_exit EXIT

echo "Starting continuous plant AE characterization"
echo "  Experiment : $EXPERIMENT"
echo "  Log        : $LOGFILE"
echo "  Args       : $*"
echo "  Time       : $(date -Iseconds)"
echo ""

# Run with all arguments passed through; tee to file and stdout.
# (No exec — the EXIT trap must run after the Python process finishes.)
"$PYTHON" "$EXPERIMENT" "$@" 2>&1 | tee "$LOGFILE"
