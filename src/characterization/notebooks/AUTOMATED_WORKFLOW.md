# Automatisierter Messablauf

> **Stand 2026-06-27: Superseded.**
> `05_automated_hybrid_experiment.ipynb` wurde als primärer Bewässerungsworkflow
> ersetzt durch **`scripts/plant_in_loop_water.py`** (Cron, alle 2 Tage, 20:13 Uhr).
> Das neue Skript stoppt die kontinuierliche Messung, erfasst N_PRE + N_POST Frames
> mit vollständigem Kandidaten-Tracking (3 800 Hz, 6 750 Hz), führt 5 quantifizierte
> Hypothesentests durch (H1–H5) und startet die kontinuierliche Messung anschließend
> neu. Dry-Run erfolgreich getestet 27.06.2026
> (`data/watering_experiments/20260627_210624_dryrun/`).
>
> Diese Datei beschreibt den alten NB05-Workflow und bleibt für die
> Paper-Reproduzierbarkeit (Session `data/hybrid_watering_experiment/20260623_232016/`)
> erhalten. Für neue Bewässerungsexperimente NB05 **nicht** mehr starten.

## Ziel (NB05, historisch)

`05_automated_hybrid_experiment.ipynb` war der primäre Ablauf für den
Bewässerungsversuch. Das Notebook kombiniert zwei Auswertungen über denselben
ununterbrochenen Messstrom:

- Ein Rolling Window überwacht fortlaufend alle zwanzig 5-kHz-Bänder von
  0 bis 100 kHz und erkennt neue, verschwindende oder wandernde Peaks.
- Snapshots markieren reproduzierbare Zeitbereiche vor, während und nach der
  Bewässerung. Sie werden aus demselben Datenstrom ausgewählt und anschließend
  vollständig analysiert.

Damit entstehen keine Messlücke und kein Wechsel der Oszilloskopeinstellungen
zwischen Referenz und Bewässerung.

## Ablauf

1. Home Assistant, Mikrocontroller, Pumpe und Oszilloskop werden geprüft.
2. Der Rolling-Monitor startet und lernt während der Warm-up-Frames das aktuelle
   Spektrum.
3. Die letzten Frames vor dem Eingriff werden rückwirkend aus dem RAM-Ring als
   `snapshot_pre_watering` gesichert.
4. Das vorhandene Aktorprogramm bewässert die Pflanze einmal.
5. Die Messung läuft während der Bewässerung ohne Unterbrechung weiter.
6. Nach einer konfigurierbaren Beruhigungsphase wird
   `snapshot_post_watering` aufgenommen.
7. Das Notebook erzeugt automatisch Spektren mit markierten Peaks,
   Spektraldifferenzen, Änderungen der Bandenergie und zugeordnete
   Frequenzverschiebungen.

Die während des Aktorlaufs erfassten Frames werden zusätzlich als
`snapshot_watering_event` gespeichert. Dieser kurze Zustand beschreibt vor
allem Pumpe, Wasserbewegung und unmittelbare Reaktion. Für die eigentliche
Frequenzverschiebung ist der Vergleich `post_watering_vs_pre` maßgeblich.

## Voraussetzungen

- Rigol DS1104Z ist per LAN unter der in `config.yaml` eingetragenen Adresse
  erreichbar.
- Der Mikrocontroller ist eingeschaltet und Home Assistant ist erreichbar.
- Die Aktorkonfiguration in `src/actuator/giessen_pflanze1.py` ist korrekt.
- Vor dem Start ist die Pumpe aus und genügend Wasser vorhanden.
- Die Python-Umgebung unter `src/characterization/.venv` enthält die
  Projektabhängigkeiten.

## Start

Vom Projektstamm:

```bash
cd src/characterization
./setup_jupyter.sh
.venv/bin/jupyter lab notebooks/00_control_panel.ipynb
```

Im Control Panel das gewünschte Notebook auswählen und starten. Alternativ kann
das Experiment-Notebook direkt in Jupyter geöffnet werden; als Kernel
`Plant AE (Projekt I1)` verwenden.

Im Notebook zunächst die Initialisierungszellen ausführen. Die Hardwaremessung
wird ausschließlich durch die letzte, standardmäßig auskommentierte Zelle
gestartet:

```python
actuator = HomeAssistantPlant1Actuator()
experiment = AutomatedHybridExperiment(actuator)
results = experiment.run()
```

Der Aufruf bewässert die Pflanze automatisch genau einmal. Er darf deshalb
nicht versehentlich mehrfach ausgeführt werden.

Nach dem Auslösen misst der Ablauf mindestens bis zum Ende der im Aktormodul
definierten Gießzeit. Anschließend wartet er mit einem begrenzten Timeout darauf,
dass Home Assistant Skript und Pumpe wieder als bereit meldet. Dadurch kann eine
kurze Statusverzögerung von Home Assistant den Bewässerungszustand nicht
vorzeitig beenden.

Die Standardparameter sind:

```python
AutomatedHybridExperiment(
    actuator,
    warmup_frames=10,
    pre_snapshot_frames=20,
    settle_frames=5,
    post_snapshot_frames=20,
    memory_fraction=0.75,
    reserve_gib=4.0,
    persist_rolling_events=True,
)
```

`memory_fraction` ist eine Obergrenze. Der Monitor berücksichtigt zusätzlich
den aktuell freien Arbeitsspeicher und lässt mindestens `reserve_gib` für
Betriebssystem, Jupyter und Analyse frei.

## Ergebnisse

Rohdaten eines Laufs:

```text
data/plant_ae_hybrid/<Zeitstempel>/
├── hybrid_manifest.json
├── rolling_events/
├── snapshot_pre_watering/
├── snapshot_watering_event/
└── snapshot_post_watering/
```

Abbildungen und Tabellen:

```text
data/reports/notebooks/hybrid/<Zeitstempel>/
├── snapshot_pre_watering/
├── snapshot_watering_event/
├── snapshot_post_watering/
├── watering_vs_pre/
└── post_watering_vs_pre/
```

Das Manifest protokolliert UTC-Zeitpunkte, Zustandswechsel, Parameter,
Oszilloskopeinstellungen und die Sequenznummern sämtlicher Snapshot-Frames.
Damit lässt sich jeder Vergleich auf die zugrunde liegenden Frames
zurückführen.

Normale Rolling-Frames verbleiben im begrenzten RAM-Ring und werden nicht auf
die Festplatte geschrieben. Dauerhaft gespeichert werden nur die drei
Snapshots, kompakte erkannte Rolling-Ereignisse, das Manifest und die
Auswertung.

## Interpretation und Grenzen

- Eine neue oder verschobene Frequenz ist nur belastbar, wenn sie über mehrere
  Frames beziehungsweise Kanäle reproduzierbar erscheint und nicht allein mit
  Pumpe, Netzbrummen oder Mikrocontrollerbetrieb zusammenfällt.
- Der MCU-Einfluss sollte in einem separaten Lauf mit identischen
  Oszilloskopeinstellungen geprüft werden. Ein Neustart des Oszilloskops
  zwischen Vergleichszuständen macht diesen Vergleich nicht kausal eindeutig.
- Die zeitliche Auflösung wird praktisch durch die LAN-Übertragung vollständiger
  Rigol-Wellenformen begrenzt. Die Sequenznummern sind daher verlässlicher als
  eine angenommene feste Frame-Rate.
- Ein einzelner Bewässerungsversuch reicht nicht für eine statistisch belastbare
  biologische Aussage. Die Automatisierung stellt sicher, dass Wiederholungen
  nach demselben Protokoll durchgeführt werden können.

## Abbruch

Bei einem Fehler wird der bisherige Zustand im Manifest erhalten. Vor einem
Neustart muss geprüft werden, ob die Pumpe tatsächlich aus ist. Ein abgebrochener
Lauf wird nicht fortgesetzt; für einen neuen Versuch wird ein neuer
Zeitstempelordner angelegt.
