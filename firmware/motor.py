from machine import Pin, PWM

from pins import PIN_CRUSH, PIN_IR, PIN_IREF, PIN_MOTOR_H, PIN_MOTOR_L

IR_PIN = PIN_IR

# 调试用：在 PC 界面测好占空比后改此常量（0–100 %）
PRESS_PWM_DUTY_PCT = 25.0

PRESS_PWM_FREQ_HZ = 1000
MOTOR_PAUSE_S = 1
MOTOR_RUN_S = 1


def _pct_to_u16(pct):
    pct = max(0.0, min(100.0, float(pct)))
    return int(pct * 65535 / 100.0 + 0.5)


class PressMotor:
    def __init__(
        self,
        pin_iref=PIN_IREF,
        pin_h=PIN_MOTOR_H,
        pin_l=PIN_MOTOR_L,
        freq_hz=PRESS_PWM_FREQ_HZ,
        duty_pct=PRESS_PWM_DUTY_PCT,
    ):
        self._duty_pct = float(duty_pct)
        self.pwm = PWM(Pin(int(pin_iref)), freq=int(freq_hz))
        self.h = Pin(int(pin_h), Pin.OUT)
        self.l = Pin(int(pin_l), Pin.OUT)
        self.set_duty_pct(self._duty_pct)
        self.stop()

    def set_duty_pct(self, pct):
        self._duty_pct = max(0.0, min(100.0, float(pct)))
        self.pwm.duty_u16(_pct_to_u16(self._duty_pct))

    def duty_pct(self):
        return self._duty_pct

    def forward(self):
        self.l.value(0)
        self.h.value(1)

    def reverse(self):
        self.h.value(0)
        self.l.value(1)

    def stop(self):
        self.h.value(0)
        self.l.value(0)

    def down(self):
        self.forward()

    def up(self):
        self.reverse()


class CrushMotor:
    def __init__(self, pin=PIN_CRUSH):
        self.out = Pin(int(pin), Pin.OUT)
        self.off()

    def on(self):
        self.out.value(1)

    def off(self):
        self.out.value(0)


# 兼容旧名
Motor = PressMotor
