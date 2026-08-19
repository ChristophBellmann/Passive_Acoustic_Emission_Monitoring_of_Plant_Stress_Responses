#!/usr/bin/env python3
"""
Messung akustischer Emissionen der Pflanze mit 3 Piezos in der Erde.

Setup:
- CH1: Piezo + LM358 Verstärker + 820kΩ, 10:1 Probe
- CH2: Piezo + 820kΩ, 1:1 Probe  
- CH3: Piezo direkt, 1:1 Probe

Ziel: Akustische Emissionen der Pflanze im Bereich 20 Hz - 100 kHz
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
from scope.plotting import plot_fft, plot_welch, plot_time_domain, plot_channel_comparison

console = Console()


def configure_for_plant_ae(conn: InstrumentConnection, config: ExperimentConfig):
    """Konfiguriere Oszilloskop für Pflanzen-AE-Messung."""
    console.print("\n[bold cyan]Konfiguriere für Pflanzen-AE-Messung (3 Kanäle)...[/bold cyan]")
    
    conn.write(":STOP")
    time.sleep(0.5)
    
    # CH1: Piezo + Verstärker + 820kΩ, 10:1
    console.print("  CH1 (Piezo + LM358 + 820kΩ, 10:1):")
    conn.write(":CHAN1:COUP AC")
    conn.write(":CHAN1:PROB 10")
    conn.write(":CHAN1:SCAL 0.01")  # 10 mV/div (empfindlich)
    conn.write(":CHAN1:OFFS 0")
    conn.write(":CHAN1:DISP ON")
    console.print("    [green]✓[/green] AC, 10:1, 10 mV/div")
    
    # CH2: Piezo + 820kΩ, 1:1
    console.print("  CH2 (Piezo + 820kΩ, 1:1):")
    conn.write(":CHAN2:COUP AC")
    conn.write(":CHAN2:PROB 1")
    conn.write(":CHAN2:SCAL 0.01")  # 10 mV/div
    conn.write(":CHAN2:OFFS 0")
    conn.write(":CHAN2:DISP ON")
    console.print("    [green]✓[/green] AC, 1:1, 10 mV/div")
    
    # CH3: Piezo direkt, 1:1
    console.print("  CH3 (Piezo direkt, 1:1):")
    conn.write(":CHAN3:COUP AC")
    conn.write(":CHAN3:PROB 1")
    conn.write(":CHAN3:SCAL 0.01")  # 10 mV/div
    conn.write(":CHAN3:OFFS 0")
    conn.write(":CHAN3:DISP ON")
    console.print("    [green]✓[/green] AC, 1:1, 10 mV/div")
    
    # Zeitbasis: optimiert für 20 Hz - 100 kHz
    console.print("  Zeitbasis:")
    conn.write(":TIM:SCAL 0.0001")  # 100 µs/div (für 100 kHz)
    conn.write(":TIM:OFFS 0")
    console.print("    [green]✓[/green] 100 µs/div (20 Hz - 100 kHz)")
    
    # Trigger: Auto für kontinuierliche Erfassung
    console.print("  Trigger:")
    conn.write(":TRIG:MODE AUTO")
    conn.write(":TRIG:EDGE:SOUR CHAN1")
    conn.write(":TRIG:EDGE:LEV 0.02")  # 20 mV
    console.print("    [green]✓[/green] Auto-Trigger auf CH1, 20 mV")
    
    # Sample-Rate: optimiert für akustischen Bereich
    console.print("  Akquisition:")
    conn.write(":ACQ:MDEP 12000")
    conn.write(":ACQ:SRAT 1000000")  # 1 MSa/s (Nyquist = 500 kHz)
    console.print("    [green]✓[/green] 1 MSa/s, 12k Punkte")
    
    time.sleep(0.5)
    conn.write(":RUN")
    console.print("\n[bold green]✓ Oszilloskop konfiguriert für Pflanzen-AE[/bold green]")


def acquire_continuous(conn: InstrumentConnection, config: ExperimentConfig, n_captures: int = 30):
    """Führe kontinuierliche Messung durch."""
    console.print(f"\n[bold magenta]Führe {n_captures} kontinuierliche Messungen durch...[/bold magenta]")
    console.print("  [cyan]Die Pflanze kann jetzt akustische Emissionen erzeugen.[/cyan]\n")
    
    captures = []
    channels = [1, 2, 3]
    
    with Progress() as progress:
        task = progress.add_task("Aufnahme...", total=n_captures * len(channels))
        
        for i in range(n_captures):
            for ch in channels:
                try:
                    cap = acquire_single_capture(conn, ch, config, capture_id=i)
                    captures.append(cap)
                except Exception as e:
                    console.print(f"  [yellow]Fehler bei CH{ch}, Capture {i}: {e}[/yellow]")
                progress.update(task, advance=1)
            
            if i < n_captures - 1:
                time.sleep(0.3)
    
    console.print(f"\n[green]✓[/green] {len(captures)} Aufnahmen abgeschlossen\n")
    return captures


def analyze_channel(captures_ch, channel_num, config: ExperimentConfig):
    """Analysiere Aufnahmen eines Kanals."""
    if not captures_ch:
        return None
    
    # Preprocessing und Spektralanalyse für jede Aufnahme
    all_welch = []
    all_peaks = []
    preprocessing_results = []
    
    for i, cap in enumerate(captures_ch):
        # Preprocessing
        pre = preprocess(
            cap.time_vector,
            cap.voltage_vector,
            remove_dc_flag=True,
            detrend_flag=True,
            window="hann",
        )
        preprocessing_results.append(pre)
        
        # Welch PSD
        sample_rate = 1.0 / cap.metadata.sample_interval_s
        welch = compute_welch(
            pre.voltage,
            sample_rate,
            nperseg=min(4096, len(pre.voltage)),
            overlap=0.5,
        )
        all_welch.append(welch)
        
        # Peak-Detection (nur im relevanten Frequenzbereich)
        peaks = detect_peaks_in_welch(
            welch,
            prominence_db=6,
            min_distance_hz=50,
            max_peaks=30,
            ignore_bands_hz=[[48, 52], [98, 102], [148, 152], [198, 202]],
            channel=channel_num,
            capture_id=i,
        )
        # Filtere auf akustischen Bereich
        peaks = [p for p in peaks if 20 <= p.frequency_hz <= 100000]
        all_peaks.extend(peaks)
    
    # Durchschnittliches Welch-Spektrum
    avg_psd = np.mean([w.psd for w in all_welch], axis=0)
    avg_welch = type(all_welch[0])(frequencies=all_welch[0].frequencies, psd=avg_psd)
    
    # Signalhöhe über alle Aufnahmen
    max_amps = [np.max(np.abs(pre.voltage)) for pre in preprocessing_results]
    rms_values = [np.sqrt(np.mean(pre.voltage**2)) for pre in preprocessing_results]
    
    return {
        "channel": channel_num,
        "n_captures": len(captures_ch),
        "avg_welch": avg_welch,
        "all_peaks": all_peaks,
        "preprocessing": preprocessing_results,
        "sample_rate": 1.0 / captures_ch[0].metadata.sample_interval_s,
        "max_amplitude_mean": np.mean(max_amps),
        "max_amplitude_std": np.std(max_amps),
        "rms_mean": np.mean(rms_values),
        "rms_std": np.std(rms_values),
    }


def print_comparison(results):
    """Drucke Vergleich der drei Kanäle."""
    console.print("\n" + "="*90)
    console.print("[bold green]PFLANZEN-AE ANALYSE: VERGLEICH DER 3 PIEZOS[/bold green]")
    console.print("="*90)
    
    # Tabelle für Signalhöhe
    table = Table(title="Signalhöhe", show_header=True, header_style="bold magenta")
    table.add_column("Kanal", style="cyan")
    table.add_column("Konfiguration", style="white")
    table.add_column("Max. Amp (mV)", style="green", justify="right")
    table.add_column("RMS (mV)", style="yellow", justify="right")
    table.add_column("Peaks", style="blue", justify="right")
    
    ch_names = {
        1: "Piezo + LM358 + 820kΩ (10:1)",
        2: "Piezo + 820kΩ (1:1)",
        3: "Piezo direkt (1:1)",
    }
    
    for ch_num in [1, 2, 3]:
        if ch_num in results and results[ch_num]:
            r = results[ch_num]
            table.add_row(
                f"CH{ch_num}",
                ch_names[ch_num],
                f"{r['max_amplitude_mean']*1000:.2f} ± {r['max_amplitude_std']*1000:.2f}",
                f"{r['rms_mean']*1000:.2f} ± {r['rms_std']*1000:.2f}",
                str(len(r['all_peaks'])),
            )
    
    console.print(table)
    
    # Resonanzfrequenzen pro Kanal
    console.print("\n[bold cyan]Dominante Frequenzen (20 Hz - 100 kHz):[/bold cyan]")
    
    for ch_num in [1, 2, 3]:
        if ch_num not in results or not results[ch_num]:
            continue
        
        r = results[ch_num]
        peaks = r['all_peaks']
        
        if not peaks:
            console.print(f"\n  CH{ch_num}: [yellow]Keine signifikanten Peaks[/yellow]")
            continue
        
        # Gruppiere Peaks nach Frequenz
        freqs = sorted([p.frequency_hz for p in peaks])
        clusters = []
        current_cluster = [freqs[0]]
        
        for f in freqs[1:]:
            if f - current_cluster[-1] < 100:  # 100 Hz Toleranz
                current_cluster.append(f)
            else:
                clusters.append(current_cluster)
                current_cluster = [f]
        clusters.append(current_cluster)
        
        # Sortiere nach Häufigkeit
        clusters.sort(key=len, reverse=True)
        
        console.print(f"\n  CH{ch_num} ({ch_names[ch_num]}):")
        
        # Top 5 Frequenzen
        for i, cluster in enumerate(clusters[:5]):
            mean_freq = np.mean(cluster)
            count = len(cluster)
            proms = [p.prominence_db for p in peaks if abs(p.frequency_hz - mean_freq) < 100]
            max_prom = max(proms) if proms else 0
            
            if mean_freq < 1000:
                freq_str = f"{mean_freq:.1f} Hz"
            else:
                freq_str = f"{mean_freq/1000:.2f} kHz"
            
            console.print(f"    {i+1}. {freq_str}: {count}x, Prominenz {max_prom:.1f} dB")
    
    console.print("\n" + "="*90)


def save_results(captures, results, output_dir: Path):
    """Speichere Ergebnisse."""
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Rohdaten
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(exist_ok=True)
    for cap in captures:
        save_capture_npz(cap, raw_dir)
    
    # Analyse
    analysis_dir = output_dir / "analysis"
    analysis_dir.mkdir(exist_ok=True)
    
    # Zusammenfassung
    summary = {
        "timestamp": timestamp,
        "setup": {
            "CH1": "Piezo + LM358 + 820kΩ, 10:1",
            "CH2": "Piezo + 820kΩ, 1:1",
            "CH3": "Piezo direkt, 1:1",
        },
        "n_captures_per_channel": 30,
    }
    
    for ch_num in [1, 2, 3]:
        if ch_num in results and results[ch_num]:
            r = results[ch_num]
            summary[f"CH{ch_num}"] = {
                "max_amplitude_mV_mean": float(r['max_amplitude_mean'] * 1000),
                "max_amplitude_mV_std": float(r['max_amplitude_std'] * 1000),
                "rms_mV_mean": float(r['rms_mean'] * 1000),
                "rms_mV_std": float(r['rms_std'] * 1000),
                "n_peaks": len(r['all_peaks']),
            }
    
    summary_file = analysis_dir / f"{timestamp}_summary.yaml"
    with open(summary_file, "w") as f:
        yaml.dump(summary, f, default_flow_style=False)
    
    # Plots
    plots_dir = output_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Zeitbereich für jeden Kanal (erste Aufnahme)
    for ch_num in [1, 2, 3]:
        if ch_num not in results or not results[ch_num]:
            continue
        
        r = results[ch_num]
        pre = r['preprocessing'][0]
        time_vec = captures[[c.metadata.channel for c in captures].index(ch_num)].time_vector
        time_vec = time_vec[:len(pre.voltage)]
        
        plot_time_domain(
            time_vec * 1000,
            pre.voltage * 1000,
            ch_num,
            f"CH{ch_num}",
            plots_dir / f"{timestamp}_ch{ch_num}_time.png",
            title=f"Kanal {ch_num} - Zeitbereich",
        )
        
        # Welch PSD
        plot_welch(
            r['avg_welch'],
            ch_num,
            f"CH{ch_num}",
            plots_dir / f"{timestamp}_ch{ch_num}_welch.png",
            peaks=r['all_peaks'][:10],
            min_freq=20,
            max_freq=min(100000, r['sample_rate']/2),
        )
    
    # Kanalvergleich
    if all(ch in results and results[ch] for ch in [1, 2, 3]):
        plot_channel_comparison(
            results[1]['avg_welch'],
            results[2]['avg_welch'],
            "CH1 (verstärkt)",
            "CH2 (820kΩ)",
            plots_dir / f"{timestamp}_comparison_ch1_ch2.png",
            peaks_ch1=results[1]['all_peaks'][:10],
            peaks_ch2=results[2]['all_peaks'][:10],
        )
        
        plot_channel_comparison(
            results[2]['avg_welch'],
            results[3]['avg_welch'],
            "CH2 (820kΩ)",
            "CH3 (direkt)",
            plots_dir / f"{timestamp}_comparison_ch2_ch3.png",
            peaks_ch1=results[2]['all_peaks'][:10],
            peaks_ch2=results[3]['all_peaks'][:10],
        )
    
    console.print(f"\n[green]✓[/green] Ergebnisse gespeichert in {output_dir}")
    console.print(f"  Zusammenfassung: {summary_file}")
    console.print(f"  Plots: {plots_dir}")


def main():
    """Hauptprogramm."""
    console.print("\n[bold blue]╔═══════════════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║     PFLANZEN-AE MESSUNG: 3 PIEZOS IN DER ERDE               ║[/bold blue]")
    console.print("[bold blue]╚═══════════════════════════════════════════════════════════════╝[/bold blue]\n")
    
    # Lade Konfiguration
    config_path = Path(__file__).parent / "configs" / "experiment_piezo_stainless.yaml"
    if not config_path.exists():
        console.print(f"[red]Fehler: Konfigurationsdatei nicht gefunden: {config_path}[/red]")
        sys.exit(1)
    
    config = load_config(config_path)
    
    # Erweitere Config für 3 Kanäle
    from scope.config import ChannelSetting
    config.oscilloscope.channels = [1, 2, 3]
    config.oscilloscope.channel_settings[1] = ChannelSetting(
        enabled=True, label="piezo_amp_820k", probe_ratio=10, coupling="AC"
    )
    config.oscilloscope.channel_settings[2] = ChannelSetting(
        enabled=True, label="piezo_820k", probe_ratio=1, coupling="AC"
    )
    config.oscilloscope.channel_settings[3] = ChannelSetting(
        enabled=True, label="piezo_direct", probe_ratio=1, coupling="AC"
    )
    
    # Verbinde mit Oszilloskop
    console.print(f"[cyan]Verbinde mit Oszilloskop: {config.instrument.visa_resource}[/cyan]")
    
    try:
        with InstrumentConnection(config) as conn:
            idn = conn.query("*IDN?")
            console.print(f"[green]✓[/green] Verbunden: {idn}\n")
            
            # Konfiguriere für Pflanzen-AE
            configure_for_plant_ae(conn, config)
            
            # Ausgabe-Verzeichnis
            output_dir = Path(__file__).parent / "data" / "plant_ae_3ch" / datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Führe Messungen durch
            captures = acquire_continuous(conn, config, n_captures=30)
            
            if not captures:
                console.print("[red]Keine Messungen erfolgreich![/red]")
                sys.exit(1)
            
            # Analysiere pro Kanal
            console.print("[bold]Analysiere Daten...[/bold]")
            results = {}
            
            for ch_num in [1, 2, 3]:
                captures_ch = [c for c in captures if c.metadata.channel == ch_num]
                if captures_ch:
                    result = analyze_channel(captures_ch, ch_num, config)
                    results[ch_num] = result
                    console.print(f"  CH{ch_num}: {len(captures_ch)} Aufnahmen, {len(result['all_peaks'])} Peaks")
            
            # Drucke Vergleich
            print_comparison(results)
            
            # Speichere Ergebnisse
            save_results(captures, results, output_dir)
            
    except Exception as e:
        console.print(f"\n[red]Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    console.print("\n[bold green]✓ Messung abgeschlossen![/bold green]\n")


if __name__ == "__main__":
    main()
