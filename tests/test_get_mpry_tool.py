"""Unit tests for get_mpry MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGetMpryTool(unittest.TestCase):
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

    def test_list_includes_get_mpry(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        self.assertIn("get_mpry", {t.name for t in tools})

    def test_call_get_mpry_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="0.0 0.0 90.0")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("get_mpry", {}))
        mock_drone.send_command.assert_awaited_once_with("mpry?")
        self.assertEqual(result[0].text, "0.0 0.0 90.0")

    def test_call_get_mpry_error_raises(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="error timeout")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(RuntimeError):
                asyncio.run(srv.app._call("get_mpry", {}))


if __name__ == "__main__":
    unittest.main()
