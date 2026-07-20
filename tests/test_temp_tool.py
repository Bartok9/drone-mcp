"""Unit tests for get_temp MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGetTempTool(unittest.TestCase):
    def test_list_and_call_get_temp(self):
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
            self.assertIn("get_temp", names)
            temp_tool = next(t for t in tools if t.name == "get_temp")
            self.assertEqual(temp_tool.inputSchema.get("properties"), {})
            self.assertIn("temp", (temp_tool.description or "").lower())

            mock_drone = MagicMock()
            mock_drone.send_command = AsyncMock(return_value="45~48C")
            with patch.object(tello_mcp, "drone", mock_drone):
                result = asyncio.run(srv.app._call("get_temp", {}))
            mock_drone.send_command.assert_awaited_once_with("temp?")
            self.assertEqual(result[0].text, "45~48C")


if __name__ == "__main__":
    unittest.main()
