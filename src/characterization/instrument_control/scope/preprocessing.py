"""Signal preprocessing functions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import signal as sp_signal


@dataclass
class PreprocessingResult:
    time_vector: np.ndarray
    voltage: np.ndarray
    dc_removed: bool
    detrended: bool
    is_clipped: bool
    is_flatline: bool
    has_nan_or_inf: bool
    clipping_fraction: float


def remove_dc(voltage: np.ndarray) -> np.ndarray:
    return voltage - np.nanmean(voltage)


def detrend_signal(voltage: np.ndarray, method: str = "linear") -> np.ndarray:
    return sp_signal.detrend(voltage, type=method)


def detect_clipping(
    voltage: np.ndarray, threshold_fraction: float = 0.98
) -> tuple[bool, float]:
    if len(voltage) == 0:
        return False, 0.0
    vmin, vmax = np.nanmin(voltage), np.nanmax(voltage)
    rng = vmax - vmin
    if rng == 0:
        return True, 1.0
    near_max = np.sum(voltage >= vmax - rng * (1 - threshold_fraction))
    near_min = np.sum(voltage <= vmin + rng * (1 - threshold_fraction))
    clipped_count = near_max + near_min
    fraction = clipped_count / len(voltage)
    return fraction > 0.01, fraction


def detect_flatline(voltage: np.ndarray, tol: float = 1e-12) -> bool:
    if len(voltage) < 2:
        return True
    return np.nanmax(np.abs(np.diff(voltage))) < tol


def check_nan_inf(voltage: np.ndarray) -> bool:
    return bool(np.any(np.isnan(voltage)) or np.any(np.isinf(voltage)))


def apply_window(voltage: np.ndarray, window: str = "hann") -> np.ndarray:
    n = len(voltage)
    if n == 0:
        return voltage
    win = sp_signal.get_window(window, n)
    return voltage * win


def preprocess(
    time_vector: np.ndarray,
    voltage: np.ndarray,
    remove_dc_flag: bool = True,
    detrend_flag: bool = True,
    window: str = "hann",
    clipping_threshold: float = 0.98,
) -> PreprocessingResult:
    v = voltage.copy().astype(np.float64)
    has_nan_inf = check_nan_inf(v)
    if has_nan_inf:
        v = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)

    dc_removed = False
    if remove_dc_flag:
        v = remove_dc(v)
        dc_removed = True

    detrended = False
    if detrend_flag:
        v = detrend_signal(v)
        detrended = True

    is_clipped, clip_frac = detect_clipping(v, clipping_threshold)
    is_flat = detect_flatline(v)

    v_windowed = apply_window(v, window)

    return PreprocessingResult(
        time_vector=time_vector.copy(),
        voltage=v_windowed,
        dc_removed=dc_removed,
        detrended=detrended,
        is_clipped=is_clipped,
        is_flatline=is_flat,
        has_nan_or_inf=has_nan_inf,
        clipping_fraction=clip_frac,
    )
