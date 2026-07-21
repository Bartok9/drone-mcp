"""Unit tests for get_time MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGetTimeTool(unittest.TestCase):
    def test_list_and_call_get_time(self):
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
            self.assertIn("get_time", names)
            time_tool = next(t for t in tools if t.name == "get_time")
            self.assertEqual(time_tool.inputSchema.get("properties"), {})
            desc = (time_tool.description or "").lower()
            self.assertTrue("time" in desc or "flight" in desc)

            mock_drone = MagicMock()
            mock_drone.send_command = AsyncMock(return_value="12s")
            with patch.object(tello_mcp, "drone", mock_drone):
                result = asyncio.run(srv.app._call("get_time", {}))
            mock_drone.send_command.assert_awaited_once_with("time?")
            self.assertEqual(result[0].text, "12s")


if __name__ == "__main__":
    unittest.main()
