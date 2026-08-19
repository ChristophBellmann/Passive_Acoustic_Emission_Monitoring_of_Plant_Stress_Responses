#!/usr/bin/env bash
# analyze_overnight.sh  –  Analyse der Pflanzendaten des aktuellen continuous-Runs.
#
# Führt folgende Schritte durch:
#   1. Frequenzanalyse auf den neuesten Raw-Daten (falls vorhanden).
#   2. Aggregierung der PSD-Snapshots des aktuellsten continuous-Runs.
#
# HINWEIS: Dieses Skript analysiert *vorhandene* Daten.  Neue Daten werden
# nur durch den laufenden Daemon gesammelt (run_continuous.sh).  Beide müssen
# separat gestartet werden:
#   - Datenerhebung:  tmux new -s plant_ae 'bash run_continuous.sh'
#   - Tagesanalyse:   einmalig oder per cron  'bash analyze_overnight.sh'
#
# Empfohlener Cron-Eintrag (07:30 täglich):
#   30 7 * * *  cd /pfad/zu/src/characterization && bash analyze_overnight.sh >> \
#               data/continuous_plant_ae_20260622/logs/cron.log 2>&1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$SCRIPT_DIR/.venv/bin/python3"
ANALYSIS="$SCRIPT_DIR/frequency_analysis.py"
DATA_ROOT="$SCRIPT_DIR/data"
REPORT_DIR="$DATA_ROOT/reports/frequency_analysis"

echo "=== Pflanzen-AE Tagesanalyse  $(date -Iseconds) ==="
echo ""

# --- Schritt 1: Frequenzanalyse auf den neuesten Raw-Daten ---
# Suche das aktuellste experiment_*-Rohdaten-Verzeichnis mit gültigen Captures
RAW_DIR=""
for candidate in \
    "$DATA_ROOT/plant_ae_optimized/20260621_200339/raw" \
    "$DATA_ROOT/watering_experiment/"*/raw; do
    if [[ -d "$candidate" ]] && ls "$candidate"/*_capture_ch1.npz &>/dev/null 2>&1; then
        RAW_DIR="$candidate"
    fi
done

if [[ -n "$RAW_DIR" ]]; then
    echo "[1/2] Frequenzanalyse auf: $RAW_DIR"
    "$PYTHON" "$ANALYSIS" --data-dir "$RAW_DIR" --out-dir "$REPORT_DIR"
    echo "  → Report: $REPORT_DIR"
else
    echo "[1/2] Keine Raw-Daten gefunden — Schritt übersprungen."
fi

# --- Schritt 2: Zusammenfassung der PSD-Snapshots des aktuellsten Runs ---
CONTINUOUS_ROOT="$DATA_ROOT/continuous_plant_ae_20260622"
if [[ -d "$CONTINUOUS_ROOT" ]]; then
    # Neuestes Run-Verzeichnis (YYYYMMDD_HHMMSS format)
    LATEST_RUN=$(ls -1dt "$CONTINUOUS_ROOT"/2026*/ 2>/dev/null | head -1 || true)
    if [[ -n "$LATEST_RUN" ]] && [[ -d "${LATEST_RUN}psd_snapshots" ]]; then
        SNAP_DIR="${LATEST_RUN}psd_snapshots"
        N_SNAPS=$(ls "$SNAP_DIR"/*.npz 2>/dev/null | wc -l)
        echo "[2/2] Continuous-Run: $LATEST_RUN"
        echo "       PSD-Snapshots: $N_SNAPS"
        if [[ "$N_SNAPS" -gt 0 ]]; then
            "$PYTHON" - "$SNAP_DIR" <<'PYEOF'
import sys
from pathlib import Path
import numpy as np

snap_dir = Path(sys.argv[1])
snaps = sorted(snap_dir.glob("*.npz"))
if not snaps:
    print("  Keine Snapshots.")
    sys.exit(0)

print(f"  {len(snaps)} Snapshots, neuester: {snaps[-1].name}")

# Track peak frequency across snapshots
peak_freqs = []
band_energies = []
for snap in snaps:
    d = np.load(snap)
    freqs = d["frequencies"]
    psd = d["mean_psd"]
    mask = (freqs >= 500) & (freqs <= 100_000)
    if mask.any():
        peak_freqs.append(float(freqs[mask][np.argmax(psd[mask])]))
    band_energies.append(d["band_energy"])

if peak_freqs:
    arr = np.array(peak_freqs)
    print(f"  Dominierende Spitzenfrequenz:")
    print(f"    Median  : {np.median(arr)/1e3:.2f} kHz")
    print(f"    Bereich : {arr.min()/1e3:.2f}–{arr.max()/1e3:.2f} kHz")
    print(f"    Stabilität (IQR): {(np.percentile(arr,75)-np.percentile(arr,25))/1e3:.2f} kHz")
PYEOF
        fi
    else
        echo "[2/2] Kein aktueller continuous-Run mit psd_snapshots/ gefunden."
        echo "      Daemon noch nicht gestartet? → bash run_continuous.sh"
    fi
else
    echo "[2/2] Kein continuous-Experiment-Verzeichnis vorhanden."
    echo "      Daemon noch nicht gestartet? → bash run_continuous.sh"
fi

echo ""
echo "=== Analyse abgeschlossen: $(date -Iseconds) ==="

# --- Schritt 3: Neue Daten und Analyseergebnisse in Git einchecken ---
GIT_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || true)"
if [[ -n "$GIT_ROOT" ]]; then
    echo ""
    echo "[3/3] Einchecken neuer Daten via Git (LFS für .npz)..."
    cd "$GIT_ROOT"

    # Analysereports (kleine Dateien, reguläres Git)
    git add \
        "src/characterization/data/reports/" \
        2>/dev/null || true

    # Kompakte PSD-Snapshots (LFS-tracked .npz, ≈50-100 kB)
    if [[ -n "$LATEST_RUN" ]] && [[ -d "${LATEST_RUN}psd_snapshots" ]]; then
        git add "${LATEST_RUN}psd_snapshots/" 2>/dev/null || true
    fi

    # Peak-Tracks und Summary-Plots des continuous-Runs
    if [[ -n "$LATEST_RUN" ]]; then
        git add "${LATEST_RUN}peak_tracks.csv" \
                "${LATEST_RUN}continuous_summary.png" \
                "${LATEST_RUN}manifest.json" 2>/dev/null || true
    fi

    # Long-Capture-Daten (LFS-tracked, falls vorhanden)
    LONG_CAP_DIR="$DATA_ROOT/long_captures"
    if [[ -d "$LONG_CAP_DIR" ]]; then
        git add "$LONG_CAP_DIR/" 2>/dev/null || true
    fi

    if git diff --cached --quiet; then
        echo "  → Keine neuen Daten zum Einchecken."
    else
        DATE_STR=$(date +%Y-%m-%d)
        git commit -m "Automatisches Tagesupdate $DATE_STR: Messungen + Analyse"
        git push origin main
        echo "  → Commit und Push erfolgreich."
    fi
else
    echo "[3/3] Kein Git-Repository — Einchecken übersprungen."
fi

echo ""
echo "Nächste Schritte:"
echo "  Neue Daten erheben  : tmux new -s plant_ae 'bash src/characterization/run_continuous.sh'"
echo "  Report ansehen      : $REPORT_DIR/frequency_characterization_report.md"
