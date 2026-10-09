import unittest

from config import detector_cfg, sanitize


class ConfigTest(unittest.TestCase):
    def test_defaults(self):
        cfg = sanitize({})
        self.assertEqual(cfg["leave_delay_s"], 15)
        self.assertEqual(cfg["trigger_mode"], "hold")
        self.assertEqual(cfg["trigger_hold_s"], 1)
        self.assertEqual(cfg["flush_count"], 1)
        self.assertEqual(cfg["flush_interval_s"], 30)
        self.assertEqual(detector_cfg(cfg)["leave_delay_s"], 15)
        self.assertEqual(detector_cfg(cfg)["trigger_mode"], "hold")
        self.assertEqual(cfg["release_deg"], 0)
        self.assertEqual(cfg["press_deg"], 70)
        self.assertEqual(cfg["crush_s"], 15)

    def test_servo_angles_clamped(self):
        cfg = sanitize({"release_deg": -5, "press_deg": 200})
        self.assertEqual(cfg["release_deg"], 0)
        self.assertEqual(cfg["press_deg"], 180)

    def test_crush_dir(self):
        self.assertEqual(sanitize({})["crush_dir"], "fwd")
        self.assertEqual(sanitize({"crush_dir": "rev"})["crush_dir"], "rev")
        self.assertEqual(sanitize({"crush_dir": "reverse"})["crush_dir"], "rev")

    def test_wifi_password_removed(self):
        cfg = sanitize({"wifi_password": "toilet123"})
        self.assertNotIn("wifi_password", cfg)

    def test_bench_mode_not_persisted(self):
        cfg = sanitize({"bench_mode": True})
        self.assertNotIn("bench_mode", cfg)

    def test_lang_defaults_zh(self):
        self.assertEqual(sanitize({})["lang"], "zh")
        self.assertEqual(sanitize({"lang": "en"})["lang"], "en")
        self.assertEqual(sanitize({"lang": "EN-US"})["lang"], "en")

    def test_leave_delay_clamped(self):
        self.assertEqual(sanitize({"leave_delay_s": 999})["leave_delay_s"], 300)
        self.assertEqual(sanitize({"leave_delay_s": 0})["leave_delay_s"], 0.1)


    def test_seconds_allow_decimal(self):
        self.assertEqual(sanitize({"leave_delay_s": 1.5})["leave_delay_s"], 1.5)
        self.assertEqual(sanitize({"flush_interval_s": 2.5})["flush_interval_s"], 2.5)
        self.assertEqual(sanitize({"flush_count": 2.8})["flush_count"], 2)


if __name__ == "__main__":
    unittest.main()
