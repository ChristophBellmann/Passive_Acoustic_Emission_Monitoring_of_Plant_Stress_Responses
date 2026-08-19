#!/usr/bin/env python3
"""Overnight continuous AE monitor — equivalent to NB04 cell 3, CLI-safe."""
import sys, time, json, importlib.util
from pathlib import Path

CHAR_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(CHAR_ROOT))

from plant_ae.deep_acquisition import (
    configure_deep_memory_scope,
    acquire_deep_memory_frame,
    DEFAULT_SAMPLE_RATE_HZ,
    DEFAULT_MEMORY_DEPTH,
)
from plant_ae.rolling import (
    ContinuousFrequencyMonitor,
    extract_frame_features,
    MAINS_HARMONIC_BANDS_HZ,
)
from plant_ae.watering import CHANNELS, CONFIG_PATH
from scope.config import load_config
from scope.instrument import InstrumentConnection

# ── Temperature polling via Home Assistant ────────────────────────────────────
_actuator_path = CHAR_ROOT.parent / "actuator" / "giessen_pflanze1.py"
_spec = importlib.util.spec_from_file_location("plant1_actuator", _actuator_path)
_act_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_act_mod)
_sync_dir = _act_mod.DEFAULT_SYNC_DIR
_sync_mod = _act_mod.load_homeassistant_sync(_sync_dir)
_ha_url, _ha_token = _act_mod.load_connection_settings(_sync_mod, _sync_dir, ha_url=None, token=None)
_ha_client = _sync_mod.HomeAssistantRestClient(_ha_url, _ha_token, timeout=5.0)
TEMPERATURE_ENTITY = "sensor.satellite1_c412d0_temperature"

def _poll_temperature() -> float | None:
    try:
        result = _ha_client.get(f"/api/states/{TEMPERATURE_ENTITY}")
        return float(result["state"])
    except Exception:
        return None

# ── Monitor setup ─────────────────────────────────────────────────────────────
monitor = ContinuousFrequencyMonitor(
    persist_events=True,
    persist_frames=True,
    save_event_raw=False,
    timezone_name="Europe/Berlin",
    day_start_hour=6,
    night_start_hour=22,
    temperature_poller=_poll_temperature,
)
monitor.output_dir.mkdir(parents=True, exist_ok=True)

config = load_config(CONFIG_PATH)
sequence = 0
MAX_CONSEC_ERRORS = 5
RECONNECT_WAIT_S  = 30

print(f"[{time.strftime('%H:%M:%S')}] Overnight monitor started — output: {monitor.output_dir}")

def _log(kind: str, **extra):
    from datetime import datetime, timezone
    event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(),
             "type": kind, "sequence_at_event": sequence, **extra}
    with (monitor.output_dir / "events.jsonl").open("a") as fh:
        fh.write(json.dumps(event) + "\n")

try:
    while True:
        try:
            with InstrumentConnection(config) as conn:
                profile = configure_deep_memory_scope(conn)
                print(f"[{time.strftime('%H:%M:%S')}] Connected — "
                      f"{profile['sample_rate_hz']/1e3:.0f} kSa/s, "
                      f"{profile['memory_depth']:,} pts")
                _log("connection_ok")
                consec_errors = 0

                while True:
                    try:
                        captures = acquire_deep_memory_frame(
                            conn, config, sequence=sequence,
                            sample_rate_hz=DEFAULT_SAMPLE_RATE_HZ,
                            memory_depth=DEFAULT_MEMORY_DEPTH,
                        )
                        frame = extract_frame_features(
                            sequence, captures,
                            ignore_frequency_bands_hz=MAINS_HARMONIC_BANDS_HZ,
                        )
                        events = monitor.process_frame(frame)
                        consec_errors = 0
                        if events:
                            print(f"[{time.strftime('%H:%M:%S')}] seq {sequence:5d}: "
                                  f"{len(events)} event(s)")
                            for e in events:
                                print(f"  [{e['type']}]",
                                      {k: v for k, v in e.items() if k != "type"})
                        elif sequence % 10 == 0:
                            print(f"[{time.strftime('%H:%M:%S')}] seq {sequence:5d}  "
                                  f"(no events)")
                        sequence += 1

                    except KeyboardInterrupt:
                        raise
                    except Exception as exc:
                        consec_errors += 1
                        print(f"[{time.strftime('%H:%M:%S')}] seq {sequence}: "
                              f"error ({consec_errors}/{MAX_CONSEC_ERRORS}) — {exc}")
                        if consec_errors >= MAX_CONSEC_ERRORS:
                            _log("connection_lost", consecutive_errors=consec_errors,
                                 last_error=str(exc))
                            break
                        time.sleep(2.0)

        except KeyboardInterrupt:
            raise
        except Exception as exc:
            print(f"[{time.strftime('%H:%M:%S')}] Connection failed: {exc}")
            _log("connection_error", error=str(exc))

        print(f"[{time.strftime('%H:%M:%S')}] Reconnect in {RECONNECT_WAIT_S}s …")
        time.sleep(RECONNECT_WAIT_S)

except KeyboardInterrupt:
    print(f"\n[{time.strftime('%H:%M:%S')}] Stopped at seq {sequence}")
finally:
    monitor.finish("finished")
    print("Status:", monitor.status())
    print(f"Data: {monitor.output_dir}")
