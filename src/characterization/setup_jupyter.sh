#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
KERNEL_NAME="${KERNEL_NAME:-plant-ae}"
KERNEL_DISPLAY_NAME="${KERNEL_DISPLAY_NAME:-Plant AE (Projekt I1)}"

"$PYTHON_BIN" -m venv .venv
. .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -e ".[notebooks,extra]"
python -m ipykernel install --user --name "$KERNEL_NAME" --display-name "$KERNEL_DISPLAY_NAME"

cat <<MSG

Jupyter-Umgebung ist bereit.

Start:
  cd $ROOT
  .venv/bin/jupyter lab notebooks/00_control_panel.ipynb

Kernel:
  $KERNEL_DISPLAY_NAME ($KERNEL_NAME)

Hinweis:
  Home Assistant ist portabel standardmaessig aus. Auf der Mess-Workstation
  im Control Panel aktivieren oder PLANT_AE_HOMEASSISTANT_ENABLED=1 setzen.
  Dann HA_URL, HA_TOKEN und ggf. HOMEASSISTANT_SYNC_DIR oder
  HOMEASSISTANT_SYNC_ENV_FILE setzen.
MSG
