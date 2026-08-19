# Hardware Setup Changes — CH2 → CH4 and MEMS Retrofit

> **Pflichtdokumentation für alle Auswertungen, die Setup-Übergänge betreffen.**

## Zusammenfassung

| Zeitraum | Aktive Kanäle | Sensoren |
|----------|---------------|----------|
| **Phase 1** (2026-06-21 — 2026-06-22) | CH1, CH2, CH3 | CH1 = LM358 + 820 kΩ (Stab), CH2 = 820 kΩ (Platte), CH3 = direkt |
| **Phase 2** (2026-06-22 — 2026-07-13) | **CH1, CH3, CH4** | CH1 = LM358 + 820 kΩ (passiv, Topfrand, EM-Referenz), CH3 = Piezo + Verstärker + 820 kΩ (Erde, Pflanzennähe), CH4 = Piezo + Verstärker + 820 kΩ (Edelstahlstab neben Pflanze) |
| **Phase 3** (seit 2026-07-14) | **CH1, CH3, CH4** | CH1 = Piezo + bestehender LM-Verstärker, CH3 = MEMS-Mikrofon + bestehender LM-Verstärker, CH4 = MEMS-Mikrofon + bestehender LM-Verstärker |

## Was ist passiert

- **2026-06-22**: CH2 (Piezo auf 0.8 mm Edelstahlplatte, 1:1-Tastkopf) ist ausgefallen.
  Diagnose: Hardware-Defekt. Kanal liefert keine verwertbaren Daten mehr.
- **2026-06-22 (gleicher Tag)**: CH4 (Verstärker + 820 kΩ, Edelstahlstab neben Pflanze) wurde
  als Ersatz verkabelt und konfiguriert. Er ist seitdem Teil des aktiven 3-Kanal-Setups.
- **2026-07-14**: Der Messaufbau wurde verlagert. CH1 bleibt als Piezo-Kanal am bestehenden
  LM-Verstärker. Die bisherigen Piezo-Sensoren an CH3 und CH4 wurden durch MEMS-Mikrofone
  ersetzt; die vorhandenen LM-Verstärkerstufen bleiben an beiden Kanälen in Gebrauch.
- **Phase-3-Infrastruktur**: Home Assistant ist am neuen Standort nicht verfügbar. Daher gibt
  es keine automatische Bewässerung und keine Temperaturmessung. Entsprechende Routinen und
  Datenfelder im Bestand gehören ausschließlich zu historischen Phase-1/2-Experimenten.

## Wo es im Code dokumentiert ist

- `instrument_control/plant_ae/watering.py:618` — `CHANNELS = (1, 3, 4)  # CH2 defekt (Hardware-Ausfall)`
- `instrument_control/plant_ae/deep_acquisition.py:34` — Docstring-Header: "Active channels (CH2 disabled — hardware defect)"
- `instrument_control/plant_ae/deep_acquisition.py:49` — `conn.write(":CHAN2:DISP OFF")  # CH2 defekt`
- `instrument_control/plant_ae/deep_acquisition.py` — aktuelle Sensorbelegung in
  `CHANNEL_HW_CONFIG` und im Konfigurations-Docstring
- `instrument_control/plant_ae/watering.py` — aktuelle Bezeichnungen in `CHANNEL_LABELS`

## Welche Auswertungen Phase-1 (mit CH2) sind, welche Phase-2

### Phase 1 (CH1+CH2+CH3) — vor 2026-06-22

- `experiment_plant_acoustic_emissions_20260621/` (Pilot-Scan 2026-06-21)
- `data/plant_ae_optimized/` (21.06. Capture-Sessions)
- `data/plant_ae/` (21.06. Capture-Sessions)
- `data/plant_ae_3ch/` (21.06. Capture-Sessions, falls vorhanden)
- `data/long_captures/` (frühe Aufnahmen, sofern vor 22.06.)
- `data/reports/frequency_analysis_baseline_20260622/frequency_characterization_report.md` (vom 22.06., 16:59 — *vor* CH2-Ausfall oder gerade noch mit CH2)
- `data/reports/frequency_analysis/frequency_characterization_report.md` (vom 23.06., 07:30 — *vor* CH2-Ausfall, oder 4-Channel-Setup)
- `data/reference_channel_experiment/20260623_121656/` (23.06. 12:16 — *nach* CH2-Ausfall, aber nutzt CH2 in anderem Kontext: expliziter Vergleich mit Referenz)
- `data/spatial_sensor_experiment/20260623_130722/` (23.06. 13:07 — Spatial-Variation, CH2 hier als Test-Sensor genutzt)

### Phase 2 (CH1+CH3+CH4) — ab 2026-06-22

- `experiment_continuous_plant_ae_20260622/` (alle Läufe ab 22.06. 17:52)
- `data/continuous_plant_ae_20260622/` (alle Runs)
- `data/hybrid_watering_experiment/20260623_232016/` (Bewässerungstest 23.06. 23:20)
- `data/impulse_response/` (falls nach 22.06.)

Diese Einordnung als Phase 2 gilt nur für Aufnahmen bis einschließlich 2026-07-13.

### Phase 3 (CH1 Piezo, CH3+CH4 MEMS) — ab 2026-07-14

- Alle neu angelegten Messungen ab der Verlagerung des Aufbaus.
- Phase-3-Daten müssen in Manifesten und Reports ausdrücklich als
  `CH1=Piezo, CH3=MEMS, CH4=MEMS` gekennzeichnet werden.
- Phase-3-Manifeste müssen `automatic_watering=false`, `temperature_recording=false` und
  `home_assistant_available=false` ausweisen.

### Achtung: Falsche Marker im Bestand

- `data/reports/frequency_analysis_baseline_20260622/` zeigt im Header "CH1+CH2+CH3" — dies ist konsistent mit dem Erstellungsdatum 22.06. 16:59 (vor CH2-Ausfall). Report ist **valide für Phase 1**, aber **nicht direkt vergleichbar** mit Phase-2-Reports.
- `data/reports/frequency_analysis/` zeigt im Header ebenfalls "CH1+CH2+CH3" — Erstellungsdatum 23.06. 07:30. Hier ist **unklar**, ob die zugrundeliegenden Captures vor oder nach dem CH2-Ausfall gemacht wurden. Die Header-Information ist **unzuverlässig**.

## Auswertungs-Implikationen

1. **4.3 kHz / 4.15 kHz Kandidat**: In Phase-1-Berichten sichtbar auf "CH1+CH3" (mit Anmerkung "absent on CH2"). In Phase 2 (CH2 weg, CH4 neu) ist die Aussage "absent on CH2" **nicht mehr falsifizierbar**. Die aktuelle Validierung an Phase-2-Daten (3.8 kHz auf CH3+CH4 in 16/16 Frames) ist ein **neuer**, unabhängiger Befund, nicht eine Replikation.
2. **Cross-Channel-Aussagen** aus Phase-1 (z. B. "Plausibilität steigt wenn auf CH1+CH2+CH3") sind in Phase-2 **nicht anwendbar**. Phase-2-Validierung muss auf (CH1, CH3, CH4) lauten.
3. **Amplitude-Vergleiche** zwischen Phase 1 und Phase 2 sind **nicht möglich** für CH2↔CH4 (verschiedene mechanische Kopplung: Platte vs. Stab). Auch CH1 ist in beiden Phasen **nicht amplituden-kalibriert**.
4. **Phase-2↔Phase-3-Vergleiche** auf CH3 und CH4 sind keine direkten Sensorvergleiche: MEMS-Mikrofone und Piezo-Sensoren besitzen unterschiedliche Empfindlichkeiten, Richtcharakteristiken und Frequenzgänge. Vor quantitativen Vergleichen ist eine eigene Phase-3-Kalibrierung erforderlich.

## Empfohlene Konvention für künftige Reports

- **Im Header** jedes Phase-2-Reports: "Active channels: CH1, CH3, CH4 (CH2 disabled, replaced 2026-06-22)."
- **In jeder Phase-1-Auswertung**: explizit "pre-CH2-defect" oder "Phase 1 setup (CH1+CH2+CH3)" als Marker.
- **Bei Vergleich Phase 1 ↔ Phase 2**: niemals "CH2 in beiden Phasen" implizieren — getrennt ausweisen.
- **In jedem Phase-3-Report**: "CH1 = Piezo + LM-Verstärker; CH3/CH4 = MEMS-Mikrofon + LM-Verstärker" ausweisen.
- **Keine Phase-3-Auswertung** darf eine Home-Assistant-Bewässerung oder Temperaturreihe implizieren.
