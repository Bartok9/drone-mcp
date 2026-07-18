"""Unit tests for set_speed MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


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


class TestSetSpeedTool(unittest.TestCase):
    def _server(self):
        with patch.object(tello_mcp, "Server", FakeServer):
            return tello_mcp.MCPTelloServer()

    def test_list_and_happy_path(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        names = {t.name for t in tools}
        self.assertIn("set_speed", names)
        t = next(x for x in tools if x.name == "set_speed")
        self.assertIn("speed", t.inputSchema["properties"])
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("set_speed", {"speed": 50}))
        mock_drone.send_command.assert_awaited_once_with("speed 50")
        self.assertEqual(result[0].text, "ok")

    def test_rejects_bool_float_oor_missing(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("set_speed", {"speed": True}))
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("set_speed", {"speed": 50.0}))
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("set_speed", {"speed": 5}))
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("set_speed", {"speed": 101}))
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("set_speed", {}))
        mock_drone.send_command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
