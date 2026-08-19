"""CLI entry point for scope."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import typer
from rich.console import Console
from rich.table import Table

from . import __version__
from .acquisition import acquire_series, acquire_single_capture, save_capture_csv, save_capture_npz
from .config import ExperimentConfig, load_config
from .instrument import InstrumentConnection, read_oscilloscope_settings
from .peak_detection import assess_repeatability, detect_peaks_in_welch
from .plausibility import run_plausibility_checks
from .plotting import (
    plot_channel_comparison,
    plot_fft,
    plot_peak_summary,
    plot_spectrogram,
    plot_time_domain,
    plot_time_domain_zoom,
    plot_welch,
)
from .preprocessing import preprocess
from .reporting import generate_report
from .spectral import compute_fft, compute_stft, compute_welch
from .utils import ensure_output_dirs, timestamp_str

app = typer.Typer(name="scope", help="Oscilloscope vibration characterization")
console = Console()


def _resolve_config(config: str) -> Path:
    p = Path(config)
    if not p.exists():
        console.print(f"[red]Config not found: {p}[/red]")
        raise typer.Exit(1)
    return p


@app.command()
def check_connection(config: str = typer.Option(..., "--config", "-c")):
    """Check connection to the oscilloscope."""
    cfg_path = _resolve_config(config)
    cfg = load_config(cfg_path)
    console.print(f"Connecting to {cfg.instrument.visa_resource} ...")
    try:
        with InstrumentConnection(cfg) as conn:
            idn = conn.query("*IDN?")
            console.print(f"[green]Connected![/green]")
            console.print(f"IDN: {idn}")
            for ch in cfg.oscilloscope.channels:
                settings = read_oscilloscope_settings(conn, ch)
                console.print(f"\nCH{ch}:")
                console.print(f"  Enabled: {settings.enabled}")
                console.print(f"  Coupling: {settings.coupling}")
                console.print(f"  Probe ratio: {settings.probe_ratio}")
                console.print(f"  VScale: {settings.vertical_scale_v_per_div} V/div")
                console.print(f"  VOffset: {settings.vertical_offset_v} V")
                console.print(f"  HScale: {settings.horizontal_scale_s_per_div} s/div")
                console.print(f"  Sample rate: {settings.sample_rate_sa_per_s:.0f} Sa/s")
                console.print(f"  Memory depth: {settings.memory_depth}")
                console.print(f"  Trigger: {settings.trigger_mode} / {settings.trigger_source} @ {settings.trigger_level_v:.3f} V")
    except Exception as e:
        console.print(f"[red]Connection failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def acquire(
    config: str = typer.Option(..., "--config", "-c"),
    captures: Optional[int] = typer.Option(None, "--captures", "-n"),
):
    """Acquire waveform data from the oscilloscope."""
    cfg_path = _resolve_config(config)
    cfg = load_config(cfg_path)
    if captures is not None:
        cfg.acquisition.captures = captures

    base_dir = cfg_path.parent
    dirs = ensure_output_dirs(base_dir)

    console.print(f"Acquiring {cfg.acquisition.captures} captures from {cfg.instrument.visa_resource} ...")
    try:
        with InstrumentConnection(cfg) as conn:
            from tqdm import tqdm
            total = cfg.acquisition.captures * len([
                ch for ch in cfg.oscilloscope.channels
                if cfg.oscilloscope.channel_settings.get(ch, None) is None
                or cfg.oscilloscope.channel_settings[ch].enabled
            ])
            pbar = tqdm(total=total, desc="Acquiring", file=sys.stderr)
            all_captures = []
            for i in range(cfg.acquisition.captures):
                for ch in cfg.oscilloscope.channels:
                    ch_cfg = cfg.oscilloscope.channel_settings.get(ch)
                    if ch_cfg and not ch_cfg.enabled:
                        continue
                    cap = acquire_single_capture(conn, ch, cfg, capture_id=i)
                    all_captures.append(cap)
                    save_capture_npz(cap, dirs["raw"])
                    if cfg.output.save_raw_csv:
                        save_capture_csv(cap, dirs["raw"])
                    pbar.update(1)
                if i < cfg.acquisition.captures - 1 and cfg.acquisition.delay_between_captures_s > 0:
                    import time
                    time.sleep(cfg.acquisition.delay_between_captures_s)
            pbar.close()
    except Exception as e:
        console.print(f"[red]Acquisition failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Saved {len(all_captures)} captures to {dirs['raw']}[/green]")


@app.command()
def analyze(
    config: str = typer.Option(..., "--config", "-c"),
    input_dir: str = typer.Option(..., "--input", "-i"),
):
    """Analyze previously acquired waveform data."""
    cfg_path = _resolve_config(config)
    cfg = load_config(cfg_path)
    input_path = Path(input_dir)
    if not input_path.exists():
        console.print(f"[red]Input directory not found: {input_path}[/red]")
        raise typer.Exit(1)

    base_dir = cfg_path.parent
    dirs = ensure_output_dirs(base_dir)
    processed_dir = dirs["processed"]

    npz_files = sorted(input_path.glob("*.npz"))
    if not npz_files:
        console.print("[red]No .npz files found in input directory.[/red]")
        raise typer.Exit(1)

    console.print(f"Found {len(npz_files)} captures to analyze.")

    from .acquisition import Capture, CaptureMetadata
    all_peaks_by_ch: dict[int, list[list]] = {}
    all_welch_by_ch: dict[int, list] = {}
    preprocessing_results: dict[int, object] = {}
    plot_paths: dict[str, Path] = {}
    sample_rate = 0.0

    for npz_file in npz_files:
        data = np.load(npz_file, allow_pickle=True)
        time_vec = data["time_vector"]
        voltage = data["voltage_vector"]
        meta_arr = data["metadata"]
        meta = meta_arr[0] if meta_arr.ndim > 0 else meta_arr
        ch = int(meta["channel"]) if hasattr(meta, "__getitem__") else int(meta.item()["channel"])
        sample_rate = float(meta["sample_rate_sa_per_s"]) if hasattr(meta, "__getitem__") else float(meta.item()["sample_rate_sa_per_s"])

        pre = preprocess(
            time_vec, voltage,
            remove_dc_flag=cfg.processing.remove_dc,
            detrend_flag=cfg.processing.detrend,
            window=cfg.processing.window,
            clipping_threshold=cfg.plausibility.clipping_threshold_fraction,
        )
        preprocessing_results[ch] = pre

        ts = timestamp_str()
        plot_time_domain(
            time_vec, voltage, ch, str(meta["channel_label"] if hasattr(meta, "__getitem__") else meta.item()["channel_label"]),
            processed_dir / f"ch{ch}_{ts}_time.png",
        )
        plot_time_domain_zoom(
            time_vec, pre.voltage, ch, str(meta["channel_label"] if hasattr(meta, "__getitem__") else meta.item()["channel_label"]),
            processed_dir / f"ch{ch}_{ts}_time_zoom.png",
        )

        fft_res = compute_fft(pre.voltage, sample_rate, window=cfg.processing.window)
        plot_fft(
            fft_res, ch, str(meta["channel_label"] if hasattr(meta, "__getitem__") else meta.item()["channel_label"]),
            processed_dir / f"ch{ch}_{ts}_fft.png",
            min_freq=cfg.processing.min_frequency_hz,
            max_freq=cfg.processing.max_frequency_hz,
        )

        welch_res = compute_welch(
            pre.voltage, sample_rate,
            nperseg=cfg.processing.welch.nperseg,
            overlap=cfg.processing.welch.overlap,
        )
        if ch not in all_welch_by_ch:
            all_welch_by_ch[ch] = []
        all_welch_by_ch[ch].append(welch_res)

        if cfg.processing.stft.enabled:
            stft_res = compute_stft(
                pre.voltage, sample_rate,
                nperseg=cfg.processing.stft.nperseg,
                overlap=cfg.processing.stft.overlap,
            )
            plot_spectrogram(
                stft_res, ch, str(meta["channel_label"] if hasattr(meta, "__getitem__") else meta.item()["channel_label"]),
                processed_dir / f"ch{ch}_{ts}_spectrogram.png",
                max_freq=cfg.processing.max_frequency_hz,
            )

        peaks = detect_peaks_in_welch(
            welch_res,
            prominence_db=cfg.peak_detection.prominence_db,
            min_distance_hz=cfg.peak_detection.min_distance_hz,
            max_peaks=cfg.peak_detection.max_peaks,
            ignore_bands_hz=cfg.peak_detection.ignore_frequency_bands_hz,
            channel=ch,
        )
        if ch not in all_peaks_by_ch:
            all_peaks_by_ch[ch] = []
        all_peaks_by_ch[ch].append(peaks)

    peaks_by_ch_final: dict[int, list] = {}
    for ch, peak_list in all_peaks_by_ch.items():
        all_p = []
        for cap_peaks in peak_list:
            all_p.extend(cap_peaks)
        peaks_by_ch_final[ch] = all_p

    for ch, welch_list in all_welch_by_ch.items():
        avg_psd = np.mean([w.psd for w in welch_list], axis=0)
        avg_welch = type(welch_list[0])(frequencies=welch_list[0].frequencies, psd=avg_psd)
        ts = timestamp_str()
        plot_welch(
            avg_welch, ch, "average",
            processed_dir / f"ch{ch}_{ts}_welch.png",
            peaks=peaks_by_ch_final.get(ch),
            min_freq=cfg.processing.min_frequency_hz,
            max_freq=cfg.processing.max_frequency_hz,
        )
        plot_peak_summary(
            peaks_by_ch_final.get(ch, []), ch,
            processed_dir / f"ch{ch}_{ts}_peaks.png",
        )

    if 1 in all_welch_by_ch and 2 in all_welch_by_ch:
        avg_w1 = type(all_welch_by_ch[1][0])(
            frequencies=all_welch_by_ch[1][0].frequencies,
            psd=np.mean([w.psd for w in all_welch_by_ch[1]], axis=0),
        )
        avg_w2 = type(all_welch_by_ch[2][0])(
            frequencies=all_welch_by_ch[2][0].frequencies,
            psd=np.mean([w.psd for w in all_welch_by_ch[2]], axis=0),
        )
        ts = timestamp_str()
        plot_channel_comparison(
            avg_w1, avg_w2,
            cfg.oscilloscope.channel_settings.get(1, None) and cfg.oscilloscope.channel_settings[1].label or "CH1",
            cfg.oscilloscope.channel_settings.get(2, None) and cfg.oscilloscope.channel_settings[2].label or "CH2",
            processed_dir / f"comparison_{ts}.png",
            peaks_ch1=peaks_by_ch_final.get(1),
            peaks_ch2=peaks_by_ch_final.get(2),
        )

    repeatability_by_ch: dict[int, dict[float, bool]] = {}
    for ch, peak_list in all_peaks_by_ch.items():
        rep = assess_repeatability(
            peak_list,
            freq_tolerance_hz=cfg.peak_detection.min_distance_hz / 2,
            min_fraction=cfg.plausibility.repeatability_min_fraction,
        )
        repeatability_by_ch[ch] = rep
        for peaks in peak_list:
            for p in peaks:
                for rep_freq, is_rep in rep.items():
                    if abs(p.frequency_hz - rep_freq) < cfg.peak_detection.min_distance_hz / 2:
                        p.is_repeatable = is_rep

    channel_peaks_map = {ch: peaks_by_ch_final.get(ch, []) for ch in cfg.oscilloscope.channels}
    plausibility_results: dict[int, list] = {}
    for ch, peaks in peaks_by_ch_final.items():
        pre = preprocessing_results.get(ch)
        if pre is None:
            continue
        results = run_plausibility_checks(
            peaks, {ch: pre}, sample_rate, cfg, channel_peaks_map
        )
        plausibility_results[ch] = results

    report_path = dirs["reports"] / f"{timestamp_str()}_report.md"
    generate_report(
        config=cfg,
        config_path=str(cfg_path),
        preprocessing_results={ch: v for ch, v in preprocessing_results.items()},
        peaks_by_channel=peaks_by_ch_final,
        plausibility_results=plausibility_results,
        plot_paths=plot_paths,
        output_path=report_path,
        n_captures=cfg.acquisition.captures,
        sample_rate=sample_rate,
    )

    console.print(f"[green]Analysis complete. Report: {report_path}[/green]")


@app.command()
def report(
    config: str = typer.Option(..., "--config", "-c"),
    input_dir: str = typer.Option(..., "--input", "-i"),
):
    """Generate a report from processed data."""
    console.print("Report generation is integrated into the 'analyze' command.")
    console.print("Run: python -m scope.cli analyze --config <config> --input <dir>")


@app.command()
def run(
    config: str = typer.Option(..., "--config", "-c"),
    captures: Optional[int] = typer.Option(None, "--captures", "-n"),
):
    """Full pipeline: acquire + analyze."""
    cfg_path = _resolve_config(config)
    cfg = load_config(cfg_path)
    if captures is not None:
        cfg.acquisition.captures = captures

    base_dir = cfg_path.parent
    dirs = ensure_output_dirs(base_dir)
    raw_dir = dirs["raw"]

    console.print(f"[bold]Step 1: Acquiring data...[/bold]")
    try:
        with InstrumentConnection(cfg) as conn:
            from tqdm import tqdm
            all_captures = []
            for i in range(cfg.acquisition.captures):
                for ch in cfg.oscilloscope.channels:
                    ch_cfg = cfg.oscilloscope.channel_settings.get(ch)
                    if ch_cfg and not ch_cfg.enabled:
                        continue
                    cap = acquire_single_capture(conn, ch, cfg, capture_id=i)
                    all_captures.append(cap)
                    save_capture_npz(cap, raw_dir)
                    if cfg.output.save_raw_csv:
                        save_capture_csv(cap, raw_dir)
                if i < cfg.acquisition.captures - 1 and cfg.acquisition.delay_between_captures_s > 0:
                    import time
                    time.sleep(cfg.acquisition.delay_between_captures_s)
    except Exception as e:
        console.print(f"[red]Acquisition failed: {e}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Acquired {len(all_captures)} captures.[/green]")
    console.print(f"[bold]Step 2: Analyzing data...[/bold]")

    from typer import main as typer_main
    analyze(config=str(cfg_path), input_dir=str(raw_dir))


def main():
    app()


if __name__ == "__main__":
    main()
