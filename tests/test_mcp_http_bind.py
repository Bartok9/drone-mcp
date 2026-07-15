"""Unit tests for MCP_HOST / MCP_PORT HTTP bind resolution."""
import os
import unittest

import tello_mcp


class TestLoadMcpHttpBind(unittest.TestCase):
    def setUp(self):
        self._h = os.environ.pop("MCP_HOST", None)
        self._p = os.environ.pop("MCP_PORT", None)

    def tearDown(self):
        for key, prev in (("MCP_HOST", self._h), ("MCP_PORT", self._p)):
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev

    def test_defaults(self):
        self.assertEqual(tello_mcp.load_mcp_http_bind(), ("0.0.0.0", 3000))

    def test_custom(self):
        os.environ["MCP_HOST"] = "127.0.0.1"
        os.environ["MCP_PORT"] = "8080"
        self.assertEqual(tello_mcp.load_mcp_http_bind(), ("127.0.0.1", 8080))

    def test_reject_empty_host(self):
        os.environ["MCP_HOST"] = "   "
        with self.assertRaises(ValueError):
            tello_mcp.load_mcp_http_bind()

    def test_reject_bad_port(self):
        for raw in ("0", "65536", "-1", "3000x", "30.5", "true"):
            os.environ["MCP_PORT"] = raw
            with self.assertRaises(ValueError):
                tello_mcp.load_mcp_http_bind()

    def test_boundary_ports(self):
        os.environ["MCP_PORT"] = "1"
        self.assertEqual(tello_mcp.load_mcp_http_bind()[1], 1)
        os.environ["MCP_PORT"] = "65535"
        self.assertEqual(tello_mcp.load_mcp_http_bind()[1], 65535)


if __name__ == "__main__":
    unittest.main()
