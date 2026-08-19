#!/usr/bin/env python3
"""
Verbesserte Pflanzen-AE-Messung mit optimierten Einstellungen.

Problem: Vorherige Messung hatte nur 4.8 µs Aufnahmezeit (zu kurz!)
Lösung: Sample-Rate reduzieren und Speichertiefe erhöhen

Ziel: 100 ms Aufnahmezeit bei 1 MSa/s = 100000 Punkte
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import numpy as np
import yaml
from rich.console import Console
from rich.progress import Progress

sys.path.insert(0, str(Path(__file__).resolve().parent / "instrument_control"))

from scope.config import ExperimentConfig, load_config, ChannelSetting
from scope.instrument import InstrumentConnection
from scope.acquisition import acquire_single_capture, save_capture_npz
from scope.preprocessing import preprocess
from scope.spectral import compute_fft, compute_welch, amplitude_to_db
from scipy.signal import find_peaks

console = Console()


def configure_optimized(conn: InstrumentConnection):
    """Konfiguriere Oszilloskop für lange Aufnahme."""
    console.print("\n[bold cyan]Optimierte Konfiguration für Pflanzen-AE...[/bold cyan]")
    
    conn.write(":STOP")
    time.sleep(0.5)
    
    # Kanäle
    console.print("  Kanäle:")
    conn.write(":CHAN1:COUP AC")
    conn.write(":CHAN1:PROB 10")
    conn.write(":CHAN1:SCAL 0.2")  # 200 mV/div für verstärktes Signal (verhindert Übersteuerung)
    conn.write(":CHAN1:DISP ON")
    
    conn.write(":CHAN2:COUP AC")
    conn.write(":CHAN2:PROB 1")
    conn.write(":CHAN2:SCAL 0.01")  # 10 mV/div
    conn.write(":CHAN2:DISP ON")
    
    conn.write(":CHAN3:COUP AC")
    conn.write(":CHAN3:PROB 1")
    conn.write(":CHAN3:SCAL 0.01")  # 10 mV/div
    conn.write(":CHAN3:DISP ON")
    console.print("    [green]✓[/green] CH1 (10:1, 200mV/div), CH2 (1:1, 10mV/div), CH3 (1:1, 10mV/div)")
    
    # Zeitbasis: 10 ms/div → 100 ms total bei 10 Div
    console.print("  Zeitbasis:")
    conn.write(":TIM:SCAL 0.01")  # 10 ms/div
    conn.write(":TIM:OFFS 0")
    console.print("    [green]✓[/green] 10 ms/div → ~100 ms Aufnahme")
    
    # Sample-Rate: 1 MSa/s für 100 kHz Nyquist
    console.print("  Akquisition:")
    conn.write(":ACQ:MDEP 100000")  # 100k Punkte
    conn.write(":ACQ:SRAT 1000000")  # 1 MSa/s
    console.print("    [green]✓[/green] 1 MSa/s, 100k Punkte → 100 ms")
    
    # Trigger
    conn.write(":TRIG:MODE AUTO")
    conn.write(":TRIG:EDGE:SOUR CHAN1")
    conn.write(":TRIG:EDGE:LEV 0.02")
    
    time.sleep(0.5)
    conn.write(":RUN")
    
    # Verifiziere Einstellungen
    srate = float(conn.query(":ACQ:SRAT?"))
    tscal = float(conn.query(":TIM:SCAL?"))
    
    # Memory Depth kann "AUTO" oder ein Zahlenwert sein
    mdep_str = conn.query(":ACQ:MDEP?")
    try:
        mdep = float(mdep_str)
        mdep_str_display = f"{int(mdep)} Punkte"
    except ValueError:
        mdep = 100000  # Default wenn AUTO
        mdep_str_display = "AUTO (~100k)"
    
    console.print(f"\n  [bold]Tatsächliche Einstellungen:[/bold]")
    console.print(f"    Sample-Rate: {srate/1e6:.2f} MSa/s")
    console.print(f"    Memory Depth: {mdep_str_display}")
    console.print(f"    Zeitbasis: {tscal*1000:.1f} ms/div")
    console.print(f"    Erwartete Dauer: {mdep/srate*1000:.1f} ms")
    
    console.print("\n[bold green]✓ Optimiert für Pflanzen-AE (20 Hz - 100 kHz)[/bold green]")


def acquire_long_capture(conn: InstrumentConnection, config: ExperimentConfig, n_captures: int = 20):
    """Führe längere Messungen durch."""
    console.print(f"\n[bold magenta]Führe {n_captures} Messungen durch (je ~100 ms)...[/bold magenta]")
    
    captures = []
    channels = [1, 2, 3]
    
    # Starte Oszilloskop und warte auf erste Daten
    conn.write(":RUN")
    time.sleep(0.5)
    
    with Progress() as progress:
        task = progress.add_task("Aufnahme...", total=n_captures * len(channels))
        
        for i in range(n_captures):
            # Lese Daten während das Oszilloskop läuft
            for ch in channels:
                try:
                    cap = acquire_single_capture(conn, ch, config, capture_id=i, stop_before=False, run_after=False)
                    captures.append(cap)
                except Exception as e:
                    console.print(f"  [yellow]Fehler CH{ch}: {e}[/yellow]")
                progress.update(task, advance=1)
            
            if i < n_captures - 1:
                # Warte bis neue Daten aufgezeichnet wurden
                time.sleep(0.3)
    
    console.print(f"\n[green]✓[/green] {len(captures)} Aufnahmen abgeschlossen\n")
    return captures


def analyze_detailed(captures, output_dir: Path):
    """Detaillierte Analyse mit Fokus auf akustischen Bereich."""
    console.print("[bold]Analysiere Daten...[/bold]")
    
    results = {}
    
    for ch in [1, 2, 3]:
        ch_captures = [c for c in captures if c.metadata.channel == ch]
        if not ch_captures:
            console.print(f"\n  === KANAL {ch} ===")
            console.print("    [yellow]Keine Daten vorhanden[/yellow]")
            continue
        
        console.print(f"\n  === KANAL {ch} ===")
        
        # Analysiere erste Aufnahme detailliert
        cap = ch_captures[0]
        time_vec = cap.time_vector
        voltage = cap.voltage_vector
        
        # Überprüfe ob Daten vorhanden sind
        if len(voltage) == 0:
            console.print("    [yellow]Keine Daten in dieser Aufnahme[/yellow]")
            continue
        
        sample_rate = 1.0 / cap.metadata.sample_interval_s
        
        print(f"    Sample-Rate: {sample_rate/1e3:.1f} kSa/s")
        print(f"    Punkte: {len(voltage)}")
        print(f"    Dauer: {len(voltage)/sample_rate*1000:.1f} ms")
        print(f"    Nyquist: {sample_rate/2/1000:.1f} kHz")
        print(f"    Peak-to-Peak: {(np.max(voltage)-np.min(voltage))*1000:.2f} mV")
        print(f"    RMS: {np.sqrt(np.mean(voltage**2))*1000:.2f} mV")
        
        # Preprocessing
        pre = preprocess(time_vec, voltage, remove_dc_flag=True, detrend_flag=True, window='hann')
        
        # FFT
        fft = compute_fft(pre.voltage, sample_rate, window='hann')
        amp_db = amplitude_to_db(fft.amplitude)
        
        # Suche Peaks im akustischen Bereich (20 Hz - 100 kHz)
        mask = (fft.frequencies >= 20) & (fft.frequencies <= 100000)
        freqs_akustisch = fft.frequencies[mask]
        amp_db_akustisch = amp_db[mask]
        
        if len(amp_db_akustisch) > 0:
            peaks_idx, props = find_peaks(amp_db_akustisch, prominence=3, distance=5)
            
            if len(peaks_idx) > 0:
                sorted_idx = peaks_idx[np.argsort(props['prominences'])[::-1]]
                print(f"\n    Akustische Peaks (20 Hz - 100 kHz):")
                
                for i, idx in enumerate(sorted_idx[:10]):
                    freq = freqs_akustisch[idx]
                    prom_idx = np.where(peaks_idx == idx)[0][0]
                    
                    if freq < 1000:
                        freq_str = f'{freq:.1f} Hz'
                    else:
                        freq_str = f'{freq/1000:.2f} kHz'
                    
                    print(f"      {i+1}. {freq_str:12s}: {amp_db_akustisch[idx]:6.1f} dB, Prom: {props['prominences'][prom_idx]:.1f} dB")
            else:
                print(f"    Keine akustischen Peaks (prominence > 3 dB)")
        
        # Speichere Ergebnisse
        results[ch] = {
            'time_vec': time_vec,
            'voltage': voltage,
            'preprocessed': pre.voltage,
            'sample_rate': sample_rate,
            'fft': fft,
            'amp_db': amp_db,
        }
    
    return results


def main():
    """Hauptprogramm."""
    console.print("\n[bold blue]╔═══════════════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║  VERBESSERTE PFLANZEN-AE MESSUNG (LANGE AUFNAHME)          ║[/bold blue]")
    console.print("[bold blue]╚═══════════════════════════════════════════════════════════════╝[/bold blue]\n")
    
    config_path = Path(__file__).parent / "config.yaml"
    config = load_config(config_path)
    
    console.print(f"[cyan]Verbinde mit Oszilloskop: {config.instrument.visa_resource}[/cyan]")
    
    try:
        with InstrumentConnection(config) as conn:
            idn = conn.query("*IDN?")
            console.print(f"[green]✓[/green] Verbunden: {idn}\n")
            
            # Optimierte Konfiguration
            configure_optimized(conn)
            
            # Ausgabe-Verzeichnis
            output_dir = Path(__file__).parent / "data" / "plant_ae_optimized" / datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Messung
            captures = acquire_long_capture(conn, config, n_captures=20)
            
            if not captures:
                console.print("[red]Keine Messungen erfolgreich![/red]")
                sys.exit(1)
            
            # Analyse
            results = analyze_detailed(captures, output_dir)
            
            # Speichere Rohdaten
            raw_dir = output_dir / "raw"
            raw_dir.mkdir(parents=True, exist_ok=True)
            for cap in captures:
                save_capture_npz(cap, raw_dir)
            
            console.print(f"\n[green]✓[/green] Daten gespeichert in {output_dir}")
            
    except Exception as e:
        console.print(f"\n[red]Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    console.print("\n[bold green]✓ Messung abgeschlossen![/bold green]\n")


if __name__ == "__main__":
    main()
