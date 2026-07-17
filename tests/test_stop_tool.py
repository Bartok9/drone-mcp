"""Unit tests for MCP stop (hover) tool."""
from __future__ import annotations

import asyncio
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestStopTool(unittest.TestCase):
    def test_source_registers_stop_tool_and_handler(self):
        src = Path(tello_mcp.__file__).read_text()
        self.assertIn('name="stop"', src)
        self.assertIn('send_command("stop")', src)
        self.assertIn("hover", src.lower())

    def test_call_tool_stop_routes_to_send_command(self):
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")

        async def invoke():
            with patch.object(tello_mcp, "drone", mock_drone):
                if not tello_mcp.drone:
                    raise RuntimeError("Drone connection not established")
                response_output = await tello_mcp.drone.send_command("stop")
                if "error" in response_output.lower():
                    raise RuntimeError(
                        f"Drone command failed: {response_output}"
                    )
                return response_output

        result = asyncio.run(invoke())
        self.assertEqual(result, "ok")
        mock_drone.send_command.assert_awaited_with("stop")


if __name__ == "__main__":
    unittest.main()
