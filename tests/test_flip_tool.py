"""Unit tests for flip MCP tool fail-closed allowlist (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestFlipTool(unittest.TestCase):
    def _server(self):
        class FakeServer:
            def __init__(self, name, version):
                self.name = name
                self.version = version
                self._list = None
                self._call = None

            def list_tools(self):
                def deco(fn):
                    self._list = fn
                    return fn

                return deco

            def call_tool(self):
                def deco(fn):
                    self._call = fn
                    return fn

                return deco

            def create_initialization_options(self):
                return {}

        with patch.object(tello_mcp, "Server", FakeServer):
            return tello_mcp.MCPTelloServer()

    def test_list_and_call_flip_ok(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        names = {t.name for t in tools}
        self.assertIn("flip", names)
        flip_tool = next(t for t in tools if t.name == "flip")
        direction_schema = flip_tool.inputSchema["properties"]["direction"]
        self.assertEqual(set(direction_schema.get("enum", [])), {"l", "r", "f", "b"})
        self.assertIn("direction", flip_tool.inputSchema.get("required", []))

        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("flip", {"direction": "f"}))
        mock_drone.send_command.assert_awaited_once_with("flip f")
        self.assertEqual(result[0].text, "ok")

    def test_flip_rejects_unknown_direction(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("flip", {"direction": "up"}))
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("flip", {"direction": True}))
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("flip", {}))
        mock_drone.send_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
