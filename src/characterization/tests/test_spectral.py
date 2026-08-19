"""Tests for spectral analysis functions."""

import numpy as np
import pytest

from scope.spectral import (
    FFTResult,
    WelchResult,
    amplitude_to_db,
    compute_fft,
    compute_stft,
    compute_welch,
    psd_to_db,
)


def test_compute_fft_sine_wave():
    fs = 10000.0
    t = np.arange(0, 1.0, 1.0 / fs)
    freq = 440.0
    signal = np.sin(2 * np.pi * freq * t)
    result = compute_fft(signal, fs)
    peak_idx = np.argmax(result.amplitude[1:]) + 1
    peak_freq = result.frequencies[peak_idx]
    assert abs(peak_freq - freq) < 2.0


def test_compute_fft_empty():
    result = compute_fft(np.array([]), 1000.0)
    assert len(result.frequencies) == 0


def test_compute_welch_sine_wave():
    fs = 10000.0
    t = np.arange(0, 2.0, 1.0 / fs)
    freq = 1000.0
    signal = np.sin(2 * np.pi * freq * t)
    result = compute_welch(signal, fs, nperseg=2048)
    peak_idx = np.argmax(result.psd[1:]) + 1
    peak_freq = result.frequencies[peak_idx]
    assert abs(peak_freq - freq) < 10.0


def test_compute_stft_shape():
    fs = 8000.0
    signal = np.random.randn(8000)
    result = compute_stft(signal, fs, nperseg=512, overlap=0.5)
    assert result.magnitude.ndim == 2
    assert len(result.frequencies) == result.magnitude.shape[0]
    assert len(result.times) == result.magnitude.shape[1]


def test_amplitude_to_db():
    amp = np.array([1.0, 0.1, 0.01])
    db = amplitude_to_db(amp)
    np.testing.assert_allclose(db, [0.0, -20.0, -40.0], atol=0.01)


def test_psd_to_db():
    psd = np.array([1.0, 0.1, 0.01])
    db = psd_to_db(psd)
    np.testing.assert_allclose(db, [0.0, -10.0, -20.0], atol=0.01)
