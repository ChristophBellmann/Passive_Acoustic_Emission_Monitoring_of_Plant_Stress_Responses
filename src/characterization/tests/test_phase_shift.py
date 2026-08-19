"""Tests for CH3/CH4 phase-delay analysis."""

from __future__ import annotations

import numpy as np

from plant_ae.phase_shift import cross_spectral_phase_candidates, gcc_phat_delay


def test_gcc_phat_detects_positive_integer_sample_delay() -> None:
    sample_rate = 500_000.0
    delay_samples = 12
    rng = np.random.default_rng(42)
    reference = rng.normal(size=16_384)
    delayed = np.concatenate([np.zeros(delay_samples), reference[:-delay_samples]])

    estimate = gcc_phat_delay(
        reference,
        delayed,
        sample_rate,
        max_delay_s=200e-6,
        interpolation=4,
    )

    assert abs(estimate.delay_s - delay_samples / sample_rate) <= 0.5 / sample_rate
    assert estimate.confidence > 10


def test_cross_spectral_phase_candidates_find_known_delay() -> None:
    sample_rate = 500_000.0
    delay_samples = 8
    rng = np.random.default_rng(7)
    reference = rng.normal(size=65_536)
    delayed = np.concatenate([np.zeros(delay_samples), reference[:-delay_samples]])

    _, _, _, candidates = cross_spectral_phase_candidates(
        reference,
        delayed,
        sample_rate,
        min_frequency_hz=2_000,
        max_frequency_hz=80_000,
        nperseg=8192,
        coherence_threshold=0.8,
        min_bandwidth_hz=5_000,
        max_abs_delay_s=200e-6,
    )

    assert candidates
    assert abs(candidates[0].delay_s - delay_samples / sample_rate) < 2e-6
    assert candidates[0].mean_coherence > 0.8
