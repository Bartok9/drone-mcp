"""Unit tests for go MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGoTool(unittest.TestCase):
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

    def test_list_includes_go(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        self.assertIn("go", {t.name for t in tools})

    def test_call_go_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(
                srv.app._call("go", {"x": 50, "y": 0, "z": 0, "speed": 20})
            )
        mock_drone.send_command.assert_awaited_once_with("go 50 0 0 20")
        self.assertEqual(result[0].text, "ok")

    def test_reject_bool_x(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(
                    srv.app._call("go", {"x": True, "y": 0, "z": 0, "speed": 20})
                )
        mock_drone.send_command.assert_not_awaited()

    def test_reject_all_zero(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(
                    srv.app._call("go", {"x": 0, "y": 0, "z": 0, "speed": 20})
                )
        mock_drone.send_command.assert_not_awaited()

    def test_reject_speed_out_of_range(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(
                    srv.app._call("go", {"x": 10, "y": 0, "z": 0, "speed": 5})
                )
        mock_drone.send_command.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
