#![no_std]
#![no_main]

use cortex_m_rt::entry;
use embedded_hal::digital::OutputPin;
use panic_halt as _;
use rp_pico::hal::{
    clocks::{init_clocks_and_plls, Clock},
    gpio::{FunctionPio0, Pins},
    pac,
    pio::{PIOBuilder, PIOExt},
    sio::Sio,
    timer::Timer,
    watchdog::Watchdog,
};

const XOSC_CRYSTAL_HZ: u32 = 12_000_000;

const F_START_HZ: u32 = 20;
const F_STOP_HZ: u32 = 100_000;
const SWEEP_US: u32 = 30_000_000; // 30s sweep → 1.5s/Band, genug für VISA-Transfer
const UPDATE_US: u32 = 100; // 10000 target updates/s
const MARKER_STEP_HZ: u32 = 5_000;
const MARKER_PULSE_US: u64 = 500;

fn frequency_for_elapsed_us(elapsed_us: u32) -> u32 {
    if elapsed_us >= SWEEP_US {
        return F_STOP_HZ;
    }

    let span_hz = F_STOP_HZ - F_START_HZ;
    F_START_HZ + (((span_hz as u64 * elapsed_us as u64) + (SWEEP_US / 2) as u64)
        / SWEEP_US as u64) as u32
}

fn pio_delay_count(clock_hz: u32, freq_hz: u32) -> u32 {
    let freq_hz = freq_hz.clamp(F_START_HZ, F_STOP_HZ);
    let period_cycles = clock_hz as u64 / freq_hz as u64;

    // The PIO loop costs 7 cycles per full output period outside the two
    // delay loops. Subtract that so high frequencies stay close to target.
    period_cycles
        .saturating_sub(7)
        .checked_div(2)
        .unwrap_or(1)
        .max(1)
        .min(u32::MAX as u64) as u32
}

#[entry]
fn main() -> ! {
    let mut pac = pac::Peripherals::take().unwrap();
    let mut watchdog = Watchdog::new(pac.WATCHDOG);

    let clocks = init_clocks_and_plls(
        XOSC_CRYSTAL_HZ,
        pac.XOSC,
        pac.CLOCKS,
        pac.PLL_SYS,
        pac.PLL_USB,
        &mut pac.RESETS,
        &mut watchdog,
    )
    .ok()
    .unwrap();

    let sio = Sio::new(pac.SIO);
    let pins = Pins::new(
        pac.IO_BANK0,
        pac.PADS_BANK0,
        sio.gpio_bank0,
        &mut pac.RESETS,
    );

    let drive = pins.gpio15.into_function::<FunctionPio0>();
    let drive_pin_id = drive.id().num;
    let mut trigger = pins.gpio14.into_push_pull_output();
    let mut led = pins.gpio25.into_push_pull_output();
    let timer = Timer::new(pac.TIMER, &mut pac.RESETS, &clocks);

    let program = pio_proc::pio_asm!(
        "pull block",
        "mov x, osr",
        ".wrap_target",
        "mov y, x",
        "set pins, 1",
        "high:",
        "jmp y-- high",
        "mov y, x",
        "set pins, 0",
        "low:",
        "jmp y-- low",
        "pull noblock",
        "mov x, osr",
        ".wrap",
    );

    let (mut pio, sm0, _, _, _) = pac.PIO0.split(&mut pac.RESETS);
    let installed = pio.install(&program.program).unwrap();
    let (mut sm, _rx, mut tx) = PIOBuilder::from_installed_program(installed)
        .set_pins(drive_pin_id, 1)
        .clock_divisor_fixed_point(1, 0)
        .build(sm0);
    sm.set_pindirs([(drive_pin_id, rp_pico::hal::pio::PinDir::Output)]);

    let clock_hz = clocks.system_clock.freq().to_Hz();
    while !tx.write(pio_delay_count(clock_hz, F_START_HZ)) {}
    let mut sm = sm.start();

    loop {
        let _ = led.set_high();
        let _ = trigger.set_low();
        let start = timer.get_counter().ticks();
        let mut next_marker_hz = MARKER_STEP_HZ;
        let mut trigger_until = 0u64; // kein Start-of-Loop-Trigger → genau 20 Marker/Sweep

        let mut elapsed = 0;
        while elapsed <= SWEEP_US {
            let now = timer.get_counter().ticks();
            if trigger_until != 0 && now >= trigger_until {
                let _ = trigger.set_low();
                trigger_until = 0;
            }

            let freq = frequency_for_elapsed_us(elapsed);
            if freq >= next_marker_hz {
                let _ = trigger.set_high();
                trigger_until = now + MARKER_PULSE_US;
                next_marker_hz += MARKER_STEP_HZ;
            }

            sm.drain_tx_fifo();
            let _ = tx.write(pio_delay_count(clock_hz, freq));

            let target = start + elapsed as u64 + UPDATE_US as u64;
            while timer.get_counter().ticks() < target {
                cortex_m::asm::nop();
            }

            elapsed += UPDATE_US;
        }

        let _ = led.set_low();
        let _ = trigger.set_low();
    }
}
