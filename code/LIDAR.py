import adafruit_vl53l0x
import board
import busio

class VL53L0X(adafruit_vl53l0x.VL53L0X):
    def __init__(self):
        
        i2c = busio.I2C(board.SCL, board.SDA)
        print("i2c",i2c)

        super().__init__(i2c)
