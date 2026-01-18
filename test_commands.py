import asyncio
import os
from sharkiq import get_ayla_api
from dotenv import load_dotenv

load_dotenv()

async def test_commands():
    api = get_ayla_api(os.getenv("SHARK_EMAIL"), os.getenv("SHARK_PASSWORD"))
    await api.async_sign_in()
    
    vacuums = await api.async_get_devices()
    vac = vacuums[0]
    await vac.async_update()
    
    # Get all settable properties
    print("=== SETTABLE PROPERTIES ===")
    for prop in sorted(vac._settable_properties or []):
        print(f"  {prop}")
    
    # Check current Exec values
    print("\n=== EXEC PROPERTIES ===")
    print(f"Exec_Command: {vac.property_values.get('Exec_Command')}")
    print(f"Exec_Response: {vac.property_values.get('Exec_Response')}")
    
    # Check for any movement-related properties
    print("\n=== POTENTIAL MOVEMENT PROPERTIES ===")
    for key, val in vac.property_values.items():
        if any(x in key.lower() for x in ['move', 'drive', 'motor', 'wheel', 'direction', 'speed', 'nav', 'control']):
            print(f"  {key}: {val}")

asyncio.run(test_commands())
