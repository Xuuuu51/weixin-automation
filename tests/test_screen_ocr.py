import unittest

from weixin_automation.ocr import normalize_recognized_lines
from weixin_automation.screen import choose_largest_window


class ScreenOcrTests(unittest.TestCase):
    def test_choose_largest_window_prefers_matching_pid_and_area(self):
        windows = [
            {"kCGWindowOwnerPID": 7, "kCGWindowBounds": {"Width": 500, "Height": 400}},
            {"kCGWindowOwnerPID": 9, "kCGWindowBounds": {"Width": 200, "Height": 100}},
            {"kCGWindowOwnerPID": 7, "kCGWindowBounds": {"Width": 100, "Height": 100}},
        ]

        self.assertEqual(choose_largest_window(windows, owner_pid=7), windows[0])

    def test_choose_largest_window_ignores_zero_sized_windows(self):
        windows = [
            {"kCGWindowOwnerPID": 7, "kCGWindowBounds": {"Width": 0, "Height": 400}},
            {"kCGWindowOwnerPID": 7, "kCGWindowBounds": {"Width": 200, "Height": 100}},
        ]

        self.assertEqual(choose_largest_window(windows, owner_pid=7), windows[1])

    def test_normalize_recognized_lines_drops_empty_lines_and_deduplicates(self):
        lines = ["  你好  ", "", "你好", "收到", "收到"]

        self.assertEqual(normalize_recognized_lines(lines), ["你好", "收到"])


if __name__ == "__main__":
    unittest.main()
