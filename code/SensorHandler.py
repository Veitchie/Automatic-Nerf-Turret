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
        self._personSensorMode = "Largest_Area" # Or Most_Confident

        # Handler variables
        self._facesDetected = False
        self._continuousUpdate = False
        self._face = -1
        
        print("Setup complete.")
    
    def start(self):
        self._personSensor.start()

    def update(self):
        if self._personSensorMode == "Largest_Area":
            self._face = self._personSensor.getLargestFace()
        if self._face != -1:
            self._facesDetected = True
        else:
            self._facesDetected = False
        return self._face

    def continuousUpdate(self):
        while self._continuousUpdate:
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
        threshold  = 3
        if abs(face[0] - centre[0]) <= threshold and abs(face[1] - centre[1]) <= threshold:
            print("Face detected: %smm away" % (self.getDistance()))
            return True
        return False

    def continuousDistance(self):
        with self._lidar.continuous_mode():
            while True:
                print("Range: {0}mm".format(self._lidar.range))
    
    def facesDetected(self):
        return self._facesDetected

    def getFace(self):
        return self._face
    
    def getFaceCoordinates(self):
        if self.facesDetected():
            return self._personSensor.getAngleEstimate(self.getFace()["box_centre"])
        return -1

def main():
    sensorHandler = SensorHandler()

    x = ""
    while not x == "c":
        sensorHandler.update()
        if sensorHandler.facesDetected():
            print(sensorHandler.getFaceCoordinates())
        
        x = input()
    
    
    

if __name__ == '__main__':
    main()