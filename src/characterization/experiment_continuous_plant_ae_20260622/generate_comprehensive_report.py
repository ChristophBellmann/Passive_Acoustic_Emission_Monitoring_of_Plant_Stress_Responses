#!/usr/bin/env python3
"""
Erweiterte Dokumentation mit Visualisierungen und Event-Analyse.
Generiert PDF-Bericht mit Plots und detaillierter Analyse.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd


def load_jsonl(filepath: Path) -> List[Dict]:
    """Lade JSONL-Datei."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_manifest(session_dir: Path) -> Dict:
    """Lade Manifest."""
    with open(session_dir / "manifest.json", 'r') as f:
        return json.load(f)


def analyze_events(events: List[Dict]) -> pd.DataFrame:
    """Analysiere Events und erstelle DataFrame."""
    if not events:
        return pd.DataFrame()
    
    df = pd.DataFrame(events)
    
    # Konvertiere Timestamps
    if 'timestamp_utc' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp_utc'])
        df = df.sort_values('timestamp')
    
    return df


def plot_timeline(events_df: pd.DataFrame, pdf: PdfPages) -> None:
    """Plot Event-Timeline."""
    if events_df.empty:
        return
    
    fig, ax = plt.subplots(figsize=(12, 4))
    
    # Event-Typen zählen (verwende 'event' statt 'type')
    event_types = events_df['event'].value_counts()
    
    # Timeline erstellen
    for event_type in event_types.index:
        type_events = events_df[events_df['event'] == event_type]
        ax.scatter(type_events['timestamp'], 
                  [event_types.index.tolist().index(event_type)] * len(type_events),
                  label=event_type, alpha=0.6, s=50)
    
    ax.set_yticks(range(len(event_types)))
    ax.set_yticklabels(event_types.index)
    ax.set_xlabel('Time')
    ax.set_ylabel('Event Type')
    ax.set_title('Event Timeline')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()


def plot_frequency_analysis(frames: List[Dict], pdf: PdfPages) -> None:
    """Plot Frequenzband-Analyse über Zeit."""
    if not frames:
        return
    
    # Extrahiere Frequenzbänder
    timestamps = []
    band_energies = {}
    
    for frame in frames:
        ts = pd.to_datetime(frame.get('timestamp_utc'))
        timestamps.append(ts)
        
        for band_name, band_data in frame.get('frequency_bands', {}).items():
            if band_name not in band_energies:
                band_energies[band_name] = []
            band_energies[band_name].append(band_data.get('energy', 0))
    
    if not timestamps or not band_energies:
        print("  No frequency band data available, skipping...")
        return
    
    # Plot 1: Heatmap der Frequenzbänder
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Erstelle Matrix
    bands = sorted(band_energies.keys())
    matrix = np.array([band_energies[band] for band in bands])
    
    # Heatmap
    im = ax.imshow(matrix, aspect='auto', cmap='viridis', 
                   extent=[mdates.date2num(timestamps[0]), 
                           mdates.date2num(timestamps[-1]),
                           -0.5, len(bands)-0.5])
    
    ax.set_yticks(range(len(bands)))
    ax.set_yticklabels(bands)
    ax.set_xlabel('Time')
    ax.set_ylabel('Frequency Band')
    ax.set_title('Frequency Band Energy Over Time')
    
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Energy')
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()
    
    # Plot 2: Top Frequenzbänder über Zeit
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Top 5 energie-reichste Bänder
    total_energies = {band: sum(energies) for band, energies in band_energies.items()}
    top_bands = sorted(total_energies.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for band_name, _ in top_bands:
        ax.plot(timestamps, band_energies[band_name], label=band_name, linewidth=2)
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Energy')
    ax.set_title('Top 5 Frequency Bands Over Time')
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()


def plot_channel_statistics(frames: List[Dict], pdf: PdfPages) -> None:
    """Plot Kanal-Statistiken."""
    if not frames:
        return
    
    # Extrahiere Kanal-Daten
    timestamps = []
    channel_rms = {}
    channel_peaks = {}
    
    for frame in frames:
        ts = pd.to_datetime(frame.get('timestamp_utc'))
        timestamps.append(ts)
        
        for ch_name, ch_data in frame.get('channels', {}).items():
            if ch_name not in channel_rms:
                channel_rms[ch_name] = []
                channel_peaks[ch_name] = []
            
            channel_rms[ch_name].append(ch_data.get('rms_mv', 0))
            channel_peaks[ch_name].append(ch_data.get('peak_mv', 0))
    
    if not timestamps or not channel_rms:
        print("  No channel data available, skipping...")
        return
    
    # Plot 1: RMS pro Kanal
    fig, axes = plt.subplots(len(channel_rms), 1, figsize=(12, 3*len(channel_rms)))
    if len(channel_rms) == 1:
        axes = [axes]
    
    for ax, (ch_name, rms_values) in zip(axes, channel_rms.items()):
        ax.plot(timestamps, rms_values, linewidth=2, color='blue')
        ax.set_ylabel('RMS (mV)')
        ax.set_title(f'{ch_name} - RMS Voltage')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    axes[-1].set_xlabel('Time')
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()
    
    # Plot 2: Peak pro Kanal
    fig, axes = plt.subplots(len(channel_peaks), 1, figsize=(12, 3*len(channel_peaks)))
    if len(channel_peaks) == 1:
        axes = [axes]
    
    for ax, (ch_name, peak_values) in zip(axes, channel_peaks.items()):
        ax.plot(timestamps, peak_values, linewidth=2, color='red')
        ax.set_ylabel('Peak (mV)')
        ax.set_title(f'{ch_name} - Peak Voltage')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    axes[-1].set_xlabel('Time')
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()


def plot_soil_moisture(env_data: List[Dict], pdf: PdfPages) -> None:
    """Plot Bodenfeuchte über Zeit."""
    if not env_data:
        return
    
    timestamps = []
    moisture = []
    
    for entry in env_data:
        if 'soil_moisture_percent' in entry and entry['soil_moisture_percent'] is not None:
            timestamps.append(pd.to_datetime(entry['timestamp_utc']))
            moisture.append(entry['soil_moisture_percent'])
    
    if not timestamps:
        return
    
    fig, ax = plt.subplots(figsize=(12, 4))
    
    ax.plot(timestamps, moisture, linewidth=2, color='green', marker='o', markersize=4)
    ax.set_xlabel('Time')
    ax.set_ylabel('Soil Moisture (%)')
    ax.set_title('Soil Moisture Over Time')
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    # Füge Referenzlinien hinzu
    ax.axhline(y=30, color='orange', linestyle='--', alpha=0.5, label='30% threshold')
    ax.legend()
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()


def plot_spectral_detections(events: List[Dict], pdf: PdfPages) -> None:
    """Plot detaillierte Analyse der spektralen Detections."""
    # Extrahiere alle Detections aus spectral_change Events
    all_detections = []
    
    for event in events:
        if event.get('event') == 'spectral_change' and 'detections' in event:
            for detection in event['detections']:
                detection_copy = detection.copy()
                detection_copy['timestamp_utc'] = event['timestamp_utc']
                detection_copy['sequence'] = event.get('sequence', 0)
                all_detections.append(detection_copy)
    
    if not all_detections:
        return
    
    df = pd.DataFrame(all_detections)
    df['timestamp'] = pd.to_datetime(df['timestamp_utc'])
    
    # Plot 1: Frequenzverteilung pro Kanal
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for ch_num, ax in enumerate(axes, 1):
        ch_detections = df[df['channel'] == ch_num]
        
        if len(ch_detections) > 0:
            ax.hist(ch_detections['frequency_hz'] / 1000, bins=50, alpha=0.7, color='blue')
            ax.set_xlabel('Frequency (kHz)')
            ax.set_ylabel('Count')
            ax.set_title(f'CH{ch_num} - Frequency Distribution')
            ax.grid(True, alpha=0.3)
            
            # Markiere 39 kHz Bereich
            ax.axvline(x=39, color='red', linestyle='--', alpha=0.5, label='39 kHz')
            ax.legend()
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()
    
    # Plot 2: 39 kHz Bereich über Zeit (CH3 und CH4 — Phase 2; CH2 disabled)
    fig, ax = plt.subplots(figsize=(12, 5))

    for ch_num in [3, 4]:  # CH2 disabled (hardware fault)
        ch_detections = df[(df['channel'] == ch_num) & 
                          (df['frequency_hz'] >= 38000) & 
                          (df['frequency_hz'] <= 40000)]
        
        if len(ch_detections) > 0:
            ax.scatter(ch_detections['timestamp'], 
                      ch_detections['frequency_hz'] / 1000,
                      label=f'CH{ch_num}', alpha=0.6, s=50)
    
    ax.set_xlabel('Time')
    ax.set_ylabel('Frequency (kHz)')
    ax.set_title('39 kHz Region - CH3 and CH4 Over Time (Phase 2 setup, CH2 disabled)')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()
    
    # Plot 3: Prominence vs Frequency
    fig, ax = plt.subplots(figsize=(12, 5))

    for ch_num in [1, 3, 4]:  # CH2 disabled (hardware fault)
        ch_detections = df[df['channel'] == ch_num]
        if len(ch_detections) > 0:
            ax.scatter(ch_detections['frequency_hz'] / 1000,
                      ch_detections['prominence_db'],
                      label=f'CH{ch_num}', alpha=0.5, s=30)
    
    ax.set_xlabel('Frequency (kHz)')
    ax.set_ylabel('Prominence (dB)')
    ax.set_title('Detection Prominence vs Frequency')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Markiere 39 kHz Bereich
    ax.axvspan(38, 40, alpha=0.2, color='red', label='39 kHz region')
    ax.legend()
    
    plt.tight_layout()
    pdf.savefig(fig)
    plt.close()


def generate_text_report(
    manifest: Dict,
    frames: List[Dict],
    events: List[Dict],
    events_df: pd.DataFrame,
    env_data: List[Dict]
) -> str:
    """Generiere Text-Bericht."""
    started = datetime.fromisoformat(manifest['started_utc'].replace('Z', '+00:00'))
    now = datetime.now(started.tzinfo)
    runtime = now - started
    runtime_minutes = runtime.total_seconds() / 60
    
    report = []
    report.append("# Continuous Plant AE Characterization - Comprehensive Report")
    report.append("")
    report.append(f"**Generated:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Experiment:** {manifest['experiment']['name']}")
    report.append(f"**Run ID:** {manifest['run_id']}")
    report.append(f"**Status:** {manifest['status']}")
    report.append(f"**Runtime:** {runtime_minutes:.1f} minutes ({runtime})")
    report.append("")
    
    # Configuration
    report.append("## Configuration")
    report.append("")
    scope_settings = manifest.get('verified_scope_settings', {})
    report.append(f"- **Sample Rate:** {scope_settings.get('sample_rate_hz', 0) / 1e6:.1f} MSa/s")
    report.append(f"- **Time Base:** {scope_settings.get('horizontal_scale_s_per_div', 0) * 1000:.1f} ms/div")
    report.append(f"- **Trigger:** {scope_settings.get('trigger_mode', 'N/A')} on {scope_settings.get('trigger_source', 'N/A')}")
    report.append("")
    
    # Frame Analysis
    report.append("## Frame Analysis")
    report.append("")
    report.append(f"- **Total Frames:** {len(frames)}")
    
    if frames:
        total_events = sum(f.get('event_count', 0) for f in frames)
        frames_with_events = sum(1 for f in frames if f.get('event_count', 0) > 0)
        report.append(f"- **Frames with Events:** {frames_with_events}")
        report.append(f"- **Total Events:** {total_events}")
    report.append("")
    
    # Event Analysis
    if not events_df.empty:
        report.append("## Event Analysis")
        report.append("")
        report.append(f"- **Total Events:** {len(events_df)}")
        report.append("")
        
        if 'event' in events_df.columns:
            report.append("### Event Types")
            report.append("")
            for event_type, count in events_df['event'].value_counts().items():
                report.append(f"- **{event_type}:** {count}")
            report.append("")
        
        # Spectral Change Analysis
        spectral_events = [e for e in events if e.get('event') == 'spectral_change']
        if spectral_events:
            report.append("### Spectral Changes")
            report.append("")
            report.append(f"- **Total spectral change events:** {len(spectral_events)}")
            
            # Extrahiere alle Detections
            all_detections = []
            for event in spectral_events:
                if 'detections' in event:
                    all_detections.extend(event['detections'])
            
            if all_detections:
                report.append(f"- **Total peak detections:** {len(all_detections)}")
                report.append("")
                
                # Analysiere nach Kanal
                ch_counts = {}
                for det in all_detections:
                    ch = det.get('channel', 0)
                    ch_counts[ch] = ch_counts.get(ch, 0) + 1
                
                report.append("#### Detections per Channel")
                report.append("")
                for ch in sorted(ch_counts.keys()):
                    report.append(f"- **CH{ch}:** {ch_counts[ch]} detections")
                report.append("")
                
                # 39 kHz Analyse
                detections_39k = [d for d in all_detections 
                                 if 38000 <= d.get('frequency_hz', 0) <= 40000]
                if detections_39k:
                    report.append("#### 39 kHz Region Analysis")
                    report.append("")
                    report.append(f"- **Detections in 38-40 kHz range:** {len(detections_39k)}")
                    
                    ch_39k = {}
                    for det in detections_39k:
                        ch = det.get('channel', 0)
                        ch_39k[ch] = ch_39k.get(ch, 0) + 1
                    
                    for ch in sorted(ch_39k.keys()):
                        report.append(f"- **CH{ch}:** {ch_39k[ch]} detections")
                    
                    report.append("")
                    report.append("**Note:** Recurring activity in the 39 kHz range has been observed, ")
                    report.append("particularly on CH3 and CH4 (Phase 2 setup; CH2 disabled due to hardware fault, replaced by CH4 on 2026-06-22). This may indicate biological activity ")
                    report.append("or environmental interference. Further investigation is needed.")
                    report.append("")
    
    # Soil Moisture
    if env_data:
        moisture_values = [e.get('soil_moisture_percent') for e in env_data 
                          if e.get('soil_moisture_percent') is not None]
        if moisture_values:
            report.append("## Soil Moisture")
            report.append("")
            report.append(f"- **Current:** {moisture_values[-1]:.1f}%")
            report.append(f"- **Average:** {np.mean(moisture_values):.1f}%")
            report.append(f"- **Min:** {np.min(moisture_values):.1f}%")
            report.append(f"- **Max:** {np.max(moisture_values):.1f}%")
            report.append("")
    
    # Summary
    report.append("## Summary")
    report.append("")
    report.append(f"The experiment has been running for {runtime_minutes:.1f} minutes ")
    report.append(f"and has characterized {len(frames)} frames. ")
    
    if frames:
        total_events = sum(f.get('event_count', 0) for f in frames)
        if total_events > 0:
            report.append(f"A total of {total_events} acoustic events were detected. ")
        else:
            report.append("No acoustic events were detected so far. ")
    
    if env_data:
        moisture_values = [e.get('soil_moisture_percent') for e in env_data 
                          if e.get('soil_moisture_percent') is not None]
        if moisture_values:
            report.append(f"The average soil moisture is {np.mean(moisture_values):.1f}%.")
    
    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Report automatically generated at {now.strftime('%Y-%m-%d %H:%M:%S')}*")
    
    return '\n'.join(report)


def main():
    """Hauptfunktion."""
    # Finde neueste Session
    data_dir = Path(__file__).parent.parent / "data" / "continuous_plant_ae_20260622"
    sessions = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name != "logs"])
    
    if not sessions:
        print("No sessions found!")
        sys.exit(1)
    
    latest_session = sessions[-1]
    print(f"Analyzing session: {latest_session.name}")
    
    # Lade Daten
    manifest = load_manifest(latest_session)
    frames = load_jsonl(latest_session / "frame_characterization.jsonl")
    env_data = load_jsonl(latest_session / "environment.jsonl")
    events = load_jsonl(latest_session / "experiment_events.jsonl")
    
    # Analysiere Events
    events_df = analyze_events(events)
    
    # Erstelle PDF
    pdf_path = latest_session / "comprehensive_report.pdf"
    
    with PdfPages(pdf_path) as pdf:
        # Plot 1: Event Timeline
        print("Creating event timeline...")
        plot_timeline(events_df, pdf)
        
        # Plot 2: Frequency Analysis
        print("Creating frequency analysis...")
        plot_frequency_analysis(frames, pdf)
        
        # Plot 3: Channel Statistics
        print("Creating channel statistics...")
        plot_channel_statistics(frames, pdf)
        
        # Plot 4: Soil Moisture
        print("Creating soil moisture plot...")
        plot_soil_moisture(env_data, pdf)
        
        # Plot 5: Spectral Detections (39 kHz analysis)
        print("Creating spectral detection analysis...")
        plot_spectral_detections(events, pdf)
    
    print(f"PDF created: {pdf_path}")
    
    # Erstelle Text-Bericht
    report_text = generate_text_report(manifest, frames, events, events_df, env_data)
    report_path = latest_session / "comprehensive_report.md"
    
    with open(report_path, 'w') as f:
        f.write(report_text)
    
    print(f"Report created: {report_path}")
    
    # Konvertiere zu PDF
    import subprocess
    try:
        subprocess.run([
            'pandoc', str(report_path),
            '-o', str(report_path.with_suffix('.pdf')),
            '--pdf-engine=xelatex',
            '-V', 'geometry:margin=2.5cm'
        ], check=True)
        print(f"Text report PDF created: {report_path.with_suffix('.pdf')}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not convert to PDF: {e}")
        print("The markdown report is still available.")
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
