"""Unit tests for get_state MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import MagicMock, patch

import tello_mcp


class TestGetStateTool(unittest.TestCase):
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

    def test_list_includes_get_state(self):
        srv = self._server()
        tools = asyncio.run(srv.app._list())
        names = {t.name for t in tools}
        self.assertIn("get_state", names)

    def test_call_get_state_ok(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.receive_state.return_value = "bat:90;h:0;"
        with patch.object(tello_mcp, "drone", mock_drone):
            result = asyncio.run(srv.app._call("get_state", {}))
        mock_drone.receive_state.assert_called_once()
        self.assertEqual(result[0].text, "bat:90;h:0;")

    def test_call_get_state_timeout_errors(self):
        srv = self._server()
        mock_drone = MagicMock()
        mock_drone.receive_state.return_value = "error timeout"
        with patch.object(tello_mcp, "drone", mock_drone):
            with self.assertRaises(RuntimeError):
                asyncio.run(srv.app._call("get_state", {}))


if __name__ == "__main__":
    unittest.main()
