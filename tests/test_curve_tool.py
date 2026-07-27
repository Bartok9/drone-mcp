"""Unit tests for curve MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestCurveTool(unittest.TestCase):
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

    def test_list_includes_curve(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        self.assertIn("curve", {t.name for t in tools})

    def test_call_curve_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(
                srv.app._call(
                    "curve",
                    {
                        "x1": 20,
                        "y1": 0,
                        "z1": 0,
                        "x2": 40,
                        "y2": 20,
                        "z2": 0,
                        "speed": 30,
                    },
                )
            )
        mock_drone.send_command.assert_awaited_once_with("curve 20 0 0 40 20 0 30")
        self.assertEqual(result[0].text, "ok")

    def test_reject_bool_x1(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(
                    srv.app._call(
                        "curve",
                        {
                            "x1": True,
                            "y1": 0,
                            "z1": 0,
                            "x2": 40,
                            "y2": 0,
                            "z2": 0,
                            "speed": 30,
                        },
                    )
                )
        mock_drone.send_command.assert_not_awaited()

    def test_reject_speed_out_of_range(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(
                    srv.app._call(
                        "curve",
                        {
                            "x1": 20,
                            "y1": 0,
                            "z1": 0,
                            "x2": 40,
                            "y2": 0,
                            "z2": 0,
                            "speed": 80,
                        },
                    )
                )
        mock_drone.send_command.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
