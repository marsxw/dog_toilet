from machine import ADC, Pin
import time

from pins import PIN_CRUSH_IN1, PIN_CRUSH_IN2, PIN_IADC, PIN_IR

IR_PIN = PIN_IR

# I = V_adc / (R_sense * gain) = V_adc / 1.05
R_SENSE_OHM = 0.1
I_GAIN = 10.5
I_OVERCURRENT_A = 4.0
I_SAMPLES = 32
I_TRIM = 6
I_EMA_ALPHA = 0.18


def adc_volts_to_amps(volts):
    denom = R_SENSE_OHM * I_GAIN
    if denom <= 0:
        return 0.0
    return float(volts) / denom


class MotorCurrent:
    def __init__(self, pin=PIN_IADC):
        self.pin_num = int(pin)
        self.adc = ADC(Pin(self.pin_num))
        self.adc.atten(ADC.ATTN_11DB)
        try:
            self.adc.width(ADC.WIDTH_12BIT)
        except (AttributeError, ValueError):
            pass
        self._ema_v = None

    def _read_volts_once(self):
        try:
            return self.adc.read_uv() / 1e6
        except AttributeError:
            return self.adc.read() * 3.3 / 4095.0

    def raw(self):
        return self.adc.read()

    def voltage(self):
        return self.read()[0]

    def amps(self, samples=I_SAMPLES):
        return self.read(samples)[1]

    def read(self, samples=I_SAMPLES):
        n = int(samples)
        if n < 1:
            n = 1
        vals = []
        for _ in range(n):
            vals.append(self._read_volts_once())
            time.sleep_us(40)
        vals.sort()
        trim = I_TRIM if n > I_TRIM * 2 + 4 else 0
        if trim:
            vals = vals[trim : n - trim]
        acc = 0.0
        for v in vals:
            acc += v
        burst = acc / len(vals)
        if self._ema_v is None:
            self._ema_v = burst
        else:
            self._ema_v = I_EMA_ALPHA * burst + (1.0 - I_EMA_ALPHA) * self._ema_v
        a = adc_volts_to_amps(self._ema_v)
        raw = int(self._ema_v / 3.3 * 4095.0 + 0.5)
        if raw < 0:
            raw = 0
        return self._ema_v, a, raw


class CrushMotor:
    def __init__(self, pin_in1=PIN_CRUSH_IN1, pin_in2=PIN_CRUSH_IN2, direction="fwd"):
        self.in1 = Pin(int(pin_in1), Pin.OUT)
        self.in2 = Pin(int(pin_in2), Pin.OUT)
        self.set_direction(direction)
        self.off()

    def set_direction(self, direction):
        d = str(direction or "fwd").lower()
        self.direction = "rev" if d in ("rev", "reverse", "1", "b") else "fwd"
        return self.direction

    def on(self):
        if self.direction == "rev":
            self.reverse()
        else:
            self.forward()

    def forward(self):
        self.in2.value(0)
        self.in1.value(1)

    def reverse(self):
        self.in1.value(0)
        self.in2.value(1)

    def off(self):
        self.in1.value(0)
        self.in2.value(0)

    def stop(self):
        self.off()

    def is_on(self):
        return bool(self.in1.value() or self.in2.value())
