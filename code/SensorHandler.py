from PersonSensor import PersonSensor
from adafruit_vl53l0x import VL53L0X
import board
import busio

class SensorHandler:
    """
    This class controls the LIDAR & Person Sensor and has various modules to process their data.
    """
    
    def __init__(self):
        
        # Setup VL53L0X
        print("Setting up VL53L0X...")        
        self.lidar = VL53L0X(busio.I2C(board.SCL, board.SDA))
        
        # Setup Person Sensor
        self.personSensor = PersonSensor()
        
        print("Setup complete.")
    
    def getDistance(self):
        return self.lidar.range
    
    def getFaceFromCentre(self, confidence = 95, uniqueValues = True):
        return self.personSensor.getLargestFace(confidence, uniqueValues)


def main():
    sensorHandler = SensorHandler()
    print("%smm" % (sensorHandler.getDistance()))
    
    
    

if __name__ == '__main__':
    main()