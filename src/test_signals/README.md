# Test Signals

Hardware test signal generation for sensor/amplifier characterization.

## Platform: Raspberry Pi Pico (RP2040, Rust + PIO)

Use `pico_rust_sweep/` for the hardware sweep. PIO0 generates the GP15 square
wave in hardware. Rust updates the PIO delay target at 10 kHz.

Sweep: 20 Hz -> 100 kHz, linear, 5 s per sweep.
GP14 emits a 500 us trigger pulse at sweep start and every 5 kHz.

```bash
rustup target add thumbv6m-none-eabi
cargo install elf2uf2-rs

cd pico_rust_sweep
cargo build --release
elf2uf2-rs target/thumbv6m-none-eabi/release/pico_rust_sweep \
  target/thumbv6m-none-eabi/release/pico_rust_sweep.uf2
cp target/thumbv6m-none-eabi/release/pico_rust_sweep.uf2 /media/$USER/RPI-RP2/
```

### Legacy MicroPython Setup

1. Hold BOOTSEL, plug in USB → Pico mounts as `RPI-RP2`
2. Flash MicroPython firmware:
   ```bash
   wget -O /tmp/mp.uf2 https://micropython.org/download/RPI_PICO/RPI_PICO-latest.uf2
   cp /tmp/mp.uf2 /media/$USER/RPI-RP2/
   ```
3. Upload scripts:
   ```bash
   cd pico/
   ./flash.sh          # uses .venv/bin/mpremote
   ```

### Scripts

| File | Purpose |
|------|---------|
| `pico_rust_sweep/src/main.rs` | Rust/PIO linear sweep 20 Hz -> 100 kHz on GP15, 5 s/sweep, 10k target updates/s, GP14 5 kHz markers |
| `pico/main.py` (= `freq_sweep.py`) | Legacy MicroPython sweep |
| `pico/boot.py` | Runs before main.py; hardware init placeholder |
| `pico/flash.sh` | Uploads boot.py + main.py via mpremote |

### Wiring (acoustic signal-chain measurement)

```
Pico GP14 (Pin 19) ───────────── Rigol CH1 trigger/marker input
Pico GP15 (Pin 20) ── 100 ohm ── Piezo (+)
Pico GND  (Pin 23) ───────────── Piezo (-)
LM358 sensor CH3   ─────────── Rigol CH3  (steel + LM358 + 830k, acoustic response)
LM358 sensor CH4   ─────────── Rigol CH4  (steel + LM358 + 830k, acoustic response)

Optional, if available:
Pico GP15 after 100 ohm ─────── Rigol CH2/other spare channel (drive reference)
```


### Monitor sweep output

```bash
.venv/bin/mpremote connect /dev/ttyACM0 repl
```

### LM358 module

- Circuit: `LM358-Amplifier-module-circuit.png`
