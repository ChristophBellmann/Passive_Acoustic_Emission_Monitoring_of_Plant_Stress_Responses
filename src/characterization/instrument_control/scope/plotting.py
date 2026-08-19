"""Plotting functions for vibration characterization."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .peak_detection import SpectralPeak
from .spectral import FFTResult, StftResult, WelchResult, amplitude_to_db, psd_to_db


def plot_time_domain(
    time_vector: np.ndarray,
    voltage: np.ndarray,
    channel: int,
    label: str,
    output_path: Path,
    title: Optional[str] = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(time_vector * 1e3, voltage, linewidth=0.5)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(title or f"Time Domain - CH{channel} ({label})")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_time_domain_zoom(
    time_vector: np.ndarray,
    voltage: np.ndarray,
    channel: int,
    label: str,
    output_path: Path,
    center_idx: Optional[int] = None,
    window_samples: int = 500,
) -> Path:
    if center_idx is None:
        center_idx = int(np.argmax(np.abs(voltage)))
    start = max(0, center_idx - window_samples // 2)
    end = min(len(time_vector), center_idx + window_samples // 2)
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(time_vector[start:end] * 1e3, voltage[start:end], linewidth=0.8)
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(f"Zoomed Time Domain - CH{channel} ({label})")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_fft(
    fft_result: FFTResult,
    channel: int,
    label: str,
    output_path: Path,
    min_freq: float = 0,
    max_freq: Optional[float] = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(12, 5))
    amp_db = amplitude_to_db(fft_result.amplitude)
    ax.plot(fft_result.frequencies, amp_db, linewidth=0.5)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Amplitude (dB)")
    ax.set_title(f"FFT Amplitude Spectrum - CH{channel} ({label})")
    if min_freq is not None:
        ax.set_xlim(left=min_freq)
    if max_freq is not None:
        ax.set_xlim(right=max_freq)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_welch(
    welch: WelchResult,
    channel: int,
    label: str,
    output_path: Path,
    peaks: Optional[list[SpectralPeak]] = None,
    min_freq: float = 0,
    max_freq: Optional[float] = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(12, 5))
    psd_db = psd_to_db(welch.psd)
    ax.plot(welch.frequencies, psd_db, linewidth=0.5, label="Welch PSD")
    if peaks:
        for p in peaks:
            ax.axvline(p.frequency_hz, color="red", alpha=0.3, linewidth=0.5)
            ax.annotate(
                f"{p.frequency_hz:.1f} Hz",
                xy=(p.frequency_hz, psd_db[np.argmin(np.abs(welch.frequencies - p.frequency_hz))]),
                fontsize=7,
                rotation=45,
                alpha=0.7,
            )
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("PSD (dB)")
    ax.set_title(f"Welch PSD - CH{channel} ({label})")
    if min_freq is not None:
        ax.set_xlim(left=min_freq)
    if max_freq is not None:
        ax.set_xlim(right=max_freq)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_spectrogram(
    stft: StftResult,
    channel: int,
    label: str,
    output_path: Path,
    max_freq: Optional[float] = None,
) -> Path:
    fig, ax = plt.subplots(figsize=(12, 6))
    magnitude_db = amplitude_to_db(stft.magnitude)
    t_mesh, f_mesh = np.meshgrid(stft.times, stft.frequencies)
    pcm = ax.pcolormesh(
        stft.times * 1e3,
        stft.frequencies,
        magnitude_db,
        shading="gouraud",
        cmap="viridis",
    )
    fig.colorbar(pcm, ax=ax, label="Magnitude (dB)")
    ax.set_xlabel("Time (ms)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title(f"Spectrogram - CH{channel} ({label})")
    if max_freq is not None:
        ax.set_ylim(top=max_freq)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_peak_summary(
    peaks: list[SpectralPeak],
    channel: int,
    output_path: Path,
) -> Path:
    if not peaks:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, f"No peaks detected on CH{channel}", ha="center", va="center")
        ax.axis("off")
        fig.savefig(output_path, dpi=150)
        plt.close(fig)
        return output_path

    fig, ax = plt.subplots(figsize=(10, 5))
    freqs = [p.frequency_hz for p in peaks]
    proms = [p.prominence_db for p in peaks]
    colors = []
    for p in peaks:
        if "mains" in p.plausibility_label:
            colors.append("red")
        elif "switching" in p.plausibility_label:
            colors.append("orange")
        elif "mechanical" in p.plausibility_label:
            colors.append("green")
        else:
            colors.append("gray")
    ax.barh(range(len(freqs)), proms, color=colors, alpha=0.7)
    ax.set_yticks(range(len(freqs)))
    ax.set_yticklabels([f"{f:.1f} Hz" for f in freqs], fontsize=8)
    ax.set_xlabel("Prominence (dB)")
    ax.set_title(f"Peak Summary - CH{channel}")
    ax.grid(True, alpha=0.3, axis="x")
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def plot_channel_comparison(
    welch_ch1: WelchResult,
    welch_ch2: WelchResult,
    label_ch1: str,
    label_ch2: str,
    output_path: Path,
    peaks_ch1: Optional[list[SpectralPeak]] = None,
    peaks_ch2: Optional[list[SpectralPeak]] = None,
) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    psd_db1 = psd_to_db(welch_ch1.psd)
    psd_db2 = psd_to_db(welch_ch2.psd)
    ax1.plot(welch_ch1.frequencies, psd_db1, linewidth=0.5, label=label_ch1)
    if peaks_ch1:
        for p in peaks_ch1:
            ax1.axvline(p.frequency_hz, color="red", alpha=0.3, linewidth=0.5)
    ax2.plot(welch_ch2.frequencies, psd_db2, linewidth=0.5, label=label_ch2, color="tab:orange")
    if peaks_ch2:
        for p in peaks_ch2:
            ax2.axvline(p.frequency_hz, color="red", alpha=0.3, linewidth=0.5)
    ax1.set_ylabel("PSD (dB)")
    ax1.set_title("Channel Comparison - Welch PSD")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)
    ax2.set_xlabel("Frequency (Hz)")
    ax2.set_ylabel("PSD (dB)")
    ax2.legend(fontsize=8)
    ax2.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path
