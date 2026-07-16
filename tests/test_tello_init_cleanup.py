"""Tello.__init__ must close the UDP socket on connection failure after bind."""
import socket
import unittest
from unittest import mock

import tello_mcp


class TestTelloInitSocketCleanup(unittest.TestCase):
    def test_timeout_after_bind_closes_socket(self):
        sock = mock.Mock()
        sock.bind.return_value = None
        sock.settimeout.return_value = None
        sock.sendto.return_value = None
        sock.recvfrom.side_effect = socket.timeout()

        with mock.patch("tello_mcp.socket.socket", return_value=sock):
            with self.assertRaises(ConnectionError):
                tello_mcp.Tello()

        sock.close.assert_called()

    def test_non_ok_response_closes_socket(self):
        sock = mock.Mock()
        sock.bind.return_value = None
        sock.settimeout.return_value = None
        sock.sendto.return_value = None
        sock.recvfrom.return_value = (b"error", ("192.168.10.1", 8889))

        with mock.patch("tello_mcp.socket.socket", return_value=sock):
            with self.assertRaises(ConnectionError):
                tello_mcp.Tello()

        sock.close.assert_called()

    def test_successful_init_leaves_socket_open(self):
        sock = mock.Mock()
        sock.bind.return_value = None
        sock.settimeout.return_value = None
        sock.sendto.return_value = None
        sock.recvfrom.return_value = (b"ok", ("192.168.10.1", 8889))

        with mock.patch("tello_mcp.socket.socket", return_value=sock):
            drone = tello_mcp.Tello()

        sock.close.assert_not_called()
        drone.close()
        sock.close.assert_called()


if __name__ == "__main__":
    unittest.main()
