"""Unit tests for motoron/motoroff MCP tools (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestMotorTools(unittest.TestCase):
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

    def test_list_includes_motor_tools(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        names = {t.name for t in tools}
        self.assertIn("motoron", names)
        self.assertIn("motoroff", names)

    def test_call_motoron_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("motoron", {}))
        mock_drone.send_command.assert_awaited_once_with("motoron")
        self.assertEqual(result[0].text, "ok")

    def test_call_motoroff_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.send_command = AsyncMock(return_value="ok")
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("motoroff", {}))
        mock_drone.send_command.assert_awaited_once_with("motoroff")
        self.assertEqual(result[0].text, "ok")


if __name__ == "__main__":
    unittest.main()
