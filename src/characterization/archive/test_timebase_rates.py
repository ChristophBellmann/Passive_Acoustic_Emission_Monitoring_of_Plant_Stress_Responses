#!/usr/bin/env python3
"""
Testet welche Sample-Rates bei verschiedenen Zeitbasen vom Rigol DS1104Z verwendet werden.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "instrument_control"))

from scope.config import load_config
from scope.instrument import InstrumentConnection

def test_timebase_sample_rates():
    config = load_config('experiment_plant_acoustic_emissions_20260621/config.yaml')

    print("=" * 70)
    print("TEST: Sample-Rates bei verschiedenen Zeitbasen")
    print("=" * 70)

    # Zu testende Zeitbasen (in Sekunden/Division)
    timebases = [
        1e-6,     # 1 µs/div
        2e-6,     # 2 µs/div
        5e-6,     # 5 µs/div
        10e-6,    # 10 µs/div
        20e-6,    # 20 µs/div
        50e-6,    # 50 µs/div
        100e-6,   # 100 µs/div
        200e-6,   # 200 µs/div
        500e-6,   # 500 µs/div
        1e-3,     # 1 ms/div
        2e-3,     # 2 ms/div
        5e-3,     # 5 ms/div
        10e-3,    # 10 ms/div
        20e-3,    # 20 ms/div
        50e-3,    # 50 ms/div
        100e-3,   # 100 ms/div
        200e-3,   # 200 ms/div
        500e-3,   # 500 ms/div
        1.0,      # 1 s/div
    ]

    results = []

    with InstrumentConnection(config) as conn:
        print("\nTeste Zeitbasen...\n")
        print(f"{'Zeitbasis':>15} {'Sample-Rate':>15} {'Aufnahme (100k)':>20} {'Nyquist':>15}")
        print("-" * 70)

        for timebase in timebases:
            # Setze Zeitbasis
            conn.write(f":TIM:SCAL {timebase}")
            time.sleep(0.2)

            # Lese tatsächliche Sample-Rate
            actual_rate = float(conn.query(":ACQ:SRAT?"))

            # Berechne Aufnahmezeit und Nyquist
            record_length = 100000  # 100k Samples
            capture_time = record_length / actual_rate
            nyquist = actual_rate / 2

            # Formatiere Zeitbasis
            if timebase < 1e-3:
                tb_str = f"{timebase*1e6:.1f} µs/div"
            elif timebase < 1:
                tb_str = f"{timebase*1e3:.1f} ms/div"
            else:
                tb_str = f"{timebase:.1f} s/div"

            # Formatiere Sample-Rate
            if actual_rate >= 1e9:
                sr_str = f"{actual_rate/1e9:.2f} GSa/s"
            elif actual_rate >= 1e6:
                sr_str = f"{actual_rate/1e6:.2f} MSa/s"
            else:
                sr_str = f"{actual_rate/1e3:.2f} kSa/s"

            # Formatiere Aufnahmezeit
            if capture_time >= 1:
                ct_str = f"{capture_time:.2f} s"
            elif capture_time >= 1e-3:
                ct_str = f"{capture_time*1e3:.2f} ms"
            else:
                ct_str = f"{capture_time*1e6:.2f} µs"

            # Formatiere Nyquist
            if nyquist >= 1e9:
                nq_str = f"{nyquist/1e9:.2f} GHz"
            elif nyquist >= 1e6:
                nq_str = f"{nyquist/1e6:.2f} MHz"
            else:
                nq_str = f"{nyquist/1e3:.2f} kHz"

            print(f"{tb_str:>15} {sr_str:>15} {ct_str:>20} {nq_str:>15}")

            results.append({
                'timebase': timebase,
                'sample_rate': actual_rate,
                'capture_time': capture_time,
                'nyquist': nyquist
            })

    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)

    # Finde eindeutige Sample-Rates
    unique_rates = sorted(set(r['sample_rate'] for r in results))

    print(f"\nGefundene Sample-Rates ({len(unique_rates)}):")
    for rate in unique_rates:
        if rate >= 1e9:
            rate_str = f"{rate/1e9:.2f} GSa/s"
        elif rate >= 1e6:
            rate_str = f"{rate/1e6:.2f} MSa/s"
        else:
            rate_str = f"{rate/1e3:.2f} kSa/s"
        print(f"  - {rate_str}")

    # Finde Rate am nächsten an 1 MSa/s
    target = 1e6
    closest_rate = min(unique_rates, key=lambda x: abs(x - target))

    if closest_rate >= 1e9:
        cr_str = f"{closest_rate/1e9:.2f} GSa/s"
    elif closest_rate >= 1e6:
        cr_str = f"{closest_rate/1e6:.2f} MSa/s"
    else:
        cr_str = f"{closest_rate/1e3:.2f} kSa/s"

    print(f"\nRate am nächsten an 1 MSa/s:")
    print(f"  → {cr_str}")
    print(f"  → Aufnahmezeit bei 100k Samples: {100000/closest_rate*1000:.2f} ms")
    print(f"  → Nyquist-Frequenz: {closest_rate/2/1000:.1f} kHz")

    # Finde beste Rate für 100 ms Aufnahmezeit
    target_time = 0.1  # 100 ms
    best_rate = min(unique_rates, key=lambda x: abs(100000/x - target_time))

    if best_rate >= 1e9:
        br_str = f"{best_rate/1e9:.2f} GSa/s"
    elif best_rate >= 1e6:
        br_str = f"{best_rate/1e6:.2f} MSa/s"
    else:
        br_str = f"{best_rate/1e3:.2f} kSa/s"

    print(f"\nBeste Rate für ~100 ms Aufnahmezeit:")
    print(f"  → {br_str}")
    print(f"  → Aufnahmezeit bei 100k Samples: {100000/best_rate*1000:.2f} ms")
    print(f"  → Nyquist-Frequenz: {best_rate/2/1000:.1f} kHz")

if __name__ == "__main__":
    test_timebase_sample_rates()
