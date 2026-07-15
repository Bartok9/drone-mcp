"""Unit tests for TELLO_SOCKET_TIMEOUT resolution (no UDP bind)."""
import os
import unittest

import tello_mcp


class TestLoadSocketTimeout(unittest.TestCase):
    def setUp(self):
        self._prev = os.environ.pop("TELLO_SOCKET_TIMEOUT", None)

    def tearDown(self):
        if self._prev is None:
            os.environ.pop("TELLO_SOCKET_TIMEOUT", None)
        else:
            os.environ["TELLO_SOCKET_TIMEOUT"] = self._prev

    def test_default(self):
        self.assertEqual(tello_mcp.load_socket_timeout(), 10.0)

    def test_valid(self):
        os.environ["TELLO_SOCKET_TIMEOUT"] = "5.5"
        self.assertEqual(tello_mcp.load_socket_timeout(), 5.5)

    def test_reject_zero_negative(self):
        for raw in ("0", "-1", "0.05"):
            os.environ["TELLO_SOCKET_TIMEOUT"] = raw
            with self.assertRaises(ValueError):
                tello_mcp.load_socket_timeout()

    def test_reject_too_large(self):
        os.environ["TELLO_SOCKET_TIMEOUT"] = "121"
        with self.assertRaises(ValueError):
            tello_mcp.load_socket_timeout()

    def test_reject_non_numeric(self):
        os.environ["TELLO_SOCKET_TIMEOUT"] = "10abc"
        with self.assertRaises(ValueError):
            tello_mcp.load_socket_timeout()

    def test_reject_nan_inf(self):
        for raw in ("nan", "inf", "-inf"):
            os.environ["TELLO_SOCKET_TIMEOUT"] = raw
            with self.assertRaises(ValueError):
                tello_mcp.load_socket_timeout()

    def test_boundary_max(self):
        os.environ["TELLO_SOCKET_TIMEOUT"] = "120"
        self.assertEqual(tello_mcp.load_socket_timeout(), 120.0)

    def test_boundary_min(self):
        os.environ["TELLO_SOCKET_TIMEOUT"] = "0.1"
        self.assertEqual(tello_mcp.load_socket_timeout(), 0.1)


if __name__ == "__main__":
    unittest.main()
