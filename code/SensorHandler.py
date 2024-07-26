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
        print("setting up Person Sensor...")
        self._personSensor = PersonSensor()
        self._psFaceCentreOffset = (-12,-10)

        self._continousUpdate = False
        
        print("Setup complete.")
    
    def start(self):
        self._personSensor.start()

    def update(self):
        self._personSensor.update()

    def continousUpdate(self):
        while self._continousUpdate:
            self.update()

    def getDistance(self):
        # Return distance in mm
        return self._lidar.range
    
    def getFaceFromCentre(self, confidence = 95, uniqueValues = True):
        face, unique = self._personSensor.getLargestFace(confidence, uniqueValues)
        if uniqueValues:
            if unique:
                return face
            else:
                return -1
        return face
    
    def isFaceCentred(self, face):
        centre = self._psFaceCentreOffset
        threshhold  = 3
        if abs(face[0] - centre[0]) <= threshhold and abs(face[1] - centre[1]) <= threshhold:
            print("Face detected: %smm away" % (self.getDistance()))
            return True
        return False

    def continuousDistance(self):
        with self._lidar.continuous_mode():
            while True:
                print("Range: {0}mm".format(self._lidar.range))

def main():
    sensorHandler = SensorHandler()

    while True:
        sensorHandler.update()
        face = sensorHandler.getFaceFromCentre(confidence = 80, uniqueValues = True)
        if (face != -1):
            print(face)
            sensorHandler.isFaceCentred(face)
    
    
    

if __name__ == '__main__':
    main()