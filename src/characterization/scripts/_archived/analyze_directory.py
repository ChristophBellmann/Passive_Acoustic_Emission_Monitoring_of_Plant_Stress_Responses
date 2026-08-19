"""Analyze a directory of previously acquired captures."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "instrument_control"))


def main():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "configs/experiment_piezo_stainless.yaml"
    input_dir = sys.argv[2] if len(sys.argv) > 2 else "data/raw"
    from scope.cli import app
    import typer
    typer.main.get_command(app)(["analyze", "--config", config_path, "--input", input_dir])


if __name__ == "__main__":
    main()
