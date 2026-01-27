# Shark Robot Control

Two control methods available:

## Method 1: Cloud API (No Hardware Mod)
Control via Shark's cloud - start/stop/dock only.

```bash
cp .env.example .env
# Edit .env with SharkClean credentials
source venv/bin/activate
python main.py
```

### Cloud API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Robot status |
| POST | `/start` | Start cleaning |
| POST | `/pause` | Pause |
| POST | `/dock` | Return to dock |
| POST | `/find` | Make robot chirp |

---

## Method 2: LLM + MCP Control (Hardware Mod)
Full control via Portenta H7 - drive, turn, vacuum control.

### Architecture
```
Claude (LLM) ◄──MCP──► MCP Server ◄──WiFi──► Portenta H7 ──► Motors
```

### Hardware Required
- Arduino Portenta H7
- Motor driver (L298N/DRV8833)
- Access to robot motor connectors

### Setup
1. Flash `firmware-portenta/shark_controller.ino` to Portenta
2. Update WiFi credentials in firmware
3. Wire motors to Portenta via motor driver
4. Add to MCP config:
```json
{
  "mcpServers": {
    "shark-robot": {
      "command": "python3",
      "args": ["/home/riley/shark/mcp-server/shark_mcp.py"]
    }
  }
}
```

### MCP Tools
| Tool | Description |
|------|-------------|
| robot_forward | Move forward |
| robot_backward | Move backward |
| robot_turn_left | Turn left |
| robot_turn_right | Turn right |
| robot_stop | Stop all |
| robot_vacuum_on | Start vacuum |
| robot_status | Get status |
| robot_sensors | Read sensors |

### Example Commands to LLM
- "Drive forward slowly for 2 seconds"
- "Turn right 90 degrees"
- "Start vacuuming at 50% power"
- "Check the sensor readings"
- "Stop the robot"

---

## Files
```
shark/
├── main.py                    # Cloud API server
├── mcp-server/
│   ├── shark_mcp.py          # MCP server for LLM
│   └── test_robot.py         # Direct test script
├── firmware-portenta/
│   └── shark_controller.ino  # Portenta firmware
└── sharkiq/                   # SharkIQ library
```
