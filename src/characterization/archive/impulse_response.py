#!/usr/bin/env python3
"""
Klopfantwort-Messung für Piezo 2 mit 1 MOhm Widerstand.

Misst:
- Impulsantwort (Klopfen)
- Ausschwingdauer
- Resonanzfrequenzen
- Signalhöhe
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import numpy as np
import yaml
from rich.console import Console
from rich.progress import Progress
from rich.table import Table
from scipy import signal as sp_signal

sys.path.insert(0, str(Path(__file__).resolve().parent / "instrument_control"))

from scope.config import ExperimentConfig, load_config
from scope.instrument import InstrumentConnection, read_oscilloscope_settings
from scope.acquisition import acquire_single_capture, save_capture_npz
from scope.preprocessing import preprocess
from scope.spectral import compute_fft, compute_welch, amplitude_to_db
from scope.peak_detection import detect_peaks_in_welch
from scope.plotting import plot_fft, plot_welch, plot_time_domain

console = Console()


def configure_for_impulse_response(conn: InstrumentConnection, config: ExperimentConfig):
    """Konfiguriere Oszilloskop für Impulsantwort-Messung."""
    console.print("\n[bold cyan]Konfiguriere für Klopfantwort-Messung...[/bold cyan]")
    
    conn.write(":STOP")
    time.sleep(0.5)
    
    # CH1: deaktiviert (nicht benötigt)
    console.print("  CH1: deaktiviert")
    conn.write(":CHAN1:DISP OFF")
    
    # CH2: Piezo mit 1 MOhm Widerstand
    console.print("  CH2 (Piezo + 1MΩ):")
    conn.write(":CHAN2:COUP AC")
    conn.write(":CHAN2:PROB 1")
    conn.write(":CHAN2:SCAL 0.01")  # 10 mV/div (hohe Empfindlichkeit)
    conn.write(":CHAN2:OFFS 0")
    conn.write(":CHAN2:DISP ON")
    console.print("    [green]✓[/green] AC-Kopplung, 1:1, 10 mV/div")
    
    # Zeitbasis: längere Aufnahme für Ausschwingvorgang
    console.print("  Zeitbasis:")
    conn.write(":TIM:SCAL 0.0005")  # 500 µs/div (10 ms total bei 12k Punkten)
    conn.write(":TIM:OFFS 0")
    console.print("    [green]✓[/green] 500 µs/div (für Ausschwingvorgang)")
    
    # Trigger: Single-Shot auf steigende Flanke
    console.print("  Trigger:")
    conn.write(":TRIG:MODE EDGE")
    conn.write(":TRIG:EDGE:SOUR CHAN2")
    conn.write(":TRIG:EDGE:SLOPE POS")
    conn.write(":TRIG:EDGE:LEV 0.02")  # 20 mV Trigger-Level
    console.print("    [green]✓[/green] Single-Shot, CH2, steigende Flanke, 20 mV")
    
    # Sample-Rate: Maximum
    console.print("  Akquisition:")
    conn.write(":ACQ:MDEP 12000")
    conn.write(":ACQ:SRAT 125000000")  # 125 MSa/s
    console.print("    [green]✓[/green] 125 MSa/s, 12k Punkte")
    
    time.sleep(0.5)
    
    # Arm trigger für Single-Shot
    conn.write(":SING")
    console.print("\n[bold green]✓ Bereit für Klopfantwort-Messung[/bold green]")
    console.print("[yellow]  Warte auf Trigger (Klopfen)...[/yellow]")


def acquire_impulse_response(conn: InstrumentConnection, config: ExperimentConfig, n_captures: int = 10):
    """Führe Impulsantwort-Messungen durch."""
    console.print(f"\n[bold magenta]Führe {n_captures} Klopfantwort-Messungen durch...[/bold magenta]")
    console.print("  [cyan]Bitte auf den Piezo-Sensor klopfen![/cyan]\n")
    
    captures = []
    
    # Erhöhe Timeout für Wartezeit auf Trigger
    original_timeout = conn._inst.timeout
    conn._inst.timeout = 60000  # 60 Sekunden
    
    with Progress() as progress:
        task = progress.add_task("Warte auf Klopfen...", total=n_captures)
        
        for i in range(n_captures):
            # Arm trigger
            conn.write(":SING")
            
            # Warte auf Trigger durch Versuch Daten zu lesen
            # Im Single-Shot-Modus blockiert :WAV:DATA? bis Trigger erfolgt
            try:
                cap = acquire_single_capture(conn, 2, config, capture_id=i)
                captures.append(cap)
                progress.update(task, advance=1)
                console.print(f"  [green]✓[/green] Messung {i+1} erfolgreich (Peak: {np.max(np.abs(cap.voltage_vector))*1000:.2f} mV)")
            except Exception as e:
                console.print(f"  [yellow]Timeout bei Messung {i+1}: {e}[/yellow]")
                # Versuche Oszilloskop zurückzusetzen
                try:
                    conn.write(":STOP")
                    time.sleep(0.5)
                except:
                    pass
                continue
            
            # Kurze Pause
            time.sleep(0.5)
    
    # Stelle ursprünglichen Timeout wieder her
    conn._inst.timeout = original_timeout
    
    console.print(f"\n[green]✓[/green] {len(captures)} Impulsantworten aufgenommen\n")
    return captures


def analyze_impulse_response(capture, config: ExperimentConfig):
    """Analysiere einzelne Impulsantwort."""
    time_vec = capture.time_vector
    voltage = capture.voltage_vector
    sample_rate = 1.0 / capture.metadata.sample_interval_s
    
    # Preprocessing
    pre = preprocess(
        time_vec, voltage,
        remove_dc_flag=True,
        detrend_flag=False,
        window="boxcar",  # Kein Window für Impulsantwort
    )
    
    # Signalhöhe
    peak_to_peak = np.max(pre.voltage) - np.min(pre.voltage)
    rms = np.sqrt(np.mean(pre.voltage**2))
    max_amplitude = np.max(np.abs(pre.voltage))
    
    # Impulsantwort: Finde Maximum
    max_idx = np.argmax(np.abs(pre.voltage))
    max_time = time_vec[max_idx]
    max_voltage = pre.voltage[max_idx]
    
    # Ausschwingdauer: Zeit bis Signal auf 5% des Maximums abgefallen ist (40 dB)
    threshold = max_amplitude * 0.01  # 1% = 40 dB
    decay_time = 0
    
    # Suche nach rechts vom Maximum
    for i in range(max_idx, len(pre.voltage)):
        if np.abs(pre.voltage[i]) < threshold:
            decay_time = time_vec[i] - max_time
            break
    
    if decay_time == 0:
        decay_time = time_vec[-1] - max_time
    
    # FFT für Resonanzfrequenzen
    fft_result = compute_fft(pre.voltage, sample_rate, window="hann")
    
    # Welch für bessere Frequenzauflösung
    welch_result = compute_welch(
        pre.voltage, sample_rate,
        nperseg=min(4096, len(pre.voltage)),
        overlap=0.5,
    )
    
    # Peak-Detection
    peaks = detect_peaks_in_welch(
        welch_result,
        prominence_db=6,
        min_distance_hz=100,
        max_peaks=20,
    )
    
    return {
        "time_vector": time_vec,
        "voltage": pre.voltage,
        "sample_rate": sample_rate,
        "peak_to_peak": peak_to_peak,
        "rms": rms,
        "max_amplitude": max_amplitude,
        "max_time": max_time,
        "max_voltage": max_voltage,
        "decay_time": decay_time,
        "fft": fft_result,
        "welch": welch_result,
        "peaks": peaks,
    }


def print_results(all_results):
    """Drucke Zusammenfassung der Ergebnisse."""
    console.print("\n" + "="*80)
    console.print("[bold green]KLOPFANTWORT-ANALYSE: PIEZO 2 + 1 MΩ[/bold green]")
    console.print("="*80)
    
    # Statistiken über alle Messungen
    n = len(all_results)
    
    # Signalhöhe
    peak_to_peaks = [r["peak_to_peak"] for r in all_results]
    rms_values = [r["rms"] for r in all_results]
    max_amps = [r["max_amplitude"] for r in all_results]
    
    console.print("\n[bold cyan]1. SIGNALHÖHE[/bold cyan]")
    console.print(f"  Peak-to-Peak:  {np.mean(peak_to_peaks)*1000:.2f} ± {np.std(peak_to_peaks)*1000:.2f} mV")
    console.print(f"  RMS:           {np.mean(rms_values)*1000:.2f} ± {np.std(rms_values)*1000:.2f} mV")
    console.print(f"  Max. Amplitude:{np.mean(max_amps)*1000:.2f} ± {np.std(max_amps)*1000:.2f} mV")
    
    # Ausschwingdauer
    decay_times = [r["decay_time"] for r in all_results]
    
    console.print("\n[bold cyan]2. AUSSCHWINGDAUER[/bold cyan]")
    console.print(f"  Mittelwert:    {np.mean(decay_times)*1000:.2f} ± {np.std(decay_times)*1000:.2f} ms")
    console.print(f"  Minimum:       {np.min(decay_times)*1000:.2f} ms")
    console.print(f"  Maximum:       {np.max(decay_times)*1000:.2f} ms")
    
    # Resonanzfrequenzen
    console.print("\n[bold cyan]3. RESONANZFREQUENZEN[/bold cyan]")
    
    # Sammle alle Peaks
    all_peaks = []
    for r in all_results:
        all_peaks.extend(r["peaks"])
    
    if not all_peaks:
        console.print("  [yellow]Keine signifikanten Resonanzfrequenzen gefunden[/yellow]")
    else:
        # Gruppiere Peaks nach Frequenz (±500 Hz Toleranz)
        freqs = sorted([p.frequency_hz for p in all_peaks])
        clusters = []
        current_cluster = [freqs[0]]
        
        for f in freqs[1:]:
            if f - current_cluster[-1] < 500:
                current_cluster.append(f)
            else:
                clusters.append(current_cluster)
                current_cluster = [f]
        clusters.append(current_cluster)
        
        # Sortiere nach Häufigkeit
        clusters.sort(key=len, reverse=True)
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Frequenz (Hz)", style="cyan", justify="right")
        table.add_column("Häufigkeit", style="green", justify="right")
        table.add_column("Prominenz (dB)", style="yellow", justify="right")
        table.add_column("Streuung (Hz)", style="blue", justify="right")
        
        for cluster in clusters[:10]:  # Top 10
            mean_freq = np.mean(cluster)
            count = len(cluster)
            std_freq = np.std(cluster) if len(cluster) > 1 else 0
            
            # Finde höchste Prominenz für diese Frequenz
            proms = [p.prominence_db for p in all_peaks if abs(p.frequency_hz - mean_freq) < 500]
            max_prom = max(proms) if proms else 0
            
            table.add_row(
                f"{mean_freq:.0f}",
                f"{count}/{n}",
                f"{max_prom:.1f}",
                f"{std_freq:.0f}",
            )
        
        console.print(table)
    
    console.print("\n" + "="*80)


def save_results(captures, all_results, output_dir: Path):
    """Speichere Ergebnisse."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Speichere Rohdaten
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    for cap in captures:
        save_capture_npz(cap, raw_dir)
    
    # Speichere Analyse-Ergebnisse
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    
    # Zusammenfassung
    summary = {
        "timestamp": timestamp,
        "n_captures": len(captures),
        "signal_height": {
            "peak_to_peak_mV_mean": float(np.mean([r["peak_to_peak"] for r in all_results]) * 1000),
            "peak_to_peak_mV_std": float(np.std([r["peak_to_peak"] for r in all_results]) * 1000),
            "rms_mV_mean": float(np.mean([r["rms"] for r in all_results]) * 1000),
            "rms_mV_std": float(np.std([r["rms"] for r in all_results]) * 1000),
            "max_amplitude_mV_mean": float(np.mean([r["max_amplitude"] for r in all_results]) * 1000),
            "max_amplitude_mV_std": float(np.std([r["max_amplitude"] for r in all_results]) * 1000),
        },
        "decay_time": {
            "mean_ms": float(np.mean([r["decay_time"] for r in all_results]) * 1000),
            "std_ms": float(np.std([r["decay_time"] for r in all_results]) * 1000),
            "min_ms": float(np.min([r["decay_time"] for r in all_results]) * 1000),
            "max_ms": float(np.max([r["decay_time"] for r in all_results]) * 1000),
        },
    }
    
    summary_file = analysis_dir / f"{timestamp}_summary.yaml"
    with open(summary_file, "w") as f:
        yaml.dump(summary, f, default_flow_style=False)
    
    # Speichere einzelne Ergebnisse
    for i, result in enumerate(all_results):
        result_file = analysis_dir / f"{timestamp}_capture_{i:03d}.npz"
        np.savez(
            result_file,
            time_vector=result["time_vector"],
            voltage=result["voltage"],
            peak_to_peak=result["peak_to_peak"],
            rms=result["rms"],
            max_amplitude=result["max_amplitude"],
            decay_time=result["decay_time"],
        )
    
    # Speichere Plots
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    for i, result in enumerate(all_results):
        # Zeitbereich (korrigiere Dimensionen)
        time_ms = result["time_vector"][:len(result["voltage"])] * 1000
        voltage_mv = result["voltage"] * 1000
        
        plot_time_domain(
            time_ms,
            voltage_mv,
            2,
            "Piezo + 1MΩ",
            plots_dir / f"{timestamp}_capture_{i:03d}_time.png",
            title=f"Klopfantwort #{i+1}",
        )
        
        # FFT
        plot_fft(
            result["fft"],
            2,
            "Piezo + 1MΩ",
            plots_dir / f"{timestamp}_capture_{i:03d}_fft.png",
            min_freq=1000,
            max_freq=min(100000, result["sample_rate"]/2),
        )
        
        # Welch
        plot_welch(
            result["welch"],
            2,
            "Piezo + 1MΩ",
            plots_dir / f"{timestamp}_capture_{i:03d}_welch.png",
            peaks=result["peaks"],
            min_freq=1000,
            max_freq=min(100000, result["sample_rate"]/2),
        )
    
    console.print(f"\n[green]✓[/green] Ergebnisse gespeichert in {output_dir}")
    console.print(f"  Zusammenfassung: {summary_file}")
    console.print(f"  Plots: {plots_dir}")


def main():
    """Hauptprogramm."""
    console.print("\n[bold blue]╔═══════════════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║         KLOPFANTWORT-MESSUNG: PIEZO 2 + 1 MΩ WIDERSTAND     ║[/bold blue]")
    console.print("[bold blue]╚═══════════════════════════════════════════════════════════════╝[/bold blue]\n")
    
    # Lade Konfiguration
    config_path = Path(__file__).parent / "configs" / "experiment_piezo_stainless.yaml"
    if not config_path.exists():
        console.print(f"[red]Fehler: Konfigurationsdatei nicht gefunden: {config_path}[/red]")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # Verbinde mit Oszilloskop
    console.print(f"[cyan]Verbinde mit Oszilloskop: {config.instrument.visa_resource}[/cyan]")
    
    try:
        with InstrumentConnection(config) as conn:
            idn = conn.query("*IDN?")
            console.print(f"[green]✓[/green] Verbunden: {idn}\n")
            
            # Konfiguriere für Impulsantwort
            configure_for_impulse_response(conn, config)
            
            # Ausgabe-Verzeichnis
            output_dir = Path(__file__).parent / "data" / "impulse_response" / datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Führe Messungen durch
            n_captures = 10
            captures = acquire_impulse_response(conn, config, n_captures)
            
            if not captures:
                console.print("[red]Keine Messungen erfolgreich![/red]")
                sys.exit(1)
            
            # Analysiere alle Messungen
            console.print("[bold]Analysiere Impulsantworten...[/bold]")
            all_results = []
            for i, cap in enumerate(captures):
                result = analyze_impulse_response(cap, config)
                all_results.append(result)
                console.print(f"  Messung {i+1}/{len(captures)}: Peak={result['max_amplitude']*1000:.2f} mV, Ausschwingzeit={result['decay_time']*1000:.2f} ms")
            
            # Drucke Ergebnisse
            print_results(all_results)
            
            # Speichere Ergebnisse
            save_results(captures, all_results, output_dir)
            
    except Exception as e:
        console.print(f"\n[red]Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    console.print("\n[bold green]✓ Messung abgeschlossen![/bold green]\n")


if __name__ == "__main__":
    main()
