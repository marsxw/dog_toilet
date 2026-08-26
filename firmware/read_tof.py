from machine import I2C, Pin
import time
from vl53l0x import VL53L0X

i2c = I2C(0, scl=Pin(9), sda=Pin(8), freq=400000)
print("i2c scan:", i2c.scan())

tof = VL53L0X(i2c)
print("VL53L0X init ok")

for i in range(1000):
    mm = tof.ping()
    triggered = mm < 500
    print("%d: %d mm  toilet=%s" % (i + 1, mm, triggered))
    time.sleep(0.4)
