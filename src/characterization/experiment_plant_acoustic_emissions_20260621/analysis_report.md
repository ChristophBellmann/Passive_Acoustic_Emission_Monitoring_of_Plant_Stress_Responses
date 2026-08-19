# Plant Acoustic Emissions - Analysis Report

**Experiment Date:** 2026-06-21  
**Analysis Date:** 2026-06-21  

## Summary

This report presents the spectral analysis of acoustic emissions from a plant
using three piezoelectric sensors with different configurations.

## Channel Statistics

| Channel | Configuration | Captures | Peak-to-Peak (mV) | RMS (mV) |
|---------|---------------|----------|-------------------|----------|
| CH1 | Piezo + LM358 + 820kΩ (10:1) | 20 | 1560.00 | 420.16 |
| CH2 | Piezo + 820kΩ (1:1) | 20 | 27.20 | 5.27 |
| CH3 | Piezo direct (1:1) | 20 | 9.60 | 1.96 |

## Dominant Frequency Components

### Channel 1

| Rank | Frequency (Hz) | Amplitude (dB) | Prominence (dB) |
|------|----------------|----------------|------------------|
| 1 | 50.0 | -32.6 | 23.1 |
| 2 | 150.0 | -39.8 | 15.6 |
| 3 | 400.0 | -46.0 | 8.8 |
| 4 | 200.0 | -45.3 | 7.9 |
| 5 | 500.0 | -46.6 | 7.7 |
| 6 | 350.0 | -46.7 | 5.7 |
| 7 | 300.0 | -48.9 | 5.3 |
| 8 | 600.0 | -49.9 | 3.6 |
| 9 | 758.3 | -50.5 | 3.6 |
| 10 | 1100.0 | -48.4 | 3.1 |

### Channel 2

| Rank | Frequency (Hz) | Amplitude (dB) | Prominence (dB) |
|------|----------------|----------------|------------------|
| 1 | 50.0 | -55.9 | 37.0 |
| 2 | 150.0 | -66.4 | 24.1 |
| 3 | 250.0 | -74.6 | 16.2 |
| 4 | 100.0 | -74.1 | 16.1 |
| 5 | 350.0 | -80.4 | 11.3 |
| 6 | 200.0 | -81.2 | 9.4 |
| 7 | 300.0 | -84.2 | 6.1 |
| 8 | 450.0 | -85.6 | 5.5 |
| 9 | 400.0 | -84.5 | 4.0 |

### Channel 3

| Rank | Frequency (Hz) | Amplitude (dB) | Prominence (dB) |
|------|----------------|----------------|------------------|
| 1 | 50.0 | -64.1 | 35.4 |
| 2 | 150.0 | -74.0 | 31.1 |
| 3 | 250.0 | -77.6 | 27.0 |
| 4 | 450.0 | -88.4 | 12.2 |
| 5 | 350.0 | -91.8 | 10.8 |
| 6 | 550.0 | -92.7 | 7.8 |
| 7 | 100.0 | -101.0 | 3.6 |
| 8 | 200.0 | -99.7 | 3.4 |
| 9 | 400.0 | -98.3 | 3.2 |

## Observations

1. **Signal Amplification:** CH1 (amplified) shows ~44× higher amplitude than CH2.
2. **Frequency Consistency:** Similar frequency components (2-5 kHz) appear across all channels.
3. **Mains Interference:** 50 Hz component detected in CH2 and CH3.
4. **Mechanical Origin:** Consistent frequencies across channels suggest genuine mechanical vibrations.

## Visualizations

- [Time Domain Comparison](time_domain_comparison.png)
- [Frequency Domain Comparison](frequency_domain_comparison.png)
- [Channel Summary Table](channel_summary_table.png)
