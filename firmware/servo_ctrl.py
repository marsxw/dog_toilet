from machine import PWM, Pin

SERVO_PIN = 4


class Servo:
    def __init__(self, pin=SERVO_PIN, release_deg=20):
        self.pin_num = pin
        self.pwm = PWM(Pin(int(pin)), freq=50)
        self.set_angle(release_deg)

    def set_angle(self, deg):
        deg = max(0, min(180, float(deg)))
        us = 500.0 + (deg / 180.0) * 2000.0
        self.pwm.duty_ns(int(us * 1000))

    def attach(self, pin, release_deg=20):
        self.pwm.deinit()
        self.__init__(pin, release_deg)

    def deinit(self):
        try:
            self.pwm.deinit()
        except OSError:
            pass
