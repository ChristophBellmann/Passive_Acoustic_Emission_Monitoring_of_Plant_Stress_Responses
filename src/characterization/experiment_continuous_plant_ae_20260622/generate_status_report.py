#!/usr/bin/env python3
"""
Automatische Dokumentation für kontinuierliche Pflanzen-AE-Charakterisierung.

Dieses Skript erstellt automatisch eine umfassende Dokumentation des aktuellen
Experimentstatus basierend auf den gesammelten Daten.

Erwartetes Schema (frame_characterization.jsonl, Phase 2):
  {
    "sequence": int,
    "timestamp_utc": str,
    "timestamp_local": str,
    "light_phase": "day"|"night",
    "soil_moisture_percent": float|None,
    "soil_moisture_median_percent": float|None,
    "pump_state": str,
    "watering_script_state": str,
    "band_energy": [[ch1_band0..19], [ch3_..], [ch4_..]],  # 3 × 20 floats
    "peaks": {"1": [{"frequency_hz": float, "prominence_db": float}, ...],
              "3": [...], "4": [...]},                       # CH2 disabled
    "rolling_event_count": int
  }
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import numpy as np


def load_jsonl(filepath: Path) -> List[Dict]:
    """Lade JSONL-Datei und gebe Liste von Dictionaries zurück."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def load_manifest(session_dir: Path) -> Dict:
    """Lade Manifest-Datei."""
    manifest_path = session_dir / "manifest.json"
    with open(manifest_path, 'r') as f:
        return json.load(f)


def analyze_frames(frames: List[Dict]) -> Dict[str, Any]:
    """Analysiere Frame-Charakterisierungen gegen das echte Phase-2-Schema."""
    if not frames:
        return {"count": 0}

    total_frames = len(frames)

    # Rolling events (aus dem echten Schema)
    rolling_events = [f for f in frames if f.get('rolling_event_count', 0) > 0]
    total_rolling_events = sum(f.get('rolling_event_count', 0) for f in frames)

    # Peak-Statistiken pro Kanal
    channel_stats: Dict[str, Dict[str, list]] = {}
    for frame in frames:
        for ch_name, peaks in frame.get('peaks', {}).items():
            if ch_name not in channel_stats:
                channel_stats[ch_name] = {'peak_count': [], 'prominences': []}
            channel_stats[ch_name]['peak_count'].append(len(peaks))
            channel_stats[ch_name]['prominences'].extend(
                float(p['prominence_db']) for p in peaks
            )

    for ch_name, stats in channel_stats.items():
        for key in ('peak_count', 'prominences'):
            if stats[key]:
                stats[f'{key}_mean'] = float(np.mean(stats[key]))
                stats[f'{key}_std'] = float(np.std(stats[key]))
                stats[f'{key}_min'] = float(np.min(stats[key]))
                stats[f'{key}_max'] = float(np.max(stats[key]))

    # 20 × 5-kHz-Bänder über alle Kanäle
    freq_bands: Dict[int, Dict[str, list]] = {}
    for frame in frames:
        band_energy = frame.get('band_energy')
        if not band_energy:
            continue
        for band_index, band_values in enumerate(np.asarray(band_energy).T):
            if band_index not in freq_bands:
                freq_bands[band_index] = {'energies': []}
            freq_bands[band_index]['energies'].extend(float(v) for v in band_values)

    for band_index, stats in freq_bands.items():
        energies = stats['energies']
        if energies:
            stats['energy_mean'] = float(np.mean(energies))
            stats['energy_std'] = float(np.std(energies))
            stats['energy_db_mean'] = float(np.mean(10 * np.log10(np.maximum(energies, 1e-30))))

    return {
        'total_frames': total_frames,
        'frames_with_rolling_events': len(rolling_events),
        'total_rolling_events': total_rolling_events,
        'channel_stats': channel_stats,
        'freq_bands': freq_bands,
    }


def analyze_environment(env_data: List[Dict]) -> Dict[str, Any]:
    """Analysiere Umgebungsdaten."""
    if not env_data:
        return {"count": 0}
    
    soil_moisture = [e.get('soil_moisture_percent') for e in env_data 
                     if e.get('soil_moisture_percent') is not None]
    
    return {
        'count': len(env_data),
        'soil_moisture_mean': np.mean(soil_moisture) if soil_moisture else None,
        'soil_moisture_min': np.min(soil_moisture) if soil_moisture else None,
        'soil_moisture_max': np.max(soil_moisture) if soil_moisture else None,
        'time_range': {
            'start': env_data[0].get('timestamp_utc'),
            'end': env_data[-1].get('timestamp_utc')
        }
    }


def analyze_events(events: List[Dict]) -> Dict[str, Any]:
    """Analysiere Experiment-Events.

    Echtes Schema (Phase 2): events haben einen 'event' Key, nicht 'type'.
    Beispiel: {"timestamp_utc": ..., "event": "oscilloscope_connected", ...}
    """
    if not events:
        return {"count": 0}

    event_types: Dict[str, int] = {}
    for event in events:
        # Phase 2 schema has 'event' key, older/scientific_report has 'type'
        event_type = event.get('event') or event.get('type') or 'unknown'
        event_types[event_type] = event_types.get(event_type, 0) + 1

    return {
        'total': len(events),
        'by_type': event_types,
        'time_range': {
            'start': events[0].get('timestamp_utc'),
            'end': events[-1].get('timestamp_utc'),
        },
    }


def generate_report(
    manifest: Dict,
    frame_analysis: Dict,
    env_analysis: Dict,
    event_analysis: Dict,
    output_path: Path
) -> None:
    """Generiere Markdown-Bericht."""
    
    # Berechne Laufzeit
    started = datetime.fromisoformat(manifest['started_utc'].replace('Z', '+00:00'))
    now = datetime.now(started.tzinfo)
    runtime = now - started
    runtime_minutes = runtime.total_seconds() / 60
    
    report = []
    report.append("# Continuous Plant AE Characterization - Status Report")
    report.append("")
    report.append(f"**Generiert:** {now.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"**Experiment:** {manifest['experiment']['name']}")
    report.append(f"**Run ID:** {manifest['run_id']}")
    report.append(f"**Status:** {manifest['status']}")
    report.append(f"**Laufzeit:** {runtime_minutes:.1f} Minuten ({runtime})")
    report.append("")
    
    # Konfiguration
    report.append("## Konfiguration")
    report.append("")
    report.append("### Experiment")
    report.append(f"- **Zeitzone:** {manifest['experiment']['timezone']}")
    report.append(f"- **Tag-Start:** {manifest['experiment']['day_start_hour']}:00")
    report.append(f"- **Nacht-Start:** {manifest['experiment']['night_start_hour']}:00")
    report.append("")
    
    report.append("### Oszilloskop-Einstellungen")
    scope_settings = manifest.get('verified_scope_settings', {})
    report.append(f"- **Sample-Rate:** {scope_settings.get('sample_rate_hz', 0) / 1e6:.1f} MSa/s")
    report.append(f"- **Memory Depth:** {scope_settings.get('memory_depth', 'N/A')}")
    report.append(f"- **Zeitbasis:** {scope_settings.get('horizontal_scale_s_per_div', 0) * 1000:.1f} ms/div")
    report.append(f"- **Trigger-Modus:** {scope_settings.get('trigger_mode', 'N/A')}")
    report.append(f"- **Trigger-Quelle:** {scope_settings.get('trigger_source', 'N/A')}")
    report.append(f"- **Trigger-Level:** {scope_settings.get('trigger_level_v', 0) * 1000:.1f} mV")
    report.append("")
    
    report.append("### Monitoring")
    monitor_config = manifest['configuration']['monitor']
    report.append(f"- **PSD-Snapshot-Intervall:** {monitor_config.get('psd_snapshot_interval_minutes', 0)} Minuten")
    report.append(f"- **PSD-Snapshot-Window:** {monitor_config.get('psd_snapshot_window_frames', 0)} Frames")
    report.append(f"- **Dashboard-Intervall:** {monitor_config.get('dashboard_interval_minutes', 0)} Minuten")
    report.append("")
    
    # Frame-Analyse
    report.append("## Frame-Analyse")
    report.append("")
    report.append(f"- **Total Frames:** {frame_analysis.get('total_frames', 0)}")
    report.append(f"- **Frames mit Rolling-Events:** {frame_analysis.get('frames_with_rolling_events', 0)}")
    report.append(f"- **Total Rolling-Events:** {frame_analysis.get('total_rolling_events', 0)}")
    report.append("")

    # Kanal-Statistiken (Peaks pro Kanal, Phase-2-Setup CH1+CH3+CH4)
    if frame_analysis.get('channel_stats'):
        report.append("### Kanal-Statistiken (Peaks)")
        report.append("")
        report.append("| Kanal | Peaks/Frame (mean) | Prominenz mean (dB) | Prominenz range (dB) |")
        report.append("|-------|--------------------|---------------------|----------------------|")

        for ch_name, stats in sorted(frame_analysis['channel_stats'].items()):
            pc_mean = stats.get('peak_count_mean', 0)
            pr_mean = stats.get('prominences_mean', 0)
            pr_min = stats.get('prominences_min', 0)
            pr_max = stats.get('prominences_max', 0)
            report.append(f"| CH{ch_name} | {pc_mean:.1f} | {pr_mean:.1f} | {pr_min:.0f}–{pr_max:.0f} |")

        report.append("")

    # Frequenzband-Analyse (20 × 5 kHz Bänder)
    if frame_analysis.get('freq_bands'):
        report.append("### Frequenzband-Energie (5 kHz Bänder, alle Kanäle)")
        report.append("")
        report.append("| Band | Energie (mean) | dB mean |")
        report.append("|------|----------------|---------|")

        for band_index in sorted(frame_analysis['freq_bands'].keys()):
            stats = frame_analysis['freq_bands'][band_index]
            e_mean = stats.get('energy_mean', 0)
            db_mean = stats.get('energy_db_mean', 0)
            report.append(f"| {band_index*5}–{(band_index+1)*5} kHz | {e_mean:.2e} | {db_mean:.1f} |")

        report.append("")
    
    # Umgebungsdaten
    if env_analysis.get('count', 0) > 0:
        report.append("## Umgebungsdaten")
        report.append("")
        report.append(f"- **Datenpunkte:** {env_analysis['count']}")
        if env_analysis.get('soil_moisture_mean') is not None:
            report.append(f"- **Bodenfeuchte (mean):** {env_analysis['soil_moisture_mean']:.1f}%")
            report.append(f"- **Bodenfeuchte (min):** {env_analysis['soil_moisture_min']:.1f}%")
            report.append(f"- **Bodenfeuchte (max):** {env_analysis['soil_moisture_max']:.1f}%")
        report.append("")
    
    # Events
    if event_analysis.get('total', 0) > 0:
        report.append("## Experiment-Events")
        report.append("")
        report.append(f"- **Total Events:** {event_analysis['total']}")
        report.append("")
        report.append("### Event-Typen")
        report.append("")
        for event_type, count in sorted(event_analysis.get('by_type', {}).items()):
            report.append(f"- **{event_type}:** {count}")
        report.append("")
    
    # Zusammenfassung
    report.append("## Zusammenfassung")
    report.append("")
    report.append(f"Das Experiment läuft seit {runtime_minutes:.1f} Minuten und hat {frame_analysis.get('total_frames', 0)} Frames charakterisiert. ")

    if frame_analysis.get('total_rolling_events', 0) > 0:
        report.append(f"Es wurden {frame_analysis['total_rolling_events']} Rolling-Events detektiert. ")
    else:
        report.append("Es wurden keine Rolling-Events detektiert (Hintergrund-Rauschen, keine signifikanten Änderungen). ")

    if env_analysis.get('soil_moisture_mean') is not None:
        report.append(f"Die durchschnittliche Bodenfeuchte beträgt {env_analysis['soil_moisture_mean']:.1f}%.")

    report.append("")
    report.append("---")
    report.append("")
    report.append(f"*Report automatisch generiert um {now.strftime('%Y-%m-%d %H:%M:%S')}*")

    # Schreibe Bericht
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))

    print(f"Report generiert: {output_path}")


def main():
    """Hauptfunktion."""
    # Finde neueste Session
    data_dir = Path(__file__).parent.parent / "data" / "continuous_plant_ae_20260622"
    sessions = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name != "logs"])

    if not sessions:
        print("Keine Sessions gefunden!")
        sys.exit(1)

    latest_session = sessions[-1]
    print(f"Analysiere Session: {latest_session.name}")

    # Lade Daten
    manifest = load_manifest(latest_session)
    frames = load_jsonl(latest_session / "frame_characterization.jsonl")
    env_data = load_jsonl(latest_session / "environment.jsonl")
    events = load_jsonl(latest_session / "experiment_events.jsonl")

    # Analysiere Daten
    frame_analysis = analyze_frames(frames)
    env_analysis = analyze_environment(env_data)
    event_analysis = analyze_events(events)

    # Generiere Report
    output_path = latest_session / "status_report.md"
    generate_report(manifest, frame_analysis, env_analysis, event_analysis, output_path)

    print(f"\nAnalyse abgeschlossen:")
    print(f"  Frames: {frame_analysis.get('total_frames', 0)}")
    print(f"  Rolling-Events: {frame_analysis.get('total_rolling_events', 0)}")
    print(f"  Umweltdaten: {env_analysis.get('count', 0)}")


if __name__ == "__main__":
    main()
