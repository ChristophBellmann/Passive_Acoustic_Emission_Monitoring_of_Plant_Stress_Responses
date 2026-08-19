from __future__ import annotations

import unittest
from typing import Any

from giessen_pflanze1 import (
    BODENFEUCHTE_ENTITY,
    GIESSZEIT_ENTITY,
    GIESSZEIT_SEKUNDEN,
    GIESS_SCRIPT_ENTITY,
    PUMPE_ENTITY,
    bodenfeuchte_text,
    giessen,
)


class FakeRestClient:
    def __init__(
        self, script_state: str = "off", bodenfeuchte_state: str = "42.5"
    ) -> None:
        self.script_state = script_state
        self.bodenfeuchte_state = bodenfeuchte_state
        self.posts: list[tuple[str, dict[str, Any]]] = []

    def get(self, path: str) -> dict[str, str]:
        if path == f"/api/states/{GIESS_SCRIPT_ENTITY}":
            return {"entity_id": GIESS_SCRIPT_ENTITY, "state": self.script_state}
        if path == f"/api/states/{GIESSZEIT_ENTITY}":
            return {"entity_id": GIESSZEIT_ENTITY, "state": "10"}
        if path == f"/api/states/{PUMPE_ENTITY}":
            return {"entity_id": PUMPE_ENTITY, "state": "off"}
        if path == f"/api/states/{BODENFEUCHTE_ENTITY}":
            return {
                "entity_id": BODENFEUCHTE_ENTITY,
                "state": self.bodenfeuchte_state,
            }
        raise AssertionError(f"Unerwarteter GET-Aufruf: {path}")

    def post(
        self, path: str, payload: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        self.posts.append((path, payload or {}))
        return []


class GiessenTest(unittest.TestCase):
    def test_gibt_bodenfeuchte_mit_prozent_aus(self) -> None:
        self.assertEqual(bodenfeuchte_text(FakeRestClient()), "42.5 %")

    def test_offline_bodenfeuchte_ist_nicht_verfuegbar(self) -> None:
        client = FakeRestClient(bodenfeuchte_state="unavailable")

        self.assertEqual(bodenfeuchte_text(client), "nicht verfügbar")

    def test_setzt_zehn_sekunden_und_startet_script(self) -> None:
        client = FakeRestClient()

        giessen(client)

        self.assertEqual(
            client.posts,
            [
                (
                    "/api/services/input_number/set_value",
                    {"entity_id": GIESSZEIT_ENTITY, "value": GIESSZEIT_SEKUNDEN},
                ),
                (
                    "/api/services/script/turn_on",
                    {"entity_id": GIESS_SCRIPT_ENTITY},
                ),
            ],
        )

    def test_dry_run_schreibt_nichts(self) -> None:
        client = FakeRestClient()

        giessen(client, dry_run=True)

        self.assertEqual(client.posts, [])

    def test_laufendes_script_wird_nicht_erneut_gestartet(self) -> None:
        client = FakeRestClient(script_state="on")

        with self.assertRaisesRegex(RuntimeError, "läuft bereits"):
            giessen(client)

        self.assertEqual(client.posts, [])

    def test_nicht_verfuegbares_script_bricht_ab(self) -> None:
        client = FakeRestClient(script_state="unavailable")

        with self.assertRaisesRegex(RuntimeError, "nicht verfügbar"):
            giessen(client)

        self.assertEqual(client.posts, [])


if __name__ == "__main__":
    unittest.main()
