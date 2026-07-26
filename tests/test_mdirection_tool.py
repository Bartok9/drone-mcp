"""Unit tests for mdirection MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestMdirectionTool(unittest.TestCase):
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

    def test_list_includes_mdirection(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        names = {t.name for t in tools}
        self.assertIn("mdirection", names)

    def test_call_mdirection_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("mdirection", {"direction": 2}))
        mock_drone.send_command.assert_awaited_once_with("mdirection 2")
        self.assertEqual(result[0].text, "ok")

    def test_reject_bool_direction(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("mdirection", {"direction": True}))
        mock_drone.send_command.assert_not_awaited()

    def test_reject_out_of_range(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(ValueError):
                asyncio.run(srv.app._call("mdirection", {"direction": 3}))
        mock_drone.send_command.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
