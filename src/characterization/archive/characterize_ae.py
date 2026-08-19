#!/usr/bin/env python3
"""
Systematic characterization of plant AE in 5 kHz steps.

Analyzes decimated data in frequency bands:
0-5 kHz, 5-10 kHz, 10-15 kHz, ..., 95-100 kHz

Creates for each band:
- Frequency spectrum
- Peak detection
- Statistics
- Summary
"""

import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from datetime import datetime

def analyze_frequency_band(voltage_data, sample_rate, f_low, f_high, output_dir, band_name):
    """
    Analyzes a single frequency band.
    
    Args:
        voltage_data: Voltage signal
        sample_rate: Sample rate in Hz
        f_low: Lower frequency limit in Hz
        f_high: Upper frequency limit in Hz
        output_dir: Output directory
        band_name: Name of the frequency band (e.g. "0-5kHz")
    
    Returns:
        dict with analysis results
    """
    # Calculate FFT
    n = len(voltage_data)
    fft_data = np.fft.fft(voltage_data)
    fft_freqs = np.fft.fftfreq(n, 1/sample_rate)
    
    # Only positive frequencies
    positive_mask = fft_freqs >= 0
    fft_freqs_pos = fft_freqs[positive_mask]
    fft_magnitude = np.abs(fft_data[positive_mask]) / n
    fft_phase = np.angle(fft_data[positive_mask])
    
    # Filter to desired frequency band
    band_mask = (fft_freqs_pos >= f_low) & (fft_freqs_pos <= f_high)
    fft_freqs_band = fft_freqs_pos[band_mask]
    fft_magnitude_band = fft_magnitude[band_mask]
    fft_phase_band = fft_phase[band_mask]
    
    # Peak detection
    if len(fft_magnitude_band) > 0:
        # Adaptive threshold: 10% of maximum in band
        threshold = np.max(fft_magnitude_band) * 0.1
        peaks, properties = signal.find_peaks(
            fft_magnitude_band,
            height=threshold,
            distance=max(1, int(100 / (sample_rate / len(fft_magnitude_band))))
        )
        
        # Sort by height
        if len(peaks) > 0:
            peak_heights = properties['peak_heights']
            sorted_indices = np.argsort(peak_heights)[::-1]
            peaks = peaks[sorted_indices]
            peak_heights = peak_heights[sorted_indices]
    else:
        peaks = []
        peak_heights = []
    
    # Statistics
    stats = {
        'band_name': band_name,
        'f_low_hz': f_low,
        'f_high_hz': f_high,
        'n_points': len(voltage_data),
        'sample_rate_hz': sample_rate,
        'duration_ms': n / sample_rate * 1000,
        'v_max_mv': np.max(voltage_data) * 1000,
        'v_min_mv': np.min(voltage_data) * 1000,
        'v_pp_mv': (np.max(voltage_data) - np.min(voltage_data)) * 1000,
        'v_rms_mv': np.sqrt(np.mean(voltage_data**2)) * 1000,
        'band_max_mv': np.max(fft_magnitude_band) * 1000 if len(fft_magnitude_band) > 0 else 0,
        'band_mean_mv': np.mean(fft_magnitude_band) * 1000 if len(fft_magnitude_band) > 0 else 0,
        'band_energy': np.sum(fft_magnitude_band**2) if len(fft_magnitude_band) > 0 else 0,
        'n_peaks': len(peaks),
        'peaks': []
    }
    
    # Peak details
    for i, peak_idx in enumerate(peaks[:10]):  # Top 10 peaks
        peak_freq = fft_freqs_band[peak_idx]
        peak_amp = fft_magnitude_band[peak_idx]
        stats['peaks'].append({
            'frequency_hz': peak_freq,
            'amplitude_mv': peak_amp * 1000,
            'rank': i + 1
        })
    
    # Create plot
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f'Frequency Band Analysis: {band_name}', fontsize=16, fontweight='bold')
    
    # Plot 1: Frequency Spectrum (linear)
    ax1 = axes[0, 0]
    ax1.plot(fft_freqs_band / 1e3, fft_magnitude_band * 1000, linewidth=1, color='blue')
    if len(peaks) > 0:
        ax1.plot(fft_freqs_band[peaks] / 1e3, fft_magnitude_band[peaks] * 1000,
                'ro', markersize=8, label=f'{len(peaks)} Peaks')
        ax1.legend()
    ax1.set_xlabel('Frequency (kHz)')
    ax1.set_ylabel('Amplitude (mV)')
    ax1.set_title('Frequency Spectrum (linear)')
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Frequency Spectrum (dB)
    ax2 = axes[0, 1]
    fft_db = 20 * np.log10(fft_magnitude_band + 1e-12)
    ax2.plot(fft_freqs_band / 1e3, fft_db, linewidth=1, color='green')
    if len(peaks) > 0:
        ax2.plot(fft_freqs_band[peaks] / 1e3, fft_db[peaks],
                'ro', markersize=8, label=f'{len(peaks)} Peaks')
        ax2.legend()
    ax2.set_xlabel('Frequency (kHz)')
    ax2.set_ylabel('Amplitude (dB)')
    ax2.set_title('Frequency Spectrum (dB)')
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Time Domain (Zoom)
    ax3 = axes[1, 0]
    # Show 10 ms or total duration, whichever is shorter
    zoom_duration = min(10e-3, stats['duration_ms'] / 1000)
    zoom_samples = int(zoom_duration * sample_rate)
    time_zoom = np.arange(zoom_samples) / sample_rate * 1000
    ax3.plot(time_zoom, voltage_data[:zoom_samples] * 1000, linewidth=0.5, color='red')
    ax3.set_xlabel('Time (ms)')
    ax3.set_ylabel('Voltage (mV)')
    ax3.set_title(f'Time Domain (Zoom: {zoom_duration*1000:.1f} ms)')
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Statistics Table
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    table_data = [
        ['Parameter', 'Value'],
        ['Frequency Band', f'{f_low/1e3:.1f} - {f_high/1e3:.1f} kHz'],
        ['Sample Rate', f'{sample_rate/1e3:.1f} kHz'],
        ['Recording Duration', f'{stats["duration_ms"]:.2f} ms'],
        ['Max. Voltage', f'{stats["v_max_mv"]:.2f} mV'],
        ['Min. Voltage', f'{stats["v_min_mv"]:.2f} mV'],
        ['Peak-to-Peak', f'{stats["v_pp_mv"]:.2f} mV'],
        ['RMS', f'{stats["v_rms_mv"]:.2f} mV'],
        ['Band Energy', f'{stats["band_energy"]:.2e}'],
        ['Number of Peaks', f'{stats["n_peaks"]}'],
    ]
    
    if len(peaks) > 0:
        table_data.append(['Top Peak', f'{stats["peaks"][0]["frequency_hz"]/1e3:.2f} kHz'])
        table_data.append(['Top Amplitude', f'{stats["peaks"][0]["amplitude_mv"]:.2f} mV'])
    
    table = ax4.table(cellText=table_data, cellLoc='left', loc='center',
                      colWidths=[0.4, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)
    
    # Header style
    for i in range(2):
        table[(0, i)].set_facecolor('#4CAF50')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax4.set_title('Summary', pad=20)
    
    plt.tight_layout()
    
    # Save plot
    plot_file = output_dir / f'analysis_{band_name}.png'
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    return stats


def create_summary_report(all_stats, output_dir):
    """
    Creates a summary report for all frequency bands.
    
    Args:
        all_stats: List of statistics dicts for all bands
        output_dir: Output directory
    """
    # Create Summary Plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Systematic Characterization: Plant AE (0-100 kHz)',
                 fontsize=18, fontweight='bold')
    
    # Plot 1: Band Energy vs Frequency
    ax1 = axes[0, 0]
    bands = [s['band_name'] for s in all_stats]
    energies = [s['band_energy'] for s in all_stats]
    x_pos = np.arange(len(bands))
    ax1.bar(x_pos, energies, color='steelblue', alpha=0.7)
    ax1.set_xlabel('Frequency Band')
    ax1.set_ylabel('Band Energy')
    ax1.set_title('Energy Distribution across Frequency Bands')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(bands, rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Number of Peaks per Band
    ax2 = axes[0, 1]
    n_peaks = [s['n_peaks'] for s in all_stats]
    ax2.bar(x_pos, n_peaks, color='coral', alpha=0.7)
    ax2.set_xlabel('Frequency Band')
    ax2.set_ylabel('Number of Peaks')
    ax2.set_title('Peak Density across Frequency Bands')
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(bands, rotation=45, ha='right')
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Plot 3: Maximum Amplitude per Band
    ax3 = axes[1, 0]
    max_amps = [s['band_max_mv'] for s in all_stats]
    ax3.bar(x_pos, max_amps, color='seagreen', alpha=0.7)
    ax3.set_xlabel('Frequency Band')
    ax3.set_ylabel('Max. Amplitude (mV)')
    ax3.set_title('Maximum Amplitude per Frequency Band')
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(bands, rotation=45, ha='right')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Plot 4: Top Peaks across All Bands
    ax4 = axes[1, 1]
    all_peaks = []
    for stats in all_stats:
        for peak in stats['peaks'][:3]:  # Top 3 per band
            all_peaks.append({
                'frequency_hz': peak['frequency_hz'],
                'amplitude_mv': peak['amplitude_mv'],
                'band': stats['band_name']
            })
    
    if all_peaks:
        # Sort by amplitude
        all_peaks.sort(key=lambda x: x['amplitude_mv'], reverse=True)
        top_peaks = all_peaks[:20]  # Top 20 overall
        
        peak_freqs = [p['frequency_hz'] / 1e3 for p in top_peaks]
        peak_amps = [p['amplitude_mv'] for p in top_peaks]
        peak_bands = [p['band'] for p in top_peaks]
        
        scatter = ax4.scatter(peak_freqs, peak_amps, c=peak_amps, cmap='viridis',
                             s=100, edgecolors='black', linewidth=1)
        ax4.set_xlabel('Frequency (kHz)')
        ax4.set_ylabel('Amplitude (mV)')
        ax4.set_title('Top 20 Peaks across All Bands')
        ax4.grid(True, alpha=0.3)
        
        # Add text labels
        for i, (freq, amp, band) in enumerate(zip(peak_freqs, peak_amps, peak_bands)):
            if i < 5:  # Label only top 5
                ax4.annotate(f'{freq:.1f}kHz', (freq, amp),
                           xytext=(5, 5), textcoords='offset points',
                           fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    
    # Speichere Summary-Plot
    summary_file = output_dir / 'summary_all_bands.png'
    plt.savefig(summary_file, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Create Text Report
    report_file = output_dir / 'analysis_report.txt'
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("SYSTEMATIC CHARACTERIZATION: PLANT AE (0-100 kHz)\n")
        f.write("=" * 80 + "\n")
        f.write(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Analyzed Bands: {len(all_stats)}\n")
        f.write("\n")
        
        # Summary
        f.write("SUMMARY\n")
        f.write("-" * 80 + "\n")
        
        total_peaks = sum(s['n_peaks'] for s in all_stats)
        total_energy = sum(s['band_energy'] for s in all_stats)
        max_band = max(all_stats, key=lambda x: x['band_energy'])
        
        f.write(f"Total Number of Peaks: {total_peaks}\n")
        f.write(f"Total Energy: {total_energy:.2e}\n")
        f.write(f"Most Energetic Band: {max_band['band_name']} ({max_band['band_energy']:.2e})\n")
        f.write("\n")
        
        # Detailed results per band
        f.write("DETAILED RESULTS\n")
        f.write("-" * 80 + "\n\n")
        
        for stats in all_stats:
            f.write(f"Band: {stats['band_name']}\n")
            f.write(f"  Frequency Range: {stats['f_low_hz']/1e3:.1f} - {stats['f_high_hz']/1e3:.1f} kHz\n")
            f.write(f"  Band Energy: {stats['band_energy']:.2e}\n")
            f.write(f"  Max. Amplitude: {stats['band_max_mv']:.2f} mV\n")
            f.write(f"  Number of Peaks: {stats['n_peaks']}\n")
            
            if stats['n_peaks'] > 0:
                f.write(f"  Top Peaks:\n")
                for peak in stats['peaks'][:5]:
                    f.write(f"    {peak['rank']}. {peak['frequency_hz']/1e3:.2f} kHz "
                           f"({peak['amplitude_mv']:.2f} mV)\n")
            else:
                f.write(f"  → No significant peaks found\n")
            
            f.write("\n")
        
        # Recommendations
        f.write("RECOMMENDATIONS\n")
        f.write("-" * 80 + "\n")
        
        # Find bands with significant signals
        significant_bands = [s for s in all_stats if s['n_peaks'] > 0 and s['band_energy'] > 1e-6]
        
        if significant_bands:
            f.write(f"Significant signals found in {len(significant_bands)} bands:\n")
            for band in significant_bands:
                f.write(f"  - {band['band_name']}: {band['n_peaks']} peaks, "
                       f"energy {band['band_energy']:.2e}\n")
        else:
            f.write("No significant signals found in the 0-100 kHz range.\n")
            f.write("Possible causes:\n")
            f.write("  - No acoustic emissions during measurement\n")
            f.write("  - Signal too weak (noise)\n")
            f.write("  - Incorrect sensor placement\n")
        
        f.write("\n")
        f.write("=" * 80 + "\n")
    
    print(f"Summary report created: {report_file}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Systematic characterization of plant AE in 5 kHz steps"
    )
    parser.add_argument(
        "data_dir",
        type=Path,
        help="Directory with decimated data (.npz files)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output directory (default: data_dir/characterization)"
    )
    parser.add_argument(
        "-f", "--max-freq",
        type=float,
        default=100e3,
        help="Maximum frequency in Hz (default: 100000)"
    )
    parser.add_argument(
        "-s", "--step",
        type=float,
        default=5e3,
        help="Step size in Hz (default: 5000)"
    )
    
    args = parser.parse_args()
    
    # Setze Ausgabeverzeichnis
    if args.output is None:
        output_dir = args.data_dir / "characterization"
    else:
        output_dir = args.output
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("SYSTEMATIC CHARACTERIZATION: PLANT AE")
    print("=" * 80)
    print()
    
    # Find decimated files
    npz_files = sorted(args.data_dir.glob("decimated_*.npz"))
    
    if not npz_files:
        print(f"No decimated files found in {args.data_dir}")
        return
    
    print(f"Found: {len(npz_files)} files")
    print(f"Frequency range: 0 - {args.max_freq/1e3:.0f} kHz")
    print(f"Step size: {args.step/1e3:.0f} kHz")
    print(f"Output: {output_dir}")
    print()
    
    # Analyze first file
    first_file = npz_files[0]
    print(f"Analyzing: {first_file.name}")
    
    data = np.load(first_file)
    voltage_data = data['voltage']
    sample_rate = data['sample_rate']
    
    print(f"  Sample Rate: {sample_rate/1e3:.1f} kHz")
    print(f"  Points: {len(voltage_data)}")
    print(f"  Duration: {len(voltage_data) / sample_rate * 1000:.2f} ms")
    print()
    
    # Create frequency bands
    n_bands = int(args.max_freq / args.step)
    all_stats = []
    
    for i in range(n_bands):
        f_low = i * args.step
        f_high = (i + 1) * args.step
        band_name = f"{f_low/1e3:.0f}-{f_high/1e3:.0f}kHz"
        
        print(f"Analyzing band {i+1}/{n_bands}: {band_name}")
        
        stats = analyze_frequency_band(
            voltage_data, sample_rate,
            f_low, f_high,
            output_dir, band_name
        )
        
        all_stats.append(stats)
        
        # Short summary
        if stats['n_peaks'] > 0:
            print(f"  → {stats['n_peaks']} peaks found")
            if stats['peaks']:
                top_peak = stats['peaks'][0]
                print(f"    Top: {top_peak['frequency_hz']/1e3:.2f} kHz "
                      f"({top_peak['amplitude_mv']:.2f} mV)")
        else:
            print(f"  → No significant peaks")
    
    print()
    print("Creating summary report...")
    create_summary_report(all_stats, output_dir)
    
    print()
    print("=" * 80)
    print("CHARACTERIZATION COMPLETE")
    print("=" * 80)
    print()
    print(f"Results in: {output_dir}")
    print(f"  - {n_bands} individual analyses (analysis_*.png)")
    print(f"  - Summary plot (summary_all_bands.png)")
    print(f"  - Text report (analysis_report.txt)")
    print()


if __name__ == "__main__":
    main()
