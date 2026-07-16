# Tello Drone MCP Server

A Model Context Protocol (MCP) server implementation for controlling the DJI Tello drone. This server allows any MCP-compatible client to control a Tello drone through a standardized interface. 

## This is under active development, read [security considerations](#security-considerations)


## Features

- MCP Support 
- Real-time drone control through SSE (Server-Sent Events)
- Robust error handling and logging
- CORS-enabled for web clients (like mcp inspector)
- Supports basic Tello drone commands:
  - Takeoff
  - Land
  - Move (up/down/left/right/forward/back)
  - Rotate (clockwise/counter-clockwise)

## Prerequisites

- Python 3.7+
- DJI Tello drone
- Network connection to the Tello drone
- Root/sudo access (required for UDP socket binding)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd drone-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## MCP Configuration

To enable your MCP client to connect to the Tello drone server, add the following configuration to your `mcp.json` file (usually located at `~/.cursor/mcp.json` or in your project directory):

```json
{
  "tello-drone": {
    "url": "http://localhost:3000/sse"
  }
}
```

This configuration allows MCP-enabled tools and models to automatically discover and connect to your Tello drone server.

## Usage

1. Connect to your Tello drone's WiFi network (usually starts with "TELLO-").

2. Start the MCP server:
```bash
sudo python tello_mcp.py
```

The server will:
- Initialize connection with the Tello drone
- Start the MCP server on `http://0.0.0.0:3000`
- Set up SSE endpoint at `/sse`
- Handle messages at `/message`

Ensure the server is running before you plan to use it in your client (cursor, windsurf, code).

## Available Tools

The server provides the following MCP tools:

### 1. Takeoff
```json
{
    "name": "takeoff",
    "description": "Commands the Tello drone to take off",
    "inputSchema": {
        "type": "object",
        "properties": {}
    }
}
```

### 2. Land
```json
{
    "name": "land",
    "description": "Commands the Tello drone to land",
    "inputSchema": {
        "type": "object",
        "properties": {}
    }
}
```

### 3. Get Battery
```json
{
    "name": "get_battery",
    "description": "Reads the Tello battery level percentage (read-only; no flight motion)",
    "inputSchema": {"type": "object", "properties": {}}
}
```

Returns the drone's battery response string (typically a percentage number as text).

### 4. Move
```json
{
    "name": "move",
    "description": "Moves the Tello drone in a specified direction",
    "inputSchema": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["up", "down", "left", "right", "forward", "back"]
            },
            "distance": {
                "type": "integer",
                "minimum": 20,
                "maximum": 500
            }
        },
        "required": ["direction", "distance"]
    }
}
```

### 5. Rotate
```json
{
    "name": "rotate",
    "description": "Rotates the Tello drone clockwise or counter-clockwise",
    "inputSchema": {
        "type": "object",
        "properties": {
            "direction": {
                "type": "string",
                "enum": ["cw", "ccw"]
            },
            "degrees": {
                "type": "integer",
                "minimum": 1,
                "maximum": 3600
            }
        },
        "required": ["direction", "degrees"]
    }
}
```

## MCP Client Integration

To connect an MCP client:

1. Start your server and Connect to the SSE endpoint:
```
GET http://localhost:3000/sse
```

2. Prompt your MCP enabled model, which will communicate via SSE
```
event: endpoint
data: /message?sessionId=<session-id>
```

3. Send initialize request:
```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize"
}
```

4. List available tools:
```json
{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "listTools"
}
```

5. Call a tool (example - takeoff):
```json
{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "callTool",
    "params": {
        "name": "takeoff",
        "arguments": {}
    }
}
```

## Error Handling

The server implements comprehensive error handling:
- Drone connection failures
- Invalid commands
- Network timeouts
- Protocol errors
- Invalid tool parameters

All errors are logged and returned as proper JSON-RPC 2.0 error responses.

## Logging

The server logs to stderr with detailed information about:
- Server startup/shutdown
- Drone connection status
- Command execution
- Client connections
- Error conditions

## Security Considerations

- The server requires root/sudo access to bind to UDP ports
- No authentication is implemented (rely on network security)
- CORS is enabled for all origins (*)
- Use in a controlled environment only

## Development

The server is built using:
- Python's `mcp` library for protocol handling
- Starlette for HTTP/SSE transport
- Uvicorn as the ASGI server
- Native Python socket library for drone UDP communication

## Troubleshooting

1. **Server won't start:**
   - Ensure you have sudo/root access
   - Check if the Tello's WiFi is connected
   - Verify no other process is using port 3000

2. **Drone won't connect:**
   - Ensure drone is powered on
   - Check WiFi connection
   - Verify no other application is controlling the drone

3. **Commands fail:**
   - Check drone battery level
   - Ensure drone is in a safe flying environment
   - Verify command parameters are within allowed ranges

## License

MIT

## Contributing

Welcome to contribute. 