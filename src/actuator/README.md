# Actuator: Pflanze 1 bewässern

`giessen_pflanze1.py` startet über Home Assistant die Bewässerung von
Pflanze 1 für fest eingestellte 10 Sekunden. Vor dem Start gibt es außerdem
die aktuelle Bodenfeuchte in Prozent aus.

Das Programm verwendet die Zugangsdaten und den REST-Client aus
`HOMEASSISTANT_SYNC_DIR` oder, falls nicht gesetzt:

```text
~/.local/share/homeassistant_sync
```

Vor dem Start setzt es
`input_number.pflanze1_giesszeit_sekunden` auf `10` und startet anschließend
`script.pflanze1_giessen`. Der Timer läuft damit auf Home Assistant und nicht
im lokalen Python-Prozess.

## Bodenfeuchte auslesen

`giessen_pflanze1.py` gibt mit `--dry-run` die aktuelle Bodenfeuchte aus,
ohne die Pumpe zu starten:

```bash
python3 giessen_pflanze1.py --dry-run
```

Pflanze 1 gießen:

```bash
python3 giessen_pflanze1.py
```

Home-Assistant-Zugriffe sind im portablen Jupyter-Workflow standardmäßig
deaktiviert. Zum Aktivieren:

```bash
export PLANT_AE_HOMEASSISTANT_ENABLED=1
export HA_URL=...
export HA_TOKEN=...
```

Alternativ `giessen_pflanze1.py --enable-homeassistant` verwenden. Auf neuen
Workstations zusätzlich entweder `HOMEASSISTANT_SYNC_ENV_FILE` oder
`HOMEASSISTANT_SYNC_DIR` setzen, falls der REST-Client nicht unter
`~/.local/share/homeassistant_sync` liegt.
