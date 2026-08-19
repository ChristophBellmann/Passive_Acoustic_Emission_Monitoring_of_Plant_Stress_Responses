# Vorfall-Report: 2026-06-22 (Dienstag Nachmittag/Abend)

> **Operator-Bericht:** „Als ich Sensoren neu verdrahtet habe, hat das
> Oszilloskop geschaltet. Vermutlich sind in den Rohdaten fehlerhafte
> bzw. durch mechanische Einwirkung kompromittierte Daten."

## Zusammenfassung

- **Datum:** 2026-06-22 (Dienstag)
- **Zeitfenster:** 17:52:20 – 19:05:46 CEST (Europe/Berlin)
- **Dauer:** 73 min, 310 Frames
- **Betroffene Session:** `data/continuous_plant_ae_20260622/20260622_175202/`
- **Verdächtige Frames:** 298 von 310 (96%)
- **Saubere Frames:** 12 (vor dem ersten Multi-Band-Event um 17:55:11)
- **Pilot-Sweeps danach (19:07–19:28):** sauber

## Befund: 83 Multi-Band-Drop-Events

Während der 73 Minuten wurden **83 Frames** detektiert, in denen
gleichzeitig ≥3 Frequenzbänder ihre Energie um ≥4 dB änderten — oft
auf mehreren Kanälen simultan. Die Amplitude einzelner Drops reichte
bis zu **101 dB** in einem einzigen Band. Das ist **kein
Pflanzenpeak**, das sind mechanische oder elektrische Artefakte.

### Typische Beispiele

**Seq 12 (17:55:11, +2:51 nach Start)** — 6 Bänder auf 2 Kanälen:
```
CH2  0-5 kHz:  +15.0 dB
CH2  5-10 kHz: +12.2 dB
CH2 10-15 kHz:  +5.6 dB
CH2 30-35 kHz:  -6.7 dB
CH3  0-5 kHz:  +14.7 dB
```

**Seq 32 (17:59:54)** — 8 Bänder auf CH3, alle negativ:
```
CH3 15-20 kHz:  -4.1 dB
CH3 35-40 kHz: -10.3 dB
CH3 50-55 kHz: -13.2 dB
CH3 60-65 kHz:  -8.7 dB
CH3 70-75 kHz: -13.8 dB
```

**Seq 35 (18:00:37)** — sehr große negative ΔB auf CH2:
```
CH2 10-15 kHz: -19.0 dB
CH2 20-25 kHz: -14.6 dB
CH2 25-30 kHz: -14.3 dB
CH2 30-35 kHz: -20.8 dB
CH3 10-15 kHz:  -7.6 dB
```

## Zeitlicher Ablauf

| Zeit (lokal) | seq | Was | Status |
|--------------|-----|-----|--------|
| 17:52:20 | 0 | Run start, sauber | ✅ |
| 17:54:?? | 0–11 | Sensor-Verdrahtung läuft (Operator-Bericht) | ⚠ Eingriff |
| 17:55:11 | 12 | Erster Multi-Band-Drop, +15 dB auf CH2+CH3 im 0-5 kHz Band | ⚠ Kompromittiert |
| 17:55 – 19:05 | 12–309 | 83 weitere Multi-Band-Events, ΔB bis 101 | ⚠ Kompromittiert |
| 19:05:46 | 310 | Run-Ende | — |
| 19:07:02 | — | `20260622_190618` startet (1 Frame) | ✅ sauber |
| 19:08:06 | — | `20260622_190723` startet (29 Frames) | ✅ sauber |
| 19:27:16 | — | `20260622_192633` startet (3 Frames) | ✅ sauber |

## Saubere Daten aus dieser Zeit

- **`20260622_175202`, seq 0–11 (17:52:20 – 17:55:11):** 12 Frames vor dem
  ersten Multi-Band-Drop. **Diese 12 Frames sind paper-tauglich** (vor
  dem Operator-Eingriff).
- **`20260622_190618`, `20260622_190723`, `20260622_192633`:** Pilot-Snapshot-
  Sweeps nach Vorfall, sauber. Diese wurden für die Pilot-Figure im Paper
  verwendet.

## Was NICHT kompromittiert ist

- **Pilot-Snapshot-Sweeps** (22.06. 19:07–19:28): 33 Frames total, alle sauber
- **Continuous-Lauf 23.06. 23:38** (`20260623_233855`): für Paper-Statistiken
  verwendet, sauber
- **Hybrid-Watering-Lauf 23.06. 23:20** (`20260623_232016`): sauber
- **Aktueller Live-Run 24.06. 01:01** (`20260624_010136`): 52 Frames, 0 verdächtige
  Events, stabil

## Empfehlungen

### Für aktuelle Datenanalyse
1. **`20260622_175202` NICHT in Paper-Statistiken einbeziehen.** Die 12
   sauberen Frames (seq 0–11) sind nicht repräsentativ für „Continuous
   Monitoring über Nacht" — sie sind 12 Frames über 2:51 min.
2. **Paper-Figuren** verwenden weiterhin die Pilot-Snapshot-Sweeps
   (19:07–19:28) als Hauptinput. Das ist bereits korrekt in `make_figures.py`.

### Für künftige Messungen
3. **Operator-Logbuch** führen (siehe `OPERATOR_LOGBOOK.md`).
4. **Automatischer Spike-Rejector** in `continuous_characterization.py`:
   ```python
   if len(band_changes) >= 3:
       mark_frame_as_suspect(frame)
   ```
5. **Hardware-Änderungen nur bei gestopptem Run** (heute bereits Praxis).

## Reproduktion der Analyse

```bash
cd src/characterization
.venv/bin/python << 'PYEOF'
import json
from pathlib import Path
from datetime import datetime

RUN = Path("data/continuous_plant_ae_20260622/20260622_175202")
events = [json.loads(l) for l in (RUN/"experiment_events.jsonl").read_text().splitlines() if l.strip()]

multi = [e for e in events if e.get("event")=="spectral_change"
         and sum(1 for d in e.get("detections",[])
                 if d.get("type")=="band_energy_change") >= 3]

print(f"Session: 20260622_175202 (310 frames)")
print(f"Multi-Band-Events: {len(multi)}")
if multi:
    first = datetime.fromisoformat(multi[0]['timestamp_utc'].replace('Z','+00:00')).astimezone()
    last  = datetime.fromisoformat(multi[-1]['timestamp_utc'].replace('Z','+00:00')).astimezone()
    print(f"Zeitfenster: {first.isoformat()} – {last.isoformat()}")
    print(f"Vorfall-Dauer: {(last-first).total_seconds()/60:.1f} min")
    max_db = max(abs(d['change_db']) for e in multi
                 for d in e.get('detections',[])
                 if d.get('type')=='band_energy_change')
    print(f"Max ΔB in einem Event: {max_db:.0f} dB")
PYEOF
```

## Referenzen

- `HARDWARE_CHANGELOG.md` — Setup-Änderungen
- `OPERATOR_LOGBOOK.md` — Logbuch-Vorlage (zu erstellen)
- `notebooks/README.md` — Method-Cards der betroffenen Notebooks
