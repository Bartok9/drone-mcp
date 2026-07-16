"""Unit tests for read-only get_battery MCP tool (no hardware)."""
import unittest
from unittest import mock

import mcp.types
import tello_mcp


class TestBatteryQueryCommand(unittest.TestCase):
    def test_command_string(self):
        self.assertEqual(tello_mcp.battery_query_command(), "battery?")


class TestGetBatteryToolDispatch(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self._prev = tello_mcp.drone

    async def asyncTearDown(self):
        tello_mcp.drone = self._prev

    async def test_list_tools_includes_get_battery(self):
        server = tello_mcp.MCPTelloServer()
        handler = server.app.request_handlers[mcp.types.ListToolsRequest]
        result = await handler(mcp.types.ListToolsRequest(method="tools/list", params=None))
        # result is ServerResult wrapping ListToolsResult
        tools = result.root.tools
        names = [t.name for t in tools]
        self.assertIn("get_battery", names)

    async def test_call_tool_sends_battery_query(self):
        mock_drone = mock.AsyncMock()
        mock_drone.send_command = mock.AsyncMock(return_value="87")
        tello_mcp.drone = mock_drone
        server = tello_mcp.MCPTelloServer()
        handler = server.app.request_handlers[mcp.types.CallToolRequest]
        req = mcp.types.CallToolRequest(
            method="tools/call",
            params=mcp.types.CallToolRequestParams(name="get_battery", arguments={}),
        )
        result = await handler(req)
        mock_drone.send_command.assert_awaited_with("battery?")
        content = result.root.content
        self.assertEqual(content[0].text, "87")


if __name__ == "__main__":
    unittest.main()
