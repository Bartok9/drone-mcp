"""Unit tests for Tello MCP command allowlists (no real UDP)."""
import unittest

import tello_mcp as tm


class TestValidateMove(unittest.TestCase):
    def test_ok(self):
        d, n = tm.validate_move_arguments({"direction": "forward", "distance": 50})
        self.assertEqual((d, n), ("forward", 50))

    def test_bad_direction_injection(self):
        with self.assertRaises(ValueError):
            tm.validate_move_arguments({"direction": "forward; rm -rf /", "distance": 50})

    def test_direction_not_enum(self):
        with self.assertRaises(ValueError):
            tm.validate_move_arguments({"direction": "flip", "distance": 50})

    def test_distance_range(self):
        with self.assertRaises(ValueError):
            tm.validate_move_arguments({"direction": "up", "distance": 10})
        with self.assertRaises(ValueError):
            tm.validate_move_arguments({"direction": "up", "distance": 999})

    def test_bool_not_int(self):
        with self.assertRaises(ValueError):
            tm.validate_move_arguments({"direction": "up", "distance": True})

    def test_missing(self):
        with self.assertRaises(ValueError):
            tm.validate_move_arguments({"direction": "up"})


class TestValidateRotate(unittest.TestCase):
    def test_ok(self):
        d, n = tm.validate_rotate_arguments({"direction": "cw", "degrees": 90})
        self.assertEqual((d, n), ("cw", 90))

    def test_bad_dir(self):
        with self.assertRaises(ValueError):
            tm.validate_rotate_arguments({"direction": "left", "degrees": 90})

    def test_degrees_range(self):
        with self.assertRaises(ValueError):
            tm.validate_rotate_arguments({"direction": "ccw", "degrees": 0})
        with self.assertRaises(ValueError):
            tm.validate_rotate_arguments({"direction": "ccw", "degrees": 4000})


class TestSendCommandAllowlist(unittest.IsolatedAsyncioTestCase):
    async def test_refuse_unknown_token(self):
        # Minimal fake: bind skipped by building object without __init__
        t = object.__new__(tm.Tello)
        t.tello_address = ("127.0.0.1", 8889)
        t.sock = None
        with self.assertRaises(ValueError):
            await t.send_command("reboot")


if __name__ == "__main__":
    unittest.main()
