"""Unit tests for emergency MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestEmergencyTool(unittest.TestCase):
    def test_list_and_call_emergency(self):
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
            self.assertIn("emergency", names)
            em_tool = next(t for t in tools if t.name == "emergency")
            self.assertEqual(em_tool.inputSchema.get("properties"), {})
            desc = (em_tool.description or "").lower()
            self.assertTrue("emergency" in desc or "motor" in desc)

            mock_drone = MagicMock()
            mock_drone.send_command = AsyncMock(return_value="ok")
            with patch.object(tello_mcp, "drone", mock_drone):
                result = asyncio.run(srv.app._call("emergency", {}))
            mock_drone.send_command.assert_awaited_once_with("emergency")
            self.assertEqual(result[0].text, "ok")


if __name__ == "__main__":
    unittest.main()
