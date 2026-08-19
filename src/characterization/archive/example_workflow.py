#!/usr/bin/env python3
"""
Beispiel-Workflow: Komplette Pflanzen-AE-Messung mit Dezimierung

Dieses Skript demonstriert den vollständigen Workflow:
1. Messung mit optimalen Einstellungen (100µs/div, 1 GSa/s)
2. Dezimierung auf 500 kHz
3. Analyse und Visualisierung
"""

import sys
from pathlib import Path
import subprocess
from datetime import datetime

def run_workflow():
    """Führt den kompletten Workflow aus."""
    
    print("=" * 80)
    print("KOMPLETTER WORKFLOW: Pflanzen-AE-Messung mit Dezimierung")
    print("=" * 80)
    print()
    
    # Erstelle Zeitstempel für Verzeichnisnamen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_dir = Path("data") / f"plant_ae_{timestamp}"
    
    print(f"Schritt 1: Messung durchführen")
    print(f"  Verzeichnis: {base_dir}")
    print(f"  Einstellungen: 100µs/div, 1 GSa/s, 1.2ms Aufnahmezeit")
    print()
    
    # Führe Messung durch
    try:
        result = subprocess.run(
            ["python", "plant_ae_3ch_measurement.py"],
            cwd=Path(__file__).parent,
            check=True
        )
        print("  ✓ Messung abgeschlossen")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Fehler bei Messung: {e}")
        return
    
    print()
    print(f"Schritt 2: Daten dezimieren")
    print(f"  Von: 1 GSa/s → 500 kHz")
    print(f"  Faktor: 2000×")
    print(f"  Ergebnis: 1.2M Punkte → 600 Punkte")
    print()
    
    # Finde das neueste Messverzeichnis
    data_dirs = sorted(Path("data").glob("plant_ae_*"))
    if not data_dirs:
        print("  ✗ Keine Messdaten gefunden")
        return
    
    latest_dir = data_dirs[-1]
    
    # Führe Dezimierung durch
    try:
        result = subprocess.run(
            ["python", "decimate_data.py", str(latest_dir)],
            cwd=Path(__file__).parent,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("  ✓ Dezimierung abgeschlossen")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Fehler bei Dezimierung: {e}")
        print(e.stdout)
        print(e.stderr)
        return
    
    print()
    print(f"Schritt 3: Daten analysieren")
    print(f"  FFT-Analyse")
    print(f"  Peak-Detection")
    print(f"  Visualisierung")
    print()
    
    # Finde dezimiertes Verzeichnis
    decimated_dirs = sorted(latest_dir.glob("decimated_*"))
    if not decimated_dirs:
        print("  ✗ Keine dezimierten Daten gefunden")
        return
    
    decimated_dir = decimated_dirs[-1]
    
    # Führe Analyse durch
    try:
        result = subprocess.run(
            ["python", "analyze_decimated.py", str(decimated_dir)],
            cwd=Path(__file__).parent,
            check=True,
            capture_output=True,
            text=True
        )
        print(result.stdout)
        print("  ✓ Analyse abgeschlossen")
    except subprocess.CalledProcessError as e:
        print(f"  ✗ Fehler bei Analyse: {e}")
        print(e.stdout)
        print(e.stderr)
        return
    
    print()
    print("=" * 80)
    print("WORKFLOW ABGESCHLOSSEN")
    print("=" * 80)
    print()
    print("Ergebnisse:")
    print(f"  Rohdaten: {latest_dir}/")
    print(f"  Dezimierte Daten: {decimated_dir}/")
    print(f"  Analyse-Plot: {decimated_dir}/analysis.png")
    print()
    print("Nächste Schritte:")
    print(f"  1. Öffne {decimated_dir}/analysis.png")
    print(f"  2. Untersuche die Frequenzspektren")
    print(f"  3. Identifiziere dominante Frequenzen")
    print(f"  4. Vergleiche mit Referenzmessungen")
    print()


def main():
    """Hauptfunktion."""
    try:
        run_workflow()
    except KeyboardInterrupt:
        print("\n\nWorkflow abgebrochen.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
