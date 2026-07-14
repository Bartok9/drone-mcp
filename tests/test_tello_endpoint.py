"""Unit tests for TELLO_IP / TELLO_CMD_PORT resolution (no UDP)."""
import os
import unittest
from unittest.mock import patch

import tello_mcp as tm


class TestLoadTelloEndpoint(unittest.TestCase):
    def test_defaults(self):
        with patch.dict(os.environ, {}, clear=True):
            # clear=True drops all env; helper should still default
            host, port = tm.load_tello_endpoint()
        self.assertEqual(host, "192.168.10.1")
        self.assertEqual(port, 8889)

    def test_env_override(self):
        with patch.dict(
            os.environ, {"TELLO_IP": "10.0.0.5", "TELLO_CMD_PORT": "9999"}, clear=False
        ):
            host, port = tm.load_tello_endpoint()
        self.assertEqual(host, "10.0.0.5")
        self.assertEqual(port, 9999)

    def test_strip_ip(self):
        host, port = tm.load_tello_endpoint(ip="  192.168.1.1  ", port=8889)
        self.assertEqual(host, "192.168.1.1")
        self.assertEqual(port, 8889)

    def test_empty_ip_rejected(self):
        with self.assertRaises(ValueError):
            tm.load_tello_endpoint(ip="   ", port=8889)

    def test_bad_port_string(self):
        with self.assertRaises(ValueError):
            tm.load_tello_endpoint(ip="192.168.10.1", port="8889abc")

    def test_port_out_of_range(self):
        with self.assertRaises(ValueError):
            tm.load_tello_endpoint(ip="192.168.10.1", port=0)
        with self.assertRaises(ValueError):
            tm.load_tello_endpoint(ip="192.168.10.1", port=70000)

    def test_bool_port_rejected(self):
        with self.assertRaises(ValueError):
            tm.load_tello_endpoint(ip="192.168.10.1", port=True)


if __name__ == "__main__":
    unittest.main()
