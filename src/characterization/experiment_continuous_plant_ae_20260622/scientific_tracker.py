#!/usr/bin/env python3
"""
Wissenschaftliches Tracking-System für Pflanzen-AE-Experiment.

Implementiert statistische Methoden zur Erkennung signifikanter Veränderungen
und erstellt reproduzierbare Reports mit vollständiger Methodik-Dokumentation.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from scipy import stats
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')


@dataclass
class StatisticalMetrics:
    """Statistische Metriken für ein Frequenzband/Kanal."""
    mean: float
    std: float
    median: float
    q25: float
    q75: float
    iqr: float
    min: float
    max: float
    n_samples: int
    timestamp: str


@dataclass
class FrequencyPeak:
    """Detektierter Frequenzpeak mit statistischen Eigenschaften."""
    frequency_hz: float
    amplitude_mv: float
    prominence_db: float
    channel: int
    first_seen: str
    last_seen: str
    occurrence_count: int
    mean_frequency: float
    std_frequency: float
    trend: str  # 'stable', 'drifting_up', 'drifting_down'


@dataclass
class TrackingState:
    """Gesamtzustand des Tracking-Systems."""
    experiment_start: str
    last_update: str
    baseline_established: bool
    baseline_duration_minutes: float
    channels: Dict[str, StatisticalMetrics]
    frequency_bands: Dict[str, StatisticalMetrics]
    persistent_peaks: List[FrequencyPeak]
    soil_moisture_stats: Optional[StatisticalMetrics]
    event_counts: Dict[str, int]


class ScientificTracker:
    """Wissenschaftliches Tracking-System mit statistischen Methoden."""
    
    def __init__(self, session_dir: Path, state_file: Optional[Path] = None):
        self.session_dir = session_dir
        self.state_file = state_file or (session_dir / "tracking_state.json")
        self.state = self._load_or_initialize_state()
        
        # Statistische Schwellenwerte (angepasst für 500 kHz Sample-Rate)
        self.SIGNIFICANCE_LEVEL = 0.05  # p-Wert für Signifikanztests
        self.DRIFT_THRESHOLD_STD = 2.0  # Anzahl Standardabweichungen für Drift
        self.MIN_OCCURRENCES = 5  # Mindestanzahl für persistenten Peak
        self.BASELINE_MINUTES = 30  # Mindestdauer für Baseline
        
        # Erweiterte Peak-Tracker-Parameter (aus config.yaml)
        self.PEAK_TRACKER_CONFIG = {
            'match_tolerance_hz': 500,
            'max_missed': 5,
            'min_points_for_drift': 12,
            'min_displacement_hz': 500,
            'min_slope_hz_per_second': 0.5,
            'min_r_squared': 0.8,
            'event_cooldown_frames': 30
        }
        
        # Persistent Peaks Konfiguration
        self.PERSISTENT_PEAKS_CONFIG = {
            'tolerance_hz': 500,
            'persistence_frames': 12,
            'cooldown_frames': 60,
            'bin_width_hz': 250
        }
        
        # Akquisitions-Profil
        self.ACQUISITION_PROFILE = {
            'profile': 'deep_memory_500k',
            'sample_rate_hz': 500000,
            'memory_depth': 300000,
            'chunk_points': 250000,
            'max_frequency_hz': 100000
        }
        
    def _load_or_initialize_state(self) -> TrackingState:
        """Lade oder initialisiere Tracking-Zustand."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                data = json.load(f)
                # Rekonstruiere Dataclasses
                state = TrackingState(
                    experiment_start=data['experiment_start'],
                    last_update=data['last_update'],
                    baseline_established=data['baseline_established'],
                    baseline_duration_minutes=data['baseline_duration_minutes'],
                    channels={k: StatisticalMetrics(**v) for k, v in data['channels'].items()},
                    frequency_bands={k: StatisticalMetrics(**v) for k, v in data['frequency_bands'].items()},
                    persistent_peaks=[FrequencyPeak(**p) for p in data['persistent_peaks']],
                    soil_moisture_stats=StatisticalMetrics(**data['soil_moisture_stats']) if data.get('soil_moisture_stats') else None,
                    event_counts=data.get('event_counts', {})
                )
                return state
        else:
            # Initialisiere neuen Zustand
            return TrackingState(
                experiment_start=datetime.now().isoformat(),
                last_update=datetime.now().isoformat(),
                baseline_established=False,
                baseline_duration_minutes=0.0,
                channels={},
                frequency_bands={},
                persistent_peaks=[],
                soil_moisture_stats=None,
                event_counts={}
            )
    
    def save_state(self) -> None:
        """Speichere aktuellen Zustand."""
        with open(self.state_file, 'w') as f:
            json.dump(asdict(self.state), f, indent=2)
    
    def update_from_data(self, frames: List[Dict], events: List[Dict], env_data: List[Dict]) -> Dict:
        """
        Aktualisiere Tracking-Zustand mit neuen Daten.
        
        Returns:
            Dict mit Änderungen und signifikanten Erkenntnissen
        """
        changes = {
            'timestamp': datetime.now().isoformat(),
            'significant_changes': [],
            'new_peaks': [],
            'lost_peaks': [],
            'drifts': [],
            'amplitude_changes': []
        }
        
        # Update Channel-Statistiken
        channel_changes = self._update_channel_statistics(frames)
        changes['amplitude_changes'].extend(channel_changes)
        
        # Update Frequency-Band-Statistiken
        band_changes = self._update_frequency_band_statistics(frames)
        
        # Update Persistent Peaks
        peak_changes = self._update_persistent_peaks(events)
        changes['new_peaks'].extend(peak_changes['new'])
        changes['lost_peaks'].extend(peak_changes['lost'])
        changes['drifts'].extend(peak_changes['drifts'])
        
        # Update Soil Moisture
        if env_data:
            self._update_soil_moisture(env_data)
        
        # Update Event Counts
        self._update_event_counts(events)
        
        # Check for significant changes
        changes['significant_changes'] = self._detect_significant_changes()
        
        # Update timestamp
        self.state.last_update = datetime.now().isoformat()
        
        # Check if baseline is established
        if not self.state.baseline_established:
            start_time = datetime.fromisoformat(self.state.experiment_start)
            elapsed = (datetime.now() - start_time).total_seconds() / 60
            if elapsed >= self.BASELINE_MINUTES:
                self.state.baseline_established = True
                self.state.baseline_duration_minutes = elapsed
        
        # Save state
        self.save_state()
        
        return changes
    
    def _update_channel_statistics(self, frames: List[Dict]) -> List[Dict]:
        """Aktualisiere Kanal-Statistiken und erkenne Änderungen."""
        changes = []
        
        for ch_name in ['CH1', 'CH3', 'CH4']:  # CH2 disabled (hardware fault)
            rms_values = []
            peak_values = []
            
            for frame in frames:
                if ch_name in frame.get('channels', {}):
                    ch_data = frame['channels'][ch_name]
                    if 'rms_mv' in ch_data:
                        rms_values.append(ch_data['rms_mv'])
                    if 'peak_mv' in ch_data:
                        peak_values.append(ch_data['peak_mv'])
            
            if rms_values:
                # Berechne neue Statistiken
                new_stats = StatisticalMetrics(
                    mean=np.mean(rms_values),
                    std=np.std(rms_values),
                    median=np.median(rms_values),
                    q25=np.percentile(rms_values, 25),
                    q75=np.percentile(rms_values, 75),
                    iqr=np.percentile(rms_values, 75) - np.percentile(rms_values, 25),
                    min=np.min(rms_values),
                    max=np.max(rms_values),
                    n_samples=len(rms_values),
                    timestamp=datetime.now().isoformat()
                )
                
                # Vergleiche mit vorherigen Statistiken
                if ch_name in self.state.channels:
                    old_stats = self.state.channels[ch_name]
                    
                    # T-Test für signifikante Änderung
                    if old_stats.n_samples > 1 and new_stats.n_samples > 1:
                        # Vereinfachter Test: Prüfe ob neue Mittelwert außerhalb ±2σ liegt
                        z_score = abs(new_stats.mean - old_stats.mean) / old_stats.std if old_stats.std > 0 else 0
                        
                        if z_score > self.DRIFT_THRESHOLD_STD:
                            change_pct = ((new_stats.mean - old_stats.mean) / old_stats.mean * 100) if old_stats.mean > 0 else 0
                            changes.append({
                                'channel': ch_name,
                                'metric': 'rms_mv',
                                'old_mean': old_stats.mean,
                                'new_mean': new_stats.mean,
                                'change_pct': change_pct,
                                'z_score': z_score,
                                'significant': z_score > self.DRIFT_THRESHOLD_STD
                            })
                
                # Update state
                self.state.channels[ch_name] = new_stats
        
        return changes
    
    def _update_frequency_band_statistics(self, frames: List[Dict]) -> List[Dict]:
        """Aktualisiere Frequenzband-Statistiken."""
        # Ähnlich wie Channel-Statistiken, aber für Frequenzbänder
        # Wird hier vereinfacht implementiert
        return []
    
    def _update_persistent_peaks(self, events: List[Dict]) -> Dict:
        """Aktualisiere persistente Peaks und erkenne neue/verlorene Peaks."""
        changes = {'new': [], 'lost': [], 'drifts': []}
        
        # Extrahiere alle Peak-Detections aus spectral_change Events
        all_detections = []
        for event in events:
            if event.get('event') == 'spectral_change' and 'detections' in event:
                for det in event['detections']:
                    # Nur new_peak Detections verarbeiten
                    if det.get('type') == 'new_peak':
                        det_copy = det.copy()
                        det_copy['timestamp'] = event['timestamp_utc']
                        all_detections.append(det_copy)
        
        if not all_detections:
            return changes
        
        # Gruppiere nach (channel, frequency_bin)
        # Verwende bin_width_hz aus Konfiguration (250 Hz für 500 kHz Sample-Rate)
        bin_width = self.PERSISTENT_PEAKS_CONFIG['bin_width_hz']
        peak_groups = {}
        
        for det in all_detections:
            ch = det.get('channel', 0)
            freq = det.get('frequency_hz', 0)
            
            # Stelle sicher, dass frequency_hz existiert
            if freq == 0:
                continue
            
            # Frequenz-Binning mit konfigurierter Breite
            freq_bin = round(freq / bin_width) * bin_width
            key = (ch, freq_bin)
            
            if key not in peak_groups:
                peak_groups[key] = []
            peak_groups[key].append(det)
        
        # Aktualisiere persistente Peaks
        # Verwende persistence_frames aus Konfiguration (12 Frames)
        min_occurrences = self.PERSISTENT_PEAKS_CONFIG['persistence_frames']
        
        for (ch, freq_bin), detections in peak_groups.items():
            if len(detections) >= min_occurrences:
                # Berechne Statistiken
                freqs = [d.get('frequency_hz', 0) for d in detections if d.get('frequency_hz', 0) > 0]
                amps = [d.get('prominence_db', 0) for d in detections]
                
                if not freqs:
                    continue
                
                mean_freq = np.mean(freqs)
                std_freq = np.std(freqs)
                
                # Bestimme Trend mit erweiterten Kriterien
                if std_freq < 100:
                    trend = 'stable'
                elif len(freqs) >= self.PEAK_TRACKER_CONFIG['min_points_for_drift']:
                    # Lineare Regression für Trend mit strengeren Kriterien
                    x = np.arange(len(freqs))
                    slope, intercept, r_value, p_value, std_err = stats.linregress(x, freqs)
                    
                    # Berechne R-squared
                    r_squared = r_value ** 2
                    
                    # Berechne Displacement
                    displacement = abs(freqs[-1] - freqs[0])
                    
                    # Prüfe ob Drift signifikant ist
                    if (displacement >= self.PEAK_TRACKER_CONFIG['min_displacement_hz'] and
                        abs(slope) >= self.PEAK_TRACKER_CONFIG['min_slope_hz_per_second'] and
                        r_squared >= self.PEAK_TRACKER_CONFIG['min_r_squared']):
                        if slope > 0:
                            trend = 'drifting_up'
                        else:
                            trend = 'drifting_down'
                    else:
                        trend = 'stable'
                else:
                    trend = 'stable'
                
                # Prüfe ob Peak bereits existiert
                # Verwende tolerance_hz aus Konfiguration (500 Hz)
                tolerance = self.PERSISTENT_PEAKS_CONFIG['tolerance_hz']
                existing_peak = None
                for peak in self.state.persistent_peaks:
                    if peak.channel == ch and abs(peak.mean_frequency - mean_freq) < tolerance:
                        existing_peak = peak
                        break
                
                if existing_peak:
                    # Update existing peak
                    existing_peak.last_seen = detections[-1]['timestamp']
                    existing_peak.occurrence_count += len(detections)
                    existing_peak.mean_frequency = mean_freq
                    existing_peak.std_frequency = std_freq
                    existing_peak.trend = trend
                    
                    if trend != 'stable':
                        changes['drifts'].append({
                            'channel': ch,
                            'frequency_hz': mean_freq,
                            'trend': trend,
                            'occurrences': existing_peak.occurrence_count,
                            'slope_hz_per_s': slope if 'slope' in locals() else 0,
                            'r_squared': r_squared if 'r_squared' in locals() else 0
                        })
                else:
                    # New persistent peak
                    new_peak = FrequencyPeak(
                        frequency_hz=mean_freq,
                        amplitude_mv=np.mean(amps) if amps else 0,
                        prominence_db=np.max(amps) if amps else 0,
                        channel=ch,
                        first_seen=detections[0]['timestamp'],
                        last_seen=detections[-1]['timestamp'],
                        occurrence_count=len(detections),
                        mean_frequency=mean_freq,
                        std_frequency=std_freq,
                        trend=trend
                    )
                    self.state.persistent_peaks.append(new_peak)
                    changes['new'].append({
                        'channel': ch,
                        'frequency_hz': mean_freq,
                        'prominence_db': np.max(amps) if amps else 0,
                        'occurrences': len(detections),
                        'bin_width_hz': bin_width
                    })
        
        return changes
    
    def _update_soil_moisture(self, env_data: List[Dict]) -> None:
        """Aktualisiere Bodenfeuchte-Statistiken."""
        moisture_values = [e.get('soil_moisture_percent') for e in env_data 
                          if e.get('soil_moisture_percent') is not None]
        
        if moisture_values:
            self.state.soil_moisture_stats = StatisticalMetrics(
                mean=np.mean(moisture_values),
                std=np.std(moisture_values),
                median=np.median(moisture_values),
                q25=np.percentile(moisture_values, 25),
                q75=np.percentile(moisture_values, 75),
                iqr=np.percentile(moisture_values, 75) - np.percentile(moisture_values, 25),
                min=np.min(moisture_values),
                max=np.max(moisture_values),
                n_samples=len(moisture_values),
                timestamp=datetime.now().isoformat()
            )
    
    def _update_event_counts(self, events: List[Dict]) -> None:
        """Aktualisiere Event-Counts."""
        for event in events:
            event_type = event.get('event', 'unknown')
            self.state.event_counts[event_type] = self.state.event_counts.get(event_type, 0) + 1
    
    def _detect_significant_changes(self) -> List[Dict]:
        """Erkenne signifikante Veränderungen."""
        significant = []
        
        # Check for new persistent peaks
        for peak in self.state.persistent_peaks:
            if peak.occurrence_count == self.MIN_OCCURRENCES:
                significant.append({
                    'type': 'new_persistent_peak',
                    'channel': peak.channel,
                    'frequency_hz': peak.frequency_hz,
                    'prominence_db': peak.prominence_db,
                    'description': f"New persistent peak at {peak.frequency_hz/1000:.1f} kHz on CH{peak.channel}"
                })
        
        # Check for amplitude drifts
        for ch_name, stats in self.state.channels.items():
            if stats.std > 0:
                cv = stats.std / stats.mean if stats.mean > 0 else 0
                if cv > 0.3:  # Variationskoeffizient > 30%
                    significant.append({
                        'type': 'high_amplitude_variability',
                        'channel': ch_name,
                        'cv': cv,
                        'description': f"High amplitude variability on {ch_name} (CV={cv:.2f})"
                    })
        
        return significant
    
    def generate_baseline_report(self, output_path: Path) -> None:
        """Generiere umfassenden Baseline-Report."""
        # Implementation in generate_scientific_report.py
        pass


def load_jsonl(filepath: Path) -> List[Dict]:
    """Lade JSONL-Datei."""
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data


def main():
    """Hauptfunktion."""
    # Finde neueste Session
    data_dir = Path(__file__).parent.parent / "data" / "continuous_plant_ae_20260622"
    sessions = sorted([d for d in data_dir.iterdir() if d.is_dir() and d.name != "logs"])
    
    if not sessions:
        print("No sessions found!")
        return
    
    latest_session = sessions[-1]
    print(f"Processing session: {latest_session.name}")
    
    # Lade Daten
    frames = load_jsonl(latest_session / "frame_characterization.jsonl")
    events = load_jsonl(latest_session / "experiment_events.jsonl")
    env_data = load_jsonl(latest_session / "environment.jsonl")
    
    # Initialisiere Tracker
    tracker = ScientificTracker(latest_session)
    
    # Update mit allen Daten
    changes = tracker.update_from_data(frames, events, env_data)
    
    # Print Summary
    print(f"\nTracking Update:")
    print(f"  Channels tracked: {len(tracker.state.channels)}")
    print(f"  Persistent peaks: {len(tracker.state.persistent_peaks)}")
    print(f"  New peaks: {len(changes['new_peaks'])}")
    print(f"  Significant changes: {len(changes['significant_changes'])}")
    
    if changes['significant_changes']:
        print("\nSignificant Changes:")
        for change in changes['significant_changes']:
            print(f"  - {change['description']}")
    
    if changes['new_peaks']:
        print("\nNew Persistent Peaks:")
        for peak in changes['new_peaks']:
            print(f"  - CH{peak['channel']}: {peak['frequency_hz']/1000:.1f} kHz "
                  f"(prominence: {peak['prominence_db']:.1f} dB)")
    
    print(f"\nState saved to: {tracker.state_file}")


if __name__ == "__main__":
    main()
