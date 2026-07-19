import asyncio
import socket
import sys
import logging
from typing import Optional, Any, Sequence
import uvicorn
import json

from pydantic import BaseModel 
from sse_starlette.sse import EventSourceResponse 

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware # Use Starlette's CORS
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent # Use MCP types

# Configure logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# Change logger name slightly to differentiate
logger = logging.getLogger("tello_mcp_server_lib") 

# Tello drone configuration
TELLO_IP = '192.168.10.1'
TELLO_CMD_PORT = 8889
TELLO_STATE_PORT = 8890
TIMEOUT = 10.0  # seconds

# Tello drone communication class
class Tello:
    """Handles communication with the Tello drone."""
    def __init__(self, local_ip='0.0.0.0', local_port=8889):
        self.local_ip = local_ip
        self.local_port = local_port
        self.tello_address = (TELLO_IP, TELLO_CMD_PORT)
        self.response = None
        self.state = None
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        logger.info(f"Binding UDP socket to {self.local_ip}:{self.local_port}")
        try:
            self.sock.bind((self.local_ip, self.local_port))
        except OSError as e:
            logger.error(f"Failed to bind socket to {self.local_ip}:{self.local_port}. Error: {e}")
            raise ConnectionError(f"Socket bind error: {e}")

        self.sock.settimeout(TIMEOUT)

        logger.info(f"Sending initial command: command to {self.tello_address}")
        try:
            self.sock.sendto("command".encode('utf-8'), self.tello_address)
            response, _ = self.sock.recvfrom(1024)
            # Decode response, expecting UTF-8 and specifically "ok"
            try:
                self.response = response.decode('utf-8').strip()
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode initial response from drone: {response!r} - Error: {e}")
                raise ConnectionError(f"Received non-UTF8 response from drone: {response!r}")
                
            logger.info(f"Received initial response: {self.response}")
            # Strict check for "ok"
            if self.response != "ok":
                logger.error(f"Failed to enter SDK mode. Expected 'ok', got: '{self.response}'")
                raise ConnectionError(f"Failed to enter SDK mode (response: '{self.response}')")
            else:
                 logger.info("Successfully entered SDK mode.")
                 
        except socket.timeout:
            logger.error("Initial command timed out.")
            raise ConnectionError("Failed to get response from Tello (timeout).")
        except OSError as e:
            logger.error(f"Network error sending initial command: {e}")
            raise ConnectionError(f"Network error initializing Tello: {e}")

    async def send_command(self, command: str) -> str:
        logger.info(f"Sending command: {command} to {self.tello_address}")

        def blocking_io():
            # This function contains the blocking socket operations
            self.sock.sendto(command.encode('utf-8'), self.tello_address)
            logger.debug(f"Sent command {command}. Waiting for response...")
            try:
                response_bytes, addr = self.sock.recvfrom(1024)
                logger.debug(f"Received {len(response_bytes)} bytes from {addr}")
                # Attempt to decode, ignore errors for general responses for now
                decoded_response = response_bytes.decode('utf-8', errors='ignore').strip()
                logger.debug(f"Decoded response: {decoded_response}")
                return decoded_response
            except socket.timeout:
                 logger.warning(f"Timeout waiting for response to command: {command}")
                 return "error timeout"
            except Exception as sock_err:
                 logger.error(f"Socket error receiving response for {command}: {sock_err}")
                 return f"error socket: {sock_err}"
                 
        try:
            # Run the blocking I/O in a separate thread
            self.response = await asyncio.to_thread(blocking_io)
            logger.info(f"Received response for {command}: {self.response}")
            return self.response
        except Exception as e:
            logger.error(f"Error in send_command wrapper for {command}: {e}")
            return f"error wrapper: {e}"

    def close(self):
        logger.info("Closing Tello connection.")
        self.sock.close()

# Global drone instance (initialized later in main)
drone: Optional[Tello] = None



# MCP Server Class using the library approach
class MCPTelloServer:
    def __init__(self):
        logger.info("Initializing MCPTelloServer using mcp.server.Server")
        # Use the Server class from the mcp library
        self.app = Server(
            name='tello-drone-controller-lib', 
            version='1.0.1'
        ) 
        self.setup_tools()

    def setup_tools(self):
        # Register list_tools handler
        @self.app.list_tools()
        async def list_tools() -> list[Tool]:
            logger.info("list_tools called by MCP client")
            # Define tools directly here
            tools = [
                Tool(
                    name="takeoff",
                    description="Commands the Tello drone to take off",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="land",
                    description="Commands the Tello drone to land",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="move",
                    description="Moves the Tello drone in a specified direction",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "direction": {"type": "string", "enum": ["up", "down", "left", "right", "forward", "back"]},
                            "distance": {"type": "integer", "minimum": 20, "maximum": 500}
                        },
                        "required": ["direction", "distance"]
                    }
                ),
                Tool(
                    name="rotate",
                    description="Rotates the Tello drone clockwise or counter-clockwise",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "direction": {"type": "string", "enum": ["cw", "ccw"]},
                            "degrees": {"type": "integer", "minimum": 1, "maximum": 3600}
                        },
                        "required": ["direction", "degrees"]
                    }
                ),
                Tool(
                    name="get_sn",
                    description="Reads the Tello serial number (SDK sn? query); read-only telemetry",
                    inputSchema={"type": "object", "properties": {}}
                )
            ]
            logger.info(f"Returning {len(tools)} tools.")
            return tools

        # Register call_tool handler
        @self.app.call_tool()
        async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
            # Use the global drone instance
            global drone 
            logger.info(f"call_tool called for '{name}' with args: {arguments}")

            if not drone:
                logger.error(f"Drone not available for tool call: {name}")
                # MCP library expects raising exceptions for errors
                raise RuntimeError("Drone connection not established")

            # Validate arguments (basic)
            if not isinstance(arguments, dict):
                 logger.error(f"Invalid arguments type for {name}: {type(arguments)}")
                 raise ValueError("Arguments must be a JSON object (dict)")

            try:
                response_output = "error: unknown tool" # Default error
                
                if name == "takeoff":
                    response_output = await drone.send_command("takeoff")
                elif name == "land":
                    response_output = await drone.send_command("land")
                elif name == "move":
                    direction = arguments.get("direction")
                    distance = arguments.get("distance")
                    if not direction or distance is None: # Check distance too
                        raise ValueError("Missing direction or distance for move")
                    # Add type/range check for distance
                    if not isinstance(distance, int) or not (20 <= distance <= 500):
                         raise ValueError("Distance must be an integer between 20 and 500")
                    response_output = await drone.send_command(f"{direction} {distance}")
                elif name == "rotate":
                    direction = arguments.get("direction")
                    degrees = arguments.get("degrees")
                    if not direction or degrees is None: # Check degrees too
                         raise ValueError("Missing direction or degrees for rotate")
                    # Add type/range check for degrees
                    if not isinstance(degrees, int) or not (1 <= degrees <= 3600):
                         raise ValueError("Degrees must be an integer between 1 and 3600")
                    response_output = await drone.send_command(f"{direction} {degrees}")
                elif name == "get_sn":
                    response_output = await drone.send_command("sn?")
                else:
                    # MCP Server should raise error for unknown tool
                    logger.error(f"Unknown tool requested in call_tool: {name}")
                    raise ValueError(f"Unknown tool: {name}")

                # Check drone response for errors
                if "error" in response_output.lower():
                    logger.error(f"Drone command error for {name}: {response_output}")
                    raise RuntimeError(f"Drone command failed: {response_output}")
                else:
                    # Success - return as TextContent list
                    logger.info(f"Tool {name} executed. Drone response: {response_output}")
                    return [TextContent(type="text", text=response_output)]

            except ValueError as ve: # Catch argument validation errors
                 logger.error(f"Invalid arguments for tool {name}: {ve}")
                 raise ve # Re-raise for MCP library to handle
            except Exception as e:
                # Catch unexpected errors during command execution
                logger.error(f"Error executing tool {name}: {e}", exc_info=True)
                raise RuntimeError(f"Error executing tool {name}: {str(e)}")


# Function to create the Starlette App 
def create_starlette_app(tello_mcp_server: MCPTelloServer):
    # Use the SseServerTransport, providing the path for POST messages
    sse_transport = SseServerTransport("/message") 

    # Define handlers using the transport
    class HandleSSE:
        async def __call__(self, scope, receive, send):
            # This connects the SSE stream to the MCP Server logic
            logger.info("HandleSSE called (GET /sse)")
            async with sse_transport.connect_sse(scope, receive, send) as streams:
                logger.info("Running tello_mcp_server.app.run...")
                try:
                    # Run the core MCP server logic with the streams provided by the transport
                    await tello_mcp_server.app.run(
                        streams[0], # Input stream
                        streams[1], # Output stream
                        tello_mcp_server.app.create_initialization_options()
                    )
                    logger.info("tello_mcp_server.app.run completed.")
                except Exception as run_err:
                     logger.error(f"Error during tello_mcp_server.app.run: {run_err}", exc_info=True)
                     # Optionally re-raise or handle depending on desired behavior on run error
                     # For now, just log it. The connection will likely close.
            logger.info("HandleSSE finished.")

    class HandleMessages:
        async def __call__(self, scope, receive, send):
            # This handles the POST requests to /message
            logger.info(f"HandleMessages called (POST {scope.get('path')})")
            await sse_transport.handle_post_message(scope, receive, send)
            logger.info(f"HandleMessages finished (POST {scope.get('path')})")

    # Define routes for Starlette
    routes = [
        Route("/sse", endpoint=HandleSSE(), methods=["GET"]),
        # The POST path MUST match the one given to SseServerTransport
        Route("/message", endpoint=HandleMessages(), methods=["POST"]), 
    ]
    
    # Define CORS middleware for Starlette
    middleware = [
        Middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
    ]

    logger.info("Creating Starlette app with MCP routes and middleware.")
    # Create the Starlette app instance
    return Starlette(routes=routes, middleware=middleware)


# --- Main Execution ---
if __name__ == "__main__":
    # Ensure global drone is None initially
    drone = None 
    try:
        # Initialize Tello drone first - exits if it fails
        logger.info("Initializing Tello drone...")
        drone = Tello() 
        logger.info("Tello drone initialized successfully.")

        # Create the MCP Server instance
        tello_mcp_server = MCPTelloServer()

        # Create the Starlette web application using the MCP Server
        starlette_app = create_starlette_app(tello_mcp_server)
        
        # Run the Starlette app with uvicorn
        logger.info("Starting Starlette MCP server with uvicorn on 0.0.0.0:3000...")
        uvicorn.run(starlette_app, host="0.0.0.0", port=3000)
        
    except ConnectionError as e:
        # If Tello init fails, log critical error and exit.
        logger.error(f"CRITICAL: Failed to initialize Tello drone connection: {e}")
        logger.error("MCP Server cannot start without a drone connection. Exiting.")
        sys.exit(1) 
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during server startup: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if drone:
            drone.close()
        logger.info("Cleanup complete.")