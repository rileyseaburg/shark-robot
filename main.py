import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sharkiq import get_ayla_api, OperatingModes, PowerModes
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()

_SHARK_API = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _SHARK_API
    email = os.getenv("SHARK_EMAIL")
    password = os.getenv("SHARK_PASSWORD")

    if email and password:
        _SHARK_API = get_ayla_api(email, password)
        await _SHARK_API.async_sign_in()
        print(f"Connected to Shark API: {email}")
    else:
        print("SHARK_EMAIL and SHARK_PASSWORD not set - login required")

    yield

    if _SHARK_API:
        try:
            await _SHARK_API.async_sign_out()
        except:
            pass


app = FastAPI(title="Shark Robot Control API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def get_vacuum():
    if not _SHARK_API:
        raise HTTPException(
            status_code=503,
            detail="Not authenticated. Set SHARK_EMAIL and SHARK_PASSWORD in .env",
        )

    vacuums = await _SHARK_API.async_get_devices()
    if not vacuums:
        raise HTTPException(status_code=404, detail="No Shark vacuums found")

    vac = vacuums[0]
    await vac.async_update()
    return vac


# === BASIC ENDPOINTS ===


@app.get("/")
async def root():
    return {"status": "online", "authenticated": _SHARK_API is not None}


@app.get("/status")
async def get_status():
    vac = await get_vacuum()
    return {
        "name": vac.name,
        "model": vac.property_values.get("Device_Model_Number", "").strip(),
        "serial": vac.property_values.get("Device_Serial_Num", "").strip(),
        "battery": vac.property_values.get("Battery_Capacity"),
        "charging": vac.property_values.get("Charging_Status"),
        "docked": vac.property_values.get("DockedStatus"),
        "error_code": vac.error_code,
        "error_text": vac.error_text,
        "rssi": vac.property_values.get("RSSI"),
    }


@app.get("/status/full")
async def get_full_status():
    vac = await get_vacuum()
    return {
        "name": vac.name,
        "properties": dict(vac.property_values),
    }


# === CLEANING CONTROL ===


@app.post("/start")
async def start_cleaning():
    vac = await get_vacuum()
    await vac.async_set_operating_mode(OperatingModes.START)
    return {"status": "started"}


@app.post("/stop")
async def stop_cleaning():
    vac = await get_vacuum()
    await vac.async_set_operating_mode(OperatingModes.STOP)
    return {"status": "stopped"}


@app.post("/pause")
async def pause_cleaning():
    vac = await get_vacuum()
    await vac.async_set_operating_mode(OperatingModes.PAUSE)
    return {"status": "paused"}


@app.post("/dock")
async def dock_robot():
    vac = await get_vacuum()
    await vac.async_set_operating_mode(OperatingModes.RETURN)
    return {"status": "returning_to_dock"}


@app.post("/explore")
async def explore_mode():
    """Start explore/mapping mode"""
    vac = await get_vacuum()
    await vac.async_set_operating_mode(OperatingModes.EXPLORE)
    return {"status": "exploring"}


# === DEVICE CONTROL ===


@app.post("/find")
async def find_robot():
    vac = await get_vacuum()
    await vac.async_find_device()
    return {"status": "chirping"}


@app.post("/power/{mode}")
async def set_power(mode: str):
    power_map = {
        "eco": PowerModes.ECO,
        "normal": PowerModes.NORMAL,
        "max": PowerModes.MAX,
    }
    if mode.lower() not in power_map:
        raise HTTPException(
            status_code=400, detail="Invalid mode. Use: eco, normal, max"
        )

    vac = await get_vacuum()
    await vac.async_set_property_value("Power_Mode", power_map[mode.lower()].value)
    return {"power_mode": mode.lower()}


@app.post("/volume/{level}")
async def set_volume(level: int):
    if not 0 <= level <= 100:
        raise HTTPException(status_code=400, detail="Volume must be 0-100")

    vac = await get_vacuum()
    await vac.async_set_property_value("Robot_Volume_Control", level)
    return {"volume": level}


# === MANUAL DRIVE (Pulse-based) ===


class DriveCommand(BaseModel):
    direction: str  # forward, left, right
    duration_ms: int = 500  # How long to move


@app.post("/drive")
async def manual_drive(cmd: DriveCommand):
    """
    Pulse-based manual drive.
    Starts cleaning briefly then stops to create movement.
    This is a hack since Shark doesn't expose direct motor control.
    """
    vac = await get_vacuum()

    if cmd.direction not in ["forward", "left", "right"]:
        raise HTTPException(
            status_code=400, detail="Direction must be: forward, left, right"
        )

    # Start cleaning (robot will move)
    await vac.async_set_operating_mode(OperatingModes.START)

    # Wait for specified duration
    await asyncio.sleep(cmd.duration_ms / 1000.0)

    # Stop
    await vac.async_set_operating_mode(OperatingModes.PAUSE)

    return {
        "status": "moved",
        "direction": cmd.direction,
        "duration_ms": cmd.duration_ms,
        "note": "Direction is simulated - robot moves in its own path",
    }


@app.post("/nudge/{direction}")
async def nudge(direction: str, duration_ms: int = 300):
    """Quick nudge in a direction (pulse start/stop)"""
    vac = await get_vacuum()

    await vac.async_set_operating_mode(OperatingModes.START)
    await asyncio.sleep(duration_ms / 1000.0)
    await vac.async_set_operating_mode(OperatingModes.PAUSE)

    return {"status": "nudged", "duration_ms": duration_ms}


# === ROOM CLEANING ===


@app.get("/rooms")
async def get_rooms():
    """Get list of mapped rooms"""
    vac = await get_vacuum()
    room_list = vac.property_values.get("Robot_Room_List")

    if room_list and ":" in str(room_list):
        parts = room_list.split(":")
        return {"identifier": parts[0], "rooms": parts[1:]}

    return {
        "identifier": None,
        "rooms": [],
        "note": "No rooms mapped yet. Run /explore first.",
    }


class CleanRoomsRequest(BaseModel):
    rooms: List[str]


@app.post("/clean/rooms")
async def clean_rooms(req: CleanRoomsRequest):
    """Clean specific rooms"""
    vac = await get_vacuum()

    try:
        await vac.async_clean_rooms(req.rooms)
        return {"status": "cleaning_rooms", "rooms": req.rooms}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# === ADVANCED ===


@app.post("/command/{property_name}")
async def send_command(property_name: str, value: str):
    """Send raw command to a property (advanced)"""
    vac = await get_vacuum()

    # Check if property is settable
    if vac._settable_properties and property_name not in vac._settable_properties:
        raise HTTPException(
            status_code=400,
            detail=f"Property {property_name} is not settable. Available: {sorted(vac._settable_properties)}",
        )

    try:
        # Try to convert to int if it looks like a number
        if value.isdigit():
            value = int(value)
        await vac.async_set_property_value(property_name, value)
        return {"status": "sent", "property": property_name, "value": value}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/properties/settable")
async def get_settable_properties():
    """Get list of all settable properties"""
    vac = await get_vacuum()
    return {"settable_properties": sorted(vac._settable_properties or [])}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
