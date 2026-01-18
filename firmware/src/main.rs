#![no_std]
#![no_main]

use core::mem::MaybeUninit;
use embassy_executor::Spawner;
use embassy_stm32::gpio::{Level, Output, Speed};
use embassy_stm32::time::Hertz;
use embassy_stm32::{Config, SharedData};
use embassy_time::{Duration, Timer};
use defmt::*;
use static_cell::StaticCell;
use {defmt_rtt as _, panic_probe as _};

// Motor control commands
#[derive(Clone, Copy, Debug, defmt::Format)]
pub enum DriveCommand {
    Forward(u8),
    Backward(u8),
    Left(u8),
    Right(u8),
    Stop,
}

// Motor controller
pub struct Motors<'d> {
    left_pwm: Output<'d>,
    left_dir: Output<'d>,
    right_pwm: Output<'d>,
    right_dir: Output<'d>,
}

impl<'d> Motors<'d> {
    pub fn drive(&mut self, cmd: DriveCommand) {
        match cmd {
            DriveCommand::Forward(_speed) => {
                self.left_dir.set_high();
                self.right_dir.set_high();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            DriveCommand::Backward(_speed) => {
                self.left_dir.set_low();
                self.right_dir.set_low();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            DriveCommand::Left(_speed) => {
                self.left_dir.set_low();
                self.right_dir.set_high();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            DriveCommand::Right(_speed) => {
                self.left_dir.set_high();
                self.right_dir.set_low();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            DriveCommand::Stop => {
                self.left_pwm.set_low();
                self.right_pwm.set_low();
            }
        }
    }
}

// Shared data between cores - placed in shared RAM
static SHARED: StaticCell<MaybeUninit<SharedData>> = StaticCell::new();

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    info!("Shark Robot Controller v0.1");
    
    let mut config = Config::default();
    {
        use embassy_stm32::rcc::*;
        config.rcc.hse = Some(Hse {
            freq: Hertz(25_000_000),
            mode: HseMode::Oscillator,
        });
        config.rcc.pll1 = Some(Pll {
            source: PllSource::HSE,
            prediv: PllPreDiv::DIV5,
            mul: PllMul::MUL192,
            divp: Some(PllDiv::DIV2),
            divq: Some(PllDiv::DIV4),
            divr: None,
        });
        config.rcc.sys = Sysclk::PLL1_P;
        config.rcc.ahb_pre = AHBPrescaler::DIV2;
        config.rcc.apb1_pre = APBPrescaler::DIV2;
        config.rcc.apb2_pre = APBPrescaler::DIV2;
        config.rcc.apb3_pre = APBPrescaler::DIV2;
        config.rcc.apb4_pre = APBPrescaler::DIV2;
    }
    
    // Initialize shared data and get peripherals (dual-core H747)
    let shared = SHARED.init(MaybeUninit::uninit());
    let p = embassy_stm32::init_primary(config, shared);
    
    // Status LED (Portenta built-in RGB on PK5/6/7)
    let mut led_r = Output::new(p.PK5, Level::High, Speed::Low);
    let mut led_g = Output::new(p.PK6, Level::High, Speed::Low);
    let mut _led_b = Output::new(p.PK7, Level::High, Speed::Low);
    
    // Motor outputs - wire to Shark motor driver
    let mut motors = Motors {
        left_pwm: Output::new(p.PA0, Level::Low, Speed::High),
        left_dir: Output::new(p.PA1, Level::Low, Speed::High),
        right_pwm: Output::new(p.PA2, Level::Low, Speed::High),
        right_dir: Output::new(p.PA3, Level::Low, Speed::High),
    };
    
    info!("Motors initialized");
    led_g.set_low(); // Green = ready
    
    // Test sequence
    info!("Running motor test...");
    
    motors.drive(DriveCommand::Forward(50));
    Timer::after(Duration::from_secs(1)).await;
    motors.drive(DriveCommand::Stop);
    Timer::after(Duration::from_millis(500)).await;
    
    motors.drive(DriveCommand::Left(50));
    Timer::after(Duration::from_secs(1)).await;
    motors.drive(DriveCommand::Stop);
    Timer::after(Duration::from_millis(500)).await;
    
    motors.drive(DriveCommand::Right(50));
    Timer::after(Duration::from_secs(1)).await;
    motors.drive(DriveCommand::Stop);
    
    info!("Motor test complete");
    
    // Heartbeat
    loop {
        led_r.set_low();
        Timer::after(Duration::from_millis(100)).await;
        led_r.set_high();
        Timer::after(Duration::from_millis(900)).await;
    }
}
