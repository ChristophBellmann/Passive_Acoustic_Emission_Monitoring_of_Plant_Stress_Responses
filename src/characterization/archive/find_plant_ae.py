#!/usr/bin/env python3
"""
Automatisierte Messung und Analyse akustischer Emissionen einer Pflanze.

Dieses Skript:
1. Verbindet sich mit dem Rigol DS1104Z Oszilloskop
2. Konfiguriert optimale Einstellungen für akustische Emissionen
3. Führt Baseline-Messung durch (Umgebungsrauschen)
4. Führt aktive Messungen durch
5. Analysiert und vergleicht Spektren
6. Identifiziert signifikante Frequenzpeaks
7. Erstellt umfassenden Bericht
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

sys.path.insert(0, str(Path(__file__).resolve().parent / "instrument_control"))

from scope.config import ExperimentConfig, load_config
from scope.instrument import InstrumentConnection, read_oscilloscope_settings
from scope.acquisition import acquire_single_capture, save_capture_npz
from scope.preprocessing import preprocess
from scope.spectral import compute_fft, compute_welch, amplitude_to_db
from scope.peak_detection import detect_peaks_in_welch
from scope.plausibility import run_plausibility_checks
from scope.plotting import plot_fft, plot_welch, plot_time_domain, plot_channel_comparison
from scope.reporting import generate_report

console = Console()


class PlantAECalibration:
    """Optimale Einstellungen für akustische Emissionen der Pflanze."""
    
    def __init__(self, base_config: ExperimentConfig):
        self.config = base_config
        self._optimize_for_ae()
    
    def _optimize_for_ae(self):
        """Konfiguriere Oszilloskop für akustische Emissionen."""
        # Akustische Emissionen: typischerweise 20 kHz - 300 kHz
        # Sample-Rate muss mindestens 2x maximale Frequenz sein (Nyquist)
        # Rigol DS1104Z kann bis zu 1 GSa/s (1 GHz Bandbreite)
        
        # CH1: Piezo mit LM358 Verstärker (hohe Empfindlichkeit)
        if 1 in self.config.oscilloscope.channel_settings:
            ch1 = self.config.oscilloscope.channel_settings[1]
            ch1.coupling = "AC"  # AC-Kopplung entfernt DC-Offset
            ch1.probe_ratio = 10  # 10:1 Teiler
            # Vertikale Skala: empfindlich für schwache Signale
            # LM358 verstärkt, also mittlere Empfindlichkeit
            ch1.vertical_scale_v_per_div = 0.1  # 100 mV/div
            
        # CH2: Direkter Piezo (niedrigere Empfindlichkeit)
        if 2 in self.config.oscilloscope.channel_settings:
            ch2 = self.config.oscilloscope.channel_settings[2]
            ch2.coupling = "AC"
            ch2.probe_ratio = 1  # 1:1 direkt
            ch2.vertical_scale_v_per_div = 0.05  # 50 mV/div (empfindlicher)
        
        # Akquisition: hohe Sample-Rate für hohe Frequenzen
        self.config.acquisition.memory_depth = "AUTO"
        self.config.acquisition.waveform_mode = "RAW"
        
        # Verarbeitung: optimiert für AE-Signale
        self.config.processing.min_frequency_hz = 20  # Unterhalb hörbarer Bereich
        self.config.processing.max_frequency_hz = 300000  # 300 kHz Obergrenze
        self.config.processing.welch.nperseg = 8192  # Höhere Frequenzauflösung
        
        # Peak-Detection: empfindlicher für schwache AE-Signale
        self.config.peak_detection.prominence_db = 6  # Niedrigerer Schwellwert
        self.config.peak_detection.min_distance_hz = 100  # 100 Hz Mindestabstand
        self.config.peak_detection.max_peaks = 50  # Mehr Peaks erlauben
        
        # Ignoriere nur 50 Hz Netzbrummen und Harmonische
        self.config.peak_detection.ignore_frequency_bands_hz = [
            [48, 52],    # 50 Hz
            [98, 102],   # 100 Hz
            [148, 152],  # 150 Hz
            [198, 202],  # 200 Hz
        ]


def optimize_oscilloscope_settings(conn: InstrumentConnection, config: ExperimentConfig):
    """Optimiere Oszilloskop-Einstellungen für akustische Emissionen."""
    console.print("\n[bold cyan]Optimiere Oszilloskop-Einstellungen für akustische Emissionen...[/bold cyan]")
    
    # Stoppe Oszilloskop für Konfiguration
    conn.write(":STOP")
    time.sleep(0.5)
    
    # CH1: Piezo mit Verstärker
    console.print("  CH1 (Piezo + LM358):")
    conn.write(":CHAN1:COUP AC")
    conn.write(":CHAN1:PROB 10")
    conn.write(":CHAN1:SCAL 0.1")  # 100 mV/div
    conn.write(":CHAN1:OFFS 0")
    conn.write(":CHAN1:DISP ON")
    console.print("    [green]✓[/green] AC-Kopplung, 10:1, 100 mV/div")
    
    # CH2: Direkter Piezo
    console.print("  CH2 (Piezo direkt):")
    conn.write(":CHAN2:COUP AC")
    conn.write(":CHAN2:PROB 1")
    conn.write(":CHAN2:SCAL 0.05")  # 50 mV/div (empfindlicher)
    conn.write(":CHAN2:OFFS 0")
    conn.write(":CHAN2:DISP ON")
    console.print("    [green]✓[/green] AC-Kopplung, 1:1, 50 mV/div")
    
    # Zeitbasis: 1 ms/div für 20 kHz - 300 kHz Bereich
    console.print("  Zeitbasis:")
    conn.write(":TIM:SCAL 0.001")  # 1 ms/div
    conn.write(":TIM:OFFS 0")
    console.print("    [green]✓[/green] 1 ms/div (für hohe Frequenzen)")
    
    # Trigger: Auto-Trigger für kontinuierliche Erfassung
    console.print("  Trigger:")
    conn.write(":TRIG:MODE AUTO")
    conn.write(":TRIG:EDGE:SOUR CHAN1")
    conn.write(":TRIG:EDGE:LEV 0.1")  # 100 mV Trigger-Level
    console.print("    [green]✓[/green] Auto-Trigger auf CH1")
    
    # Sample-Rate: Maximum für beste Frequenzauflösung
    console.print("  Akquisition:")
    conn.write(":ACQ:MDEP 12000")  # 12k Punkte Speicher
    conn.write(":ACQ:SRAT 125000000")  # 125 MSa/s (max für 4 Kanäle)
    console.print("    [green]✓[/green] 125 MSa/s, 12k Punkte")
    
    time.sleep(0.5)
    conn.write(":RUN")
    console.print("\n[bold green]✓ Oszilloskop optimiert für akustische Emissionen[/bold green]")


def acquire_baseline(conn: InstrumentConnection, config: ExperimentConfig, n_captures: int = 10):
    """Führe Baseline-Messung durch (Umgebungsrauschen ohne Pflanze)."""
    console.print(f"\n[bold yellow]Baseline-Messung: {n_captures} Aufnahmen (Umgebungsrauschen)[/bold yellow]")
    console.print("  Bitte stelle sicher, dass keine mechanische Anregung erfolgt.\n")
    
    baseline_captures = []
    
    with Progress() as progress:
        task = progress.add_task("Aufnahme...", total=n_captures * len(config.oscilloscope.channels))
        
        for i in range(n_captures):
            for ch in config.oscilloscope.channels:
                cap = acquire_single_capture(conn, ch, config, capture_id=i)
                baseline_captures.append(cap)
                progress.update(task, advance=1)
            
            if i < n_captures - 1:
                time.sleep(0.5)
    
    console.print(f"[green]✓[/green] {len(baseline_captures)} Baseline-Aufnahmen abgeschlossen\n")
    return baseline_captures


def acquire_active(conn: InstrumentConnection, config: ExperimentConfig, n_captures: int = 20):
    """Führe aktive Messung durch (mit möglichen akustischen Emissionen)."""
    console.print(f"\n[bold magenta]Aktive Messung: {n_captures} Aufnahmen[/bold magenta]")
    console.print("  Die Pflanze kann jetzt akustische Emissionen erzeugen.\n")
    
    active_captures = []
    
    with Progress() as progress:
        task = progress.add_task("Aufnahme...", total=n_captures * len(config.oscilloscope.channels))
        
        for i in range(n_captures):
            for ch in config.oscilloscope.channels:
                cap = acquire_single_capture(conn, ch, config, capture_id=i)
                active_captures.append(cap)
                progress.update(task, advance=1)
            
            if i < n_captures - 1:
                time.sleep(0.3)
    
    console.print(f"[green]✓[/green] {len(active_captures)} Aktive Aufnahmen abgeschlossen\n")
    return active_captures


def analyze_captures(captures, config: ExperimentConfig, label: str):
    """Analysiere Aufnahmen und extrahiere Spektren."""
    console.print(f"\n[bold cyan]Analysiere {label}...[/bold cyan]")
    
    results_by_channel = {}
    
    for ch in config.oscilloscope.channels:
        ch_captures = [c for c in captures if c.metadata.channel == ch]
        if not ch_captures:
            continue
        
        console.print(f"  CH{ch}: {len(ch_captures)} Aufnahmen")
        
        all_welch = []
        all_peaks = []
        preprocessing_results = []
        
        for i, cap in enumerate(ch_captures):
            # Preprocessing
            pre = preprocess(
                cap.time_vector,
                cap.voltage_vector,
                remove_dc_flag=config.processing.remove_dc,
                detrend_flag=config.processing.detrend,
                window=config.processing.window,
                clipping_threshold=config.plausibility.clipping_threshold_fraction,
            )
            preprocessing_results.append(pre)
            
            # Welch PSD
            sample_rate = 1.0 / cap.metadata.sample_interval_s
            welch = compute_welch(
                pre.voltage,
                sample_rate,
                nperseg=config.processing.welch.nperseg,
                overlap=config.processing.welch.overlap,
            )
            all_welch.append(welch)
            
            # Peak-Detection
            peaks = detect_peaks_in_welch(
                welch,
                prominence_db=config.peak_detection.prominence_db,
                min_distance_hz=config.peak_detection.min_distance_hz,
                max_peaks=config.peak_detection.max_peaks,
                ignore_bands_hz=config.peak_detection.ignore_frequency_bands_hz,
                channel=ch,
                capture_id=i,
            )
            all_peaks.extend(peaks)
        
        # Durchschnittliches Welch-Spektrum
        avg_psd = np.mean([w.psd for w in all_welch], axis=0)
        avg_welch = type(all_welch[0])(frequencies=all_welch[0].frequencies, psd=avg_psd)
        
        results_by_channel[ch] = {
            "welch": avg_welch,
            "peaks": all_peaks,
            "preprocessing": preprocessing_results,
            "sample_rate": 1.0 / ch_captures[0].metadata.sample_interval_s,
        }
    
    return results_by_channel


def compare_baseline_vs_active(baseline_results, active_results, config: ExperimentConfig):
    """Vergleiche Baseline mit aktiver Messung und finde signifikante Peaks."""
    console.print("\n[bold yellow]Vergleiche Baseline mit aktiver Messung...[/bold yellow]")
    
    significant_peaks = {}
    
    for ch in config.oscilloscope.channels:
        if ch not in baseline_results or ch not in active_results:
            continue
        
        baseline_peaks = baseline_results[ch]["peaks"]
        active_peaks = active_results[ch]["peaks"]
        
        baseline_freqs = {round(p.frequency_hz, 0) for p in baseline_peaks}
        active_freqs = {round(p.frequency_hz, 0) for p in active_peaks}
        
        # Peaks die nur in aktiver Messung auftreten
        new_peaks = active_freqs - baseline_freqs
        
        # Filtere nach Amplitude (nur signifikante Peaks)
        significant = []
        for peak in active_peaks:
            if round(peak.frequency_hz, 0) in new_peaks:
                if peak.prominence_db >= config.peak_detection.prominence_db:
                    significant.append(peak)
        
        significant_peaks[ch] = significant
        
        console.print(f"  CH{ch}:")
        console.print(f"    Baseline-Peaks: {len(baseline_peaks)}")
        console.print(f"    Aktive Peaks: {len(active_peaks)}")
        console.print(f"    [bold green]Signifikante neue Peaks: {len(significant)}[/bold green]")
    
    return significant_peaks


def save_results(captures, results, significant_peaks, output_dir: Path):
    """Speichere alle Ergebnisse."""
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
    
    # Speichere signifikante Peaks als YAML
    peaks_data = {}
    for ch, peaks in significant_peaks.items():
        peaks_data[f"CH{ch}"] = [
            {
                "frequency_hz": p.frequency_hz,
                "amplitude_db": p.amplitude_db,
                "prominence_db": p.prominence_db,
                "bandwidth_hz": p.bandwidth_hz,
                "q_factor": p.q_factor,
                "snr_db": p.snr_db,
                "label": p.plausibility_label,
            }
            for p in peaks
        ]
    
    peaks_file = analysis_dir / f"{timestamp}_significant_peaks.yaml"
    with open(peaks_file, "w") as f:
        yaml.dump(peaks_data, f, default_flow_style=False)
    
    console.print(f"\n[green]✓[/green] Ergebnisse gespeichert in {output_dir}")
    console.print(f"  Signifikante Peaks: {peaks_file}")
    
    return peaks_file


def print_summary(significant_peaks):
    """Drucke Zusammenfassung der gefundenen akustischen Emissionen."""
    console.print("\n" + "="*70)
    console.print("[bold green]ZUSAMMENFASSUNG: AKUSTISCHE EMISSIONEN DER PFLANZE[/bold green]")
    console.print("="*70)
    
    total_peaks = sum(len(peaks) for peaks in significant_peaks.values())
    
    if total_peaks == 0:
        console.print("\n[yellow]Keine signifikanten akustischen Emissionen gefunden.[/yellow]")
        console.print("Mögliche Gründe:")
        console.print("  - Pflanze erzeugt gerade keine akustischen Emissionen")
        console.print("  - Sensor-Empfindlichkeit zu niedrig")
        console.print("  - Umgebungsgeräusche überdecken die Signale")
        console.print("\nEmpfehlungen:")
        console.print("  - Messung zu einem anderen Zeitpunkt wiederholen")
        console.print("  - Sensor-Kopplung verbessern (besserer Kontakt)")
        console.print("  - Verstärkung erhöhen (LM358 Gain anpassen)")
    else:
        console.print(f"\n[bold cyan]Gefundene akustische Emissionen: {total_peaks} signifikante Peaks[/bold cyan]\n")
        
        for ch, peaks in significant_peaks.items():
            if not peaks:
                continue
            
            table = Table(title=f"Kanal {ch}", show_header=True, header_style="bold magenta")
            table.add_column("Frequenz (Hz)", style="cyan", justify="right")
            table.add_column("Amplitude (dB)", style="green", justify="right")
            table.add_column("Prominenz (dB)", style="yellow", justify="right")
            table.add_column("SNR (dB)", style="blue", justify="right")
            table.add_column("Q-Faktor", style="magenta", justify="right")
            table.add_column("Label", style="white")
            
            for peak in sorted(peaks, key=lambda p: p.frequency_hz):
                table.add_row(
                    f"{peak.frequency_hz:.1f}",
                    f"{peak.amplitude_db:.1f}",
                    f"{peak.prominence_db:.1f}",
                    f"{peak.snr_db:.1f}",
                    f"{peak.q_factor:.1f}",
                    peak.plausibility_label,
                )
            
            console.print(table)
            console.print()
        
        console.print("[bold]Interpretation:[/bold]")
        console.print("  - Hohe Q-Faktoren (>10) deuten auf schmale Resonanzen hin")
        console.print("  - Frequenzen im Bereich 20-100 kHz sind typisch für Pflanzen-AE")
        console.print("  - Signale auf beiden Kanälen sind wahrscheinlicher echt")
        console.print("  - 'plausible_mechanical' = wahrscheinlich echte AE")
    
    console.print("="*70)


def main():
    """Hauptprogramm."""
    console.print("\n[bold blue]╔═══════════════════════════════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║  AUTOMATISCHE MESSUNG AKUSTISCHER EMISSIONEN EINER PFLANZE   ║[/bold blue]")
    console.print("[bold blue]╚═══════════════════════════════════════════════════════════════╝[/bold blue]\n")
    
    # Lade Konfiguration
    config_path = Path(__file__).parent / "configs" / "experiment_piezo_stainless.yaml"
    if not config_path.exists():
        console.print(f"[red]Fehler: Konfigurationsdatei nicht gefunden: {config_path}[/red]")
        sys.exit(1)
    
    base_config = load_config(config_path)
    ae_config = PlantAECalibration(base_config).config
    
    # Verbinde mit Oszilloskop
    console.print(f"[cyan]Verbinde mit Oszilloskop: {ae_config.instrument.visa_resource}[/cyan]")
    
    try:
        with InstrumentConnection(ae_config) as conn:
            idn = conn.query("*IDN?")
            console.print(f"[green]✓[/green] Verbunden: {idn}\n")
            
            # Optimiere Einstellungen
            optimize_oscilloscope_settings(conn, ae_config)
            
            # Ausgabe-Verzeichnis
            output_dir = Path(__file__).parent / "data" / "plant_ae" / datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Baseline-Messung
            console.print("\n[bold]SCHRITT 1: BASELINE-MESSUNG[/bold]")
            console.print("  (Umgebungsrauschen ohne Pflanze)")
            console.print("  [yellow]Starte in 3 Sekunden...[/yellow]")
            time.sleep(3)
            baseline_captures = acquire_baseline(conn, ae_config, n_captures=10)
            
            # Aktive Messung
            console.print("\n[bold]SCHRITT 2: AKTIVE MESSUNG[/bold]")
            console.print("  (Mit Pflanze, mögliche akustische Emissionen)")
            console.print("  [yellow]Starte in 3 Sekunden...[/yellow]")
            time.sleep(3)
            active_captures = acquire_active(conn, ae_config, n_captures=20)
            
            # Analyse
            console.print("\n[bold]SCHRITT 3: ANALYSE[/bold]")
            baseline_results = analyze_captures(baseline_captures, ae_config, "Baseline")
            active_results = analyze_captures(active_captures, ae_config, "Aktive Messung")
            
            # Vergleich
            significant_peaks = compare_baseline_vs_active(baseline_results, active_results, ae_config)
            
            # Ergebnisse speichern
            all_captures = baseline_captures + active_captures
            save_results(all_captures, {**baseline_results, **active_results}, significant_peaks, output_dir)
            
            # Zusammenfassung
            print_summary(significant_peaks)
            
    except Exception as e:
        console.print(f"\n[red]Fehler: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    console.print("\n[bold green]✓ Messung abgeschlossen![/bold green]\n")


if __name__ == "__main__":
    main()
