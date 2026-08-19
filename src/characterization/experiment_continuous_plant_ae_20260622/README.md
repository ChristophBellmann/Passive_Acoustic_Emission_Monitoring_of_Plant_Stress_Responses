# Kontinuierliche Pflanzen-AE-Charakterisierung

**Experimentdatum:** 22. Juni 2026  
**Vorgängerexperiment:** 21. Juni 2026  
**Zugehörige Analyse:** `frequency_analysis.py`

> **Stand 2026-06-27: `continuous_characterization.py` archiviert.**
> Das Standalone-Skript war bis 24.06.2026 in Betrieb (letzte Session: `20260624_160540`).
> Seit 2026-06-26 ist **`notebooks/04_continuous_frequency_sweep.ipynb` (NB04)** der einzige
> kanonische Erzeuger für neue Continuous-Sessions, gestartet via `./measurement.py start`.
> Das archivierte Skript liegt unter `_archived/continuous_characterization.py` und wird
> nicht mehr ausgeführt. Für die Paper-Reproduzierbarkeit der früheren Runs
> (`20260622_175202`, `20260624_160540`) sind die Datendateien vollständig erhalten.
>
> Neue Sessions schreiben nach `data/reports/notebooks/04_continuous_frequency_sweep/<session_id>/`.

> **Warnung Datenqualität:** Der Continuous-Lauf `20260622_175202` (17:52–19:05, 310 Frames) ist **kompromittiert** — 83 Multi-Band-Drop-Events während laufender Sensor-Verdrahtung. Siehe [`INCIDENT_REPORT.md`](./INCIDENT_REPORT.md) für die Analyse. **Nicht für Paper-Statistiken verwenden.** Saubere Daten aus dem Zeitfenster: Pilot-Snapshot-Sweeps `20260622_190618/190723/192633` und Continuous `20260623_233855`.

## Korrektive Anmerkung zu den Vorgängerergebnissen (2026-06-21)

Die im Vorgänger-README als *„neuartige Pflanzensignatur bei 71 kHz"*
bezeichnete Frequenz ist eine **Sensorresonanz** des piezoelektrischen
Aufnehmers.  Dies wurde durch Kreuzreferenz mit der Impulse-Response-Messung
(freier Ausschwingvorgang des Sensors) nachgewiesen: die 71-kHz-Linie tritt
mit 29 dB Prominenz sowohl im Pflanzensignal als auch im Ausschwingen ohne
Pflanzensignal auf.

Der stärkste validierte Pflanzen-AE-Kandidat der Voruntersuchung liegt bei
**4,3 kHz** (SNR 28 dB, 89 % Repeatability, CH1 + CH3 — Phase 1 Setup mit CH1+CH2+CH3).
> **Achtung:** Diese Aussage stammt aus einem **Phase-1-Bericht** (vor CH2-Ausfall am 2026-06-22). Im aktuellen **Phase-2-Setup (CH1+CH3+CH4, CH2 defekt)** ist der entsprechende Befund **3,8 kHz auf CH3+CH4** (16/16 Frames, Prominenz ~49 dB, siehe aktuellen `status_report.md`). Die Phase-1-Aussage „absent on CH2" ist mit totem CH2 **nicht mehr falsifizierbar** und stellt **keine unabhängige Replikation** des Phase-2-Befundes dar. Siehe [`HARDWARE_CHANGELOG.md`](./HARDWARE_CHANGELOG.md).

Weitere Kandidaten
befinden sich im Bereich 10–25 kHz, konsistent mit Literaturwerten für
Kavitations- und Wassertransport-AE.

Das vorliegende Dauerexperiment zielt darauf ab, diese Kandidaten über
mehrere Tage und Nächte zu verfolgen und den Einfluss von Tageszeit und
Bodenfeuchte zu quantifizieren.

---

Dieses Experiment führt die Charakterisierung vom 21. Juni 2026 als
kontinuierliche Messung fort. Das Dauerprofil arbeitet mit 500 kSa/s,
300.000 Punkten und einem synchronen 0,6-s-Fenster für alle drei Kanäle. Das
ergibt 1,67 Hz FFT-Auflösung und 250 kHz Nyquist-Frequenz. Ausgewertet werden
alle zwanzig 5-kHz-Bänder zwischen 0 und 100 kHz.

Zusätzlich werden regelmäßig protokolliert:

- Tag oder Nacht anhand der lokalen Uhrzeit in `Europe/Berlin`,
- Bodenfeuchte aus
  `sensor.pflanze_1_pflanze_1_bodenfeuchte`,
- Pumpenstatus,
- Status des Home-Assistant-Bewässerungsskripts,
- erkannte Peaks, Peakwanderungen und Änderungen der Bandenergie.

Ereignisse werden konservativ gefiltert:

- persistente Peaks müssen über mindestens zwölf Frames auf mindestens zwei
  Kanälen auftreten;
- Frequenzdrift wird zeitbasiert in Hz/s berechnet und nur bei paralleler Drift
  mehrerer Kanäle gemeldet;
- Bandenergieänderungen benötigen Persistenz und mindestens zwei Kanäle;
- 50-Hz-Netzfrequenz und ihre Harmonischen bis 1 kHz werden nicht als
  Pflanzenereignis gewertet.

## Sicherheitsmodell

Das Programm bewässert standardmäßig nicht. Eine automatische Bewässerung
erfordert ausdrücklich die Startoption `--enable-watering`. Die Fähigkeit kann
zusätzlich mit `watering.enabled: false` in `config.yaml` vollständig gesperrt
werden.

Ist beides aktiviert, wird nach der konfigurierten Vorlaufzeit genau einmal das
bestehende Home-Assistant-Skript gestartet. Die AE-Messung läuft dabei ohne
Unterbrechung weiter. Optional kann zusätzlich ein maximaler
Bodenfeuchtewert als Bedingung eingetragen werden.

## Hardware prüfen

Vom Projektstamm aus:

```bash
source src/characterization/.venv/bin/activate
python src/characterization/experiment_continuous_plant_ae_20260622/continuous_characterization.py --check-only
```

Dieser Aufruf liest Bodenfeuchte und Zustände, prüft das Oszilloskop und startet
keine Bewässerung.

## Dauerexperiment starten

Ohne automatische Bewässerung:

```bash
source src/characterization/.venv/bin/activate
python src/characterization/experiment_continuous_plant_ae_20260622/continuous_characterization.py
```

Beenden mit `Ctrl+C`. Dabei werden Manifest, Abschlussgrafik und Peak-Tabelle
sauber fertiggeschrieben.

Für einen begrenzten Lauf, beispielsweise 24 Stunden:

```bash
python src/characterization/experiment_continuous_plant_ae_20260622/continuous_characterization.py --duration-hours 24
```

Mit ausdrücklich aktivierter einmaliger Bewässerung:

```bash
python src/characterization/experiment_continuous_plant_ae_20260622/continuous_characterization.py --enable-watering
```

Vor diesem letzten Aufruf muss `watering.enabled` in `config.yaml` bewusst auf
`true` stehen. Dies ist in der mitgelieferten Konfiguration der Fall; ohne die
Startoption wird trotzdem nie bewässert.

## Tag und Nacht

Die Standardgrenzen sind:

- Tag: 06:00 bis 21:59 Uhr;
- Nacht: 22:00 bis 05:59 Uhr.

Die Einordnung erfolgt ausschließlich anhand der lokalen Uhrzeit und ist daher
reproduzierbar. Sie berücksichtigt bewusst nicht das aktuelle Wetter oder die
astronomischen Sonnenauf- und -untergangszeiten. Die Grenzen können in
`config.yaml` geändert werden.

## Datenspeicherung

Jeder Start erzeugt einen eigenen Ordner:

```text
src/characterization/data/continuous_plant_ae_20260622/<Zeitstempel>/
├── manifest.json
├── frame_characterization.jsonl   # Bandenergie + Peaks pro Frame
├── environment.jsonl              # Bodenfeuchte, Pumpe, Tag/Nacht
├── experiment_events.jsonl        # Zustandsänderungen und Snapshots
├── continuous_summary.png
├── peak_tracks.csv
├── dashboards/                    # Visuelles Dashboard alle 30 min
├── psd_snapshots/                 # Komprimierte Welch-PSD alle 60 min
│   └── psd_snapshot_<ISO>_seq<N>.npz
└── rolling_events/
```

### Kompakte PSD-Snapshots

Alle 60 Minuten (konfigurierbar in `config.yaml`) wird ein komprimiertes
NPZ-Archiv mit dem gemittelten Welch-PSD der letzten 30 Frames aller Kanäle
gespeichert. Jede Datei enthält:

- `frequencies` – Frequenzachse in Hz (float32)
- `mean_psd` – mittlere PSD V²/Hz über Frames × Kanäle (float32)
- `band_energy` – 3 × 20 Bandenergie-Matrix (float32)
- `n_frames` – Anzahl gemittelter Frames

Größe pro Snapshot: ≈ 50–100 kB.  Diese Dateien ermöglichen die
wissenschaftliche Frequenzanalyse ohne Zugriff auf den RAM-Ring.

### Dezimationshinweis für Rohwaveforms

Falls Rohdaten nachträglich auf eine niedrigere Abtastrate konvertiert werden
sollen (z. B. von 25 MSa/s auf 500 kSa/s für Langzeitarchive), muss ein
Anti-Aliasing-Filter angewandt werden:

```python
from scipy.signal import decimate
# Faktor 50: 25 MSa/s → 500 kSa/s
voltage_decimated = decimate(voltage_raw, q=50, ftype='fir', zero_phase=True)
```

Kein naives Striding (`voltage_raw[::50]`) – das faltet Hochfrequenzrauschen
in den Analysebereich und erzeugt Phantompeaks.

Der vollständige Wellenformverlauf bleibt in einem begrenzten RAM-Ring. Dauerhaft
gespeichert werden kompakte Frequenz-, Bandenergie-, Umwelt- und
Ereignisdatensätze sowie periodische Dashboards.

Mit den Standardwerten darf der Prozess höchstens 75 Prozent des physischen
RAMs verwenden und hält zugleich mindestens 4 GiB für Betriebssystem und
Jupyter frei.

## Wissenschaftliche Auswertung

`frame_characterization.jsonl` verbindet jeden AE-Frame mit:

- lokaler und UTC-Zeit,
- Tag-/Nachtphase,
- Bodenfeuchte,
- gleitendem Median der letzten zehn Bodenfeuchtewerte,
- Aktorzustand,
- Energien aller 20 Frequenzbänder und aller drei Kanäle,
- detektierten Peaks.

Damit können später insbesondere folgende Hypothesen untersucht werden:

- Unterschiede der Emissionen zwischen Tag und Nacht;
- Zusammenhang zwischen Bodenfeuchte und Bandenergie;
- Frequenzverschiebungen vor, während und nach einer Bewässerung;
- langsames Wandern stabiler Peaks;
- gemeinsame Änderungen über mehrere Sensoren.

Die Uhrzeit ist eine Kovariate, kein Beweis für einen biologischen
Tag-/Nachteffekt. Temperatur, Luftfeuchte, Licht und externe Vibrationen werden
derzeit nicht gemessen und bleiben mögliche Störgrößen.
