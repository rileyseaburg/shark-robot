#!/usr/bin/env python3
"""
Shark Robot MCP Server
Allows LLMs to control the robot via MCP protocol
"""

import asyncio
import json
import sys
from typing import Any
import httpx

# MCP protocol constants
JSONRPC_VERSION = "2.0"

# Robot connection settings
ROBOT_IP = "192.168.50.100"  # Portenta H7 IP - update after connecting
ROBOT_PORT = 8080


class SharkRobotMCP:
    def __init__(self):
        self.robot_url = f"http://{ROBOT_IP}:{ROBOT_PORT}"
        self.connected = False

    async def send_robot_command(self, endpoint: str, data: dict | None = None) -> dict:
        """Send command to robot firmware"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                if data:
                    resp = await client.post(f"{self.robot_url}/{endpoint}", json=data)
                else:
                    resp = await client.get(f"{self.robot_url}/{endpoint}")
                return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_tools(self) -> list:
        """Return available MCP tools"""
        return [
            {
                "name": "robot_drive",
                "description": "Drive the robot in a direction. Use this to move the robot forward, backward, or turn.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "left_speed": {
                            "type": "integer",
                            "description": "Left wheel speed (-100 to 100). Negative=backward",
                            "minimum": -100,
                            "maximum": 100,
                        },
                        "right_speed": {
                            "type": "integer",
                            "description": "Right wheel speed (-100 to 100). Negative=backward",
                            "minimum": -100,
                            "maximum": 100,
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "Duration in milliseconds (0 = continuous until stop)",
                            "minimum": 0,
                            "maximum": 10000,
                        },
                    },
                    "required": ["left_speed", "right_speed"],
                },
            },
            {
                "name": "robot_forward",
                "description": "Move the robot forward at specified speed",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "integer",
                            "description": "Speed (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "Duration in milliseconds",
                            "minimum": 0,
                            "maximum": 10000,
                        },
                    },
                    "required": ["speed"],
                },
            },
            {
                "name": "robot_backward",
                "description": "Move the robot backward at specified speed",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "integer",
                            "description": "Speed (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "Duration in milliseconds",
                            "minimum": 0,
                            "maximum": 10000,
                        },
                    },
                    "required": ["speed"],
                },
            },
            {
                "name": "robot_turn_left",
                "description": "Turn the robot left (counterclockwise)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "integer",
                            "description": "Turn speed (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "Duration in milliseconds",
                            "minimum": 0,
                            "maximum": 5000,
                        },
                    },
                    "required": ["speed"],
                },
            },
            {
                "name": "robot_turn_right",
                "description": "Turn the robot right (clockwise)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "integer",
                            "description": "Turn speed (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        },
                        "duration_ms": {
                            "type": "integer",
                            "description": "Duration in milliseconds",
                            "minimum": 0,
                            "maximum": 5000,
                        },
                    },
                    "required": ["speed"],
                },
            },
            {
                "name": "robot_stop",
                "description": "Stop all robot movement immediately",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "robot_vacuum_on",
                "description": "Turn on the vacuum suction motor",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "power": {
                            "type": "integer",
                            "description": "Vacuum power (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        }
                    },
                },
            },
            {
                "name": "robot_vacuum_off",
                "description": "Turn off the vacuum suction motor",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "robot_brush_on",
                "description": "Turn on the main brush",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "speed": {
                            "type": "integer",
                            "description": "Brush speed (0-100)",
                            "minimum": 0,
                            "maximum": 100,
                        }
                    },
                },
            },
            {
                "name": "robot_brush_off",
                "description": "Turn off the main brush",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "robot_status",
                "description": "Get current robot status (battery, sensors, motor states)",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "robot_sensors",
                "description": "Read robot sensors (bumpers, cliff sensors, wheel encoders)",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Execute a tool call"""

        if name == "robot_drive":
            return await self.send_robot_command(
                "drive",
                {
                    "left": arguments.get("left_speed", 0),
                    "right": arguments.get("right_speed", 0),
                    "duration": arguments.get("duration_ms", 0),
                },
            )

        elif name == "robot_forward":
            speed = arguments.get("speed", 50)
            duration = arguments.get("duration_ms", 0)
            return await self.send_robot_command(
                "drive", {"left": speed, "right": speed, "duration": duration}
            )

        elif name == "robot_backward":
            speed = arguments.get("speed", 50)
            duration = arguments.get("duration_ms", 0)
            return await self.send_robot_command(
                "drive", {"left": -speed, "right": -speed, "duration": duration}
            )

        elif name == "robot_turn_left":
            speed = arguments.get("speed", 50)
            duration = arguments.get("duration_ms", 0)
            return await self.send_robot_command(
                "drive", {"left": -speed, "right": speed, "duration": duration}
            )

        elif name == "robot_turn_right":
            speed = arguments.get("speed", 50)
            duration = arguments.get("duration_ms", 0)
            return await self.send_robot_command(
                "drive", {"left": speed, "right": -speed, "duration": duration}
            )

        elif name == "robot_stop":
            return await self.send_robot_command("stop")

        elif name == "robot_vacuum_on":
            power = arguments.get("power", 100)
            return await self.send_robot_command("vacuum", {"power": power})

        elif name == "robot_vacuum_off":
            return await self.send_robot_command("vacuum", {"power": 0})

        elif name == "robot_brush_on":
            speed = arguments.get("speed", 100)
            return await self.send_robot_command("brush", {"speed": speed})

        elif name == "robot_brush_off":
            return await self.send_robot_command("brush", {"speed": 0})

        elif name == "robot_status":
            return await self.send_robot_command("status")

        elif name == "robot_sensors":
            return await self.send_robot_command("sensors")

        else:
            return {"error": f"Unknown tool: {name}"}


# MCP Protocol Handler
robot = SharkRobotMCP()


async def handle_request(request: dict) -> dict | None:
    """Handle incoming MCP JSON-RPC request"""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "shark-robot-mcp", "version": "1.0.0"},
            },
        }

    elif method == "tools/list":
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "result": {"tools": robot.get_tools()},
        }

    elif method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = await robot.call_tool(tool_name, tool_args)
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            },
        }

    elif method == "notifications/initialized":
        # No response needed for notifications
        return None

    else:
        return {
            "jsonrpc": JSONRPC_VERSION,
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }


async def main():
    """Main MCP server loop - reads from stdin, writes to stdout"""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    (
        writer_transport,
        writer_protocol,
    ) = await asyncio.get_event_loop().connect_write_pipe(
        asyncio.streams.FlowControlMixin, sys.stdout
    )
    writer = asyncio.StreamWriter(
        writer_transport, writer_protocol, reader, asyncio.get_event_loop()
    )

    while True:
        try:
            line = await reader.readline()
            if not line:
                break

            line = line.decode("utf-8").strip()
            if not line:
                continue

            request = json.loads(line)
            response = await handle_request(request)

            if response:
                writer.write((json.dumps(response) + "\n").encode("utf-8"))
                await writer.drain()

        except json.JSONDecodeError as e:
            sys.stderr.write(f"JSON decode error: {e}\n")
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")


if __name__ == "__main__":
    asyncio.run(main())
