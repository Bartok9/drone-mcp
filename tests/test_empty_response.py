"""Unit tests: empty/whitespace Tello UDP response fails closed."""
from __future__ import annotations

import asyncio
import socket
import unittest
from unittest.mock import MagicMock, patch

import tello_mcp


class TestEmptyResponse(unittest.TestCase):
    def test_send_command_empty_bytes_returns_error(self):
        # Build Tello without real bind: inject fake sock
        drone = object.__new__(tello_mcp.Tello)
        drone.local_ip = "0.0.0.0"
        drone.local_port = 8889
        drone.tello_address = ("192.168.10.1", 8889)
        drone.response = None
        mock_sock = MagicMock()
        mock_sock.recvfrom.return_value = (b"", ("192.168.10.1", 8889))
        mock_sock.sendto.return_value = None
        drone.sock = mock_sock

        async def go():
            return await drone.send_command("land")

        out = asyncio.run(go())
        self.assertIn("error", out.lower())
        self.assertIn("empty", out.lower())

    def test_send_command_whitespace_returns_error(self):
        drone = object.__new__(tello_mcp.Tello)
        drone.tello_address = ("192.168.10.1", 8889)
        mock_sock = MagicMock()
        mock_sock.recvfrom.return_value = (b"   \n", ("192.168.10.1", 8889))
        drone.sock = mock_sock

        out = asyncio.run(drone.send_command("battery?"))
        self.assertIn("error", out.lower())


if __name__ == "__main__":
    unittest.main()
