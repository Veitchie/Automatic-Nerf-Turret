from SensorHandler import SensorHandler
from ServoHandler import ServoHandler
from threading import Thread
from enum import Enum
from timeit import default_timer as timer
import time

class _TurretMode(Enum):
    Shutdown = 0
    Sleep = 1
    Scan = 2
    DebugPS = 3
    AdjustTrack = 4
    AdjustGun = 5
    MANUAL = 6

def unknownCommand() -> None:
    print("Unknown command, type [exit] to exit.")

class Turret:
    def __init__(self, name = "Turret_0") -> None:
        print("--- Setting up %s components... ---" % (name))
        self._Name = name
        self._sensorHandler = SensorHandler()
        self._servoHandler = ServoHandler()
        self._mode = _TurretMode.Sleep
        self._updateThread = Thread(target=self._continuousUpdate, args=(), daemon=True)
        self._sensorsInMotion = True

        print("--- Setting up mode variables... ---")
        self._trackFromGunOffsets = [87, 0, 175]

        servoData = (self._servoHandler.getServoData("trackYaw"), self._servoHandler.getServoData("trackPitch"))
        self._scanningPositions = [ [servoData[0]["minAngle"], servoData[1]["restAngle"]], [servoData[1]["maxAngle"], servoData[1]["restAngle"]] ]
        self._scanningIndex = 0
        self._scanningPositionTime = timer()
        self._scanningDelay = 0.5
        self._scanningTimeout = 1
        self._scanningSpeed = 0.1
        self._scanningThreshold = 1
        self._scanningMode = 0 # ints used to signify mode : 0 -> Searching, 1 -> Confirming, 2 -> Targeting

        self._aTrack = 0
        self._aGun = 0

        self._servoHandler.enable()
        self._servoHandler.start()
        #self._sensorHandler.start()
        self._updateThread.start()

        print("--- Turret is ready! ---")

    def get_frame(self):
        return self._sensorHandler.getFrame()
    
    def stop(self):
        self._mode = _TurretMode.Shutdown

    def setMode(self, mode):
        if not isinstance(mode, _TurretMode):
            return
        self._mode = mode

    def _continuousUpdate(self):
        while self._mode is not _TurretMode.Shutdown:
            match self._mode:
                case _TurretMode.Sleep:
                    self._sleep()
                case _TurretMode.Scan:
                    self._scan()
                case _TurretMode.DebugPS:
                    self._debugPS()
                case _TurretMode.AdjustTrack:
                    self._adjustTrack()
                case _TurretMode.AdjustGun:
                    self._adjustGun()
                case _TurretMode.MANUAL:
                    pass
        self._servoHandler.disable()
        print("##### %s IS OFFLINE #####" % self._Name)
    
    def _adjustGun(self):
        if self._aGun != 0:
            self._servoHandler.moveTurret((self._aGun,0), throttle = 0.15, fromCentre=True)
            self._aGun = 0

    def _adjustTrack(self, adjust = (0, 0)):
        if adjust == (0, 0):
            return
        self._servoHandler.adjustCamera(adjust, throttle = 0.1)
        

    def _debugPS(self):
        self._sensorHandler.facesDetected()
        print(self._sensorHandler.getFaceAngleOffset())
    
    def _sleep(self):
        self._servoHandler.restAllMotors()
        self._scanningMode = 0

    def _matchCamera(self, distance = 100000):
        coords = [self._servoHandler.trackYaw.getCurrentAngle(fromCentre = True), self._servoHandler.trackPitch.getCurrentAngle(fromCentre = True)]
        #print("Moving gun to %s" % (coords,))
        self._servoHandler.moveTurret(coords, fromCentre = True)

    def _scan(self):
        self._sensorHandler._update()
        match self._scanningMode:

            # No targets, moving between two point while scanning
            #####################################################
            case 0:
                # While nothing is detected, continue moving between points
                if not self._sensorHandler.facesDetected():
                    if self._servoHandler.trackYaw.atPosition():
                        #print("Reached position index: %s" % (self._scanningIndex))
                        self._scanningIndex += 1
                        if self._scanningIndex >= len(self._scanningPositions):
                            self._scanningIndex = 0
                    self._servoHandler.setCamera(self._scanningPositions[self._scanningIndex], throttle = self._scanningSpeed)

                # If something is detected, stop moving to get a better look and move to case 2
                else:
                    face = self._sensorHandler.getFace()
                    if face != -1:
                        coords = (face["yaw_offset"], face["pitch_offset"])
                        #print("Stopping motion. Face detected: %s" % (coords,))
                        print("Stopping to see face",face)
                        self._servoHandler.stopTrack()
                        #time.sleep(2)#input("PAUSE")
                        self._scanningMode = 1
                        self._scanningPositionTime = timer()

            # Tracker has stopped moving and it checking for targets
            ########################################################
            case 1:
                # Look for faces after a short delay to ensure sensors are stationary
                if self._servoHandler.inMotion():
                    self._scanningPositionTime = timer()
                if (timer() - self._scanningPositionTime) > self._scanningDelay:
                #if not self._servoHandler.inMotion()  and (timer() - self._scanningPositionTime) > self._scanningDelay:
                    facesPresent = self._sensorHandler.facesDetected()
                    if facesPresent:
                        face = self._sensorHandler.getFace()
                        if face != -1:
                            coords = (face["yaw_offset"], face["pitch_offset"])
                            print("Face Detected! Moving to target: %s" % (coords,))
                            #time.sleep(2)#input("PAUSE")
                            print("Face confirmed, moving..",face)
                            self._servoHandler.adjustCamera(coords, throttle = self._scanningSpeed)
                            self._scanningMode = 2
                            self._scanningPositionTime = timer()
                        
                    # If no targets are detected within the delay window, resume scanning and move to case 1
                    if not facesPresent and (timer() - self._scanningPositionTime) > self._scanningTimeout:
                        print("Must've been the wind...")
                        self._scanningMode = 0
                        self._scanningPositionTime = timer()

            # Faces were detected and the sensors will move to the estimated location
            #########################################################################
            case 2:
                #if not self._servoHandler.inMotion() and (timer() - self._scanningPositionTime) > self._scanningDelay:
                if self._servoHandler.inMotion():
                    self._scanningPositionTime = timer()
                    print("In motion")
                if (timer() - self._scanningPositionTime) > self._scanningDelay:
                    facesPresent = self._sensorHandler.facesDetected()
                    if facesPresent:
                        face = self._sensorHandler.getFace()
                        if face != -1:
                            coords = (face["yaw_offset"], face["pitch_offset"])
                            self._scanningPositionTime = timer()
                            #print("Adjusting position, detection at: %s" % (coords,))
                            if coords[0] <= self._scanningThreshold and coords[1] <= self._scanningThreshold:
                                dist = self._sensorHandler.getDistance()
                                #print("Approx. Distance: %smm, confidence level: %s" % (dist, face["box_confidence"]))
                                #time.sleep(2)#input("PAUSE")
                                self._matchCamera(distance = dist)
                                print("Aiming turret...",face)
                            else:
                                self._servoHandler.slideCamera(coords)
                                print("Adjusting aim..",face)
                    elif not facesPresent and (timer() - self._scanningPositionTime) > self._scanningTimeout:
                        print("Must've been the wind...")
                        self._scanningMode = 0
                        self._scanningPositionTime = timer()
                


def parseNumbers(input_str):
    # Trim whitespace from the input string
    input_str = input_str.strip()

    # Check for different separators and split the input string
    if ',' in input_str:
        parts = input_str.split(',')
    else:
        parts = input_str.split()

    # Initialize the variables
    first = 0
    second = 0

    # Parse the numbers based on the length of parts
    if len(parts) == 1:
        # Single number given
        first = int(parts[0])
    elif len(parts) == 2:
        # Two numbers given
        first = int(parts[0]) if parts[0].strip() else 0
        second = int(parts[1])

    # Return the result as a tuple
    return (first, second)

if __name__ == "__main__":
    turret = Turret()

    command =  ""
    while command not in ["exit", "close", "c"]:
        newCommand = (input(">")).lower()
        if newCommand != "":
            command = newCommand

        match command:
            case "sleep":
                turret.setMode(_TurretMode.Sleep)
            case "scan":
                turret.setMode(_TurretMode.Scan)
            case "read ps":
                turret.setMode(_TurretMode.DebugPS)
            case "adjust":
                adjust = input(">>")
                turret._aTrack = parseNumbers(adjust)
                turret.setMode(_TurretMode.AdjustTrack)
            case "agun":
                turret.setMode(_TurretMode.AdjustGun)
                adjust = int(input(">>"))
                turret._aGun = adjust

