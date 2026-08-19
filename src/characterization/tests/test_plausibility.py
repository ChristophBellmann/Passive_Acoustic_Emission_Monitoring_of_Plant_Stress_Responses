"""Tests for plausibility checks."""

import numpy as np
import pytest

from scope.config import ExperimentConfig
from scope.peak_detection import SpectralPeak
from scope.plausibility import run_plausibility_checks
from scope.preprocessing import PreprocessingResult


def _make_preprocessing_result(is_clipped=False, is_flatline=False):
    return PreprocessingResult(
        time_vector=np.array([0.0, 0.001]),
        voltage=np.array([0.0, 0.0]),
        dc_removed=True,
        detrended=True,
        is_clipped=is_clipped,
        is_flatline=is_flatline,
        has_nan_or_inf=False,
        clipping_fraction=0.0,
    )


def test_mains_noise_label():
    peak = SpectralPeak(
        frequency_hz=50.0,
        amplitude=1.0,
        amplitude_db=0.0,
        prominence_db=10.0,
        is_mains_related=True,
        channel=1,
    )
    pre = _make_preprocessing_result()
    cfg = ExperimentConfig()
    results = run_plausibility_checks([peak], {1: pre}, 10000.0, cfg)
    assert results[0].label == "likely_mains_noise"


def test_flatline_label():
    peak = SpectralPeak(
        frequency_hz=200.0,
        amplitude=1.0,
        amplitude_db=0.0,
        prominence_db=10.0,
        channel=1,
    )
    pre = _make_preprocessing_result(is_flatline=True)
    cfg = ExperimentConfig()
    results = run_plausibility_checks([peak], {1: pre}, 10000.0, cfg)
    assert results[0].label == "likely_clipping_artifact"


def test_mechanical_both_channels():
    peak_ch1 = SpectralPeak(
        frequency_hz=500.0,
        amplitude=1.0,
        amplitude_db=0.0,
        prominence_db=10.0,
        is_repeatable=True,
        snr_db=20.0,
        channel=1,
    )
    peak_ch2 = SpectralPeak(
        frequency_hz=502.0,
        amplitude=1.0,
        amplitude_db=0.0,
        prominence_db=10.0,
        is_repeatable=True,
        snr_db=20.0,
        channel=2,
    )
    pre1 = _make_preprocessing_result()
    pre2 = _make_preprocessing_result()
    cfg = ExperimentConfig()
    channel_peaks = {1: [peak_ch1], 2: [peak_ch2]}
    results = run_plausibility_checks(
        [peak_ch1], {1: pre1}, 10000.0, cfg, channel_peaks
    )
    assert results[0].label == "plausible_mechanical"
