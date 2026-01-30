#!/usr/bin/env python3
"""
Test script for robot control - bypasses MCP for direct testing
"""

import httpx
import asyncio
import sys

ROBOT_IP = "192.168.50.100"  # Update with actual Portenta IP
ROBOT_PORT = 8080


async def send_command(endpoint: str, data: dict = None):
    url = f"http://{ROBOT_IP}:{ROBOT_PORT}/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            if data:
                resp = await client.post(url, json=data)
            else:
                resp = await client.get(url)
            print(f"{endpoint}: {resp.json()}")
            return resp.json()
    except Exception as e:
        print(f"Error: {e}")
        return None


async def main():
    print(f"Testing robot at {ROBOT_IP}:{ROBOT_PORT}")
    print("=" * 40)

    # Test status
    print("\n1. Getting status...")
    await send_command("status")

    # Test sensors
    print("\n2. Reading sensors...")
    await send_command("sensors")

    # Test movement
    print("\n3. Moving forward for 1 second...")
    await send_command("drive", {"left": 30, "right": 30, "duration": 1000})
    await asyncio.sleep(1.5)

    print("\n4. Turning left...")
    await send_command("drive", {"left": -30, "right": 30, "duration": 500})
    await asyncio.sleep(1)

    print("\n5. Stopping...")
    await send_command("stop")

    print("\n6. Testing vacuum (50% power for 2 sec)...")
    await send_command("vacuum", {"power": 50})
    await asyncio.sleep(2)
    await send_command("vacuum", {"power": 0})

    print("\nTest complete!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        ROBOT_IP = sys.argv[1]
    asyncio.run(main())
