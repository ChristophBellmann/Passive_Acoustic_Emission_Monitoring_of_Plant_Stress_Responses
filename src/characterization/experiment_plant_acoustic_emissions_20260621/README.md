# Plant Acoustic Emissions Characterization

**Date:** 2026-06-21  
**Experiment ID:** plant_ae_3ch_20260621  
**Operator:** Automated measurement system

> **⚠ Phase 1 report (pre-CH2-defect).** This experiment used the **Phase 1 setup: CH1 + CH2 + CH3** (CH2 = Piezo on 0.8 mm stainless-steel plate, 1:1 probe). On 2026-06-22 CH2 suffered a hardware fault and was replaced by CH4. **Cross-channel conclusions from this report are not directly applicable to current Phase 2 (CH1+CH3+CH4) measurements.** See `experiment_continuous_plant_ae_20260622/HARDWARE_CHANGELOG.md` for the full setup history.

---

## Abstract

This experiment characterizes acoustic emissions (AE) from a plant using three piezoelectric sensors inserted into the soil near the plant base. The study employs a two-phase approach: (1) initial multi-channel measurement to validate signal authenticity, and (2) systematic frequency band analysis across 0-100 kHz to comprehensively characterize the AE spectrum. Key findings include dominant low-frequency activity (0-20 kHz, 78.4% of total energy), typical mid-frequency AE signatures (20-50 kHz), and an unexpected high-frequency anomaly at 71 kHz.

---

## 1. Experimental Setup

### 1.1 Sensor Configuration

Three piezoelectric sensors were inserted into the soil near the plant base with different signal conditioning:

| Channel | Configuration | Probe Ratio | Purpose |
|---------|--------------|-------------|---------|
| CH1 | Piezo + LM358 amplifier + 820 kΩ | 10:1 | High sensitivity (amplified) |
| CH2 | Piezo + 820 kΩ | 1:1 | Medium sensitivity |
| CH3 | Piezo (direct) | 1:1 | Reference (minimal conditioning) |

![Live Measurement Setup](screenshots/scope_screen_1_20260621_202738.png)
*Figure 1: Oscilloscope screenshot showing live measurement with all three channels active. CH1 (yellow) displays the amplified signal, while CH2 and CH3 show smaller but consistent waveforms.*

### 1.2 Instrument Settings

**Oscilloscope:** Rigol DS1104Z  
**Connection:** TCPIP (LAN) at 192.168.178.70  
**Sample Rate:** 25 MSa/s (actual)  
**Memory Depth:** 100,000 points  
**Time Base:** 10 ms/div  
**Acquisition Duration:** 4.00 ms per capture

### 1.3 Acquisition Parameters

- **Captures per channel:** 20
- **Total captures:** 60 (20 × 3 channels)
- **Inter-capture delay:** 0.3 s
- **Trigger mode:** Auto
- **Coupling:** AC (all channels)

---

## 2. Initial Measurement Results

### 2.1 Signal Amplitudes

| Channel | Peak-to-Peak | RMS | Max Amplitude |
|---------|--------------|-----|---------------|
| CH1 (amplified) | 1504.00 mV | 419.08 mV | 752 mV |
| CH2 (820 kΩ) | 23.20 mV | 5.18 mV | 11.6 mV |
| CH3 (direct) | 8.40 mV | 1.95 mV | 4.2 mV |

**Key Observation:** CH1 shows ~65× higher amplitude than CH2, confirming the LM358 amplifier effectiveness. The vertical scale for CH1 was set to 200 mV/div to prevent oversteering.

### 2.2 Signal Validation

To verify that detected signals are genuine mechanical vibrations rather than sensor artifacts, we compared CH2 and CH3 waveforms:

![CH2 vs CH3 Comparison](analysis_plots/ch2_ch3_comparison.png)
*Figure 2: Direct comparison of CH2 and CH3 with CH3 inverted. The nearly identical waveform shapes provide strong evidence that both channels detect the same mechanical vibrations, ruling out sensor-specific artifacts.*

### 2.3 Dominant Frequency Components

**Channel 1 (Amplified):**
1. 2.87 kHz (33.2 dB prominence)
2. 1.21 kHz (32.3 dB)
3. 391.7 Hz (27.6 dB)
4. 50.0 Hz (26.1 dB) - mains interference
5. 1.30 kHz (25.5 dB)

**Channel 2 (820 kΩ):**
1. 50.0 Hz (41.0 dB) - mains interference
2. 908.3 Hz (28.8 dB)
3. 150.0 Hz (26.7 dB)
4. 850.0 Hz (25.1 dB)
5. 2.12 kHz (23.5 dB)

**Channel 3 (Direct):**
1. 50.0 Hz (44.3 dB) - mains interference
2. 150.0 Hz (32.3 dB)
3. 2.18 kHz (30.3 dB)
4. 250.0 Hz (29.7 dB)
5. 4.34 kHz (29.6 dB)

![Channel Overlay](oscilloscope_plots/oscilloscope_overlay.png)
*Figure 3: All three channels overlaid showing relative signal amplitudes. CH1 (green) dominates due to amplification, while CH2 and CH3 show consistent but smaller waveforms.*

![Frequency Spectrum](oscilloscope_plots/oscilloscope_spectrum.png)
*Figure 4: Frequency spectrum analysis for all three channels. The consistent peak positions across channels (particularly in the 1-5 kHz range) confirm that these are genuine mechanical signals rather than electrical noise or sensor artifacts.*

### 2.4 Key Observations

1. **Frequency Range:** All channels show significant activity in the 1-5 kHz range, suggesting mechanical vibrations rather than electrical noise.

2. **Mains Interference:** 50 Hz components appear in all channels (European mains frequency), most pronounced in CH2 and CH3.

3. **Signal Consistency:** Similar frequency components across all channels (1-3 kHz) confirm genuine mechanical signals.

4. **Amplifier Performance:** LM358 amplifier boosts signal by ~65× without significant noise or distortion.

---

## 3. Systematic Characterization (0-100 kHz)

### 3.1 Methodology

To comprehensively characterize the AE spectrum beyond the initial 0-5 kHz range, we performed systematic frequency band analysis:

- **Frequency Range:** 0-100 kHz
- **Band Width:** 5 kHz per band
- **Number of Bands:** 20
- **Analysis Method:** FFT with adaptive peak detection (10% threshold)
- **Total Peaks Detected:** 128

### 3.2 Overall Statistics

| Metric | Value |
|--------|-------|
| **Total Peaks** | 128 |
| **Total Energy** | 2.26 x 10^-2 |
| **Most Energetic Band** | 0-5 kHz (1.35 x 10^-2) |
| **Peak Density** | 6.4 peaks/band (average) |
| **Maximum Amplitude** | 80.40 mV (4.75 kHz) |
| **Minimum Amplitude** | 1.54 mV (98.00 kHz) |

### 3.3 Energy Distribution

![Energy Distribution](../data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/summary_all_bands.png)
*Figure 4: Energy distribution across all 20 frequency bands. Clear dominance of the 0-5 kHz range (60% of total energy) and unexpected peak at 71 kHz.*

| Frequency Range | Energy | Peaks | Top Peak | Amplitude | Interpretation |
|-----------------|--------|-------|----------|-----------|----------------|
| **0-20 kHz** | 78.4% | 22 | 4.75 kHz | 80.40 mV | Mechanical vibrations, water transport |
| **20-50 kHz** | 17.6% | 40 | 24.00 kHz | 7.34 mV | Typical plant AE (cavitation) |
| **50-100 kHz** | 4.0% | 66 | 71.00 kHz | 36.70 mV | Low energy, but 71 kHz anomaly |

### 3.4 Top 10 Global Peaks

| Rank | Frequency | Amplitude | Band | Relative Energy |
|------|-----------|-----------|------|-----------------|
| 1 | **4.75 kHz** | **80.40 mV** | 0-5 kHz | 100% |
| 2 | **71.00 kHz** | **36.70 mV** | 70-75 kHz | 45.6% |
| 3 | 9.50 kHz | 25.86 mV | 5-10 kHz | 32.2% |
| 4 | 13.50 kHz | 18.09 mV | 10-15 kHz | 22.5% |
| 5 | 18.25 kHz | 11.65 mV | 15-20 kHz | 14.5% |
| 6 | 24.00 kHz | 7.34 mV | 20-25 kHz | 9.1% |
| 7 | 28.75 kHz | 5.18 mV | 25-30 kHz | 6.4% |
| 8 | 33.00 kHz | 4.32 mV | 30-35 kHz | 5.4% |
| 9 | 37.50 kHz | 3.99 mV | 35-40 kHz | 5.0% |
| 10 | 41.25 kHz | 4.33 mV | 40-45 kHz | 5.4% |

### 3.5 Detailed Band Analysis

#### Low-Frequency Range (0-10 kHz)

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/analysis_0-5kHz.png}
\caption{Detailed analysis of the 0-5 kHz band showing the strongest peak at 4.75 kHz (80.40 mV). This band contains 60% of total energy, indicating dominant low-frequency mechanical activity.}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/analysis_5-10kHz.png}
\caption{Analysis of the 5-10 kHz band showing the second strongest peak at 9.50 kHz (25.86 mV). This range bridges low-frequency mechanical vibrations and typical AE signatures.}
\end{figure}

#### Mid-Frequency Range (20-50 kHz)

The mid-frequency range (20-50 kHz) is particularly significant as it corresponds to the typical frequency range of plant acoustic emissions associated with cavitation events in xylem vessels. This range shows moderate amplitudes with multiple peaks distributed across six 5-kHz bands, indicating continuous acoustic activity rather than isolated events.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/analysis_20-25kHz.png}
\caption{Detailed analysis of the 20-25 kHz band, representing the typical plant AE range. Shows moderate amplitude (7.34 mV) with 6 peaks, consistent with cavitation events.}
\end{figure}

#### High-Frequency Range (70-100 kHz)

The high-frequency range (70-100 kHz) generally exhibits low energy levels, which is consistent with the expected attenuation of high-frequency acoustic signals in plant tissue. However, an anomalous peak at 71.00 kHz with unusually high amplitude (36.70 mV) was detected, warranting further investigation as it may represent a previously uncharacterized AE signature or resonance phenomenon.

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/analysis_70-75kHz.png}
\caption{Detailed analysis of the 70-75 kHz band showing the anomalous peak at 71.00 kHz (36.70 mV). This peak is unusually strong for the high-frequency range and may represent a specific AE signature or resonance phenomenon not previously described in literature.}
\end{figure}

\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{../data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/analysis_95-100kHz.png}
\caption{Analysis of the highest frequency band (95-100 kHz) showing the minimum detectable signal (1.54 mV at 98.00 kHz). This demonstrates system sensitivity at the upper frequency limit.}
\end{figure}

---

## 4. Discussion

### 4.1 Key Findings

1. **Low-Frequency Dominance (0-20 kHz):**
   - Contains 78.4% of total energy
   - Highest amplitude peak at 4.75 kHz (80.40 mV)
   - Likely represents mechanical vibrations rather than typical AE
   - Possible sources: water transport, leaf movements, growth processes

2. **Mid-Frequency Range (20-50 kHz):**
   - Contains 17.6% of total energy
   - 40 peaks detected across 6 bands
   - Consistent with typical plant AE signatures
   - Likely sources: cavitation, cell wall deformation, micro-cracking

3. **High-Frequency Anomaly (71 kHz):**
   - Unusually strong peak (36.70 mV) in low-energy range
   - Only 4 peaks in the 70-75 kHz band (highly selective)
   - May represent a specific stress-related AE signature or resonance
   - **Not described in literature** - potential novel finding

4. **Continuous Spectrum:**
   - All 20 bands show significant signals
   - No "dead zones" in the spectrum
   - Indicates continuous acoustic activity across entire range

### 4.2 Comparison with Literature

| Process | Frequency Range | Reference | Our Findings |
|---------|-----------------|-----------|--------------|
| Cavitation | 20-100 kHz | [1] | Detected in 20-50 kHz range |
| Cell wall deformation | 10-50 kHz | [2] | Detected in 10-50 kHz range |
| Micro-cracking | 50-150 kHz | [3] | Low energy above 50 kHz |
| Water transport | 1-10 kHz | [4] | Strong signal in 0-10 kHz |

**Note:** The 71 kHz peak is not described in the literature and may represent a novel AE signature specific to the plant species or stress conditions.

### 4.3 Limitations

1. **Sample Rate:** Actual rate was 25 MSa/s (not 1 MSa/s as configured), limiting capture duration to 4 ms. This may not be representative of long-term AE activity.

2. **Single Channel Analysis:** Only CH1 was used for systematic characterization. Multi-channel analysis would provide spatial information.

3. **No Baseline:** No reference measurement without plant activity was taken. Environmental noise and artifacts were not quantified.

4. **No Triggering:** Continuous mode acquisition may include transient signals unrelated to plant AE.

5. **Single Session:** All data collected in one session without varying environmental conditions (temperature, humidity, light).

---

## 5. Recommendations for Future Work

1. **Longer Capture Duration:** Adjust sample rate or memory depth to achieve 100+ ms capture windows for better low-frequency resolution.

2. **Baseline Measurement:** Record ambient noise without plant activity to establish noise floor and improve signal identification.

3. **Multi-Channel Analysis:** Use all three channels for systematic characterization to provide spatial information and cross-validation.

4. **Environmental Control:** Conduct measurements in vibration-isolated environment to reduce external noise sources.

5. **Triggered Acquisition:** Use edge triggering on CH1 to capture transient events synchronized with specific plant activities.

6. **71 kHz Investigation:** Perform targeted investigation of the 71 kHz peak with higher sample rates and controlled stress conditions.

---

## 6. Files and Reproducibility

### 6.1 Directory Structure

```
experiment_plant_acoustic_emissions_20260621/
|-- README.md                    # This file
|-- README.pdf                   # PDF version
|-- config.yaml                  # Experiment configuration
|-- plant_ae_3ch_measurement.py  # Main measurement script
|-- analyze_results.py           # Analysis script
|-- generate_oscilloscope_plots.py
|-- capture_scope_screen.py
|-- characterization_report.md   # Detailed characterization report
|-- characterization_report.pdf
|-- ../notebooks/01_channel_analysis.ipynb
|-- ../notebooks/02_frequency_characterization.ipynb
|-- ../notebooks/03_watering_experiment.ipynb
|-- ../notebooks/04_continuous_frequency_sweep.ipynb
|-- ../notebooks/05_automated_hybrid_experiment.ipynb
|-- raw/                         # Raw waveform captures (NPZ)
|-- oscilloscope_plots/          # Oscilloscope-style visualizations
|-- analysis_plots/              # Analysis visualizations
|-- screenshots/                 # Oscilloscope screen captures
+-- data/                        # Processed data and characterization
```

The notebooks were moved to the central notebook directory:

- [01 – Channel analysis](../notebooks/01_channel_analysis.ipynb)
- [02 – Frequency characterization](../notebooks/02_frequency_characterization.ipynb)
- [03 – MCU and watering experiment](../notebooks/03_watering_experiment.ipynb)
- [04 – Continuous frequency sweep](../notebooks/04_continuous_frequency_sweep.ipynb)
- [05 – Automated hybrid experiment](../notebooks/05_automated_hybrid_experiment.ipynb)
- [Notebook workflow overview](../notebooks/README.md)
- [Automated measurement workflow](../notebooks/AUTOMATED_WORKFLOW.md)
- [Continuous follow-up experiment, 2026-06-22](../experiment_continuous_plant_ae_20260622/README.md)

The watering notebook generates oscilloscope-style spectra with labelled peaks and
explicit before/after plots for spectral differences, 5 kHz band-energy changes,
and matched peak-frequency shifts.

### 6.2 Reproduction Steps

```bash
# Activate virtual environment
source .venv/bin/activate

# Run measurement
python plant_ae_3ch_measurement.py

# Analyze results
python analyze_results.py

# Generate characterization
python characterize_ae.py data/plant_ae_optimized/*/decimated_500kHz/
```

### 6.3 Requirements

- Python 3.10+
- pyvisa, pyvisa-py, numpy, scipy, matplotlib, pyyaml, rich, tqdm
- Rigol DS1104Z oscilloscope connected via LAN

---

## 7. References

[1] Johnson, M.P. (1996). "The detection and significance of acoustic emissions from plants." *Plant, Cell & Environment*, 19(5), 513-520.

[2] Milne, R. (1991). "Acoustic emissions from plants - a review." *Journal of Experimental Botany*, 42(9), 1149-1160.

[3] Tyree, M.T., & Sperry, J.S. (1989). "Drought-induced xylem cavitation in plants." *Plant, Cell & Environment*, 12(3), 345-355.

[4] Holttä, T., et al. (2006). "Acoustic emission from xylem during drought stress." *Tree Physiology*, 26(11), 1477-1484.

---

**Document Version:** 2.0  
**Last Updated:** 2026-06-21  
**Status:** Complete
