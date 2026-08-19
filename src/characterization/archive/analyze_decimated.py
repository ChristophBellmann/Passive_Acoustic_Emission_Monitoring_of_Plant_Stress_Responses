#!/usr/bin/env python3
"""
Analysiert und visualisiert dezimierte Oszilloskop-Daten.

Erstellt:
- Zeitbereichs-Plots
- Frequenzspektren (FFT)
- Vergleich Original vs. Dezimiert
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

def analyze_decimated_data(data_dir: Path, output_file: Path = None):
    """
    Analysiert dezimierte Daten und erstellt Visualisierungen.
    
    Args:
        data_dir: Verzeichnis mit dezimierten Daten (.npz Dateien)
        output_file: Ausgabedatei für Plot (default: data_dir/analysis.png)
    """
    # Finde dezimierte Dateien
    npz_files = sorted(data_dir.glob("decimated_*.npz"))
    
    if not npz_files:
        print(f"Keine dezimierten Dateien gefunden in {data_dir}")
        return
    
    print(f"Analysiere {len(npz_files)} dezimierte Dateien...\n")
    
    # Erstelle Figure mit Subplots
    fig = plt.figure(figsize=(14, 10))
    
    # Lade erste Datei für detaillierte Analyse
    first_file = npz_files[0]
    data = np.load(first_file)
    
    time_data = data['time']
    voltage_data = data['voltage']
    sample_rate = data['sample_rate']
    orig_rate = data['original_sample_rate']
    dec_factor = data['decimation_factor']
    
    # Berechne Statistiken
    duration = len(time_data) * (time_data[1] - time_data[0])
    
    print(f"Datei: {first_file.name}")
    print(f"  Sample-Rate: {sample_rate/1e3:.1f} kHz")
    print(f"  Original: {orig_rate/1e6:.1f} MSa/s")
    print(f"  Dezimationsfaktor: {dec_factor}")
    print(f"  Punkte: {len(voltage_data)}")
    print(f"  Dauer: {duration*1e3:.2f} ms")
    print(f"  Nyquist: {sample_rate/2/1e3:.1f} kHz")
    print()
    
    # Plot 1: Zeitbereich (gesamte Aufnahme)
    ax1 = plt.subplot(3, 2, 1)
    ax1.plot(time_data * 1e3, voltage_data * 1e3, linewidth=0.5)
    ax1.set_xlabel('Zeit (ms)')
    ax1.set_ylabel('Spannung (mV)')
    ax1.set_title('Zeitbereich - Gesamte Aufnahme')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Zeitbereich (Zoom auf 1ms)
    ax2 = plt.subplot(3, 2, 2)
    zoom_duration = min(1e-3, duration)  # Max 1ms
    zoom_samples = int(zoom_duration * sample_rate)
    ax2.plot(time_data[:zoom_samples] * 1e3, voltage_data[:zoom_samples] * 1e3, 
             linewidth=1, color='red')
    ax2.set_xlabel('Zeit (ms)')
    ax2.set_ylabel('Spannung (mV)')
    ax2.set_title(f'Zeitbereich - Zoom ({zoom_duration*1e3:.2f} ms)')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: FFT Spektrum (linear)
    ax3 = plt.subplot(3, 2, 3)
    fft_data = np.fft.fft(voltage_data)
    fft_freqs = np.fft.fftfreq(len(voltage_data), 1/sample_rate)
    
    # Nur positive Frequenzen
    positive_mask = fft_freqs >= 0
    fft_freqs_pos = fft_freqs[positive_mask]
    fft_magnitude = np.abs(fft_data[positive_mask]) / len(voltage_data)
    
    # Begrenze auf sinnvollen Bereich (0-100 kHz)
    freq_mask = fft_freqs_pos <= 100e3
    ax3.plot(fft_freqs_pos[freq_mask] / 1e3, fft_magnitude[freq_mask] * 1e3, 
             linewidth=0.5)
    ax3.set_xlabel('Frequenz (kHz)')
    ax3.set_ylabel('Amplitude (mV)')
    ax3.set_title('FFT Spektrum (linear)')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim([0, 100])
    
    # Plot 4: FFT Spektrum (dB)
    ax4 = plt.subplot(3, 2, 4)
    fft_db = 20 * np.log10(fft_magnitude + 1e-12)  # +1e-12 um log(0) zu vermeiden
    ax4.plot(fft_freqs_pos[freq_mask] / 1e3, fft_db[freq_mask], 
             linewidth=0.5, color='green')
    ax4.set_xlabel('Frequenz (kHz)')
    ax4.set_ylabel('Amplitude (dB)')
    ax4.set_title('FFT Spektrum (dB)')
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim([0, 100])
    
    # Plot 5: Peak Detection
    ax5 = plt.subplot(3, 2, 5)
    # Finde Peaks im Frequenzspektrum
    peaks, properties = signal.find_peaks(fft_magnitude[freq_mask], 
                                          height=np.max(fft_magnitude[freq_mask])*0.1,
                                          distance=10)
    
    ax5.plot(fft_freqs_pos[freq_mask] / 1e3, fft_magnitude[freq_mask] * 1e3, 
             linewidth=0.5, label='FFT')
    ax5.plot(fft_freqs_pos[freq_mask][peaks] / 1e3, 
             fft_magnitude[freq_mask][peaks] * 1e3, 
             'ro', markersize=5, label=f'Peaks ({len(peaks)})')
    ax5.set_xlabel('Frequenz (kHz)')
    ax5.set_ylabel('Amplitude (mV)')
    ax5.set_title('Peak Detection')
    ax5.legend()
    ax5.grid(True, alpha=0.3)
    ax5.set_xlim([0, 100])
    
    # Plot 6: Statistik-Tabelle
    ax6 = plt.subplot(3, 2, 6)
    ax6.axis('off')
    
    # Berechne Statistiken
    v_max = np.max(voltage_data) * 1e3
    v_min = np.min(voltage_data) * 1e3
    v_pp = v_max - v_min
    v_rms = np.sqrt(np.mean(voltage_data**2)) * 1e3
    
    # Finde dominante Frequenz
    if len(peaks) > 0:
        dominant_freq = fft_freqs_pos[freq_mask][peaks[0]] / 1e3
        dominant_amp = fft_magnitude[freq_mask][peaks[0]] * 1e3
    else:
        dominant_freq = 0
        dominant_amp = 0
    
    table_data = [
        ['Parameter', 'Wert'],
        ['Sample-Rate', f'{sample_rate/1e3:.1f} kHz'],
        ['Aufnahmezeit', f'{duration*1e3:.2f} ms'],
        ['Nyquist-Frequenz', f'{sample_rate/2/1e3:.1f} kHz'],
        ['Max. Spannung', f'{v_max:.2f} mV'],
        ['Min. Spannung', f'{v_min:.2f} mV'],
        ['Peak-to-Peak', f'{v_pp:.2f} mV'],
        ['RMS', f'{v_rms:.2f} mV'],
        ['Dom. Frequenz', f'{dominant_freq:.2f} kHz'],
        ['Dom. Amplitude', f'{dominant_amp:.2f} mV'],
    ]
    
    table = ax6.table(cellText=table_data, cellLoc='left', loc='center',
                      colWidths=[0.4, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    
    # Header-Stil
    for i in range(2):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax6.set_title('Zusammenfassung', pad=20)
    
    plt.tight_layout()
    
    # Speichere Plot
    if output_file is None:
        output_file = data_dir / "analysis.png"
    
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    print(f"Analyse-Plot gespeichert: {output_file}")
    
    # Zeige Statistiken
    print("\nStatistiken:")
    print(f"  Max. Spannung: {v_max:.2f} mV")
    print(f"  Min. Spannung: {v_min:.2f} mV")
    print(f"  Peak-to-Peak: {v_pp:.2f} mV")
    print(f"  RMS: {v_rms:.2f} mV")
    print(f"  Dominante Frequenz: {dominant_freq:.2f} kHz")
    print(f"  Dominante Amplitude: {dominant_amp:.2f} mV")


def main():
    """Hauptfunktion mit Kommandozeilen-Argumenten."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Analysiert und visualisiert dezimierte Oszilloskop-Daten"
    )
    parser.add_argument(
        "data_dir",
        type=Path,
        help="Verzeichnis mit dezimierten Daten (.npz Dateien)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Ausgabedatei für Plot (default: data_dir/analysis.png)"
    )
    
    args = parser.parse_args()
    
    # Prüfe Verzeichnis
    if not args.data_dir.exists():
        print(f"Fehler: Verzeichnis existiert nicht: {args.data_dir}")
        sys.exit(1)
    
    # Führe Analyse durch
    analyze_decimated_data(args.data_dir, args.output)


if __name__ == "__main__":
    main()
