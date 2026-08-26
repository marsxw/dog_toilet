from machine import Pin

MOTOR_PIN_A = 1
MOTOR_PIN_B = 2
IR_PIN = 13
MOTOR_PAUSE_S = 1
MOTOR_RUN_S = 1


class Motor:
    def __init__(self, pin_a=MOTOR_PIN_A, pin_b=MOTOR_PIN_B):
        self.a = Pin(int(pin_a), Pin.OUT)
        self.b = Pin(int(pin_b), Pin.OUT)
        self.stop()

    def down(self):
        self.b.value(0)
        self.a.value(1)

    def up(self):
        self.a.value(0)
        self.b.value(1)

    def stop(self):
        self.a.value(0)
        self.b.value(0)
