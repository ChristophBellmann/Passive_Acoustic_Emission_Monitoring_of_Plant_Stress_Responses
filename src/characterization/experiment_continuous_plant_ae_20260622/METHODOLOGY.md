# Scientific Documentation: Plant Acoustic Emissions Tracking System

## Overview

This document describes the scientific methodology and statistical methods used in the plant acoustic emissions tracking system.

## System Architecture

### Components

1. **Scientific Tracker** (`scientific_tracker.py`)
   - Continuous monitoring of acoustic emissions
   - Statistical analysis of frequency peaks
   - Drift detection and trend analysis
   - State persistence for reproducibility

2. **Report Generator** (`generate_scientific_report.py`)
   - Automated PDF report generation
   - Professional visualizations
   - Statistical summaries
   - Methodology documentation

## Technical Configuration

### Acquisition Profile: deep_memory_500k

**Current Configuration (Updated 2026-06-22):**

- **Sample Rate:** 500 kHz (500,000 Hz)
- **Memory Depth:** 300,000 points
- **Chunk Points:** 250,000 points
- **Max Frequency:** 100 kHz
- **VISA Timeout:** 30,000 ms

**Previous Configuration (Before 2026-06-22):**

- Sample Rate: 25 MSa/s
- Memory Depth: AUTO
- Max Frequency: Not explicitly limited

**Rationale for Change:**

The reduction from 25 MSa/s to 500 kHz was implemented to:
1. Enable longer acquisition windows (600 ms vs 12 ms)
2. Reduce memory pressure during continuous operation
3. Focus on biologically relevant frequency range (0-100 kHz)
4. Improve stability for long-running experiments

**Nyquist Frequency:** 250 kHz (sufficient for 100 kHz max frequency)

## Statistical Methods

### 1. Significance Testing

**Significance Level:** α = 0.05

All statistical tests use a 5% significance level. Changes are considered significant if they exceed the defined thresholds.

### 2. Drift Detection

**Method:** Z-score analysis with ±2σ threshold

```python
z_score = abs(new_mean - old_mean) / old_std
if z_score > 2.0:
    # Significant drift detected
```

**Rationale:** A 2-sigma threshold corresponds to approximately 95% confidence interval, ensuring that only statistically significant changes are flagged.

### 3. Persistent Peak Detection

**Criteria:**
- Minimum occurrences: 5 detections (configurable: `persistence_frames`)
- Frequency binning: 250 Hz bins (configurable: `bin_width_hz`)
- Channel-specific tracking
- Match tolerance: 500 Hz (configurable: `tolerance_hz`)
- Cooldown period: 60 frames (configurable: `cooldown_frames`)

**Algorithm:**
1. Extract all `new_peak` detections from `spectral_change` events
2. Group by (channel, frequency_bin)
3. Calculate statistics for each group
4. Flag as persistent if occurrence_count >= persistence_frames

### 4. Peak Tracker with Drift Analysis

**Advanced Drift Detection Parameters:**

- **Match Tolerance:** 500 Hz
- **Max Missed Frames:** 5
- **Min Points for Drift:** 12
- **Min Displacement:** 500 Hz
- **Min Slope:** 0.5 Hz/second
- **Min R-squared:** 0.8
- **Event Cooldown:** 30 frames

**Drift Detection Algorithm:**

```python
# Linear regression on frequency time series
slope, intercept, r_value, p_value, std_err = stats.linregress(time, freqs)

# Drift is significant if:
# 1. At least 12 data points
# 2. Displacement > 500 Hz
# 3. Slope > 0.5 Hz/s
# 4. R-squared > 0.8
if (len(points) >= min_points_for_drift and
    abs(displacement) >= min_displacement_hz and
    abs(slope) >= min_slope_hz_per_second and
    r_squared >= min_r_squared):
    # Significant drift detected
```

**Rationale:** These stringent criteria ensure that only genuine frequency drifts are detected, reducing false positives from noise or temporary fluctuations.

### 5. Trend Analysis

**Method:** Linear regression on frequency time series

```python
slope, intercept, r_value, p_value, std_err = stats.linregress(x, freqs)
if slope > 10:
    trend = 'drifting_up'
elif slope < -10:
    trend = 'drifting_down'
else:
    trend = 'stable'
```

**Interpretation:**
- `stable`: Frequency variation < 10 Hz per detection
- `drifting_up`: Systematic increase in frequency
- `drifting_down`: Systematic decrease in frequency

### 6. Channel Statistics

**Metrics tracked:**
- Mean RMS voltage (mV)
- Standard deviation
- Median, Q25, Q75, IQR
- Min, Max
- Sample count

**Update frequency:** Every frame update

### 7. Soil Moisture Correlation

**Analysis:**
- Track soil moisture statistics
- Calculate coefficient of variation
- Identify correlations with AE activity

## Data Structure

### Tracking State (JSON)

```json
{
  "experiment_start": "ISO timestamp",
  "last_update": "ISO timestamp",
  "baseline_established": boolean,
  "baseline_duration_minutes": float,
  "channels": {
    "CH1": {
      "mean": float,
      "std": float,
      "median": float,
      "q25": float,
      "q75": float,
      "iqr": float,
      "min": float,
      "max": float,
      "n_samples": int,
      "timestamp": "ISO timestamp"
    }
  },
  "persistent_peaks": [
    {
      "frequency_hz": float,
      "amplitude_mv": float,
      "prominence_db": float,
      "channel": int,
      "first_seen": "ISO timestamp",
      "last_seen": "ISO timestamp",
      "occurrence_count": int,
      "mean_frequency": float,
      "std_frequency": float,
      "trend": "stable|drifting_up|drifting_down"
    }
  ],
  "soil_moisture_stats": {...},
  "event_counts": {
    "event_type": count
  }
}
```

## Report Structure

### Page 1: Title and Methodology
- Experiment metadata
- Statistical methods overview
- Summary statistics

### Page 2: Experimental Configuration
- Oscilloscope settings
- Channel configuration
- Event type distribution

### Page 3-4: Channel Statistics
- RMS voltage time series
- Statistical summary table
- Confidence intervals

### Page 5-6: Persistent Peaks
- Frequency distribution by channel
- Prominence vs frequency scatter plot
- Top 10 peaks table

### Page 7-8: Frequency Distribution
- All detections histogram
- 39 kHz region temporal evolution
- Prominence distribution

### Page 9: Soil Moisture Analysis
- Time series plot
- Statistical summary
- Interpretation

### Page 10: Summary and Conclusions
- Key findings
- Statistical confidence
- Recommendations

## Reproducibility

### State Persistence

The tracking state is saved to `tracking_state.json` after every update. This ensures:
- Exact reproducibility of analysis
- Ability to resume after interruption
- Version control of tracking parameters

### Configuration Parameters

All thresholds and parameters are defined as class constants:

```python
SIGNIFICANCE_LEVEL = 0.05
DRIFT_THRESHOLD_STD = 2.0
MIN_OCCURRENCES = 5
BASELINE_MINUTES = 30
```

### Data Sources

- **Frames:** `frame_characterization.jsonl`
- **Events:** `experiment_events.jsonl`
- **Environment:** `environment.jsonl`

All data is timestamped and can be traced back to specific measurement periods.

## Validation

### Statistical Validation

1. **Z-score threshold:** Validated against normal distribution
2. **Minimum occurrences:** Based on statistical power analysis
3. **Frequency binning:** 250 Hz bins provide sufficient resolution for 100 kHz range

### Visual Validation

Reports include multiple visualization types:
- Time series plots
- Histograms
- Scatter plots
- Statistical tables

### Cross-Channel Validation

Peaks detected on multiple channels are flagged for additional scrutiny, reducing false positives.

## Limitations

1. **Sample Rate:** 500 kHz provides 250 kHz Nyquist frequency, sufficient for 100 kHz max frequency
2. **Memory Depth:** 300,000 points at 500 kHz = 600 ms acquisition window
3. **Environmental Factors:** Temperature, humidity not fully controlled
4. **Biological Variability:** Plant state changes over time

## Future Improvements

1. **Adaptive Thresholds:** Dynamic adjustment based on baseline statistics
2. **Machine Learning:** Pattern recognition for peak classification
3. **Multi-Sensor Fusion:** Correlation across multiple sensor types
4. **Real-Time Alerting:** Immediate notification of significant events

## References

- scipy.stats documentation: https://docs.scipy.org/doc/scipy/reference/stats.html
- matplotlib documentation: https://matplotlib.org/stable/contents.html
- pandas documentation: https://pandas.pydata.org/docs/

## Contact

For questions or issues, refer to the experiment logs and tracking state files in the session directory.

---

**Document Version:** 2.0  
**Last Updated:** 2026-06-22  
**Author:** Automated Scientific Documentation System  
**Changes:** Updated for deep_memory_500k acquisition profile with advanced drift detection
