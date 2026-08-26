import unittest

from detector import IDLE, OCCUPIED, LEAVING, FLUSHING, Detector


def cfg(**kwargs):
    data = {"leave_delay_s": 15, "trigger_mode": "instant", "trigger_hold_s": 1}
    data.update(kwargs)
    return data


class DetectorTest(unittest.TestCase):
    def test_boot_high_stays_idle(self):
        d = Detector(cfg())
        self.assertIsNone(d.tick(False, 0))
        self.assertEqual(d.state, IDLE)

    def test_low_occupies_immediately(self):
        d = Detector(cfg())
        d.tick(True, 0)
        self.assertEqual(d.state, OCCUPIED)
        self.assertEqual(d.occupied_elapsed_s(0), 0)
        self.assertEqual(d.occupied_elapsed_s(2500), 2)

    def test_leave_starts_countdown(self):
        d = Detector(cfg())
        d.tick(True, 0)
        self.assertIsNone(d.tick(False, 100))
        self.assertEqual(d.state, LEAVING)
        self.assertEqual(d.leave_remain_s(100), 15)
        self.assertEqual(d.leave_remain_s(100 + 14000), 1)

    def test_leave_delay_emits_flush(self):
        d = Detector(cfg())
        d.tick(True, 0)
        d.tick(False, 100)
        event = d.tick(False, 100 + 15000)
        self.assertEqual(event, "start_flush")
        self.assertEqual(d.state, FLUSHING)

    def test_return_during_leave_does_not_cancel(self):
        d = Detector(cfg())
        d.tick(True, 0)
        d.tick(False, 100)
        self.assertIsNone(d.tick(True, 200))
        self.assertEqual(d.state, LEAVING)
        event = d.tick(True, 100 + 15000)
        self.assertEqual(event, "start_flush")
        self.assertEqual(d.state, FLUSHING)

    def test_flushing_ignores_sensor(self):
        d = Detector(cfg())
        d.tick(True, 0)
        d.tick(False, 100)
        d.tick(False, 15100)
        self.assertEqual(d.state, FLUSHING)
        d.tick(True, 16000)
        self.assertEqual(d.state, FLUSHING)

    def test_end_flush_goes_idle(self):
        d = Detector(cfg())
        d.tick(True, 0)
        d.tick(False, 100)
        d.tick(False, 15100)
        d.end_flush(20000)
        self.assertEqual(d.state, IDLE)
        d.tick(True, 20100)
        self.assertEqual(d.state, OCCUPIED)

    def test_hold_needs_continuous_presence(self):
        d = Detector(cfg(trigger_mode="hold", trigger_hold_s=1))
        d.tick(True, 0)
        self.assertEqual(d.state, IDLE)
        self.assertEqual(d.hold_remain_s(0), 1)
        d.tick(True, 500)
        self.assertEqual(d.state, IDLE)
        d.tick(False, 600)
        self.assertEqual(d.hold_remain_s(600), 0)
        d.tick(True, 700)
        self.assertEqual(d.state, IDLE)
        d.tick(True, 1700)
        self.assertEqual(d.state, OCCUPIED)

    def test_leave_ignores_ir_until_flush_done(self):
        d = Detector(cfg(trigger_mode="hold", trigger_hold_s=1, leave_delay_s=15))
        d.tick(True, 0)
        d.tick(True, 1000)
        d.tick(False, 1100)
        self.assertEqual(d.state, LEAVING)
        d.tick(True, 1200)
        self.assertEqual(d.state, LEAVING)
        d.tick(True, 2200)
        self.assertEqual(d.state, LEAVING)

    def test_hold_1_5_not_rounded_to_2(self):
        d = Detector(cfg(trigger_mode="hold", trigger_hold_s=1.5))
        d.tick(True, 0)
        self.assertEqual(d.hold_remain_s(0), 1.5)
        self.assertEqual(d.hold_remain_s(400), 1.1)


if __name__ == "__main__":
    unittest.main()
