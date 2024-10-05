from PersonSensor import PersonSensor
from Camera import Camera
from LIDAR import VL53L0X
from TfLunaI2C import TfLunaI2C
from threading import Thread
from enum import Enum
import time

def returnGreaterValue(key, arrayOfDictionaries):
    length = len(arrayOfDictionaries)
    if length == 0:
        return -1
    index = 0
    max = 0
    for i in range(length):
        item = arrayOfDictionaries[i][key]
        if item > max:
            index = i
            max = item
    return arrayOfDictionaries[index]

def returnGreaterIndex(key, arrayOfDictionaries):
    length = len(arrayOfDictionaries)
    if length == 0:
        return -1
    index = 0
    max = 0
    for i in range(length):
        item = arrayOfDictionaries[i][key]
        size = item[0] * item[1]
        if size > max:
            index = i
            max = size
    return arrayOfDictionaries[index]

class _PersonSensorMode(Enum):
    LargestArea = 1
    MostConfident = 2

class SensorHandler:
    """
    This class handles the sensors...
    """
    
    def __init__(self):
        
        # Setup VL53L0X
        #print("Setting up VL53L0X...")        
        #self._lidar = VL53L0X()
        print("Setting up TF-Luna...")
        self._lidar = TfLunaI2C()
        
        # Setup Person Sensor
        print("setting up Person Sensor...")
        self._personSensor = PersonSensor()
        self._psFaceCentreOffset = (3,-30)
        self._personSensorMode = _PersonSensorMode.MostConfident

        # Setup PiCamera
        print("Setting up PiCamera...")
        self._camera = Camera(resolution=(640,480))
        self._camera.start()

        # Handler variables & stuff
        print("Setting up Sensor Handler attributes...")
        self._facesDetected = False
        self._continuousUpdate = False
        self._face = -1
        self._faceFromCamera = False
        self._updateThread = Thread(target=self._continuousUpdateStart, args=(), daemon=True)
        self._currentTargets = []
        self._currentDistance = 0
        self._lastPositive = (-1, False)
        self.__lock = False
        
        print("Setup complete.")
    
    def start(self):
        """Start the update thread to continuously read sensor data."""
        self._continuousUpdate = True
        self._updateThread.start()
    
    def stop(self):
        """Exit running update thread."""
        self._continuousUpdate = False

    def setFaceCentreOffset(self, newCoords):
        """Set new face offset values.
        Parameters:
            newCoords (tuple / array of ints) : New coordinates denoting the error from centre i.e (2, -5)"""
        self._psFaceCentreOffset = newCoords

    def faceFusion(self, camera = None, ps = None):
        if not camera and not ps:
            return None
        if not (camera != -1 and ps != -1):
            if camera != -1:
                return camera
            return ps
        
        threshold = 5
        #print("camera / %s:\t%s" % (len(camera),camera))
        #print("person / %s:\t%s" % (len(ps),ps))
        
        arrayMatch = False
        for i in range(len(camera)):
            for j in range(len(ps)):

                a = camera[i]["box_centre"]
                b = ps[j]["box_centre"]

                x, y, z, k = a[0], a[1], b[0], b[1]
                #if abs(x - z) < threshold and abs(y - k) < threshold:
                if abs(camera[i]["yaw_offset"] - ps[j]["yaw_offset"]) < threshold and abs(camera[i]["pitch_offset"] - ps[j]["pitch_offset"]) < threshold:
                    arrayMatch = True
                    break
            
            if not arrayMatch:
                ps.append(camera[i])
            arrayMatch = False

        #print("fused / %s:\t%s" % (len(ps),ps))
        return ps

    def getFrame(self):
        return self._camera.getFrame()

    def _update(self):
        if self.__lock:
            print("Cannot update")
            return self._face
        psFaces = self._personSensor.getFaces()
        camFaces = self._camera.detectFaces(self._camera.getFrame())
        self._currentTargets = camFaces#self.faceFusion(ps=camFaces, camera=psFaces) # Swapped them around so if there's matching faces it uses the camera one
        #print("Current Targets: %s", self._currentTargets)
        
        if len(self._currentTargets) > 0:
            self._face = returnGreaterIndex("fov_range", self._currentTargets)
            self._faceFromCamera = True if (self._face["device_id"] == "camera") else False

        # Update LIDAR
        self._currentDistance = self.getDistance()

        if self._face != -1:
            self._facesDetected = True
            self._lastPositive = (self._face, self._faceFromCamera)
        else:
            self._facesDetected = False
        return self._face


    def _continuousUpdateStart(self):
        while self._continuousUpdate:
            self._update()

    def getDistance(self):
        """Return distance in cm"""
        return self._lidar.read_data()[0]
    
    def facesDetected(self):
        """Update the sensors and return True if faces are detected.
        Returns:
            When faces are detected:
                True (boolean)
            When no faces are detected:
                False (boolean)"""
        if self._continuousUpdate:
            return self._facesDetected
        self._update()
        return self._facesDetected

    def getFace(self):
        """
        Return the currently detected face.

        Returns:
            When there are faces:
                Face Data (dictionary)
            When there are no faces:
                -1"""
        if not self._continuousUpdate:
            self._update()
        self.__lock = True
        face = self._face
        self._face = -1
        self._facesDetected =False
        self.__lock = False
        return face

    def getLastPositive(self):
        return self._lastPositive[0], self._lastPositive[1]
    
    def getFaceAngleOffset(self, face = None):
        if face is None:
            face, sensor = self.getFace()#self.getLastPositive()
        if face == -1:
            return -1
        face = face["box_centre"]
        if self._facesDetected:
            if sensor:
                centreWithOffset = self._camera.getAngleEstimation(face, fromCentre = True)
            else:
                centreWithoutOffset = self._personSensor.getAngleEstimation(face, fromCentre = True)
                centreWithOffset = (centreWithoutOffset[0] - self._psFaceCentreOffset[0], (centreWithoutOffset[1] - self._psFaceCentreOffset[1]))
            return centreWithOffset
        return -1

def main():
    sensorHandler = SensorHandler()

    thresh = 2
    command =  ""
    while command not in ["exit", "close", "c"]:
        command = (input(">")).lower()
        match command:
            case "track":
                if sensorHandler.facesDetected():
                    coords = sensorHandler.getFaceAngleOffset()
                    print("Face detected at %s" % (coords,))
                    if abs(coords[0]) < thresh and abs(coords[1]) < thresh:
                        print("%smm" % (sensorHandler.getDistance()))
            case "dist":
                time.sleep(5)
                print("%smm" % (sensorHandler.getDistance()))
    
    
    

if __name__ == '__main__':
    main()