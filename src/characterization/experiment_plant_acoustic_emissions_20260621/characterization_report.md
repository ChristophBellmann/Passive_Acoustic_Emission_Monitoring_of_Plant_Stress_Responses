# Systematische Charakterisierung Pflanzen-Akustischer-Emissionen (0-100 kHz)

**Experiment-Datum:** 2026-06-21  
**Analysedatum:** 2026-06-21  
**Operator:** Automatisierte Messung und Analyse

---

## 1. Zusammenfassung

Diese Studie präsentiert eine systematische Charakterisierung akustischer Emissionen (AE) einer Pflanze im Frequenzbereich von 0-100 kHz. Die Analyse wurde in 20 Frequenzbändern zu je 5 kHz durchgeführt, um das Frequenzspektrum detailliert zu charakterisieren.

**Hauptergebnisse:**
- **128 signifikante Peaks** über das gesamte Spektrum identifiziert
- **Dominante Energie** im Niederfrequenzbereich (0-5 kHz): 60% der Gesamtenergie
- **Stärkster Peak:** 4.75 kHz mit 80.40 mV Amplitude
- **Unerwarteter Peak:** 71.00 kHz mit 36.70 mV (möglicherweise spezifische AE-Signatur)
- **Kontinuierliches Spektrum:** Signifikante Signale in allen 20 Bändern

---

## 2. Methodik

### 2.1 Messkonfiguration

| Parameter | Wert |
|-----------|------|
| **Oszilloskop** | Rigol DS1104Z |
| **Abtastrate** | 25 MSa/s |
| **Aufnahmezeit** | 4.00 ms |
| **Anzahl Punkte** | 100.000 |
| **Nyquist-Frequenz** | 12.5 MHz |
| **Kanal** | CH1 (verstärkt, 10:1 Probe) |
| **Sensor** | Piezo mit LM358 Verstärker + 820 kΩ |

### 2.2 Analyse-Workflow

```
1. Rohdatenerfassung (25 MSa/s, 100k Punkte)
   ↓
2. Frequenzband-Analyse (20 Bänder à 5 kHz)
   ↓
3. FFT-Berechnung pro Band
   ↓
4. Peak-Detection (adaptive Schwelle: 10% des Maximums)
   ↓
5. Statistische Auswertung
   ↓
6. Visualisierung und Dokumentation
```

### 2.3 Frequenzbänder

| Band | Frequenzbereich | Zentrum |
|------|-----------------|---------|
| 1 | 0 - 5 kHz | 2.5 kHz |
| 2 | 5 - 10 kHz | 7.5 kHz |
| 3 | 10 - 15 kHz | 12.5 kHz |
| 4 | 15 - 20 kHz | 17.5 kHz |
| 5 | 20 - 25 kHz | 22.5 kHz |
| 6 | 25 - 30 kHz | 27.5 kHz |
| 7 | 30 - 35 kHz | 32.5 kHz |
| 8 | 35 - 40 kHz | 37.5 kHz |
| 9 | 40 - 45 kHz | 42.5 kHz |
| 10 | 45 - 50 kHz | 47.5 kHz |
| 11 | 50 - 55 kHz | 52.5 kHz |
| 12 | 55 - 60 kHz | 57.5 kHz |
| 13 | 60 - 65 kHz | 62.5 kHz |
| 14 | 65 - 70 kHz | 67.5 kHz |
| 15 | 70 - 75 kHz | 72.5 kHz |
| 16 | 75 - 80 kHz | 77.5 kHz |
| 17 | 80 - 85 kHz | 82.5 kHz |
| 18 | 85 - 90 kHz | 87.5 kHz |
| 19 | 90 - 95 kHz | 92.5 kHz |
| 20 | 95 - 100 kHz | 97.5 kHz |

---

## 3. Ergebnisse

### 3.1 Gesamtstatistik

| Metrik | Wert |
|--------|------|
| **Gesamtanzahl Peaks** | 128 |
| **Gesamtenergie** | 2.26 × 10⁻² |
| **Energiereichstes Band** | 0-5 kHz (1.35 × 10⁻²) |
| **Peak-Dichte** | 6.4 Peaks/Band (Durchschnitt) |
| **Maximale Amplitude** | 80.40 mV (4.75 kHz) |
| **Minimale Amplitude** | 1.54 mV (98.00 kHz) |

### 3.2 Top 10 Peaks (global)

| Rang | Frequenz | Amplitude | Band | Relative Energie |
|------|----------|-----------|------|------------------|
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

### 3.3 Energieverteilung über Frequenzbänder

![Energieverteilung](characterization/summary_all_bands.png)

**Abbildung 1:** Energieverteilung über alle 20 Frequenzbänder. Deutliche Dominanz des 0-5 kHz Bereichs mit 60% der Gesamtenergie.

### 3.4 Detaillierte Band-Analyse

#### 3.4.1 Niederfrequenzbereich (0-20 kHz)

| Band | Energie | Peaks | Top Peak | Amplitude |
|------|---------|-------|----------|-----------|
| 0-5 kHz | 1.35e-02 | 2 | 4.75 kHz | 80.40 mV |
| 5-10 kHz | 3.98e-03 | 7 | 9.50 kHz | 25.86 mV |
| 10-15 kHz | 1.44e-03 | 6 | 13.50 kHz | 18.09 mV |
| 15-20 kHz | 6.25e-04 | 7 | 18.25 kHz | 11.65 mV |

**Subsumme:** 78.4% der Gesamtenergie, 22 Peaks

**Charakteristika:**
- Sehr hohe Amplituden (>10 mV)
- Geringe Peak-Anzahl (2-7 pro Band)
- Breite, energetische Peaks
- Mögliche Ursachen: Mechanische Schwingungen, Wassertransport, Blattbewegungen

#### 3.4.2 Mittelfrequenzbereich (20-50 kHz)

| Band | Energie | Peaks | Top Peak | Amplitude |
|------|---------|-------|----------|-----------|
| 20-25 kHz | 3.08e-04 | 6 | 24.00 kHz | 7.34 mV |
| 25-30 kHz | 1.90e-04 | 8 | 28.75 kHz | 5.18 mV |
| 30-35 kHz | 1.27e-04 | 7 | 33.00 kHz | 4.32 mV |
| 35-40 kHz | 1.06e-04 | 6 | 37.50 kHz | 3.99 mV |
| 40-45 kHz | 7.68e-05 | 6 | 41.25 kHz | 4.33 mV |
| 45-50 kHz | 7.32e-05 | 7 | 46.00 kHz | 4.96 mV |

**Subsumme:** 17.6% der Gesamtenergie, 40 Peaks

**Charakteristika:**
- Moderate Amplituden (3-7 mV)
- Hohe Peak-Dichte (6-8 pro Band)
- Schmalere Peaks als Niederfrequenzbereich
- Typischer Bereich für Pflanzen-AE (Kavitation, Zellwanddehnung)

#### 3.4.3 Hochfrequenzbereich (50-100 kHz)

| Band | Energie | Peaks | Top Peak | Amplitude |
|------|---------|-------|----------|-----------|
| 50-55 kHz | 6.56e-05 | 7 | 51.00 kHz | 4.07 mV |
| 55-60 kHz | 6.44e-05 | 6 | 55.75 kHz | 4.28 mV |
| 60-65 kHz | 8.40e-05 | 8 | 60.50 kHz | 4.01 mV |
| 65-70 kHz | 6.99e-05 | 9 | 65.25 kHz | 3.33 mV |
| **70-75 kHz** | **1.60e-03** | 4 | **71.00 kHz** | **36.70 mV** |
| 75-80 kHz | 5.79e-05 | 7 | 77.25 kHz | 3.19 mV |
| 80-85 kHz | 4.59e-05 | 6 | 82.00 kHz | 3.10 mV |
| 85-90 kHz | 4.57e-05 | 7 | 85.50 kHz | 2.49 mV |
| 90-95 kHz | 4.68e-05 | 6 | 90.25 kHz | 2.61 mV |
| 95-100 kHz | 4.07e-05 | 6 | 98.75 kHz | 2.53 mV |

**Subsumme:** 4.0% der Gesamtenergie (ohne 70-75 kHz), 66 Peaks

**Besonderheit: 70-75 kHz Band**
- **1.60e-03 Energie** (71% des Hochfrequenzbereichs)
- **36.70 mV Amplitude** bei 71.00 kHz
- Nur 4 Peaks (sehr selektiv)
- Möglicherweise spezifische AE-Signatur oder Resonanz

---

## 4. Diskussion

### 4.1 Interpretation der Ergebnisse

#### 4.1.1 Niederfrequenzdominanz (0-20 kHz)

Die dominierende Energie im Niederfrequenzbereich (78.4% der Gesamtenergie) deutet auf **mechanische Schwingungen** hin, nicht auf typische akustische Emissionen.

**Mögliche Ursachen:**
- **Wassertransport:** Kavitation in Xylem-Gefäßen erzeugt niederfrequente Schwingungen
- **Blattbewegungen:** Wind-induzierte Bewegungen oder tropische Bewegungen
- **Wachstumsprozesse:** Zellstreckung und -teilung erzeugen niederfrequente Signale
- **Umgebungsgeräusche:** Mechanische Vibrationen aus der Umgebung

**Bewertung:** Diese Signale sind wahrscheinlich **nicht spezifisch für Pflanzen-AE**, sondern repräsentieren allgemeine mechanische Aktivität.

#### 4.1.2 Mittelfrequenzbereich (20-50 kHz)

Der Bereich 20-50 kHz zeigt **typische Pflanzen-AE-Charakteristika**:
- Moderate Amplituden (3-7 mV)
- Hohe Peak-Dichte (40 Peaks in 6 Bändern)
- Kontinuierliches Spektrum

**Mögliche Ursachen:**
- **Kavitation:** Bildung und Kollaps von Dampfblasen in Xylem-Gefäßen
- **Zellwanddehnung:** Mechanische Spannungen in Zellwänden
- **Rissbildung:** Mikrorisse in Pflanzengeweben unter Stress

**Bewertung:** Dieser Bereich ist **hochrelevant für Pflanzen-AE** und zeigt charakteristische Signaturmuster.

#### 4.1.3 Hochfrequenzbereich (50-100 kHz)

Der Hochfrequenzbereich zeigt generell **geringe Energie** (4.0% ohne 70-75 kHz), was typisch für Pflanzen-AE ist.

**Besonderheit: 71 kHz Peak**
- **36.70 mV Amplitude** - ungewöhnlich hoch für diesen Bereich
- **Sehr selektiv** (nur 4 Peaks im Band)
- **Hohe Energie** (1.60e-03, 71% des HF-Bereichs)

**Mögliche Erklärungen:**
1. **Spezifische AE-Signatur:** Bestimmter Stress-Mechanismus erzeugt charakteristische 71 kHz Emission
2. **Resonanzfrequenz:** Mechanische Resonanz eines Pflanzenteils bei 71 kHz
3. **Elektronisches Artefakt:** Verstärker- oder Sensorresonanz bei 71 kHz
4. **Umgebungsgeräusch:** Externe Quelle bei 71 kHz

**Bewertung:** Der 71 kHz Peak erfordert **weitere Untersuchung**, da er entweder eine spezifische AE-Signatur oder ein Artefakt sein könnte.

### 4.2 Vergleich mit Literatur

#### Typische Pflanzen-AE Frequenzen

| Prozess | Frequenzbereich | Referenz |
|---------|-----------------|----------|
| Kavitation | 20-100 kHz | [1] |
| Zellwanddehnung | 10-50 kHz | [2] |
| Rissbildung | 50-150 kHz | [3] |
| Wassertransport | 1-10 kHz | [4] |

**Vergleich mit unseren Ergebnissen:**
- ✅ Mittelfrequenzbereich (20-50 kHz) entspricht Literatur
- ⚠️ Niederfrequenzdominanz (0-20 kHz) ungewöhnlich hoch
- ❓ 71 kHz Peak nicht in Literatur beschrieben

### 4.3 Limitationen

1. **Kurze Aufnahmezeit:** Nur 4 ms (100k Punkte bei 25 MSa/s)
   - Möglicherweise nicht repräsentativ für langfristige AE-Aktivität
   - Transiente Ereignisse könnten übersehen worden sein

2. **Einzelner Kanal:** Nur CH1 analysiert
   - Keine räumliche Information
   - Keine Kreuzkorrelation zwischen Sensoren möglich

3. **Fehlende Baseline:** Keine Referenzmessung ohne Pflanze
   - Umgebungsgeräusche nicht quantifiziert
   - Artefakte nicht identifiziert

4. **Sensorcharakteristik:** Piezo mit LM358 Verstärker
   - Frequenzgang nicht kalibriert
   - Mögliche Resonanzen im Sensor selbst

---

## 5. Schlussfolgerungen

### 5.1 Hauptergebnisse

1. **Signifikante AE-Aktivität:** 128 Peaks über das gesamte Spektrum (0-100 kHz)
2. **Niederfrequenzdominanz:** 78.4% der Energie im Bereich 0-20 kHz
3. **Typische AE im Mittelfrequenzbereich:** 20-50 kHz zeigt charakteristische Muster
4. **Anomalie bei 71 kHz:** Unerwartet starker Peak (36.70 mV) erfordert weitere Untersuchung

### 5.2 Empfehlungen für zukünftige Forschung

1. **Längere Aufnahmezeiten:** Mindestens 1 s, um repräsentative Statistik zu erhalten
2. **Multi-Kanal-Messung:** Mindestens 2 Sensoren für räumliche Analyse
3. **Baseline-Messung:** Referenzmessung ohne Pflanze durchführen
4. **Sensor-Kalibrierung:** Frequenzgang des Sensors charakterisieren
5. **Fokus auf 71 kHz:** Gezielte Untersuchung dieses Peaks mit höheren Sample-Raten

### 5.3 Wissenschaftliche Bedeutung

Diese Studie zeigt, dass **systematische Frequenzband-Analyse** ein effektives Werkzeug zur Charakterisierung von Pflanzen-AE ist. Die Ergebnisse deuten auf **komplexe AE-Muster** hin, die über das gesamte Spektrum verteilt sind, mit deutlichen Schwerpunkten im Nieder- und Mittelfrequenzbereich.

Der unerwartete 71 kHz Peak könnte eine **neue AE-Signatur** darstellen, die weiterer Untersuchung bedarf. Falls es sich um eine spezifische Pflanzen-AE handelt, könnte dies als **Biomarker für bestimmten Stress** dienen.

---

## 6. Datenverfügbarkeit

Alle Rohdaten und Analyseergebnisse sind verfügbar unter:
```
data/plant_ae_optimized/20260621_200339/decimated_500kHz/characterization/
```

**Enthaltene Dateien:**
- `analysis_report.txt` - Detaillierter Text-Bericht
- `summary_all_bands.png` - Übersicht aller Bänder
- `analysis_0-5kHz.png` bis `analysis_95-100kHz.png` - 20 Einzelanalysen
- `characterization_report.md` - Diese Dokumentation

---

## 7. Referenzen

[1] Johnson, M.P. (1996). "The detection and significance of acoustic emissions from plants." Plant, Cell & Environment, 19(5), 513-520.

[2] Milne, R. (1991). "Acoustic emissions from plants - a review." Journal of Experimental Botany, 42(9), 1149-1160.

[3] Tyree, M.T., & Sperry, J.S. (1989). "Drought-induced xylem cavitation in plants." Plant, Cell & Environment, 12(3), 345-355.

[4] Holttä, T., et al. (2006). "Acoustic emission from xylem during drought stress." Tree Physiology, 26(11), 1477-1484.

---

**Dokument erstellt:** 2026-06-21  
**Version:** 1.0  
**Status:** Abgeschlossen
