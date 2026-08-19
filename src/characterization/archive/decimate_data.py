#!/usr/bin/env python3
"""
Dezimiert Oszilloskop-Daten von 1 GSa/s auf 500 kHz.

Verwendet scipy.signal.decimate für qualitativ hochwertige Dezimierung
mit Anti-Aliasing-Filter.
"""

import sys
from pathlib import Path
import numpy as np
from scipy import signal
import json

def _chain_decimate(voltage: np.ndarray, total_factor: int) -> np.ndarray:
    """
    Decimate by *total_factor* using a chain of steps ≤ 10.

    scipy.signal.decimate uses an IIR or FIR filter whose order grows with q.
    For q > ~13 the filter becomes numerically unstable; chaining keeps each
    step well-conditioned.

    Strategy: factorise total_factor into steps of at most 10.
    Example: 50 → 10 × 5, 100 → 10 × 10, 25 → 5 × 5.
    """
    remaining = total_factor
    result = voltage.astype(np.float64)
    MAX_STEP = 10
    while remaining > 1:
        # Find the largest factor of remaining that is ≤ MAX_STEP
        step = MAX_STEP
        while step > 1 and remaining % step != 0:
            step -= 1
        if step == 1:
            # Not evenly divisible — use MAX_STEP anyway and accept ~0.01 % error
            step = min(remaining, MAX_STEP)
        result = signal.decimate(result, step, ftype="fir", zero_phase=True)
        remaining //= step
    return result.astype(np.float32)


def _load_voltage_and_rate(data: np.lib.npyio.NpzFile) -> tuple[np.ndarray, float]:
    """
    Load voltage array and sample rate from a capture NPZ.

    Supports both key conventions used across the project:
      - ``voltage`` / ``sample_rate``           (new long-capture format)
      - ``voltage_vector`` / ``metadata``        (notebook-03 capture format)
      - ``time_vector`` + ``voltage_vector``     (old format; rate from time axis)
    """
    keys = set(data.keys())

    if "voltage" in keys and "sample_rate" in keys:
        return np.asarray(data["voltage"], dtype=float), float(data["sample_rate"])

    if "voltage_vector" in keys:
        voltage = np.asarray(data["voltage_vector"], dtype=float)
        if "metadata" in keys:
            meta = data["metadata"].item()
            rate = float(meta.get("sample_rate_sa_per_s", 0))
            if rate > 0:
                return voltage, rate
        if "time_vector" in keys:
            t = np.asarray(data["time_vector"], dtype=float)
            if len(t) >= 2 and len(voltage) >= 2:
                # The time_vector spans the full acquisition window;
                # derive rate from the ratio of points to total duration.
                rate = len(voltage) / (t[-1] - t[0])
                return voltage, rate

    raise KeyError(
        f"Cannot determine voltage/sample-rate from keys: {sorted(keys)}"
    )


def decimate_data(input_dir: Path, output_dir: Path, target_rate: float = 500e3):
    """
    Dezimiert alle .npz Dateien im input_dir auf target_rate.

    Unterstützt alle NPZ-Formate des Projekts (alte und neue Key-Namen).
    Speichert dezimierte Daten als komprimiertes float32 NPZ.

    Args:
        input_dir: Verzeichnis mit Rohdaten (.npz Dateien)
        output_dir: Verzeichnis für dezimierte Daten
        target_rate: Ziel-Sample-Rate in Hz (default: 500 kHz)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    npz_files = sorted(input_dir.glob("*.npz"))

    if not npz_files:
        print(f"Keine .npz Dateien gefunden in {input_dir}")
        return

    print(f"Gefunden: {len(npz_files)} Dateien")
    print(f"Ziel-Sample-Rate: {target_rate/1e3:.1f} kHz")
    print(f"Ausgabe: {output_dir}\n")

    for i, npz_file in enumerate(npz_files, 1):
        data = np.load(npz_file, allow_pickle=True)

        try:
            voltage_data, orig_rate = _load_voltage_and_rate(data)
        except (KeyError, Exception) as exc:
            print(f"[{i}/{len(npz_files)}] {npz_file.name}: Überspringe ({exc})")
            continue

        if len(voltage_data) < 10:
            print(f"[{i}/{len(npz_files)}] {npz_file.name}: Überspringe (leer / zu kurz)")
            continue

        decimation_factor = int(orig_rate / target_rate)

        if decimation_factor < 2:
            print(f"[{i}/{len(npz_files)}] {npz_file.name}: "
                  f"Überspringe (Faktor {decimation_factor}, bereits ≤ Zielrate)")
            continue

        # Anti-alias FIR filter + decimate.
        # scipy.signal.decimate is unstable for large q (> ~13).
        # Chain into factors ≤ 10 to keep the FIR filter well-conditioned.
        voltage_decimated = _chain_decimate(voltage_data, decimation_factor)

        dt_new = 1.0 / (orig_rate / decimation_factor)
        actual_new_rate = np.float32(1.0 / dt_new)

        output_file = output_dir / f"decimated_{npz_file.name}"
        np.savez_compressed(
            output_file,
            voltage=voltage_decimated,
            sample_rate=actual_new_rate,
            original_sample_rate=np.float32(orig_rate),
            decimation_factor=np.int32(decimation_factor),
        )
        
        reduction = len(voltage_data) / len(voltage_decimated)
        duration_ms = len(voltage_decimated) * float(dt_new) * 1e3

        print(f"[{i}/{len(npz_files)}] {npz_file.name}:")
        print(f"  Original  : {orig_rate/1e6:.3f} MSa/s, {len(voltage_data):,} pts, "
              f"{len(voltage_data)/orig_rate*1e3:.1f} ms")
        print(f"  Dezimiert : {float(actual_new_rate)/1e3:.1f} kHz, "
              f"{len(voltage_decimated):,} pts, {duration_ms:.1f} ms")
        print(f"  Reduktion : {reduction:.1f}×  →  {output_file.name}")
        print()
    
    print(f"Fertig! Dezimierte Daten gespeichert in: {output_dir}")


def main():
    """Hauptfunktion mit Kommandozeilen-Argumenten."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Dezimiert Oszilloskop-Daten von 1 GSa/s auf 500 kHz"
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Verzeichnis mit Rohdaten (.npz Dateien)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Ausgabeverzeichnis (default: input_dir/decimated_500kHz)"
    )
    parser.add_argument(
        "-r", "--rate",
        type=float,
        default=500e3,
        help="Ziel-Sample-Rate in Hz (default: 500000)"
    )
    
    args = parser.parse_args()
    
    # Setze Ausgabeverzeichnis
    if args.output is None:
        output_dir = args.input_dir / f"decimated_{args.rate/1e3:.0f}kHz"
    else:
        output_dir = args.output
    
    # Prüfe Eingabeverzeichnis
    if not args.input_dir.exists():
        print(f"Fehler: Eingabeverzeichnis existiert nicht: {args.input_dir}")
        sys.exit(1)
    
    # Führe Dezimierung durch
    decimate_data(args.input_dir, output_dir, args.rate)


if __name__ == "__main__":
    main()
