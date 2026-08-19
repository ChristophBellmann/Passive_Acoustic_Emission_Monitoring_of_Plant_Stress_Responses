#!/usr/bin/env python3
"""
Testet welche Sample-Rates vom Rigol DS1104Z unterstützt werden.
Findet die Rate, die 1 MSa/s am nächsten kommt.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "instrument_control"))

from scope.config import load_config
from scope.instrument import InstrumentConnection

def test_sample_rates():
    config = load_config('experiment_plant_acoustic_emissions_20260621/config.yaml')

    print("=" * 70)
    print("TEST: Unterstützte Sample-Rates vom Rigol DS1104Z")
    print("=" * 70)

    # Zu testende Sample-Rates (in Sa/s)
    target_rates = [
        100e3,    # 100 kSa/s
        250e3,    # 250 kSa/s
        500e3,    # 500 kSa/s
        1e6,      # 1 MSa/s (Ziel)
        2e6,      # 2 MSa/s
        5e6,      # 5 MSa/s
        10e6,     # 10 MSa/s
        25e6,     # 25 MSa/s
        50e6,     # 50 MSa/s
        100e6,    # 100 MSa/s
        250e6,    # 250 MSa/s
        500e6,    # 500 MSa/s
        1e9,      # 1 GSa/s
    ]

    supported_rates = []

    with InstrumentConnection(config) as conn:
        print("\nTeste Sample-Rates...\n")

        for target_rate in target_rates:
            # Setze Sample-Rate
            conn.write(f":ACQ:SRAT {target_rate}")
            time.sleep(0.1)

            # Lese tatsächliche Rate
            actual_rate = float(conn.query(":ACQ:SRAT?"))

            # Prüfe ob Rate unterstützt wurde
            is_supported = abs(actual_rate - target_rate) < (target_rate * 0.01)

            if is_supported:
                status = "✓ unterstützt"
                supported_rates.append(actual_rate)
            else:
                status = f"✗ nicht unterstützt (tatsächlich: {actual_rate/1e6:.2f} MSa/s)"

            print(f"  {target_rate/1e6:>10.2f} MSa/s → {status}")

    print("\n" + "=" * 70)
    print("ZUSAMMENFASSUNG")
    print("=" * 70)

    if supported_rates:
        print(f"\nUnterstützte Sample-Rates ({len(supported_rates)}):")
        for rate in supported_rates:
            print(f"  - {rate/1e6:.2f} MSa/s")

        # Finde Rate am nächsten an 1 MSa/s
        target = 1e6
        closest_rate = min(supported_rates, key=lambda x: abs(x - target))

        print(f"\nRate am nächsten an 1 MSa/s:")
        print(f"  → {closest_rate/1e6:.2f} MSa/s")
        print(f"  → Aufnahmezeit bei 100k Samples: {100000/closest_rate*1000:.2f} ms")
        print(f"  → Nyquist-Frequenz: {closest_rate/2/1000:.1f} kHz")
    else:
        print("\nKeine der getesteten Raten wird unterstützt!")

if __name__ == "__main__":
    test_sample_rates()
