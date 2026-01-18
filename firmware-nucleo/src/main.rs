#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_stm32::gpio::{Level, Output, Speed, Pull, Input};
use embassy_stm32::time::Hertz;
use embassy_stm32::usart::{Config as UartConfig, Uart};
use embassy_stm32::Config;
use embassy_time::{Duration, Timer};
use defmt::*;
use {defmt_rtt as _, panic_probe as _};

// Motor control
#[derive(Clone, Copy, Debug, defmt::Format)]
pub enum Direction {
    Forward,
    Backward,
    Left,
    Right,
    Stop,
}

pub struct Motors<'d> {
    // Using Nucleo Arduino pins
    // D8 (PA9) -> Left Motor PWM
    // D9 (PC7) -> Left Motor Dir
    // D10 (PB6) -> Right Motor PWM  
    // D11 (PA7) -> Right Motor Dir
    left_pwm: Output<'d>,
    left_dir: Output<'d>,
    right_pwm: Output<'d>,
    right_dir: Output<'d>,
}

impl<'d> Motors<'d> {
    pub fn drive(&mut self, dir: Direction) {
        info!("Drive: {:?}", dir);
        match dir {
            Direction::Forward => {
                self.left_dir.set_high();
                self.right_dir.set_high();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            Direction::Backward => {
                self.left_dir.set_low();
                self.right_dir.set_low();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            Direction::Left => {
                self.left_dir.set_low();
                self.right_dir.set_high();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            Direction::Right => {
                self.left_dir.set_high();
                self.right_dir.set_low();
                self.left_pwm.set_high();
                self.right_pwm.set_high();
            }
            Direction::Stop => {
                self.left_pwm.set_low();
                self.right_pwm.set_low();
            }
        }
    }
}

#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    info!("Shark Controller - Nucleo F446RE");
    
    let mut config = Config::default();
    {
        use embassy_stm32::rcc::*;
        config.rcc.hse = Some(Hse {
            freq: Hertz(8_000_000),
            mode: HseMode::Bypass, // Nucleo uses ST-Link clock
        });
        config.rcc.pll_src = PllSource::HSE;
        config.rcc.pll = Some(Pll {
            prediv: PllPreDiv::DIV4,
            mul: PllMul::MUL180,
            divp: Some(PllPDiv::DIV2), // 180MHz
            divq: Some(PllQDiv::DIV8),
            divr: None,
        });
        config.rcc.sys = Sysclk::PLL1_P;
        config.rcc.ahb_pre = AHBPrescaler::DIV1;
        config.rcc.apb1_pre = APBPrescaler::DIV4;
        config.rcc.apb2_pre = APBPrescaler::DIV2;
    }
    
    let p = embassy_stm32::init(config);
    
    // Nucleo LED (PA5 = LD2)
    let mut led = Output::new(p.PA5, Level::Low, Speed::Low);
    
    // User button (PC13)
    let button = Input::new(p.PC13, Pull::None);
    
    // Motor outputs on Arduino header pins
    let mut motors = Motors {
        left_pwm: Output::new(p.PA9, Level::Low, Speed::High),   // D8
        left_dir: Output::new(p.PC7, Level::Low, Speed::High),   // D9
        right_pwm: Output::new(p.PB6, Level::Low, Speed::High),  // D10
        right_dir: Output::new(p.PA7, Level::Low, Speed::High),  // D11
    };
    
    info!("Ready! Press button to test motors");
    
    // Blink to show ready
    for _ in 0..3 {
        led.set_high();
        Timer::after(Duration::from_millis(100)).await;
        led.set_low();
        Timer::after(Duration::from_millis(100)).await;
    }
    
    loop {
        // Wait for button press
        if button.is_low() {
            info!("Button pressed - running test");
            led.set_high();
            
            // Forward 1s
            motors.drive(Direction::Forward);
            Timer::after(Duration::from_secs(1)).await;
            
            // Stop
            motors.drive(Direction::Stop);
            Timer::after(Duration::from_millis(300)).await;
            
            // Left turn
            motors.drive(Direction::Left);
            Timer::after(Duration::from_millis(500)).await;
            
            // Stop
            motors.drive(Direction::Stop);
            Timer::after(Duration::from_millis(300)).await;
            
            // Right turn
            motors.drive(Direction::Right);
            Timer::after(Duration::from_millis(500)).await;
            
            // Stop
            motors.drive(Direction::Stop);
            
            led.set_low();
            info!("Test complete");
            
            // Debounce
            Timer::after(Duration::from_millis(500)).await;
        }
        
        Timer::after(Duration::from_millis(10)).await;
    }
}
