# Operator-Logbuch

> **Zweck:** Dokumentation aller Eingriffe am Mess-Setup während
> laufender Messungen. Jeder Eingriff kann die Daten kompromittieren.
> Korrelation mit verdächtigen Multi-Band-Drop-Events (siehe
> `INCIDENT_REPORT.md`) ist nur möglich wenn das Logbuch geführt wird.

## Konvention

- **Zeitstempel:** lokal (Europe/Berlin)
- **Eintrag sofort** wenn der Eingriff stattfindet — nicht nachträglich
- **Eine Zeile pro Eingriff** — knapp, präzise
- **Was, wo, wie lange** notieren

## Eintrags-Format

```
[YYYY-MM-DD HH:MM] Kanal: was passiert ist
```

Beispiele:
- `[2026-06-22 17:54] CH1+CH2: Stecker an Oszilloskop gelöst, neu gesteckt`
- `[2026-06-22 18:30] CH3: Sensor umgesetzt, neuer Topf`
- `[2026-06-23 23:20] CH1+CH3+CH4: Home-Assistant Gieß-Skript manuell ausgelöst`

## Logbuch-Einträge

### 2026-06-22 (Dienstag)

```
[17:52:20] Run 20260622_175202 gestartet, alle 3 Kanäle aktiv (CH1+CH2+CH3)
[17:54:00] Sensor-Verdrahtung geändert (Operator-Bericht, exakte Zeit nicht bekannt)
          → vermutlich Stecker am Oszilloskop gelöst/neu gesteckt
[17:55:11] ERSTER Multi-Band-Drop detektiert (seq=12)
          → CH2 0-5 kHz +15 dB, CH3 0-5 kHz +14.7 dB simultan
[17:55 – 19:05] 83 weitere Multi-Band-Events, max ΔB = 101 dB
[19:05:46] Run 20260622_175202 beendet (310 frames)
[19:07] Pilot-Snapshot-Sweep 20260622_190618 gestartet — sauber
[19:08] Pilot-Snapshot-Sweep 20260622_190723 gestartet (29 frames) — sauber
[19:27] Pilot-Snapshot-Sweep 20260622_192633 gestartet (3 frames) — sauber
```

→ **Vorfall-Correlation:** Multi-Band-Drop-Beginn um 17:55:11 ist
   konsistent mit Sensor-Eingriff um ~17:54:00. Siehe `INCIDENT_REPORT.md`.

### 2026-06-23 (Mittwoch)

```
[10:37] Run 20260623_004453 beendet (10:37 — vermutlich Operator-Stop)
[11:36] Run 20260623_112918 gestartet
[12:09] Run 20260623_115245 gestartet (4 Minuten später, vermutlich Auto-Restart)
[12:55] Run 20260623_124732 gestartet
[13:38] Run 20260623_133857 gestartet (424 frames über 5+ Stunden)
[19:13] Run 20260623_184057 gestartet (Scope-Verbindung unterbrochen um 19:13)
[19:13] Run 20260623_184057 beendet (Verbindungsabbruch)
[22:46] Run 20260623_223952 gestartet
[23:20] Bewässerungstest 20260623_232016 (3.8 kHz +21.7 dB auf CH3)
[23:38] Run 20260623_233855 gestartet (Pilot-Continuous, 28 frames)
       → in Paper verwendet
```

### 2026-06-24 (Donnerstag)

```
[01:01] Continuous-Lauf 20260624_010136 gestartet (Phase 2, CH1+CH3+CH4)
        → läuft aktuell, 0 Multi-Band-Events in 52+ Frames
[~02:50] Fenster direkt neben der Pflanze geschlossen (Operator-Bericht)
         → Beobachtung: Amplituden bestimmter Frequenzen dauerhaft gefallen?
         → Analyse läuft, siehe INCIDENT_REPORT.md
[02:54] Oszilloskop steht jetzt am Boden (Operator-Update)
         → mögliche mechanische Kopplung mit Boden/Erde verändert
         → Bodenstellung könnte neue Resonanzen einbringen oder dämpfen
         → zukünftige Daten dieser Nacht könnten beeinflusst sein
[02:56] Rechner-Neustart (Operator-Update)
         → screen-session 'plant_ae' beendet
         → 122 frames aufgezeichnet bis 02:55:36 in 20260624_010136
         → ab 02:55 keine Daten mehr bis Neustart
[03:01] Neuer Run 20260624_030123 gestartet (Phase 2, CH1+CH3+CH4)
         → neuer Run, läuft ab 03:01
         → ab 03:04:46 erster Frame, Soil=30.2%
         → Hinweis: dieser Run startet NACH den Operator-Eingriffen
           (Fenster zu, Oszi am Boden) — Daten daher mit Vorbehalt
           bezüglich Vergleichbarkeit zu 20260624_010136
         → Vergleiche nur INNERHALB dieses Runs sinnvoll
```

## Empfehlung für künftige Messungen

1. **Vor jedem Eingriff:** Run stoppen via `screen -S plant_ae -X quit` oder
   `./measurement.py stop`. Erst nach Bestätigung dass der Run beendet ist,
   am Setup arbeiten.
2. **Nach Eingriff:** Neuen Run starten, alten archivieren.
3. **Logbuch sofort** führen — am Besten direkt in `git commit` Message
   oder als Notiz in der Run-`experiment_events.jsonl` (siehe Schema unten).

## Schema-Erweiterung für `experiment_events.jsonl`

```json
{
  "timestamp_utc": "2026-06-22T15:54:00+00:00",
  "event": "operator_intervention",
  "operator": "christoph",
  "channels": [1, 2, 3],
  "description": "Stecker an Oszilloskop gelöst, neu gesteckt",
  "estimated_duration_s": 60
}
```

Damit lassen sich verdächtige Multi-Band-Events automatisch mit Operator-
Eingriffen korrelieren.

## Referenzen

- `INCIDENT_REPORT.md` — detaillierte Analyse des 22.06.-Vorfalls
- `DATA_QUALITY.md` — Qualitäts-Metriken pro Run
- `HARDWARE_CHANGELOG.md` — Setup-Änderungen (CH2 defekt → CH4)
