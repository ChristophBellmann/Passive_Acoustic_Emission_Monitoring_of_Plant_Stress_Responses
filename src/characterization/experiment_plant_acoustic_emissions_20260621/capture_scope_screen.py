"""
Capture oscilloscope screen as PNG image.

Usage:
    python experiment_plant_acoustic_emissions_20260621/capture_scope_screen.py
"""

from __future__ import annotations

import sys
from pathlib import Path
import time

import numpy as np

# Add project src to path
PROJECT_SRC = Path(__file__).resolve().parent.parent / "instrument_control"
if PROJECT_SRC.exists():
    sys.path.insert(0, str(PROJECT_SRC))

from scope.config import load_config
from scope.instrument import InstrumentConnection


def capture_screen(conn: InstrumentConnection, output_path: Path) -> bool:
    """Capture oscilloscope screen as PNG."""
    try:
        # Rigol DS1104Z supports screen capture via SCPI
        # Command: :DISP:DATA? PNG
        # Returns binary PNG data
        
        conn.write(":DISP:DATA? PNG")
        
        # Read binary data with timeout
        raw_data = conn._inst.read_raw()
        
        # Parse IEEE 488.2 binary block header
        # Format: #<n><length><data>
        # where <n> is the number of digits in <length>
        if len(raw_data) > 0 and raw_data[0] == ord('#'):
            n_digits = int(raw_data[1:2])
            data_length = int(raw_data[2:2+n_digits])
            png_data = raw_data[2+n_digits:2+n_digits+data_length]
        else:
            # Fallback: assume entire response is PNG
            png_data = raw_data
        
        if len(png_data) == 0:
            print(f"Warning: No data received")
            return False
        
        # Save PNG
        with open(output_path, 'wb') as f:
            f.write(png_data)
        
        print(f"Screen captured: {output_path} ({len(png_data)} bytes)")
        return True
        
    except Exception as e:
        print(f"Error capturing screen: {e}")
        return False


def main() -> None:
    """Main function."""
    config_path = Path(__file__).resolve().parent / "config.yaml"
    config = load_config(config_path)
    
    output_dir = Path(__file__).resolve().parent / "screenshots"
    output_dir.mkdir(exist_ok=True)
    
    print("Connecting to oscilloscope...")
    
    try:
        with InstrumentConnection(config) as conn:
            idn = conn.query("*IDN?")
            print(f"Connected: {idn}")
            
            # Capture multiple screenshots
            for i in range(3):
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_path = output_dir / f"scope_screen_{i+1}_{timestamp}.png"
                
                print(f"\nCapturing screenshot {i+1}/3...")
                success = capture_screen(conn, output_path)
                
                if not success:
                    print(f"Failed to capture screenshot {i+1}")
                
                if i < 2:
                    time.sleep(1)
        
        print(f"\nScreenshots saved to: {output_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
