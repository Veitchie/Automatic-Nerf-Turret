from PersonSensor import PersonSensor
from LIDAR import VL53L0X

class SensorHandler:
    """
    This class handles the sensors...
    """
    
    def __init__(self):
        
        # Setup VL53L0X
        print("Setting up VL53L0X...")        
        self._lidar = VL53L0X()
        
        # Setup Person Sensor
        self._personSensor = PersonSensor()
        
        print("Setup complete.")
    
    def getDistance(self):
        # Return distance in mm
        return self._lidar.range
    
    def getFaceFromCentre(self, confidence = 95, uniqueValues = True):
        return self._personSensor.getLargestFace(confidence, uniqueValues)

    def continuousDistance(self):
        with self._lidar.continuous_mode():
            while True:
                print("Range: {0}mm".format(self._lidar.range))

def main():
    sensorHandler = SensorHandler()
    print("%smm" % (sensorHandler.getDistance()))
    
    
    

if __name__ == '__main__':
    main()