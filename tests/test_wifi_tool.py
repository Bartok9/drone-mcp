"""Unit tests for get_wifi MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGetWifiTool(unittest.TestCase):
    def test_list_and_call_get_wifi(self):
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
            srv = tello_mcp.MCPTelloServer()
            tools = asyncio.run(srv.app._list())
            names = {t.name for t in tools}
            self.assertIn("get_wifi", names)
            wifi_tool = next(t for t in tools if t.name == "get_wifi")
            self.assertEqual(wifi_tool.inputSchema.get("properties"), {})
            self.assertIn("wifi", (wifi_tool.description or "").lower())

            mock_drone = MagicMock()
            mock_drone.send_command = AsyncMock(return_value="90")
            with patch.object(tello_mcp, "drone", mock_drone):
                result = asyncio.run(srv.app._call("get_wifi", {}))
            mock_drone.send_command.assert_awaited_once_with("wifi?")
            self.assertEqual(result[0].text, "90")


if __name__ == "__main__":
    unittest.main()
