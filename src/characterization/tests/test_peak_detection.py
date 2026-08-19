"""Tests for peak detection."""

import numpy as np
import pytest

from scope.peak_detection import assess_repeatability, detect_peaks_in_welch
from scope.spectral import WelchResult, compute_welch


def test_detect_peaks_in_synthetic_welch():
    freqs = np.linspace(0, 5000, 5001)
    psd = np.ones_like(freqs) * 1e-10
    for f in [100, 500, 1200]:
        idx = int(f)
        width = 5
        lo = max(0, idx - width)
        hi = min(len(psd), idx + width + 1)
        psd[lo:hi] += 1e-4 * np.exp(-0.5 * ((freqs[lo:hi] - f) / 2) ** 2)
    welch = WelchResult(frequencies=freqs, psd=psd)
    peaks = detect_peaks_in_welch(
        welch,
        prominence_db=3.0,
        min_distance_hz=20,
        max_peaks=10,
        ignore_bands_hz=[[48, 52]],
    )
    peak_freqs = sorted([p.frequency_hz for p in peaks])
    assert any(abs(f - 100) < 10 for f in peak_freqs)
    assert any(abs(f - 500) < 10 for f in peak_freqs)
    assert any(abs(f - 1200) < 10 for f in peak_freqs)


def test_detect_peaks_ignores_mains_band():
    freqs = np.linspace(0, 500, 501)
    psd = np.ones_like(freqs) * 1e-10
    idx_50 = 50
    psd[idx_50 - 2:idx_50 + 3] = 1e-3
    welch = WelchResult(frequencies=freqs, psd=psd)
    peaks = detect_peaks_in_welch(
        welch,
        prominence_db=3.0,
        min_distance_hz=5,
        ignore_bands_hz=[[48, 52]],
    )
    for p in peaks:
        assert not (48 <= p.frequency_hz <= 52)


def test_assess_repeatability():
    from scope.peak_detection import SpectralPeak

    capture1 = [SpectralPeak(frequency_hz=100.0, amplitude=1.0, amplitude_db=0.0, prominence_db=10.0)]
    capture2 = [SpectralPeak(frequency_hz=101.0, amplitude=1.0, amplitude_db=0.0, prominence_db=10.0)]
    capture3 = [SpectralPeak(frequency_hz=100.5, amplitude=1.0, amplitude_db=0.0, prominence_db=10.0)]
    rep = assess_repeatability([capture1, capture2, capture3], freq_tolerance_hz=5.0, min_fraction=0.4)
    assert len(rep) >= 1
    assert any(rep.values())


def test_detect_peaks_empty():
    welch = WelchResult(frequencies=np.array([]), psd=np.array([]))
    peaks = detect_peaks_in_welch(welch)
    assert peaks == []
