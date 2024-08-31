import adafruit_vl53l0x
import board
import busio

# 57 64 79 98 112 121

class VL53L0X(adafruit_vl53l0x.VL53L0X):
    def __init__(self, address = 41):
        
        i2c = busio.I2C(board.SCL, board.SDA)
        print("i2c",i2c)

        super().__init__(i2c, address = address)

    def getDistance(self):
        return self.range

if __name__ == "__main__":
    lidar = VL53L0X()
    while True:
        print(lidar.getDistance())

