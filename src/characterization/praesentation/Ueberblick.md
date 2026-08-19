Signalvorverarbeitung (scope.preprocessing)

- DC-Entfernung, Detrending, Fensterung (Hann)
- Clipping-/Plausibilitätsprüfung der Rohaufnahmen

Spektrale Charakterisierung

- FFT (gemittelt über mehrere Captures) — analyze_results.py, scope.spectral.compute_fft
- Welch-PSD mit nperseg=8192 für hohe Frequenzauflösung — find_plant_ae.py, frequency_analysis.py:compute_psd/average_psd
- Bandenergien $E_b = \frac{1}{NM}\sum_n\sum_{m\in b}|X_n(m)|^2$ in 5-kHz-Bins (Paper Sec. 3.2)
- Peak-Detection (scipy.find_peaks) mit Prominenz-Schwelle, Mindestabstand, Ignorier-Bändern für 50-Hz-Netzbrummen + Harmonische; abgeleitet werden Frequenz, Prominenz, Bandbreite,
Q-Faktor und SNR

Detektions-/Vergleichsmethoden

- Baseline-vs-Active-Vergleich: signifikante neue Peaks, die nur unter Anregung auftreten (find_plant_ae.py:compare_baseline_vs_active)
- Repeatability-Check über wiederholte Captures (frequency_analysis.py:check_repeatability)
- Cross-Channel-Validierung — Peak nur echt, wenn auf mehreren Sensoren konsistent (cross_channel_validate)
- Sensor-Resonanz-Erkennung via Impuls-Antwort-Spektren, um Eigenmoden von echten AE zu trennen (load_impulse_spectra, is_sensor_resonance)

Zeit-/Kanalanalyse

- Kohärenz $\gamma^2(f)$ zwischen zwei Rod-Sensoren zur Bandbreiten-/Kalibrierungsbewertung (Gl. eq:coh)
- Time-Delay-Estimation (TDE): MLE über Phasendifferenz am Schmalband + Kreuzkorrelation als Cross-Check (scripts/calibrate_pico_sweep_phase3.py, Notebooks 08–12)

Statistische Tests (Paper Sec. 3.4)

- Wilcoxon Signed-Rank (Pre-/Post-Watering, gepaart)
- Mann-Whitney U (drift-korrigiert)
- Kendall τ (Trenddetektion)
- Benjamini-Hochberg FDR-Korrektur (α=0.05) bei Multiband-Vergleichen
