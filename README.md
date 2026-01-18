# Shark Robot Control API

## Setup

```bash
# Copy env template
cp .env.example .env

# Edit .env with your SharkClean app credentials
nano .env

# Run the server
source venv/bin/activate
python main.py
```

## API Endpoints

All endpoints return JSON:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/status` | Get robot status (model, serial, properties) |
| POST | `/start` | Start cleaning |
| POST | `/pause` | Pause cleaning |
| POST | `/stop` | Stop cleaning |
| POST | `/dock` | Return to dock |
| POST | `/find` | Make robot chirp (find it) |
| POST | `/power/{mode}` | Set power: `eco`, `normal`, `max` |

## Example Usage

```bash
# Start cleaning
curl -X POST http://localhost:8000/start

# Get status
curl http://localhost:8000/status

# Set power to max
curl -X POST http://localhost:8000/power/max

# Dock the robot
curl -X POST http://localhost:8000/dock
```

## Next: iOS App

This API is ready for your iOS app. Use your SharkClean login credentials in `.env`.
