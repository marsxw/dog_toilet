from machine import Pin

from pins import PIN_IR

# GPIO1 数字输入。触发（宠物在）= 低电平；未触发 = 高电平。不要内部上拉。
IR_ACTIVE_LOW = True


def make_ir_pin():
    return Pin(PIN_IR, Pin.IN)


def raw_value(ir_pin):
    return int(ir_pin.value())


def is_present(raw, active_low=None):
    if active_low is None:
        active_low = IR_ACTIVE_LOW
    if active_low:
        return raw == 0
    return raw == 1


def format_ir_line(raw, present):
    return "IR gpio={} raw={} present={}".format(PIN_IR, raw, 1 if present else 0)
