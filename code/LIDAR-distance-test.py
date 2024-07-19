import time

import LIDAR

vl53 = LIDAR.VL53L0X()

vl53.measurement_timing_budget = 200000 # 20ms = 20000

with vl53.continuous_mode():
    while True:
        time.sleep(0.1)

        curTime = time.time()
        print("Range: {0}mm ({1:.2f}ms)".format(vl53.range, time.time() - curTime))