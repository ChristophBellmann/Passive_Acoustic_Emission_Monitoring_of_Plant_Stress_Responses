"""Acquire a series of captures from the oscilloscope."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument_control"))

from scope.acquisition import acquire_series, save_capture_csv, save_capture_npz
from scope.config import load_config
from scope.instrument import InstrumentConnection
from scope.utils import ensure_output_dirs


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/experiment_piezo_stainless.yaml"
    cfg = load_config(config_path)
    base_dir = Path(config_path).parent
    dirs = ensure_output_dirs(base_dir)

    with InstrumentConnection(cfg) as conn:
        captures = acquire_series(conn, cfg)
        for cap in captures:
            save_capture_npz(cap, dirs["raw"])
            if cfg.output.save_raw_csv:
                save_capture_csv(cap, dirs["raw"])
        print(f"Acquired {len(captures)} captures -> {dirs['raw']}")


if __name__ == "__main__":
    main()
