"""Unit tests for get_height MCP tool (no hardware)."""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import tello_mcp


class TestGetHeightTool(unittest.TestCase):
    def test_list_tools_includes_get_height(self):
        server = tello_mcp.MCPTelloServer()
        tools = asyncio.get_event_loop().run_until_complete(
            server.app.request_handlers  # may not work
        ) if False else None
        # Drive list_tools via captured handler by constructing server and
        # invoking the registered coroutine through a thin probe.
        # The mcp Server stores handlers; instead re-instantiate and monkey-call.
        captured = {}

        class Probe:
            def list_tools(self):
                def deco(fn):
                    captured["list"] = fn
                    return fn
                return deco

            def call_tool(self):
                def deco(fn):
                    captured["call"] = fn
                    return fn
                return deco

            def create_initialization_options(self):
                return {}

        real_server = tello_mcp.Server

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
            self.assertIn("get_height", names)
            height_tool = next(t for t in tools if t.name == "get_height")
            self.assertEqual(height_tool.inputSchema.get("properties"), {})

            mock_drone = MagicMock()
            mock_drone.send_command = AsyncMock(return_value="50")
            with patch.object(tello_mcp, "drone", mock_drone):
                result = asyncio.run(srv.app._call("get_height", {}))
            mock_drone.send_command.assert_awaited_once_with("height?")
            self.assertEqual(result[0].text, "50")


if __name__ == "__main__":
    unittest.main()
