"""Reject bool/float masquerading as int for move/rotate args (no UDP)."""
import unittest

import tello_mcp as tm


class TestAssertStrictInt(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(tm.assert_strict_int("Distance", 20, 20, 500), 20)
        self.assertEqual(tm.assert_strict_int("Distance", 500, 20, 500), 500)
        self.assertEqual(tm.assert_strict_int("Degrees", 1, 1, 3600), 1)

    def test_bool_rejected(self):
        with self.assertRaises(ValueError):
            tm.assert_strict_int("Distance", True, 20, 500)
        with self.assertRaises(ValueError):
            tm.assert_strict_int("Degrees", False, 1, 3600)

    def test_float_rejected(self):
        with self.assertRaises(ValueError):
            tm.assert_strict_int("Distance", 20.0, 20, 500)

    def test_str_rejected(self):
        with self.assertRaises(ValueError):
            tm.assert_strict_int("Distance", "20", 20, 500)

    def test_range(self):
        with self.assertRaises(ValueError):
            tm.assert_strict_int("Distance", 19, 20, 500)
        with self.assertRaises(ValueError):
            tm.assert_strict_int("Distance", 501, 20, 500)


if __name__ == "__main__":
    unittest.main()
