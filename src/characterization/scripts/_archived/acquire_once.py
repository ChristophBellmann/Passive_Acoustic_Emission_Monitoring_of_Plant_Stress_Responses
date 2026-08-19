"""Acquire a single capture from the oscilloscope."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument_control"))

from scope.acquisition import acquire_single_capture, save_capture_csv, save_capture_npz
from scope.config import load_config
from scope.instrument import InstrumentConnection
from scope.utils import ensure_output_dirs


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/experiment_piezo_stainless.yaml"
    cfg = load_config(config_path)
    base_dir = Path(config_path).parent
    dirs = ensure_output_dirs(base_dir)

    with InstrumentConnection(cfg) as conn:
        for ch in cfg.oscilloscope.channels:
            cap = acquire_single_capture(conn, ch, cfg)
            npz_path = save_capture_npz(cap, dirs["raw"])
            csv_path = save_capture_csv(cap, dirs["raw"])
            print(f"CH{ch}: saved {npz_path}")
            print(f"CH{ch}: saved {csv_path}")


if __name__ == "__main__":
    main()
