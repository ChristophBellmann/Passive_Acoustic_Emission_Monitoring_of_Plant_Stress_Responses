# Daten-Dezimierung für Pflanzen-AE-Messungen

## Problem

Das Rigol DS1104Z Oszilloskop nimmt mit maximaler Sample-Rate auf:
- **1 GSa/s** bei kurzen Zeitbasen (≤1ms/div)
- **25 MSa/s** bei längeren Zeitbasen (≥10ms/div)

Für Pflanzen-Akustische-Emissionen (AE) mit maximaler Zielfrequenz von **100 kHz** ist das massiv überdimensioniert:
- Nyquist-Shannon: mindestens 200 kHz nötig
- 1 GSa/s = 5000× Überabtastung

## Lösung

**Dezimierung**: Reduzierung der Sample-Rate nach der Messung

### Empfohlene Konfiguration

**Messung:**
- Zeitbasis: **100 µs/div**
- Sample-Rate: **1 GSa/s** (automatisch)
- Punkte: **1.200.000**
- Aufnahmezeit: **1.2 ms**
- Nyquist: **500 MHz**

**Dezimierung:**
- Ziel-Sample-Rate: **500 kHz** (5× Nyquist für 100 kHz)
- Dezimationsfaktor: **2000**
- Ergebnis: **600 Punkte** für **1.2 ms**

### Vorteile

✅ **Perfekte Frequenzauflösung**: 500 kHz >> 100 kHz (keine Aliasing-Probleme)  
✅ **Handhabbare Datenmengen**: 600 Punkte statt 1.2M  
✅ **Schnelle Übertragung**: Dezimierung dauert <1 Sekunde  
✅ **Qualitätserhalt**: Anti-Aliasing-Filter verhindert Informationsverlust

## Verwendung

### 1. Daten dezimieren

```bash
# Aktiviere virtuelle Umgebung
source .venv/bin/activate

# Dezimiere alle Dateien in einem Verzeichnis
python decimate_data.py data/plant_ae_20260621_120000/

# Mit benutzerdefinierter Ziel-Sample-Rate (z.B. 250 kHz)
python decimate_data.py data/plant_ae_20260621_120000/ -r 250000

# Mit benutzerdefiniertem Ausgabeverzeichnis
python decimate_data.py data/plant_ae_20260621_120000/ -o data/decimated/
```

### 2. Daten analysieren

```bash
# Erstelle Analyse-Plots für dezimierte Daten
python analyze_decimated.py data/plant_ae_20260621_120000/decimated_500kHz/

# Mit benutzerdefinierter Ausgabedatei
python analyze_decimated.py data/plant_ae_20260621_120000/decimated_500kHz/ -o analysis.png
```

### 3. Ergebnis

**Vorher (Rohdaten):**
```
Sample-Rate: 1000.0 MSa/s
Punkte: 1200000
Aufnahmezeit: 1.20 ms
Dateigröße: ~9.6 MB pro Datei
```

**Nachher (dezimiert):**
```
Sample-Rate: 500.0 kHz
Punkte: 600
Aufnahmezeit: 1.20 ms
Dateigröße: ~5 KB pro Datei
Reduktion: 2000×
```

## Technische Details

### Dezimierungsalgorithmus

Das Skript verwendet `scipy.signal.decimate` mit:
- **FIR-Filter** (Finite Impulse Response)
- **Anti-Aliasing**: Tiefpassfilter vor Dezimierung
- **Qualitätserhalt**: Keine Informationsverluste im Frequenzbereich <100 kHz

### Warum 500 kHz?

Für eine maximale Zielfrequenz von 100 kHz:
- **Nyquist**: mindestens 200 kHz
- **Empfehlung**: 5-10× Nyquist für gute Qualität
- **500 kHz**: 5× Nyquist → optimale Qualität

### Alternative Sample-Rates

| Ziel-Frequenz | Min. Sample-Rate | Empfohlen | Dezimationsfaktor |
|---------------|------------------|-----------|-------------------|
| 100 kHz       | 200 kHz          | 500 kHz   | 2000              |
| 50 kHz        | 100 kHz          | 250 kHz   | 4000              |
| 20 kHz        | 40 kHz           | 100 kHz   | 10000             |

## Workflow

```
1. Messung mit 100µs/div (1 GSa/s, 1.2ms)
   ↓
2. Daten speichern (1.2M Punkte, ~9.6 MB)
   ↓
3. Dezimieren auf 500 kHz (600 Punkte, ~5 KB)
   ↓
4. Analysieren (FFT, Peak-Detection)
   ↓
5. Ergebnisse interpretieren
```

## Beispiel

```bash
# Kompletter Workflow
source .venv/bin/activate

# 1. Messung durchführen (mit plant_ae_3ch_measurement.py)
python plant_ae_3ch_measurement.py

# 2. Daten dezimieren
python decimate_data.py data/plant_ae_20260621_120000/

# 3. Daten analysieren
python analyze_decimated.py data/plant_ae_20260621_120000/decimated_500kHz/

# 4. Ergebnisse anzeigen
# → analysis.png öffnen
```

## Häufige Fragen

**Q: Warum nicht direkt mit niedrigerer Sample-Rate messen?**  
A: Das Rigol DS1104Z unterstützt keine einstellbare Sample-Rate über SCPI. Es verwendet immer das Maximum (1 GSa/s oder 25 MSa/s).

**Q: Gehen durch die Dezimierung Informationen verloren?**  
A: Nein, wenn die Ziel-Sample-Rate mindestens 2× der maximalen Signalfrequenz entspricht (Nyquist). Der Anti-Aliasing-Filter stellt dies sicher.

**Q: Kann ich auch andere Sample-Rates verwenden?**  
A: Ja, mit dem `-r` Parameter. Für 100 kHz Zielfrequenz sind 250-500 kHz empfehlenswert.

**Q: Wie lange dauert die Dezimierung?**  
A: Sehr schnell. 1.2M Punkte auf 600 dezimieren dauert <1 Sekunde auf einem modernen Computer.

## Referenzen

- [Nyquist-Shannon Abtasttheorem](https://de.wikipedia.org/wiki/Nyquist-Shannon-Abtasttheorem)
- [scipy.signal.decimate Dokumentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.decimate.html)
- [Anti-Aliasing Filter](https://de.wikipedia.org/wiki/Anti-Aliasing-Filter)
