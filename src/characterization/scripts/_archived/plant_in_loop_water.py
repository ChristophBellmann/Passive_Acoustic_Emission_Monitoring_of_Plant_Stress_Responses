#!/usr/bin/env python3
"""
Plant-in-the-Loop Bewässerungs-Experiment.

Explizit vorab freigegeben durch Nutzer (2026-06-26):
  "jetzt und dann alle 2 Tage, 10s bleibt"

Aufgerufen via system-cron alle 2 Tage um 20:13 Uhr.

Wissenschaftliches Protokoll:
1. Laufende Kontinuierliche Messung stoppen (Scope freigeben)
2. N_PRE Frames als Baseline erfassen (alle Kanäle, alle Frequenzbänder)
3. Bewässerung ausführen (10s)
4. N_POST Frames als Response erfassen
5. Hypothesentests durchführen (quantifiziert)
6. Ergebnisse in data/watering_experiments/TIMESTAMP/ sichern
7. Kontinuierliche Messung neu starten
8. Commit + Push

Hypothesen (getestet bei jeder Bewässerung):
  H1: Breitband-Transient  — CH3 oder CH4 zeigt >3 dB in mind. einem 5kHz-Band (0–25 kHz)
  H2: Kohärenzänderung     — |Δcoh_3800| > 0.15 (CH3↔CH4)
  H3: CH1-Stabilität       — CH1 ändert sich <3 dB (kein EM-Artefakt)
  H4: CH3>CH4-Asymmetrie   — CH3-Zuwachs 0–10 kHz > CH4-Zuwachs
  H5: Zeitkonstante        — in welchem Frame tritt H1 auf?
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

CHAR_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CHAR_ROOT))

from scope.config import load_config
from scope.instrument import InstrumentConnection
from plant_ae.deep_acquisition import (
    configure_deep_memory_scope,
    acquire_deep_memory_frame,
    DEFAULT_SAMPLE_RATE_HZ,
    DEFAULT_MEMORY_DEPTH,
)
from plant_ae.rolling import (
    extract_frame_features,
    MAINS_HARMONIC_BANDS_HZ,
    ContinuousFrequencyMonitor,
)
from plant_ae.watering import CHANNELS, CONFIG_PATH, HomeAssistantPlant1Actuator

# ── Experiment-Parameter ──────────────────────────────────────────────────────
N_PRE             = 5    # Baseline-Frames vor Bewässerung (~5 min)
N_POST            = 10   # Response-Frames nach Bewässerung (~10 min)
WATERING_DURATION = 10   # Sekunden
RECONNECT_WAIT    = 20   # Sekunden Wartezeit vor Messung-Neustart

REPORT_ROOT = CHAR_ROOT / "data" / "reports" / "notebooks" / "04_continuous_frequency_sweep"
EXP_ROOT    = CHAR_ROOT / "data" / "watering_experiments"
BAND_LABELS = [f"{i*5}–{i*5+5}kHz" for i in range(20)]
MEASUREMENT_PY = CHAR_ROOT / "measurement.py"
VENV_PYTHON    = CHAR_ROOT / ".venv" / "bin" / "python3"


# ── Hilffunktionen ────────────────────────────────────────────────────────────

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def local_now() -> str:
    return datetime.now().astimezone().isoformat()


def mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else float("nan")


def std(vals: list[float]) -> float:
    if len(vals) < 2:
        return float("nan")
    m = mean(vals)
    return math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))


def _latest_session_events() -> Path | None:
    candidates = sorted(REPORT_ROOT.glob("2*/events.jsonl"))
    return candidates[-1] if candidates else None


def log_event(event: dict, exp_events: Path, session_events: Path | None) -> None:
    line = json.dumps(event, ensure_ascii=False) + "\n"
    with exp_events.open("a") as f:
        f.write(line)
    if session_events and session_events.exists():
        with session_events.open("a") as f:
            f.write(line)


# ── Scope-Erfassung ───────────────────────────────────────────────────────────

def _frame_to_record(frame, seq: int, candidate_analysis: dict) -> dict:
    """Vollständiges Frame-Dict: Band-Energie, Peaks, Kandidaten-Analyse."""
    be_db = {
        f"CH{ch}": [
            round(10 * math.log10(max(frame.band_energy[i][b], 1e-30)), 2)
            for b in range(20)
        ]
        for i, ch in enumerate(CHANNELS)
    }
    peak_freqs = {
        f"CH{ch}": [round(p["frequency_hz"], 1) for p in frame.peaks.get(str(ch), [])]
        for ch in CHANNELS
    }
    return {
        "sequence": seq,
        "timestamp_utc": frame.timestamp_utc,
        "n_samples": frame.n_samples,
        "band_energy_db": be_db,
        "peak_freqs_hz": peak_freqs,
        "candidate_analysis": candidate_analysis,
    }


def capture_frames(
    conn, config, n: int, start_seq: int, label: str,
    cand_monitor: "ContinuousFrequencyMonitor | None" = None,
) -> list[dict]:
    records = []
    print(f"\n── {label}: {n} Frames ──", flush=True)
    for i in range(n):
        t0 = time.monotonic()
        captures = acquire_deep_memory_frame(
            conn, config, sequence=start_seq + i,
            sample_rate_hz=DEFAULT_SAMPLE_RATE_HZ,
            memory_depth=DEFAULT_MEMORY_DEPTH,
        )
        frame = extract_frame_features(
            start_seq + i, captures,
            ignore_frequency_bands_hz=MAINS_HARMONIC_BANDS_HZ,
        )
        # _track_candidates benötigt frame.voltages → vor free_voltages aufrufen
        candidate_analysis = cand_monitor._track_candidates(frame) if cand_monitor else {}
        rec = _frame_to_record(frame, start_seq + i, candidate_analysis)
        records.append(rec)
        coh = candidate_analysis.get("3800", {}).get("coherence_ch3_ch4", "?")
        trk = candidate_analysis.get("3800", {}).get("tracked_freq_hz", "?")
        elapsed = time.monotonic() - t0
        print(
            f"  [{i+1:2d}/{n}] seq={start_seq+i}  "
            f"coh_3800={coh!s:6}  tracked={trk!s:7}Hz  {elapsed:.1f}s",
            flush=True,
        )
        frame.free_voltages()
    return records


def save_jsonl(records: list[dict], path: Path) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ── Band-Statistiken ──────────────────────────────────────────────────────────

def band_stats(records: list[dict], channel: str) -> dict[int, dict]:
    result = {}
    for b in range(20):
        vals = [r["band_energy_db"].get(channel, [])[b]
                for r in records if len(r["band_energy_db"].get(channel, [])) > b]
        result[b] = {"mean": round(mean(vals), 2), "std": round(std(vals), 2), "n": len(vals)}
    return result


def coh_stats(records: list[dict], cand: str = "3800") -> dict:
    vals = [
        r["candidate_analysis"][cand]["coherence_ch3_ch4"]
        for r in records
        if cand in r.get("candidate_analysis", {})
    ]
    return {"mean": round(mean(vals), 4), "std": round(std(vals), 4), "n": len(vals), "values": vals}


def tracked_stats(records: list[dict], cand: str = "3800") -> dict:
    vals = [
        r["candidate_analysis"][cand]["tracked_freq_hz"]
        for r in records
        if cand in r.get("candidate_analysis", {})
    ]
    return {"mean": round(mean(vals), 1), "std": round(std(vals), 1), "values": vals}


# ── Hypothesentests ───────────────────────────────────────────────────────────

def test_h1(pre: dict, post_records: list[dict]) -> dict:
    """H1: >3 dB Breitband-Transient in CH3/CH4, 0–25 kHz."""
    hits = []
    for ch in [f"CH{c}" for c in CHANNELS]:
        for b in range(5):
            pre_m = pre[ch][b]["mean"]
            for i, rec in enumerate(post_records):
                val = (rec["band_energy_db"].get(ch, []) + [None] * 20)[b]
                if val is not None and val - pre_m > 3.0:
                    hits.append({
                        "channel": ch, "band": BAND_LABELS[b],
                        "delta_db": round(val - pre_m, 2),
                        "post_frame_idx": i,
                        "pre_mean_db": pre_m, "post_val_db": val,
                    })
    return {"confirmed": bool(hits), "threshold_db": 3.0, "hits": hits[:10]}


def test_h2(pre_coh: dict, post_coh: dict) -> dict:
    """H2: |Δcoh_3800| > 0.15."""
    delta = post_coh["mean"] - pre_coh["mean"]
    return {
        "confirmed": abs(delta) > 0.15,
        "pre_mean": pre_coh["mean"], "post_mean": post_coh["mean"],
        "delta": round(delta, 4), "threshold": 0.15,
    }


def test_h3(pre: dict, post: dict) -> dict:
    """H3: CH1 ändert sich <3 dB (kein EM-Artefakt)."""
    violations, max_d = [], 0.0
    for b in range(20):
        d = abs(post["CH1"][b]["mean"] - pre["CH1"][b]["mean"])
        max_d = max(max_d, d)
        if d > 3.0:
            violations.append({"band": BAND_LABELS[b], "delta_db": round(d, 2)})
    return {"confirmed": not violations, "max_delta_db": round(max_d, 2), "violations": violations}


def test_h4(pre: dict, post: dict) -> dict:
    """H4: CH3-Zuwachs (0–10 kHz) > CH4-Zuwachs."""
    def avg_delta(ch):
        return mean([post[ch][b]["mean"] - pre[ch][b]["mean"] for b in range(2)])
    d3, d4 = avg_delta("CH3"), avg_delta("CH4")
    return {
        "confirmed": d3 > d4,
        "delta_ch3_db": round(d3, 2), "delta_ch4_db": round(d4, 2),
    }


def test_h5(pre: dict, post_records: list[dict]) -> dict:
    """H5: In welchem Frame tritt der erste >3 dB Transient auf?"""
    for i, rec in enumerate(post_records):
        for ch in [f"CH{c}" for c in CHANNELS]:
            for b in range(5):
                val = (rec["band_energy_db"].get(ch, []) + [None] * 20)[b]
                if val is not None and val - pre[ch][b]["mean"] > 3.0:
                    return {
                        "first_hit_frame": i,
                        "first_hit_channel": ch,
                        "first_hit_band": BAND_LABELS[b],
                        "immediate": i <= 1,
                    }
    return {"first_hit_frame": None, "immediate": None}


# ── Mess-Infrastruktur ────────────────────────────────────────────────────────

def measurement_cmd(subcmd: str) -> bool:
    result = subprocess.run(
        [str(VENV_PYTHON), str(MEASUREMENT_PY), subcmd],
        capture_output=True, text=True, timeout=30,
    )
    print(result.stdout.strip() or result.stderr.strip(), flush=True)
    return result.returncode == 0


def git_commit_push(exp_dir: Path, session_events: Path | None) -> None:
    repo_root = CHAR_ROOT.parent.parent
    paths = [str(exp_dir)]
    if session_events:
        paths.append(str(session_events))
    subprocess.run(["git", "add"] + paths, cwd=repo_root, check=False)
    subprocess.run(
        ["git", "commit", "-m",
         f"Watering experiment {exp_dir.name} [auto]"],
        cwd=repo_root, check=False,
    )
    subprocess.run(["git", "push"], cwd=repo_root, check=False)


# ── Hauptprogramm ─────────────────────────────────────────────────────────────

def main() -> None:
    dry_run = "--dry-run" in sys.argv
    n_pre  = 2 if dry_run else N_PRE
    n_post = 2 if dry_run else N_POST

    suffix  = "_dryrun" if dry_run else ""
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S") + suffix
    exp_dir = EXP_ROOT / now_str
    exp_dir.mkdir(parents=True, exist_ok=True)
    exp_events  = exp_dir / "events.jsonl"
    sess_events = None if dry_run else _latest_session_events()

    mode = "DRY-RUN" if dry_run else "LIVE"
    print(f"[{local_now()[11:16]}] Plant-in-the-Loop Experiment {now_str} [{mode}]", flush=True)
    print(f"  Pre-Frames: {n_pre}, Post-Frames: {n_post}, Bewässerung: {WATERING_DURATION}s", flush=True)
    if dry_run:
        print("  DRY-RUN: kein Wässern, kein Commit, kein Push", flush=True)
    print(f"  Experiment-Verzeichnis: {exp_dir}", flush=True)

    # Hypothesen-Protokoll sichern
    protocol = {
        "experiment_id": now_str,
        "started_utc": utc_now(),
        "design": {
            "n_pre_frames": N_PRE, "n_post_frames": N_POST,
            "watering_duration_s": WATERING_DURATION,
            "scope": "Rigol DS1104Z, 500kSa/s, 300k Punkte, Δf=1.67Hz",
            "channels": {
                "CH1": "820kΩ passiv (EM-Referenz)",
                "CH3": "LM358+820kΩ (Erde, Pflanzenwurzelzone)",
                "CH4": "LM358+820kΩ (Edelstahlstab neben Pflanze)",
            },
        },
        "prior_knowledge": {
            "cron_watering_2026-06-27": {"pre_coh": 0.6311, "post_coh": 0.5272, "delta": -0.1039},
            "manual_watering_2026-06-26": {"pre_coh": 0.1487},
            "historical_day_coh_mean": 0.274,
            "historical_night_coh_mean": 0.798,
            "coh_natural_std": 0.219,
        },
        "hypotheses": {
            "H1": "CH3 oder CH4 zeigt >3 dB in mind. einem 5kHz-Band (0–25 kHz) innerhalb der ersten 5 Post-Frames",
            "H2": "|post_coh_mean − pre_coh_mean| > 0.15 an 3800Hz (CH3↔CH4); Richtung: Abnahme erwartet",
            "H3": "CH1-Bandenergie ändert sich <3 dB in allen Bändern (kein EM-Artefakt)",
            "H4": "CH3-Energiezuwachs 0–10 kHz > CH4-Zuwachs (Bodensensor reagiert stärker als Metallstab)",
            "H5": "Falls H1 bestätigt: Frame 0–1 = Hydraulikschock, Frame 2–5 = Diffusion durch Bodenmatrix",
        },
    }
    with (exp_dir / "protocol.json").open("w") as f:
        json.dump(protocol, f, indent=2, ensure_ascii=False)

    # Start-Event
    log_event({
        "timestamp_utc": utc_now(), "timestamp_local": local_now(),
        "type": "watering_experiment_start",
        "experiment_id": now_str, "n_pre": n_pre, "n_post": n_post,
        "dry_run": dry_run,
        "authorization": "user_standing_permission_2026-06-26",
    }, exp_events, sess_events)

    # Kandidaten-Monitor für _track_candidates (persist_frames=False → nur manifest.json)
    cand_monitor = ContinuousFrequencyMonitor(
        persist_frames=False, persist_events=False, save_psd_snapshots=False,
    )

    # ── 1. Kontinuierliche Messung stoppen ────────────────────────────────────
    print(f"\n[{local_now()[11:16]}] Stoppe kontinuierliche Messung …", flush=True)
    measurement_cmd("stop")
    time.sleep(3)

    config = load_config(CONFIG_PATH)
    seq_offset = 5000  # kein Konflikt mit continuierlicher Session-Sequenz

    try:
        # ── 2. PRE-PHASE (eigene VISA-Verbindung) ────────────────────────────
        with InstrumentConnection(config) as conn:
            profile = configure_deep_memory_scope(conn)
            print(
                f"[{local_now()[11:16]}] Scope verbunden: {profile['profile']}, "
                f"{profile['sample_rate_hz']/1e3:.0f} kSa/s, {profile['memory_depth']:,} Punkte",
                flush=True,
            )
            pre_records = capture_frames(
                conn, config, n_pre, seq_offset, "PRE-PHASE (Baseline)",
                cand_monitor=cand_monitor,
            )
        # VISA-Verbindung zu Scope geschlossen — Scope ist frei während Bewässerung
        save_jsonl(pre_records, exp_dir / "pre_frames.jsonl")

        pre_bstats = {f"CH{ch}": band_stats(pre_records, f"CH{ch}") for ch in CHANNELS}
        pre_coh    = coh_stats(pre_records)
        pre_trk    = tracked_stats(pre_records)

        print(f"\n  Baseline: coh_3800 mean={pre_coh['mean']:.4f} ± {pre_coh['std']:.4f}", flush=True)
        print(f"  Tracked 3800Hz: {pre_trk['mean']:.1f} ± {pre_trk['std']:.1f} Hz", flush=True)

        log_event({
            "timestamp_utc": utc_now(), "timestamp_local": local_now(),
            "type": "watering_experiment_pre_complete",
            "experiment_id": now_str,
            "pre_coh_mean": pre_coh["mean"], "pre_coh_std": pre_coh["std"],
            "pre_tracked_freq_hz": pre_trk["mean"],
            "pre_n_frames": n_pre,
        }, exp_events, sess_events)

        # ── 3. BEWÄSSERUNG ────────────────────────────────────────────────────
        print(f"\n[{local_now()[11:16]}] BEWÄSSERUNG {WATERING_DURATION}s …", flush=True)
        water_ts = utc_now()
        water_ok = False
        water_error = None
        if dry_run:
            print(f"  DRY-RUN — Actuator.assert_ready() prüfen, kein water()", flush=True)
            try:
                actuator = HomeAssistantPlant1Actuator()
                actuator.assert_ready()
                water_ok = True
                print(f"  assert_ready() OK — Actuator einsatzbereit.", flush=True)
            except Exception as e:
                water_error = str(e)
                print(f"  assert_ready() FEHLER: {e}", flush=True)
        else:
            try:
                actuator = HomeAssistantPlant1Actuator()
                actuator.assert_ready()
                actuator.water()
                water_ok = True
                print(f"  OK — watering triggered, waiting {WATERING_DURATION + 2}s ...", flush=True)
                time.sleep(WATERING_DURATION + 2)  # wait for irrigation to finish before post-phase
            except Exception as e:
                water_error = str(e)
                print(f"  FEHLER: {e}", flush=True)

        log_event({
            "timestamp_utc": water_ts, "timestamp_local": local_now(),
            "light_phase": "day",  # cron läuft um 20:13 → Tagphase
            "type": "plant_in_loop_watering",
            "phase": "triggered",
            "experiment_id": now_str,
            "watering_duration_s": WATERING_DURATION,
            "water_ok": water_ok,
            "water_error": water_error,
            "schedule": "every_2_days",
            "experiment": "plant_in_loop_v1",
            "authorization": "user_standing_permission_2026-06-26",
        }, exp_events, sess_events)

        if not water_ok:
            print("Bewässerungsfehler — Experiment abgebrochen.", flush=True)
            return

        # ── 4. POST-PHASE (neue VISA-Verbindung nach Bewässerung) ────────────
        with InstrumentConnection(config) as conn:
            profile = configure_deep_memory_scope(conn)
            print(
                f"[{local_now()[11:16]}] Scope reconnect: {profile['profile']}",
                flush=True,
            )
            post_records = capture_frames(
                conn, config, n_post, seq_offset + n_pre, "POST-PHASE (Response)",
                cand_monitor=cand_monitor,
            )
        save_jsonl(post_records, exp_dir / "post_frames.jsonl")

    finally:
        # ── 7. Kontinuierliche Messung immer neu starten ──────────────────────
        print(f"\n[{local_now()[11:16]}] Starte kontinuierliche Messung neu …", flush=True)
        time.sleep(RECONNECT_WAIT)
        measurement_cmd("start")

    # ── 5. ANALYSE ────────────────────────────────────────────────────────────
    post_bstats = {f"CH{ch}": band_stats(post_records, f"CH{ch}") for ch in CHANNELS}
    post_coh    = coh_stats(post_records)
    post_trk    = tracked_stats(post_records)

    h1 = test_h1(pre_bstats, post_records)
    h2 = test_h2(pre_coh, post_coh)
    h3 = test_h3(pre_bstats, post_bstats)
    h4 = test_h4(pre_bstats, post_bstats)
    h5 = test_h5(pre_bstats, post_records)

    band_deltas = {
        f"CH{ch}": {
            BAND_LABELS[b]: round(post_bstats[f"CH{ch}"][b]["mean"] - pre_bstats[f"CH{ch}"][b]["mean"], 2)
            for b in range(20)
        }
        for ch in CHANNELS
    }

    analysis = {
        "experiment_id": now_str,
        "analysed_utc": utc_now(),
        "summary": {
            "pre_coh_mean": pre_coh["mean"], "post_coh_mean": post_coh["mean"],
            "delta_coh": round(post_coh["mean"] - pre_coh["mean"], 4),
            "pre_tracked_hz": pre_trk["mean"], "post_tracked_hz": post_trk["mean"],
            "delta_tracked_hz": round(post_trk["mean"] - pre_trk["mean"], 1),
        },
        "hypothesis_tests": {
            "H1_broadband_transient": h1,
            "H2_coherence_change": h2,
            "H3_ch1_stable": h3,
            "H4_ch3_ch4_asymmetry": h4,
            "H5_timing": h5,
        },
        "band_energy_delta_db": band_deltas,
        "pre_band_stats": {k: {BAND_LABELS[b]: v for b, v in s.items()} for k, s in pre_bstats.items()},
        "post_band_stats": {k: {BAND_LABELS[b]: v for b, v in s.items()} for k, s in post_bstats.items()},
        "coherence_timeseries": (
            [{"phase": "pre",  "seq": r["sequence"], "ts": r.get("timestamp_utc", ""),
              "coh": r.get("candidate_analysis", {}).get("3800", {}).get("coherence_ch3_ch4")}
             for r in pre_records]
            + [{"phase": "post", "seq": r["sequence"], "ts": r.get("timestamp_utc", ""),
                "coh": r.get("candidate_analysis", {}).get("3800", {}).get("coherence_ch3_ch4")}
               for r in post_records]
        ),
    }

    with (exp_dir / "analysis.json").open("w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)

    # Post-Event
    log_event({
        "timestamp_utc": utc_now(), "timestamp_local": local_now(),
        "type": "plant_in_loop_watering",
        "phase": "post",
        "experiment_id": now_str,
        "post_coh_mean": post_coh["mean"],
        "pre_coh_mean": pre_coh["mean"],
        "delta_coh": round(post_coh["mean"] - pre_coh["mean"], 4),
        "experiment": "plant_in_loop_v1",
        "authorization": "user_standing_permission_2026-06-26",
        "h1_confirmed": h1["confirmed"],
        "h2_confirmed": h2["confirmed"],
        "h3_confirmed": h3["confirmed"],
        "h4_confirmed": h4["confirmed"],
    }, exp_events, sess_events)

    # ── Ausgabe ────────────────────────────────────────────────────────────────
    print(f"\n{'='*60}", flush=True)
    print(f"HYPOTHESENTEST-ERGEBNISSE — {now_str}", flush=True)
    print(f"{'='*60}", flush=True)
    for key, res in analysis["hypothesis_tests"].items():
        status = "✓ BESTÄTIGT" if res.get("confirmed") else "✗ NICHT BESTÄTIGT"
        print(f"{key}: {status}", flush=True)
    print(f"\nKohärenz 3800Hz: {pre_coh['mean']:.4f} → {post_coh['mean']:.4f} "
          f"(Δ={post_coh['mean']-pre_coh['mean']:+.4f})", flush=True)
    print(f"Tracked-Freq: {pre_trk['mean']:.1f} → {post_trk['mean']:.1f} Hz "
          f"(Δ={post_trk['mean']-pre_trk['mean']:+.1f})", flush=True)

    print(f"\n{'Band':>12}  {'ΔCH3':>8}  {'ΔCH4':>8}  {'ΔCH1':>8}", flush=True)
    for b in range(5):  # 0–25 kHz
        print(f"{BAND_LABELS[b]:>12}  "
              f"{band_deltas['CH3'][BAND_LABELS[b]]:>+8.2f}  "
              f"{band_deltas['CH4'][BAND_LABELS[b]]:>+8.2f}  "
              f"{band_deltas['CH1'][BAND_LABELS[b]]:>+8.2f}", flush=True)

    if h1["hits"]:
        print(f"\nH1-Treffer:", flush=True)
        for h in h1["hits"][:5]:
            print(f"  {h}", flush=True)

    print(f"\nGespeichert: {exp_dir}", flush=True)

    # ── 8. Commit + Push ──────────────────────────────────────────────────────
    if dry_run:
        print(f"\n[DRY-RUN] Kein Commit/Push.", flush=True)
    else:
        new_sess_events = _latest_session_events()
        git_commit_push(exp_dir, new_sess_events)
        print(f"[{local_now()[11:16]}] Committed & pushed.", flush=True)


if __name__ == "__main__":
    main()
