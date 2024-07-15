import time

import board
import busio

import adafruit_vl53l0x

# Initialize I2C bus and sensor.
i2c = busio.I2C(board.SCL, board.SDA)
print("i2c",i2c)
vl53 = adafruit_vl53l0x.VL53L0X(i2c)

vl53.measurement_timing_budget = 200000 # 20ms = 20000

with vl53.continuous_mode():
    while True:
        time.sleep(0.1)

        curTime = time.time()
        print("Range: {0}mm ({1:.2f}ms)".format(vl53.range, time.time() - curTime))