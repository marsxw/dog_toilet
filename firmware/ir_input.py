from machine import ADC, Pin

from pins import PIN_IR

# 原理图：24V 经 6.8k/1k 分压进 MCU，不要用内部上拉（会偏置、且易误判）
IR_ACTIVE_LOW = True

SCAN_GPIO = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    21,
    38,
    39,
    40,
    41,
    42,
    47,
    48,
)


def make_ir_pin(gpio=None):
    n = int(gpio if gpio is not None else PIN_IR)
    return Pin(n, Pin.IN)


def read_adc(gpio=None):
    n = int(gpio if gpio is not None else PIN_IR)
    try:
        adc = ADC(Pin(n))
        adc.atten(ADC.ATTN_11DB)
        return adc.read()
    except OSError:
        return -1


def raw_value(ir_pin):
    return int(ir_pin.value())


def is_present(raw, active_low=None):
    if active_low is None:
        active_low = IR_ACTIVE_LOW
    if active_low:
        return raw == 0
    return raw == 1


def format_ir_line(gpio, raw, adc, present):
    return "IR gpio={} raw={} adc={} present={}".format(gpio, raw, adc, 1 if present else 0)


def scan_gpio():
    parts = []
    for n in SCAN_GPIO:
        try:
            p = Pin(n, Pin.IN)
            parts.append("{}:{}".format(n, p.value()))
        except OSError:
            parts.append("{}:x".format(n))
    return " ".join(parts)
