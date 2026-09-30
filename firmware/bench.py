"""
硬件调试：与 MicroPython 控制台同一串口，用 sys.stdin.readline 收命令。
"""

import sys
import time

from machine import Pin

from ir_input import (
    format_ir_line,
    is_present,
    make_ir_pin,
    read_adc,
    raw_value,
    scan_gpio,
)
from motor import CrushMotor, PressMotor
from pins import PIN_IR


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


def _ir_report(ir_gpio, ir_pin):
    raw = raw_value(ir_pin)
    adc = read_adc(ir_gpio)
    present = is_present(raw)
    return format_ir_line(ir_gpio, raw, adc, present)


def _handle(state, cmd, args):
    press = state["press"]
    crush = state["crush"]
    ir_gpio = state["ir_gpio"]
    ir_pin = state["ir_pin"]

    if cmd == "PING":
        _reply("PONG")
    elif cmd == "IR":
        _reply(_ir_report(ir_gpio, ir_pin))
    elif cmd == "IRSCAN":
        _reply("SCAN " + scan_gpio())
    elif cmd == "IRPIN" and len(args) == 1:
        ir_gpio = int(args[0])
        ir_pin = make_ir_pin(ir_gpio)
        state["ir_gpio"] = ir_gpio
        state["ir_pin"] = ir_pin
        _reply("OK IRPIN " + _ir_report(ir_gpio, ir_pin))
    elif cmd == "PWM" and len(args) == 1:
        press.set_duty_pct(float(args[0]))
        _reply(
            "PWM pct={:.2f} est_v={:.2f}".format(
                press.duty_pct(), 24.0 * press.duty_pct() / 100.0
            )
        )
    elif cmd == "FWD":
        press.forward()
        _reply("OK FWD")
    elif cmd == "REV":
        press.reverse()
        _reply("OK REV")
    elif cmd == "STOP":
        press.stop()
        _reply("OK STOP")
    elif cmd == "CRUSH" and len(args) == 1:
        if args[0] in ("1", "ON", "on"):
            crush.on()
            _reply("OK CRUSH ON")
        else:
            crush.off()
            _reply("OK CRUSH OFF")
    elif cmd == "STATUS":
        _reply(
            "pwm={:.2f} ir={} crush={}".format(
                press.duty_pct(), raw_value(ir_pin), crush.out.value()
            )
        )
    else:
        _reply("ERR unknown")


def run_bench():
    ir_gpio = PIN_IR
    ir_pin = make_ir_pin(ir_gpio)
    state = {
        "press": PressMotor(),
        "crush": CrushMotor(),
        "ir_gpio": ir_gpio,
        "ir_pin": ir_pin,
    }

    _reply(
        "BENCH OK IR={} (no pull-up) IREF=10 H=11 L=12 CRUSH=9 cmds: IR IRSCAN IRPIN <gpio>".format(
            ir_gpio
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
