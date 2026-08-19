"""Spectral analysis: FFT, Welch PSD, STFT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import signal as sp_signal


@dataclass
class FFTResult:
    frequencies: np.ndarray
    amplitude: np.ndarray
    phase: np.ndarray


@dataclass
class WelchResult:
    frequencies: np.ndarray
    psd: np.ndarray


@dataclass
class StftResult:
    frequencies: np.ndarray
    times: np.ndarray
    magnitude: np.ndarray


def compute_fft(
    voltage: np.ndarray,
    sample_rate: float,
    window: str = "hann",
) -> FFTResult:
    n = len(voltage)
    if n == 0:
        return FFTResult(
            frequencies=np.array([]),
            amplitude=np.array([]),
            phase=np.array([]),
        )
    win = sp_signal.get_window(window, n)
    windowed = voltage * win
    fft_vals = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    amplitude = 2.0 * np.abs(fft_vals) / n
    amplitude[0] /= 2.0
    if n % 2 == 0:
        amplitude[-1] /= 2.0
    phase = np.angle(fft_vals)
    return FFTResult(frequencies=freqs, amplitude=amplitude, phase=phase)


def compute_welch(
    voltage: np.ndarray,
    sample_rate: float,
    nperseg: int = 4096,
    overlap: float = 0.5,
    window: str = "hann",
) -> WelchResult:
    nperseg = min(nperseg, len(voltage))
    noverlap = int(nperseg * overlap)
    freqs, psd = sp_signal.welch(
        voltage,
        fs=sample_rate,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        scaling="density",
    )
    return WelchResult(frequencies=freqs, psd=psd)


def compute_stft(
    voltage: np.ndarray,
    sample_rate: float,
    nperseg: int = 2048,
    overlap: float = 0.75,
    window: str = "hann",
) -> StftResult:
    nperseg = min(nperseg, len(voltage))
    noverlap = int(nperseg * overlap)
    f, t, Zxx = sp_signal.stft(
        voltage,
        fs=sample_rate,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
    )
    return StftResult(frequencies=f, times=t, magnitude=np.abs(Zxx))


def amplitude_to_db(amplitude: np.ndarray, ref: float = 1.0) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        db = 20.0 * np.log10(np.maximum(amplitude, 1e-30) / ref)
    return db


def psd_to_db(psd: np.ndarray, ref: float = 1.0) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        db = 10.0 * np.log10(np.maximum(psd, 1e-30) / ref)
    return db
