"""
工程师测试：串口命令与网页 /test 共用同一套硬件动作。
上电默认客户模式；工程师模式仅在内存中，断电后回到客户模式。
"""

import sys
import time

from ir_input import format_ir_line, is_present, make_ir_pin, raw_value
from motor import I_GAIN, I_OVERCURRENT_A, R_SENSE_OHM, CrushMotor, MotorCurrent
from pins import PIN_CRUSH_IN1, PIN_CRUSH_IN2, PIN_IADC, PIN_IR, PIN_SERVO
from servo_ctrl import FlushServo


def _parse_cmd(line):
    line = (line or "").strip()
    if not line:
        return None, None
    parts = line.split()
    return parts[0].upper(), parts[1:]


class Bench:
    def __init__(self, servo=None, crush=None, current=None, ir_pin=None):
        self.servo = servo or FlushServo()
        self.crush = crush or CrushMotor()
        self.current = current or MotorCurrent()
        self.ir_pin = ir_pin if ir_pin is not None else make_ir_pin()

    def ir_report(self):
        raw = raw_value(self.ir_pin)
        present = is_present(raw)
        return format_ir_line(raw, present)

    def current_sample(self):
        try:
            v, a, raw = self.current.read()
        except Exception as exc:
            line = "I err={}".format(exc)
            return line, None, 0.0, 0.0, 0
        line = "I gpio={} raw={} v={:.3f} a={:.2f}".format(
            self.current.pin_num, raw, v, a
        )
        tripped = None
        if self.crush.is_on() and a >= I_OVERCURRENT_A:
            self.crush.off()
            tripped = a
        return line, tripped, v, a, raw

    def snapshot(self):
        raw = raw_value(self.ir_pin)
        i_line, tripped, v, a, i_raw = self.current_sample()
        return {
            "ir_raw": raw,
            "ir_present": bool(is_present(raw)),
            "servo": float(self.servo.angle),
            "crush": 1 if self.crush.is_on() else 0,
            "i_v": v,
            "i_a": a,
            "i_raw": i_raw,
            "i_line": i_line,
            "trip": tripped,
            "release_deg": float(self.servo.release_deg),
            "press_deg": float(self.servo.press_deg),
            "crush_dir": getattr(self.crush, "direction", "fwd"),
        }

    def idle_outputs(self):
        self.crush.off()
        self.servo.release()

    def handle(self, line):
        cmd, args = _parse_cmd(line)
        if cmd is None:
            return ""
        if cmd == "PING":
            return "PONG"
        if cmd in ("ENG", "ENGINEER", "BENCH"):
            return "OK ENGINEER"
        if cmd in ("CUST", "CUSTOMER"):
            return "OK CUSTOMER"
        if cmd == "MODE":
            return "MODE"
        if cmd == "IR":
            return self.ir_report()
        if cmd == "SERVO" and len(args) == 1:
            self.servo.set_angle(float(args[0]))
            return "OK SERVO {:.1f}".format(self.servo.angle)
        if cmd == "PRESS":
            self.servo.press()
            return "OK PRESS {:.1f}".format(self.servo.angle)
        if cmd == "RELEASE":
            self.servo.release()
            return "OK RELEASE {:.1f}".format(self.servo.angle)
        if cmd == "FWD":
            self.crush.forward()
            return "OK FWD"
        if cmd == "REV":
            self.crush.reverse()
            return "OK REV"
        if cmd == "STOP":
            self.crush.off()
            return "OK STOP"
        if cmd == "CRUSH" and len(args) == 1:
            if args[0] in ("1", "ON", "on"):
                self.crush.on()
                return "OK CRUSH ON"
            self.crush.off()
            return "OK CRUSH OFF"
        if cmd in ("I", "CURRENT"):
            line, tripped, _v, _a, _raw = self.current_sample()
            if tripped is not None:
                return line + " TRIP a={:.2f}".format(tripped)
            return line
        if cmd == "STATUS":
            snap = self.snapshot()
            line = "servo={:.1f} ir={} crush={} {}".format(
                snap["servo"],
                snap["ir_raw"],
                snap["crush"],
                snap["i_line"],
            )
            if snap["trip"] is not None:
                line += " TRIP"
            return line
        return "ERR unknown"


def _reply(line):
    sys.stdout.write(line + "\n")
    try:
        sys.stdout.flush()
    except AttributeError:
        pass


def run_bench():
    bench = Bench()
    _reply(
        "BENCH OK IR={} SERVO={} CRUSH={} {} IADC={} Rs={} G={} cmds: ENG CUST IR SERVO PRESS RELEASE CRUSH I".format(
            PIN_IR,
            PIN_SERVO,
            PIN_CRUSH_IN1,
            PIN_CRUSH_IN2,
            PIN_IADC,
            R_SENSE_OHM,
            I_GAIN,
        )
    )
    while True:
        line = sys.stdin.readline()
        if not line:
            time.sleep_ms(20)
            continue
        cmd, _args = _parse_cmd(line)
        if cmd is None:
            continue
        try:
            reply = bench.handle(line)
            if reply:
                _reply(reply)
        except Exception as exc:
            _reply("ERR " + str(exc))


if __name__ == "__main__":
    run_bench()
