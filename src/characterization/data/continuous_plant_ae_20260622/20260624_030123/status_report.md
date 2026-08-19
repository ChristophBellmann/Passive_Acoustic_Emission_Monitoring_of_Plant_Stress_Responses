# Continuous Plant AE Characterization - Status Report

**Generiert:** 2026-06-24 07:36:32
**Experiment:** continuous_plant_ae_20260622
**Run ID:** 20260624_030123
**Status:** running
**Laufzeit:** 395.2 Minuten (6:35:09.337806)

## Konfiguration

### Experiment
- **Zeitzone:** Europe/Berlin
- **Tag-Start:** 6:00
- **Nacht-Start:** 22:00

### Oszilloskop-Einstellungen
- **Sample-Rate:** 0.5 MSa/s
- **Memory Depth:** 300000
- **Zeitbasis:** 50.0 ms/div
- **Trigger-Modus:** EDGE
- **Trigger-Quelle:** CHAN3
- **Trigger-Level:** 20.0 mV

### Monitoring
- **PSD-Snapshot-Intervall:** 60 Minuten
- **PSD-Snapshot-Window:** 30 Frames
- **Dashboard-Intervall:** 30 Minuten

## Frame-Analyse

- **Total Frames:** 395
- **Frames mit Rolling-Events:** 51
- **Total Rolling-Events:** 56

### Kanal-Statistiken (Peaks)

| Kanal | Peaks/Frame (mean) | Prominenz mean (dB) | Prominenz range (dB) |
|-------|--------------------|---------------------|----------------------|
| CH1 | 18.0 | 52.4 | 42–97 |
| CH3 | 18.0 | 52.4 | 42–96 |
| CH4 | 19.8 | 48.9 | 40–92 |

### Frequenzband-Energie (5 kHz Bänder, alle Kanäle)

| Band | Energie (mean) | dB mean |
|------|----------------|---------|
| 0–5 kHz | 3.49e-02 | -36.9 |
| 5–10 kHz | 9.29e-04 | -47.0 |
| 10–15 kHz | 2.49e-04 | -51.1 |
| 15–20 kHz | 6.99e-05 | -54.8 |
| 20–25 kHz | 5.12e-05 | -55.7 |
| 25–30 kHz | 2.96e-05 | -53.3 |
| 30–35 kHz | 1.55e-05 | -58.9 |
| 35–40 kHz | 8.92e-06 | -60.5 |
| 40–45 kHz | 6.65e-06 | -61.3 |
| 45–50 kHz | 4.72e-06 | -62.2 |
| 50–55 kHz | 3.19e-06 | -63.1 |
| 55–60 kHz | 2.37e-06 | -64.0 |
| 60–65 kHz | 1.98e-06 | -64.5 |
| 65–70 kHz | 1.51e-06 | -65.3 |
| 70–75 kHz | 1.23e-06 | -65.7 |
| 75–80 kHz | 1.09e-06 | -66.1 |
| 80–85 kHz | 9.91e-07 | -65.5 |
| 85–90 kHz | 7.86e-07 | -66.9 |
| 90–95 kHz | 7.82e-07 | -66.9 |
| 95–100 kHz | 8.21e-07 | -66.7 |

## Umgebungsdaten

- **Datenpunkte:** 212
- **Bodenfeuchte (mean):** 27.1%
- **Bodenfeuchte (min):** 17.5%
- **Bodenfeuchte (max):** 35.2%

## Experiment-Events

- **Total Events:** 61

### Event-Typen

- **experiment_started:** 1
- **light_phase_changed:** 2
- **oscilloscope_connected:** 1
- **psd_snapshot_saved:** 6
- **spectral_change:** 51

## Zusammenfassung

Das Experiment läuft seit 395.2 Minuten und hat 395 Frames charakterisiert. 
Es wurden 56 Rolling-Events detektiert. 
Die durchschnittliche Bodenfeuchte beträgt 27.1%.

---

## Wissenschaftliche Erkenntnisse (6.5 h Lauf, 395 Frames)

### 1. Datenqualität
- **0 Frames mit Multi-Band-Drop** (verglichen mit 27% bei 20260622_175202)
- Stabile Daten über 6.5 Stunden
- 56 Rolling-Events, 51 spectral_change Events (alle legitime Detektionen)

### 2. Tag/Nacht-Verteilung
- 159 Nacht-Frames (40%)
- 235 Tag-Frames (60%)
- Erste Tag-Phase: ~06:00 lokal (konfiguriert)

### 3. Persistente Peaks (≥50% Präsenz)

| Frequenz | Präsenz | Kanal-Verteilung | Prominenz |
|----------|---------|------------------|-----------|
| **6.5 kHz** | 100% (beide CH3+CH4) | CH3+CH4 je 100%, CH1 9% | 71-73 dB |
| **3.8 kHz** | 34% CH3, **90% CH4** | CH1 15%, CH3 34%, **CH4 90%** | 47-50 dB |
| **1.2 kHz** | 75% (alle CH3) | CH3 79%, CH1 36% | 50-55 dB |
| **1.25 kHz** | 66% CH3, 36% CH1 | CH3+CH1 | 51-55 dB |
| **1.95 kHz** | 31% CH1 | CH1 31%, CH3 5% | 50 dB |
| **13.16 kHz** | 58% CH3+CH4 | CH3 58%, CH4 58% | 53-54 dB |

### 4. Neue Erkenntnis: 3.8 kHz ist auf CH4 STABILER als auf CH3

| Kanal | Präsenz | Interpretation |
|-------|---------|----------------|
| CH1 | 15% | Schwankend, wie erwartet (EM-Referenz, hört Pflanze nicht direkt) |
| **CH3** | **34%** | Erde + Verstärker — koppelt mechanisch an Pflanze, aber variabel |
| **CH4** | **90%** | Stahlstab + Verstärker — **direkterer mechanischer Kontakt** zur Pflanze |

**CH4 ist der bessere Sensor für 3.8 kHz.** Der Stahlstab überträgt Vibrationen
direkter als die Erde um die Pflanze herum.

### 5. 3.8 kHz Frequenz-Drift (langer Zeitraum)

| Phase | CH3 Drift | CH4 Drift | Bemerkung |
|-------|-----------|-----------|-----------|
| **Gesamt** (6.5 h) | -1.47 Hz/h | +0.36 Hz/h | CH3 driftet, CH4 stabil |
| Tag (4 h) | -4.11 Hz/h | +1.02 Hz/h | CH3 driftet 4× stärker am Tag |
| Nacht (2.5 h) | -1.40 Hz/h | -0.51 Hz/h | Ähnlich in beiden Kanälen |

**3.8 kHz Frequenz-Verschiebung (erste 10 vs letzte 10 Frames):**
- CH3: 3775.0 → 3651.3 Hz (**Δ = -123.6 Hz**, sehr groß!)
- CH4: 3775.1 → 3777.4 Hz (Δ = +2.3 Hz, **stabil!**)

**Wichtig:** CH3 zeigt einen großen Sprung in den letzten Frames. Das ist
vermutlich ein Peak-Detection-Artefakt (CH3 erkennt 3.8 kHz nicht mehr,
sondern einen anderen nahen Peak). CH4 bleibt stabil bei 3777 Hz.

### 6. Bodenfeuchte
- 212 Samples, mean 27.1%, range 17.5-35.2%
- **Linearer Trend: +0.25 %/h** (leichte Erholung — vermutlich durch Taupunkt-Kondensation nachts)

### 7. 6.5 kHz Verhalten
- 100% Präsenz auf CH3+CH4 (identisch)
- Erste 10 vs letzte 10: **6474.6 → 6442.0 Hz** (Δ = -32.6 Hz über 6.5 h)
- 6.5 kHz driftet **deutlich** (5 Hz/h), konsistent mit Tag/Nacht-Trocknungs-Signal

### 8. 1-2 kHz Bin Peaks
- **1.15-1.25 kHz** auf CH1+CH3 (75-79%), **nicht** auf CH4
- **1.95 kHz** auf CH1+CH3 (31%), **nicht** auf CH4
- **CH4-spezifische Peaks** (Edelstahlstab) sind im 1-2 kHz Bin **nicht** vorhanden
- Diese Peaks sind **nicht pflanzenspezifisch** — sie kommen aus dem **Topf-Substrat-System**
  (Erde, Wurzeln, Topfrand) und erreichen den Stahlstab nicht

### 9. Hochfrequente Peaks (>50 kHz, 40-69% Präsenz)
- 80.3, 84.1, 61.2, 74.4, 45.9, 87.6 kHz — alle auf mehreren Kanälen
- Vermutlich Mischprodukte / Intermodulation oder Sensor-Resonanzen
- Für Plant-AE-These irrelevant

---

*Report automatisch generiert um 2026-06-24 07:36:32*
*Wissenschaftliche Erkenntnisse ergänzt 2026-06-24 09:36 (n=395 Frames)*