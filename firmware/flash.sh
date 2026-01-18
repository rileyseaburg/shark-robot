#!/bin/bash
# Flash script for Portenta H7 Lite

set -e

echo "Building firmware..."
cargo build --release

echo "Flashing to Portenta H7..."
probe-rs run --chip STM32H747XIHx target/thumbv7em-none-eabihf/release/shark-controller

echo "Done!"
