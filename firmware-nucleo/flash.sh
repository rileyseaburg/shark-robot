#!/bin/bash
# Flash Nucleo F446RE via ST-Link

set -e

echo "Building..."
cargo build --release

echo "Flashing to Nucleo F446RE..."
probe-rs run --chip STM32F446RETx target/thumbv7em-none-eabihf/release/shark-nucleo

echo "Done! Check RTT output for logs."
