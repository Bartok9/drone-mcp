"""Unit tests for get_attitude MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGetAttitudeTool(unittest.TestCase):
    def test_list_and_call_get_attitude(self):
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
            self.assertIn("get_attitude", names)
            att_tool = next(t for t in tools if t.name == "get_attitude")
            self.assertEqual(att_tool.inputSchema.get("properties"), {})
            desc = (att_tool.description or "").lower()
            self.assertTrue("attitude" in desc or "pitch" in desc)

            mock_drone = MagicMock()
            mock_drone.send_command = AsyncMock(return_value="pitch:0;roll:0;yaw:90;")
            with patch.object(tello_mcp, "drone", mock_drone):
                result = asyncio.run(srv.app._call("get_attitude", {}))
            mock_drone.send_command.assert_awaited_once_with("attitude?")
            self.assertEqual(result[0].text, "pitch:0;roll:0;yaw:90;")


if __name__ == "__main__":
    unittest.main()
