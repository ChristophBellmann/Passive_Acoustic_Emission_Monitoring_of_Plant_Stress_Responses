"""
Generate oscilloscope-style plots from measurement data.

This script creates publication-quality plots that mimic oscilloscope displays.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

# Add project src to path
PROJECT_SRC = Path(__file__).resolve().parent.parent / "instrument_control"
if PROJECT_SRC.exists():
    sys.path.insert(0, str(PROJECT_SRC))


def load_captures(data_dir: Path) -> dict[int, list[np.ndarray]]:
    """Load all captures from the raw data directory."""
    captures = {1: [], 2: [], 3: []}
    
    raw_dir = data_dir / "raw"
    if not raw_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")
    
    npz_files = sorted(raw_dir.glob("*.npz"))
    
    for npz_file in npz_files:
        data = np.load(npz_file, allow_pickle=True)
        voltage = data["voltage_vector"]
        
        # Extract channel from filename
        ch_str = npz_file.stem.split("_ch")[-1]
        try:
            ch = int(ch_str)
            if ch in captures:
                captures[ch].append(voltage)
        except ValueError:
            continue
    
    return captures


def plot_oscilloscope_style(captures: dict[int, list[np.ndarray]], output_dir: Path) -> None:
    """Create oscilloscope-style plots."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    sample_rate = 10000.0  # 10 kSa/s
    time_step = 1.0 / sample_rate * 1000  # ms
    
    # Plot 1: All channels overlay (like oscilloscope display)
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#0a0a0a')
    
    colors = ['#00ff00', '#ffff00', '#00ffff']  # Green, Yellow, Cyan
    labels = ['CH1 (Amplified)', 'CH2 (820kΩ)', 'CH3 (Direct)']
    
    for ch in [1, 2, 3]:
        if captures[ch]:
            voltage = captures[ch][0]
            time_ms = np.arange(len(voltage)) * time_step
            
            # Normalize for display
            voltage_normalized = voltage / np.max(np.abs(voltage)) * 0.8
            
            ax.plot(time_ms, voltage_normalized + (ch-1)*0.1, 
                   color=colors[ch-1], linewidth=1.5, label=labels[ch-1], alpha=0.8)
    
    ax.set_xlabel('Time (ms)', color='white', fontsize=12)
    ax.set_ylabel('Normalized Amplitude', color='white', fontsize=12)
    ax.set_title('Plant Acoustic Emissions - 3 Channel Measurement', 
                color='white', fontsize=14, fontweight='bold')
    ax.tick_params(colors='white')
    ax.grid(True, alpha=0.3, color='gray')
    ax.legend(loc='upper right', facecolor='#2a2a2a', edgecolor='white', labelcolor='white')
    
    # Add grid lines like oscilloscope
    for i in range(11):
        ax.axvline(x=i*12, color='gray', alpha=0.2, linewidth=0.5)
    for i in range(9):
        ax.axhline(y=i*0.25-1, color='gray', alpha=0.2, linewidth=0.5)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'oscilloscope_overlay.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    # Plot 2: Individual channel displays (like separate oscilloscope screens)
    for ch in [1, 2, 3]:
        if not captures[ch]:
            continue
        
        voltage = captures[ch][0]
        time_ms = np.arange(len(voltage)) * time_step
        
        fig, ax = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor('#1a1a1a')
        ax.set_facecolor('#0a0a0a')
        
        ax.plot(time_ms, voltage * 1000, color=colors[ch-1], linewidth=1.5)
        
        ax.set_xlabel('Time (ms)', color='white', fontsize=11)
        ax.set_ylabel('Voltage (mV)', color='white', fontsize=11)
        ax.set_title(f'Channel {ch} - {labels[ch-1]}', 
                    color='white', fontsize=13, fontweight='bold')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='gray')
        
        # Add measurement info box
        peak_to_peak = (np.max(voltage) - np.min(voltage)) * 1000
        rms = np.sqrt(np.mean(voltage**2)) * 1000
        
        info_text = f'Vpp: {peak_to_peak:.2f} mV\nRMS: {rms:.2f} mV'
        props = dict(boxstyle='round', facecolor='#2a2a2a', alpha=0.8, edgecolor='white')
        ax.text(0.02, 0.98, info_text, transform=ax.transAxes, fontsize=10,
               verticalalignment='top', bbox=props, color='white')
        
        # Add oscilloscope-style grid
        for i in range(11):
            ax.axvline(x=i*12, color='gray', alpha=0.2, linewidth=0.5)
        for i in range(9):
            ax.axhline(y=i*(np.max(voltage*1000)-np.min(voltage*1000))/8 + np.min(voltage*1000), 
                      color='gray', alpha=0.2, linewidth=0.5)
        
        plt.tight_layout()
        plt.savefig(output_dir / f'oscilloscope_ch{ch}.png', dpi=150, bbox_inches='tight')
        plt.close()
    
    # Plot 3: Frequency spectrum (like spectrum analyzer)
    from scipy import signal as sp_signal
    from scope.preprocessing import preprocess
    from scope.spectral import compute_fft, amplitude_to_db
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.patch.set_facecolor('#1a1a1a')
    
    for idx, ch in enumerate([1, 2, 3]):
        if not captures[ch]:
            continue
        
        ax = axes[idx]
        ax.set_facecolor('#0a0a0a')
        
        # Compute FFT
        voltage = captures[ch][0]
        pre = preprocess(
            np.arange(len(voltage)) / sample_rate,
            voltage,
            remove_dc_flag=True,
            detrend_flag=True,
            window="hann"
        )
        fft = compute_fft(pre.voltage, sample_rate, window="hann")
        fft_db = amplitude_to_db(fft.amplitude)
        
        # Limit to acoustic range
        mask = (fft.frequencies >= 20) & (fft.frequencies <= 5000)
        
        ax.plot(fft.frequencies[mask], fft_db[mask], color=colors[ch-1], linewidth=1.5)
        
        ax.set_xlabel('Frequency (Hz)', color='white', fontsize=10)
        ax.set_ylabel('Amplitude (dB)', color='white', fontsize=10)
        ax.set_title(f'Channel {ch} - Frequency Spectrum', 
                    color='white', fontsize=11, fontweight='bold')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='gray')
        
        # Find and mark peaks
        peaks_idx, properties = sp_signal.find_peaks(fft_db[mask], prominence=3, distance=5)
        for i, peak_idx in enumerate(peaks_idx[:5]):
            peak_freq = fft.frequencies[mask][peak_idx]
            peak_amp = fft_db[mask][peak_idx]
            ax.axvline(peak_freq, color='red', alpha=0.5, linestyle='--', linewidth=1)
            ax.annotate(f'{peak_freq:.0f} Hz', 
                       xy=(peak_freq, peak_amp),
                       xytext=(peak_freq + 100, peak_amp - 5),
                       color='yellow', fontsize=8, fontweight='bold',
                       arrowprops=dict(arrowstyle='->', color='yellow', lw=1))
    
    plt.tight_layout()
    plt.savefig(output_dir / 'oscilloscope_spectrum.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"Oscilloscope-style plots saved to: {output_dir}")


def main() -> None:
    """Main function."""
    experiment_dir = Path(__file__).resolve().parent
    plots_dir = experiment_dir / "oscilloscope_plots"
    
    # Find the latest data directory
    data_base = experiment_dir / "data" / "plant_ae_optimized"
    if data_base.exists():
        data_dirs = sorted([d for d in data_base.iterdir() if d.is_dir()])
        if data_dirs:
            latest_data_dir = data_dirs[-1]
            print(f"Using latest data from: {latest_data_dir.name}")
        else:
            print("No data directories found, using experiment_dir/raw")
            latest_data_dir = experiment_dir
    else:
        print("No data/plant_ae_optimized directory found, using experiment_dir/raw")
        latest_data_dir = experiment_dir
    
    print("Loading measurement data...")
    captures = load_captures(latest_data_dir)
    
    print(f"Loaded {sum(len(v) for v in captures.values())} captures")
    for ch in [1, 2, 3]:
        print(f"  CH{ch}: {len(captures[ch])} captures")
    
    print("\nGenerating oscilloscope-style plots...")
    plot_oscilloscope_style(captures, plots_dir)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
