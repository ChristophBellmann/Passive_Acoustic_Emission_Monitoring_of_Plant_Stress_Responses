#!/usr/bin/env python3
"""Bewässert Pflanze 1 über die Home-Assistant-REST-API für 10 Sekunden."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Protocol


GIESSZEIT_SEKUNDEN = 10
GIESSZEIT_ENTITY = "input_number.pflanze1_giesszeit_sekunden"
GIESS_SCRIPT_ENTITY = "script.pflanze1_giessen"
PUMPE_ENTITY = "switch.pflanze_1_pflanze_1_pumpe"
BODENFEUCHTE_ENTITY = "sensor.pflanze_1_pflanze_1_bodenfeuchte"
HOMEASSISTANT_ENABLED_ENV = "PLANT_AE_HOMEASSISTANT_ENABLED"
_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}
DEFAULT_SYNC_DIR = Path(
    os.environ.get(
        "HOMEASSISTANT_SYNC_DIR",
        Path.home() / ".local" / "share" / "homeassistant_sync",
    )
).expanduser()


class RestClient(Protocol):
    def get(self, path: str) -> Any: ...

    def post(self, path: str, payload: dict[str, Any] | None = None) -> Any: ...


def homeassistant_enabled(*, default: bool = False) -> bool:
    value = os.environ.get(HOMEASSISTANT_ENABLED_ENV)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in _TRUE_VALUES:
        return True
    if normalized in _FALSE_VALUES:
        return False
    raise RuntimeError(
        f"Ungültiger Wert für {HOMEASSISTANT_ENABLED_ENV}: {value!r}. "
        "Erlaubt sind 1/0, true/false, yes/no, on/off."
    )


def require_homeassistant_enabled() -> None:
    if not homeassistant_enabled(default=False):
        raise RuntimeError(
            "Home Assistant ist deaktiviert. "
            f"{HOMEASSISTANT_ENABLED_ENV}=1 setzen oder im Control Panel aktivieren."
        )


def load_homeassistant_sync(sync_dir: Path) -> Any:
    require_homeassistant_enabled()
    module_path = sync_dir / "homeassistant_sync.py"
    if not module_path.is_file():
        raise RuntimeError(f"homeassistant_sync.py nicht gefunden: {module_path}")

    spec = importlib.util.spec_from_file_location("project_homeassistant_sync", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"homeassistant_sync.py kann nicht geladen werden: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_connection_settings(
    sync_module: Any,
    sync_dir: Path,
    *,
    ha_url: str | None,
    token: str | None,
) -> tuple[str, str]:
    env_file = Path(
        os.environ.get("HOMEASSISTANT_SYNC_ENV_FILE", sync_dir / ".env")
    ).expanduser()
    env_values = sync_module.load_env_file(env_file)

    resolved_url = (
        ha_url
        or os.environ.get("HA_URL")
        or env_values.get("HA_URL")
        or "https://thinkthing"
    ).rstrip("/")
    resolved_token = token or os.environ.get("HA_TOKEN") or env_values.get("HA_TOKEN")

    if not resolved_token:
        raise RuntimeError(
            "Home-Assistant-Token fehlt. HA_TOKEN setzen oder "
            f"in {env_file} eintragen."
        )
    return resolved_url, resolved_token


def entity_state(client: RestClient, entity_id: str) -> str:
    result = client.get(f"/api/states/{entity_id}")
    if not isinstance(result, dict):
        raise RuntimeError(f"Ungültige Statusantwort für {entity_id}: {result!r}")
    return str(result.get("state", ""))


def bodenfeuchte_text(client: RestClient) -> str:
    state = entity_state(client, BODENFEUCHTE_ENTITY)
    if state in {"unavailable", "unknown", ""}:
        return "nicht verfügbar"
    try:
        value = float(state)
    except ValueError:
        return state
    return f"{value:.1f} %"


def giessen(client: RestClient, *, dry_run: bool = False) -> None:
    script_state = entity_state(client, GIESS_SCRIPT_ENTITY)
    if script_state in {"unavailable", "unknown", ""}:
        raise RuntimeError(
            f"{GIESS_SCRIPT_ENTITY} ist nicht verfügbar (Status: {script_state!r})."
        )
    if script_state == "on":
        raise RuntimeError("Das Bewässerungsskript läuft bereits.")

    giesszeit_state = entity_state(client, GIESSZEIT_ENTITY)
    if giesszeit_state in {"unavailable", "unknown", ""}:
        raise RuntimeError(f"{GIESSZEIT_ENTITY} ist nicht verfügbar.")

    pump_state = entity_state(client, PUMPE_ENTITY)
    if pump_state in {"unavailable", "unknown", ""}:
        raise RuntimeError(f"{PUMPE_ENTITY} ist nicht verfügbar.")
    if pump_state == "on":
        raise RuntimeError("Die Pumpe ist bereits eingeschaltet.")

    if dry_run:
        return

    client.post(
        "/api/services/input_number/set_value",
        {"entity_id": GIESSZEIT_ENTITY, "value": GIESSZEIT_SEKUNDEN},
    )
    client.post(
        "/api/services/script/turn_on",
        {"entity_id": GIESS_SCRIPT_ENTITY},
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pflanze 1 über Home Assistant für 10 Sekunden gießen."
    )
    parser.add_argument("--ha-url", help="Home-Assistant-Basis-URL")
    parser.add_argument("--token", help="Long-lived access token; bevorzugt HA_TOKEN")
    parser.add_argument(
        "--enable-homeassistant",
        action="store_true",
        help=f"Home-Assistant-Zugriffe für diesen Aufruf erlauben ({HOMEASSISTANT_ENABLED_ENV}=1)",
    )
    parser.add_argument(
        "--disable-homeassistant",
        action="store_true",
        help=f"Home-Assistant-Zugriffe für diesen Aufruf sperren ({HOMEASSISTANT_ENABLED_ENV}=0)",
    )
    parser.add_argument(
        "--sync-dir",
        type=Path,
        default=Path(os.environ.get("HOMEASSISTANT_SYNC_DIR", DEFAULT_SYNC_DIR)),
        help="Pfad zum vorhandenen homeassistant_sync-Verzeichnis",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verbindung und Skriptstatus prüfen, aber nicht gießen",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.enable_homeassistant and args.disable_homeassistant:
        print("Fehler: --enable-homeassistant und --disable-homeassistant schließen sich aus.", file=sys.stderr)
        return 2
    if args.enable_homeassistant:
        os.environ[HOMEASSISTANT_ENABLED_ENV] = "1"
    if args.disable_homeassistant:
        os.environ[HOMEASSISTANT_ENABLED_ENV] = "0"
    try:
        sync_module = load_homeassistant_sync(args.sync_dir)
        ha_url, token = load_connection_settings(
            sync_module,
            args.sync_dir,
            ha_url=args.ha_url,
            token=args.token,
        )
        client = sync_module.HomeAssistantRestClient(ha_url, token, timeout=12.0)
        feuchte = bodenfeuchte_text(client)
        print(f"Bodenfeuchte Pflanze 1: {feuchte}")
        giessen(client, dry_run=args.dry_run)
    except Exception as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1

    if args.dry_run:
        print(
            f"Prüfung erfolgreich: {GIESS_SCRIPT_ENTITY} ist bereit; "
            "die Pumpe wurde nicht gestartet."
        )
    else:
        print(
            f"Pflanze 1 wird {GIESSZEIT_SEKUNDEN} Sekunden gegossen "
            f"({GIESS_SCRIPT_ENTITY})."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
