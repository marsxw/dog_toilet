import asyncio
import json
import time
from machine import Pin

from config import DEFAULTS, detector_cfg, load_config, save_config
from detector import Detector, remain_s
from motor import IR_PIN, MOTOR_PAUSE_S, MOTOR_RUN_S, Motor
from web import WebServer, start_ap, stop_ap


class App:
    def __init__(self):
        self.cfg = load_config()
        self.error = ""
        self.ssid = ""
        self.wifi_on = False
        self.ir_present = False
        self._boot_ms = time.ticks_ms()
        self.detector = Detector(detector_cfg(self.cfg))
        self._flushing = False
        self._flush_lock = asyncio.Lock()
        self.flush_phase = ""
        self._wait_start_ms = 0
        self._wait_ms = 0
        self.motor = Motor()
        self.ir = Pin(IR_PIN, Pin.IN, Pin.PULL_UP)

    def status(self):
        timeout_ms = int(self.cfg["wifi_timeout_s"]) * 1000
        elapsed = time.ticks_diff(time.ticks_ms(), self._boot_ms)
        remain_s = (timeout_ms - elapsed) // 1000
        if remain_s < 0:
            remain_s = 0
        now = time.ticks_ms()
        state = self.detector.state
        wait_s = 0
        if state == "leaving":
            wait_s = self.detector.leave_remain_s(now)
        elif state == "flushing":
            wait_s = self.wait_remain_s()
        return {
            "state": state,
            "ir_present": self.ir_present,
            "leave_remain_s": self.detector.leave_remain_s(now),
            "hold_remain_s": self.detector.hold_remain_s(now),
            "flush_phase": self.flush_phase,
            "wait_s": wait_s,
            "error": self.error,
            "wifi_remain_s": remain_s,
        }

    def wait_remain_s(self):
        if self._wait_ms <= 0:
            return 0
        elapsed = time.ticks_diff(time.ticks_ms(), self._wait_start_ms)
        remain_ms = self._wait_ms - elapsed
        return remain_s(remain_ms)

    def _begin_wait(self, seconds):
        self._wait_start_ms = time.ticks_ms()
        self._wait_ms = int(float(seconds) * 1000)

    def status_json(self):
        return json.dumps(self.status())

    def apply_form(self, form):
        cfg = dict(self.cfg)
        keys = [
            "leave_delay_s",
            "trigger_mode",
            "trigger_hold_s",
            "flush_count",
            "flush_interval_s",
            "lang",
        ]
        for key in keys:
            if key in form and form[key] != "":
                cfg[key] = form[key]
        self.cfg = save_config(cfg)
        self.detector.cfg = detector_cfg(self.cfg)

    def reset_params(self):
        lang = self.cfg.get("lang") or "zh"
        cfg = dict(DEFAULTS)
        cfg["lang"] = lang
        self.cfg = save_config(cfg)
        self.detector.cfg = detector_cfg(self.cfg)

    async def flush(self):
        async with self._flush_lock:
            self._flushing = True
            try:
                n = int(self.cfg["flush_count"])
                interval = float(self.cfg["flush_interval_s"])
                for i in range(n):
                    self.flush_phase = "flushing"
                    self._begin_wait(MOTOR_RUN_S + MOTOR_PAUSE_S + MOTOR_RUN_S)
                    self.motor.down()
                    await asyncio.sleep(MOTOR_RUN_S)
                    self.motor.stop()
                    await asyncio.sleep(MOTOR_PAUSE_S)
                    self.motor.up()
                    await asyncio.sleep(MOTOR_RUN_S)
                    self.motor.stop()
                    if i < n - 1:
                        self.flush_phase = "refill"
                        self._begin_wait(interval)
                        await asyncio.sleep(interval)
            finally:
                self.motor.stop()
                self.flush_phase = ""
                self._wait_ms = 0
                self.detector.end_flush(time.ticks_ms())
                self._flushing = False

    async def sensor_loop(self):
        await asyncio.sleep_ms(200)
        sample_ms = int(self.cfg["sample_ms"])
        while True:
            if not self._flushing:
                try:
                    present = self.ir.value() == 0
                    self.ir_present = present
                    self.error = ""
                    event = self.detector.tick(present, time.ticks_ms())
                    if event == "start_flush":
                        await self.flush()
                except Exception as exc:
                    self.error = str(exc)
                    self.motor.stop()
            await asyncio.sleep_ms(sample_ms)

    async def wifi_loop(self):
        await asyncio.sleep(2)
        ap, self.ssid = start_ap()
        self.wifi_on = True
        print("AP", self.ssid, "http://192.168.4.1")
        server = WebServer(self)
        await server.start()
        timeout_ms = int(self.cfg["wifi_timeout_s"]) * 1000
        while time.ticks_diff(time.ticks_ms(), self._boot_ms) < timeout_ms:
            await asyncio.sleep(1)
        print("WiFi timeout, stopping AP")
        server.close()
        stop_ap()
        self.wifi_on = False


async def main():
    app = App()
    await asyncio.gather(app.sensor_loop(), app.wifi_loop())


try:
    asyncio.run(main())
except Exception as exc:
    print("fatal", exc)
    raise
