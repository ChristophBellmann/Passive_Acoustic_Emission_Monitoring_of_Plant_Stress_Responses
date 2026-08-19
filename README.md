# Projekt I1

Wissenschaftliche Projektausarbeitung zum Thema:

`Akustisches Plant-in-the-Loop: Nicht-invasive Wachstums- und Stressdetektion via Ultraschall-Emission als Closed-Loop-Feedback`

## Ausgangslage

Nach systematischer Abgrenzung und PRISMA-Recherche hat sich eine Forschungslücke herauskristallisiert:

**Keine Publikation integriert akustische Pflanzenemission (Ultraschall
20–100 kHz) als Echtzeit-Feedback in einen geschlossenen
Plant-in-the-Loop-Regelkreis unter Indoor-CEA-Bedingungen.**

## Kernartefakte

| Datei | Zweck |
|---|---|
| `abgrenzungstabelle/abgrenzungstabelle_akustisch_pil.md` | Vollständige Abgrenzungstabelle (62 Quellen + 11 Gegenfolien), PRISMA-validiert |
| `abgrenzungstabelle/abgrenzungstabelle.xlsx` | Excel-Tabelle mit Farbcodierung und Summary |
| `zotero/literatur.bib` | Zentrale Zotero-Quellenbasis (BibTeX) |
| `Quellen/` | 21 PDF-Volltexte der Kern- und Gegenfolien-Quellen |
| `Pflanzenwachstumssystem.tex` | Hauptdokument (LaTeX) |
| `references.tex` | Manuell gepflegte Referenzen für das Hauptdokument |

---

## Pflanzen-AE-Charakterisierung

Die praktische Signalerfassung und Auswertung befindet sich unter
[`src/characterization/`](src/characterization/). Messungen erfolgen mit dem
Rigol DS1104Z (500 kSa/s, 300 000 Punkte, Δf = 1,67 Hz, 0–250 kHz Nyquist).

### Aktuelles Kanalsetup (ab 2026-06-23 ~20:00 Uhr)

| Kanal | Kopplung | Position | Rolle |
|-------|----------|----------|-------|
| CH1 | 820 kΩ passiv | Topfrand ~3 cm | EM + Mechanik-Referenz |
| CH2 | **DEAKTIVIERT** | — | Hardware-Defekt (seit 23.06.) |
| CH3 | LM358-Verstärker + 820 kΩ | Erde, Pflanzenwurzelzone | Primärsensor (sensitiv) |
| CH4 | LM358-Verstärker + 820 kΩ | Edelstahlstab neben Pflanze | Metallkopplung / TDE-Referenz |

**Diskriminierungsprinzip:**
- CH3/CH4 >> CH1: Signal lokal bei Pflanze, kein EM-Gleichtakt
- CH3 vs. CH4: Erd- vs. Metallkopplung, Impedanzunterschied, Laufzeit (TDE mit cm-Auflösung bei ~5000 m/s im Stahl)

### Datenstand (27.06.2026)

| Kennzahl | Wert |
|----------|------|
| Sessions | 25 |
| Frames gesamt | ~4 800 (à 0,6 s Akquisition, ~62 s Frame-Abstand) |
| Messzeitraum | 22.06.2026 – laufend |
| Datenabdeckung | kontinuierlich, Tag- und Nachtphasen |
| Aktive Session | `20260627_211053` (PID 947113, Heartbeat-überwacht) |

### Messbetrieb

```bash
cd src/characterization/
./measurement.py start    # startet Jupyter-Kernel im Hintergrund
./measurement.py status   # zeigt PID, Laufzeit, letztes Frame (Heartbeat)
./measurement.py stop     # sauberer Stop mit finalem Manifest-Update
```

Für neue Workstations bevorzugt:

```bash
cd src/characterization/
./setup_jupyter.sh
.venv/bin/jupyter lab notebooks/00_control_panel.ipynb
```

Das Control-Panel-Notebook nutzt Widgets für Start/Stop/Status/Logs und kann
alle aktiven Experiment-Notebooks starten. Der stabile Kernel heißt
`plant-ae` (`Plant AE (Projekt I1)`).

Home Assistant ist im portablen Betrieb standardmäßig deaktiviert. Auf der
Mess-Workstation im Control Panel aktivieren oder
`PLANT_AE_HOMEASSISTANT_ENABLED=1` setzen.

**Robustheit:** Das Notebook enthält eine äußere Reconnect-Schleife. Nach
≥ 5 aufeinanderfolgenden Frame-Fehlern (z. B. Rigol-VISA-Disconnect via WLAN)
wird die Verbindung geschlossen und nach 30 s neu aufgebaut; `monitor`-Zustand
(Ring, Tracks, Events) bleibt erhalten. `measurement.py status` warnt, wenn
das letzte Frame >10 min zurückliegt (Heartbeat-Prüfung).

---

## Wissenschaftliche Kernbefunde (Stand 27.06.2026)

### 1 · Diurnales Kohärenzmuster bei 3 800 Hz

Die Kreuzkanal-Kohärenz CH3/CH4 bei ~3 800 Hz zeigt ein stabiles,
reproduzierbares Tagesmuster:

| Phase | Kohärenz (Mittelwert) |
|-------|-----------------------|
| Tag (06–22 Uhr) | 0,27 |
| Nacht (22–06 Uhr) | 0,80 |
| Natürliche Streuung (σ) | 0,22 |

- **CH1/CH4** bei 3 800 Hz: 0,002–0,04 — an/unter dem Kohärenz-Bias-Floor
  (1/N_seg = 1/18 ≈ 0,056), also keine EM-Quelle nachweisbar.
- **Bias-Floor** (Welch, nperseg = 16 384, ~18 Segmente bei 300 000 Punkten):
  0,056. Alle gemeldeten Kohärenzwerte liegen entweder klar darüber oder klar
  darunter.
- Das Muster **reproduziert sich sessionübergreifend** (22.06.–27.06.,
  mindestens 3 unabhängige Nächte).

**Wichtige Einschränkung:** Die getrackte Frequenz liegt im Mittel
~15–70 Hz über dem 750-Hz-Gebäudeharmonischen 5×750 = 3 750 Hz.
Der Abstand und der Tagesdrift (+140 Hz von Minimum 14 Uhr zu Maximum
02 Uhr) sprechen für ein Signal, das sich vom strukturellen Artefakt
unterscheidet — eine eindeutige Trennung erfordert weitere Analyse
(bispektrale Methoden, erweiterte Sensorik).

### 2 · 6 750 Hz: strukturelles Artefakt identifiziert

Der bisherige „6 600 Hz"-Kandidat wurde als 9. Harmonische der
Gebäude-Heizungspumpe (9 × 750 = 6 750 Hz) identifiziert:

- Mittlere getrackte Frequenz: **6 747 Hz** (2,7 Hz vom Artefakt-Sollwert)
- CH3/CH4-Kohärenz: Mittelwert 0,124, **kein Frame > 0,5**, Bias-Floor 0,056
- Schluss: keine pflanzliche Quelle — wird im Paper als strukturelles Artefakt
  geführt.

Alle Frames enthalten jetzt `nearest_artifact_hz`, `artifact_offset_hz`,
`coherence_bias_floor` und `chN_snr_db` als dokumentierte Metadaten.

### 3 · Amplitudensprung bei Bewässerung

Erstes dokumentiertes Bewässerungs-Response-Event (23.06.2026):

- 3 800 Hz Peak CH3: **+21,7 dB** nach 10 s Bewässerung
- Schmalbandig (Bandenergie 0–5 kHz gesamt: +0,2 dB), keine
  Pumpen-Schalleinleitung, sondern lokale Resonanzänderung

Bewässerungs-Events 26./27.06.2026:

| Datum | pre coh | post coh | Δcoh |
|-------|---------|----------|------|
| 26.06. 20:10 | 0,149 | — | — |
| 27.06. 20:13 | 0,631 | 0,527 | −0,104 |

---

## Plant-in-the-Loop Bewässerungs-Experiment

Die automatisierte Bewässerung (cron, alle 2 Tage, 20:13 Uhr) führt ab sofort
ein vollständiges wissenschaftliches Experiment durch:

1. **Kontinuierliche Messung stoppen** (Scope freigeben)
2. **5 Pre-Frames** (~5 min Baseline, alle Kanäle, alle Bänder + Kandidaten-Tracking)
3. **Bewässerung 10 s** (Home-Assistant-Aktuator)
4. **10 Post-Frames** (~10 min Response, identische Metriken)
5. **5 Hypothesentests** (automatisch ausgewertet):
   - H1: Breitband-Transient in CH3/CH4, 0–25 kHz (>3 dB)?
   - H2: |Δcoh₃₈₀₀| > 0,15?
   - H3: CH1 stabil (<3 dB) — kein EM-Artefakt?
   - H4: CH3-Zuwachs > CH4-Zuwachs (Bodensensor > Metallstab)?
   - H5: Timing — Frame 0–1 (Hydraulikschock) oder Frame 2–5 (Diffusion)?
6. **Ergebnisse** in `data/watering_experiments/TIMESTAMP/`
   (protocol.json, pre/post_frames.jsonl, analysis.json)
7. **Kontinuierliche Messung neu starten**
8. **Commit + Push**

Nächste Bewässerung: **2026-06-29, 20:13 Uhr** (autonom).

Dry-Run erfolgreich getestet am 27.06.2026 (`data/watering_experiments/20260627_210624_dryrun/`).

---

## Dokumentation

| Dokumentation | Inhalt |
|---|---|
| [Charakterisierungssoftware](src/characterization/README.md) | Installation, Oszilloskopanbindung, CLI, Datenaufnahme und Analysepipeline |
| [Erste Pflanzen-AE-Charakterisierung (21.06.)](src/characterization/experiment_plant_acoustic_emissions_20260621/README.md) | Versuchsaufbau, Drei-Kanal-Messungen, Spektren und erste Kandidaten |
| [Kontinuierliche Charakterisierung (ab 22.06.)](src/characterization/experiment_continuous_plant_ae_20260622/README.md) | Dauerexperiment, Tag-/Nachtzuordnung, Peaktracking, Korrekturen |
| [Incident-Report 22.06.](src/characterization/experiment_continuous_plant_ae_20260622/INCIDENT_REPORT.md) | Sensor-Verdrahtungsfehler — Datenqualitätsanalyse |
| [Phase-Shift Experiment (26.06.)](src/characterization/experiment_ch3_ch4_phase_shift_20260626/) | CH3/CH4 Phasenversatz und TDE-Analyse |

---

## Forschungsdesign (Kurzfassung)

Das Forschungsdesign umfasst zwei parallele Versuchsstandorte:

1. **Augsburg – kontaktgebundene Messung:** Piezoelektrische Sensoren (CH3/CH4,
   LM358-verstärkt) und passive EM-Referenz (CH1) am Rigol DS1104Z, 500 kSa/s.
   Kontinuierliche Aufnahme mit automatischem Commit/Push via Git LFS.
2. **Ravensburg – kontaktlose Messung:** Paralleler Aufbau mit
   MEMS-Ultraschallmikrofonen.
3. **Auswertung:** Spektren 0–100 kHz, Kandidaten-Frequenz-Tracking
   (parabole Sub-Bin-Interpolation, 1,67 Hz Auflösung), Welch-Kohärenz,
   SNR-Berechnung, Artefakt-Proximity-Dokumentation, diurnale Trendanalyse.
4. **Methodik:** Reproduzierbare Python/Jupyter-Workflows; RAM-Ring-Puffer mit
   dynamischem Budget; stündliche PSD-Snapshots; Heartbeat-Überwachung.
5. **Geltungsbereich:** Kontrollierte Indoor-Versuche; alle Kandidaten-Frequenzen
   werden auf Artefakt-Nähe (750-Hz-Harmonische) und Kohärenz-Bias-Floor geprüft.

## Build

```bash
python3 -m venv .venv && source .venv/bin/activate
make pdf
```
