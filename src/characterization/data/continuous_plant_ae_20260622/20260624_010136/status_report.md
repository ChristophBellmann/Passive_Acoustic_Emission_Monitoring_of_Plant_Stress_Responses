# Continuous Plant AE Characterization - Status Report

**Generiert:** 2026-06-24 00:59:35
**Experiment:** continuous_plant_ae_20260622
**Run ID:** 20260624_010136
**Status:** running
**Laufzeit:** 118.0 Minuten (1:57:59.211170)

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

- **Total Frames:** 122
- **Frames mit Rolling-Events:** 12
- **Total Rolling-Events:** 15

### Kanal-Statistiken (Peaks)

| Kanal | Peaks/Frame (mean) | Prominenz mean (dB) | Prominenz range (dB) |
|-------|--------------------|---------------------|----------------------|
| CH1 | 18.0 | 52.8 | 43–99 |
| CH3 | 18.0 | 50.9 | 42–90 |
| CH4 | 19.9 | 48.9 | 41–86 |

### Frequenzband-Energie (5 kHz Bänder, alle Kanäle)

| Band | Energie (mean) | dB mean |
|------|----------------|---------|
| 0–5 kHz | 1.17e-02 | -38.6 |
| 5–10 kHz | 8.95e-04 | -47.0 |
| 10–15 kHz | 2.34e-04 | -51.1 |
| 15–20 kHz | 6.44e-05 | -54.9 |
| 20–25 kHz | 5.07e-05 | -53.8 |
| 25–30 kHz | 2.79e-05 | -54.2 |
| 30–35 kHz | 1.46e-05 | -59.0 |
| 35–40 kHz | 8.59e-06 | -60.5 |
| 40–45 kHz | 6.47e-06 | -61.3 |
| 45–50 kHz | 4.61e-06 | -62.0 |
| 50–55 kHz | 3.13e-06 | -62.9 |
| 55–60 kHz | 2.34e-06 | -64.0 |
| 60–65 kHz | 2.00e-06 | -64.4 |
| 65–70 kHz | 1.53e-06 | -65.0 |
| 70–75 kHz | 1.25e-06 | -65.2 |
| 75–80 kHz | 1.12e-06 | -65.2 |
| 80–85 kHz | 9.90e-07 | -66.1 |
| 85–90 kHz | 7.87e-07 | -66.7 |
| 90–95 kHz | 7.39e-07 | -66.9 |
| 95–100 kHz | 7.68e-07 | -66.7 |

## Umgebungsdaten

- **Datenpunkte:** 62
- **Bodenfeuchte (mean):** 26.5%
- **Bodenfeuchte (min):** 17.7%
- **Bodenfeuchte (max):** 37.5%

## Experiment-Events

- **Total Events:** 17

### Event-Typen

- **experiment_started:** 1
- **light_phase_changed:** 1
- **oscilloscope_connected:** 1
- **psd_snapshot_saved:** 2
- **spectral_change:** 12

## Zusammenfassung

Das Experiment läuft seit 118.0 Minuten und hat 122 Frames charakterisiert. 
Es wurden 15 Rolling-Events detektiert. 
Die durchschnittliche Bodenfeuchte beträgt 26.5%.

---

## Operator-Vorfall 2026-06-24 02:50

**Eingriff:** Fenster neben der Pflanze geschlossen + Oszilloskop auf den Boden gestellt.

**Zeitpunkt:** ~02:50:41 (Frame 118). Pre-Vorfall = 118 Frames, Post-Vorfall = 4 Frames (Stand 02:55).

### Amplituden-Vergleich (Prominenz dB)

| Frequenz | Kanal | Pre dB (n) | Post dB (n) | Δ dB | % | Bewertung |
|----------|-------|------------|-------------|------|---|-----------|
| 3.8 kHz | CH1 | 49.0±3.9 (22) | — | — | — | nicht in Post |
| 3.8 kHz | CH3 | 49.0±3.2 (89) | 51.8 (1) | +2.8 | +6% | n=1, unsicher |
| 3.8 kHz | CH4 | 48.4±3.5 (109) | 48.6±3.3 (4) | +0.1 | +0% | **stabil** |
| 6.5 kHz | CH3 | 71.2±6.2 (118) | 70.1±6.8 (4) | -1.2 | -2% | im Rauschen |
| 6.5 kHz | CH4 | 70.9±4.9 (118) | 70.8±5.0 (4) | -0.0 | -0% | **stabil** |
| 13.16 kHz | CH3 | 54.3±4.9 (84) | 56.4±7.8 (4) | +2.2 | +4% | im Rauschen |
| **13.16 kHz** | **CH4** | 53.2±5.6 (89) | **60.5±7.3 (4)** | **+7.3** | **+14%** | ⚠ **möglicher Anstieg** |

### Spektrale Band-Energie 0-100 kHz (Pre vs Post)
**Alle 20 Bänder: ΔdB < 1.5 dB** (siehe Tabelle oben). **Keine signifikanten Änderungen im Gesamtspektrum.**

### Bodenfeuchte
- Pre: 26.7 ± 4.2 % (n=118)
- Post: 23.0 ± 1.6 % (n=4)
- Δ = -3.6 % — **im Rahmen des normalen Trocknungstrends** (~1.2 %/h)

### Vorläufige Bewertung (n=4, vorläufig)

1. **3.8 kHz und 6.5 kHz**: keine signifikanten Amplituden-Änderungen → **Hauptbefunde stabil**
2. **13.16 kHz CH4: leichter Anstieg +7 dB** — möglicherweise neue Resonanz durch Oszi-Stellung am Boden
3. **Spektralbänder 0-100 kHz**: alle stabil → **kein globaler Pegel-Abfall**
4. **Bodenfeuchte**: sinkt weiter normal → kein Fenster-bedingter Effekt

**Vorsicht:** n=4 ist zu wenig für definitive Aussage. Erste Tendenz: **keine dauerhaften Amplituden-Einbrüche** bei den Hauptfrequenzen erkennbar. Wird mit mehr Daten aktualisiert.

---

*Report automatisch generiert um 2026-06-24 00:59:35*
*Operator-Vorfall-Vergleich ergänzt 2026-06-24 02:56*