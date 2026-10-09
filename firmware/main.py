import asyncio
import json
import sys
import time

try:
    import uselect
except ImportError:
    uselect = None

from config import DEFAULTS, detector_cfg, load_config, sanitize, save_config
from detector import Detector, remain_s
from ir_input import is_present, make_ir_pin
from motor import I_OVERCURRENT_A, CrushMotor, MotorCurrent
from servo_ctrl import PRESS_HOLD_S, SERVO_MOVE_S, FlushServo
from bench import Bench
from web import AP_IP, WebServer, start_ap, stop_ap


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
        self.servo = FlushServo(
            release_deg=self.cfg["release_deg"],
            press_deg=self.cfg["press_deg"],
        )
        self.crush = CrushMotor(direction=self.cfg.get("crush_dir", "fwd"))
        self.current = MotorCurrent()
        self.ir = make_ir_pin()
        self.bench = Bench(self.servo, self.crush, self.current, self.ir)
        self.engineer_mode = False

    def enter_engineer(self):
        self.engineer_mode = True

    def leave_engineer(self):
        was = self.engineer_mode
        self.engineer_mode = False
        self.bench.idle_outputs()
        if was:
            self.detector.end_flush(time.ticks_ms())
            self._flushing = False
            self.flush_phase = ""
            self._wait_ms = 0

    def bench_cmd(self, line):
        cmd = (line or "").strip().split()
        name = cmd[0].upper() if cmd else ""
        if name in ("ENG", "ENGINEER", "BENCH"):
            self.enter_engineer()
            return "OK ENGINEER"
        if name in ("CUST", "CUSTOMER"):
            self.leave_engineer()
            return "OK CUSTOMER"
        if name == "MODE":
            return "MODE engineer" if self.engineer_mode else "MODE customer"
        if name == "PING":
            return "PONG"
        if name == "SERVOCFG" and len(cmd) >= 3:
            self.enter_engineer()
            return self.set_servo_angles(cmd[1], cmd[2], save=True, move_home=True)
        if name == "HOME" and len(cmd) >= 2:
            self.enter_engineer()
            return self.set_servo_angles(cmd[1], self.cfg["press_deg"], save=True, move_home=True)
        if name == "PRESSDEG" and len(cmd) >= 2:
            self.enter_engineer()
            return self.set_servo_angles(self.cfg["release_deg"], cmd[1], save=True, move_home=False)
        if name == "SAVE":
            self.cfg = save_config(self.cfg)
            return "OK SAVE release={:.1f} press={:.1f} crush={}".format(
                self.cfg["release_deg"], self.cfg["press_deg"], self.cfg["crush_dir"]
            )
        if name == "CRUSHDIR" and len(cmd) >= 2:
            self.enter_engineer()
            return self.set_crush_dir(cmd[1], save=True)
        hardware = name in (
            "SERVO",
            "PRESS",
            "RELEASE",
            "FWD",
            "REV",
            "STOP",
            "CRUSH",
        )
        if hardware and not self.engineer_mode:
            self.enter_engineer()
        return self.bench.handle(line)

    def set_servo_angles(self, release_deg, press_deg, save=True, move_home=False):
        cfg = dict(self.cfg)
        cfg["release_deg"] = release_deg
        cfg["press_deg"] = press_deg
        if save:
            self.cfg = save_config(cfg)
        else:
            self.cfg = sanitize(cfg)
        self.servo.set_limits(self.cfg["release_deg"], self.cfg["press_deg"])
        if move_home:
            self.servo.release()
        return "OK SERVOCFG release={:.1f} press={:.1f}".format(
            self.cfg["release_deg"], self.cfg["press_deg"]
        )

    def set_crush_dir(self, direction, save=True):
        cfg = dict(self.cfg)
        cfg["crush_dir"] = direction
        if save:
            self.cfg = save_config(cfg)
        else:
            self.cfg = sanitize(cfg)
        self.crush.set_direction(self.cfg["crush_dir"])
        if self.crush.is_on():
            self.crush.on()
        return "OK CRUSHDIR {}".format(self.cfg["crush_dir"])

    def engineer_status(self):
        snap = self.bench.snapshot()
        snap["mode"] = "engineer" if self.engineer_mode else "customer"
        snap["error"] = self.error
        snap["release_deg"] = float(self.cfg["release_deg"])
        snap["press_deg"] = float(self.cfg["press_deg"])
        snap["crush_dir"] = self.cfg.get("crush_dir", "fwd")
        return snap

    def engineer_status_json(self):
        st = self.engineer_status()
        st["trip"] = st.get("trip") is not None
        return json.dumps(st)

    def status(self):
        timeout_ms = int(self.cfg["wifi_timeout_s"]) * 1000
        elapsed = time.ticks_diff(time.ticks_ms(), self._boot_ms)
        remain_s = (timeout_ms - elapsed) // 1000
        if remain_s < 0:
            remain_s = 0
        if self.engineer_mode:
            remain_s = int(self.cfg["wifi_timeout_s"])
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
            "mode": "engineer" if self.engineer_mode else "customer",
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
            "crush_s",
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
        cfg["release_deg"] = self.cfg.get("release_deg", DEFAULTS["release_deg"])
        cfg["press_deg"] = self.cfg.get("press_deg", DEFAULTS["press_deg"])
        cfg["crush_dir"] = self.cfg.get("crush_dir", DEFAULTS["crush_dir"])
        self.cfg = save_config(cfg)
        self.detector.cfg = detector_cfg(self.cfg)
        self.servo.set_limits(self.cfg["release_deg"], self.cfg["press_deg"])
        self.crush.set_direction(self.cfg["crush_dir"])

    async def _sleep_flush(self, seconds):
        end = time.ticks_add(time.ticks_ms(), int(float(seconds) * 1000))
        while time.ticks_diff(end, time.ticks_ms()) > 0:
            if self.engineer_mode:
                return False
            if self.crush.is_on():
                try:
                    _v, amps, _raw = self.current.read(8)
                    if amps >= I_OVERCURRENT_A:
                        self.crush.off()
                        self.error = "crush overcurrent {:.2f}A".format(amps)
                except Exception:
                    pass
            remain = time.ticks_diff(end, time.ticks_ms())
            await asyncio.sleep_ms(min(80, max(10, remain)))
        return True

    async def flush(self):
        async with self._flush_lock:
            self._flushing = True
            try:
                n = int(self.cfg["flush_count"])
                interval = float(self.cfg["flush_interval_s"])
                crush_s = float(self.cfg.get("crush_s", 15))
                self.crush.set_direction(self.cfg.get("crush_dir", "fwd"))
                for i in range(n):
                    if self.engineer_mode:
                        break
                    self.flush_phase = "flushing"
                    self._begin_wait(SERVO_MOVE_S + PRESS_HOLD_S + SERVO_MOVE_S)
                    self.servo.press()
                    if not await self._sleep_flush(SERVO_MOVE_S + PRESS_HOLD_S):
                        break
                    self.servo.release()
                    if not await self._sleep_flush(SERVO_MOVE_S):
                        break
                    if crush_s > 0:
                        self.flush_phase = "crushing"
                        self._begin_wait(crush_s)
                        self.crush.on()
                        ok = await self._sleep_flush(crush_s)
                        self.crush.off()
                        if not ok:
                            break
                    if i < n - 1:
                        self.flush_phase = "refill"
                        self._begin_wait(interval)
                        if not await self._sleep_flush(interval):
                            break
            finally:
                self.crush.off()
                if not self.engineer_mode:
                    self.servo.release()
                self.flush_phase = ""
                self._wait_ms = 0
                self.detector.end_flush(time.ticks_ms())
                self._flushing = False

    async def sensor_loop(self):
        await asyncio.sleep_ms(200)
        sample_ms = int(self.cfg["sample_ms"])
        while True:
            if not self._flushing and not self.engineer_mode:
                try:
                    present = is_present(self.ir.value())
                    self.ir_present = present
                    self.error = ""
                    event = self.detector.tick(present, time.ticks_ms())
                    if event == "start_flush":
                        await self.flush()
                except Exception as exc:
                    self.error = str(exc)
                    self.servo.release()
            elif self.engineer_mode:
                try:
                    self.ir_present = is_present(self.ir.value())
                    self.error = ""
                except Exception as exc:
                    self.error = str(exc)
            await asyncio.sleep_ms(sample_ms)

    def _serial_reply(self, line):
        sys.stdout.write(line + "\n")
        try:
            sys.stdout.flush()
        except AttributeError:
            pass

    def _serial_feed(self, buf, chunk):
        buf += chunk.replace("\r\n", "\n").replace("\r", "\n")
        while "\n" in buf:
            line, buf = buf.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                reply = self.bench_cmd(line)
                if reply:
                    self._serial_reply(reply)
            except Exception as exc:
                self._serial_reply("ERR " + str(exc))
        return buf

    async def serial_loop(self):
        # USB 串口 read 可能阻塞整个 asyncio，必须先让出 CPU，等热点起来后再读
        while not self.wifi_on:
            await asyncio.sleep_ms(50)
        await asyncio.sleep_ms(300)
        poll = None
        if uselect is not None:
            try:
                poll = uselect.poll()
                poll.register(sys.stdin, uselect.POLLIN)
            except Exception:
                poll = None
        buf = ""
        while True:
            await asyncio.sleep_ms(40)
            if poll is None:
                continue
            try:
                ready = poll.poll(0)
            except Exception:
                ready = []
            if not ready:
                continue
            try:
                chunk = sys.stdin.read(1)
            except Exception:
                chunk = ""
            if chunk:
                buf = self._serial_feed(buf, chunk)

    async def wifi_loop(self):
        if not self.wifi_on:
            _ap, self.ssid = start_ap()
            self.wifi_on = True
            print("AP", self.ssid, "http://%s  engineer http://%s/test" % (AP_IP, AP_IP))
        server = WebServer(self)
        await server.start()
        timeout_ms = int(self.cfg["wifi_timeout_s"]) * 1000
        while True:
            if self.engineer_mode:
                await asyncio.sleep(1)
                continue
            if time.ticks_diff(time.ticks_ms(), self._boot_ms) >= timeout_ms:
                break
            await asyncio.sleep(1)
        print("WiFi timeout, stopping AP")
        server.close()
        stop_ap()
        self.wifi_on = False


async def main():
    try:
        ap, ssid = start_ap()
        print("AP", ssid, "http://%s  engineer http://%s/test" % (AP_IP, AP_IP))
    except Exception as exc:
        print("ap fail", exc)
        ap, ssid = None, ""
    app = App()
    if ap is not None:
        app.ssid = ssid
        app.wifi_on = True
    await asyncio.gather(app.sensor_loop(), app.wifi_loop(), app.serial_loop())


try:
    asyncio.run(main())
except Exception as exc:
    print("fatal", exc)
    raise
