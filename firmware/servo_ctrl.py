from machine import PWM, Pin

from pins import PIN_SERVO

SERVO_FREQ_HZ = 50
RELEASE_DEG = 0
PRESS_DEG = 70
SERVO_MOVE_S = 1.0
PRESS_HOLD_S = 1.0


class Servo:
    def __init__(self, pin=PIN_SERVO, release_deg=RELEASE_DEG):
        self.pin_num = int(pin)
        self.angle = float(release_deg)
        self.pwm = PWM(Pin(self.pin_num), freq=SERVO_FREQ_HZ)
        self.set_angle(release_deg)

    def set_angle(self, deg):
        deg = max(0.0, min(180.0, float(deg)))
        self.angle = deg
        us = 500.0 + (deg / 180.0) * 2000.0
        self.pwm.duty_ns(int(us * 1000))

    def attach(self, pin, release_deg=RELEASE_DEG):
        self.pwm.deinit()
        self.__init__(pin, release_deg)

    def deinit(self):
        try:
            self.pwm.deinit()
        except OSError:
            pass


class FlushServo(Servo):
    def __init__(
        self,
        pin=PIN_SERVO,
        release_deg=RELEASE_DEG,
        press_deg=PRESS_DEG,
    ):
        super().__init__(pin, release_deg)
        self.release_deg = float(release_deg)
        self.press_deg = float(press_deg)

    def set_limits(self, release_deg, press_deg):
        self.release_deg = max(0.0, min(180.0, float(release_deg)))
        self.press_deg = max(0.0, min(180.0, float(press_deg)))

    def press(self):
        self.set_angle(self.press_deg)

    def release(self):
        self.set_angle(self.release_deg)

    def down(self):
        self.press()

    def up(self):
        self.release()

    def stop(self):
        self.release()
