"""
硬件调试：与 MicroPython 控制台同一串口，用 sys.stdin.readline 收命令。
"""

import sys
import time

from ir_input import format_ir_line, is_present, make_ir_pin, raw_value
from motor import I_GAIN, I_OVERCURRENT_A, R_SENSE_OHM, CrushMotor, MotorCurrent
from pins import PIN_CRUSH_IN1, PIN_CRUSH_IN2, PIN_IADC, PIN_IR, PIN_SERVO
from servo_ctrl import FlushServo


def _reply(line):
    sys.stdout.write(line + "\n")
    try:
        sys.stdout.flush()
    except AttributeError:
        pass


def _parse_cmd(line):
    line = line.strip()
    if not line:
        return None, None
    parts = line.split()
    return parts[0].upper(), parts[1:]


def _ir_report(ir_pin):
    raw = raw_value(ir_pin)
    present = is_present(raw)
    return format_ir_line(raw, present)


def _current_sample(state):
    v, a, raw = state["current"].read()
    line = "I gpio={} raw={} v={:.3f} a={:.2f}".format(
        state["current"].pin_num, raw, v, a
    )
    tripped = None
    if state["crush"].is_on() and a >= I_OVERCURRENT_A:
        state["crush"].off()
        tripped = a
    return line, tripped


def _handle(state, cmd, args):
    servo = state["servo"]
    crush = state["crush"]
    current = state["current"]
    ir_pin = state["ir_pin"]

    if cmd == "PING":
        _reply("PONG")
    elif cmd == "IR":
        _reply(_ir_report(ir_pin))
    elif cmd == "SERVO" and len(args) == 1:
        servo.set_angle(float(args[0]))
        _reply("OK SERVO {:.1f}".format(servo.angle))
    elif cmd == "PRESS":
        servo.press()
        _reply("OK PRESS {:.1f}".format(servo.angle))
    elif cmd == "RELEASE":
        servo.release()
        _reply("OK RELEASE {:.1f}".format(servo.angle))
    elif cmd == "FWD":
        crush.forward()
        _reply("OK FWD")
    elif cmd == "REV":
        crush.reverse()
        _reply("OK REV")
    elif cmd == "STOP":
        crush.off()
        _reply("OK STOP")
    elif cmd == "CRUSH" and len(args) == 1:
        if args[0] in ("1", "ON", "on"):
            crush.on()
            _reply("OK CRUSH ON")
        else:
            crush.off()
            _reply("OK CRUSH OFF")
    elif cmd == "I" or cmd == "CURRENT":
        line, tripped = _current_sample(state)
        if tripped is not None:
            _reply(line + " TRIP a={:.2f}".format(tripped))
        else:
            _reply(line)
    elif cmd == "STATUS":
        i_line, tripped = _current_sample(state)
        line = "servo={:.1f} ir={} crush={} {}".format(
            servo.angle,
            raw_value(ir_pin),
            1 if crush.is_on() else 0,
            i_line,
        )
        if tripped is not None:
            line += " TRIP"
        _reply(line)
    else:
        _reply("ERR unknown")


def run_bench():
    state = {
        "servo": FlushServo(),
        "crush": CrushMotor(),
        "current": MotorCurrent(),
        "ir_pin": make_ir_pin(),
    }

    _reply(
        "BENCH OK IR={} SERVO={} CRUSH={} {} IADC={} Rs={} G={} cmds: IR SERVO <deg> PRESS RELEASE CRUSH I".format(
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
        cmd, args = _parse_cmd(line)
        if cmd is None:
            continue
        try:
            _handle(state, cmd, args)
        except Exception as exc:
            _reply("ERR " + str(exc))


if __name__ == "__main__":
    run_bench()
