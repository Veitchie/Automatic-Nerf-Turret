from SensorHandler import SensorHandler
from ServoHandler import ServoHandler
from threading import Thread
from enum import Enum
from timeit import default_timer as timer

class _TurretMode(Enum):
    Shutdown = 0
    Sleep = 1
    Scan = 2
    DebugPS = 3
    AdjustTrack = 4
    AdjustGun = 5

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
        self._scanningDelay = 0.1
        self._scanningTimeout = 1
        self._scanningSpeed = 0.25
        self._scanningThreshold = 1
        self._scanningMode = 0 # ints used to signify mode : 0 -> Searching, 1 -> Confirming, 2 -> Targeting

        self._aTrack = 0
        self._aGun = 0

        self._servoHandler.enable()
        self._sensorHandler.start()
        self._updateThread.start()

        print("--- Turret is ready! ---")
    
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
        self._servoHandler.disable()
        print("##### %s IS OFFLINE #####" % self._Name)
    
    def _adjustGun(self):
        if self._aGun != 0:
            self._servoHandler.moveTurret((self._aGun,0), throttle = 0.15, fromCentre=True)
            self._aGun = 0

    def _adjustTrack(self):
        if self._aTrack != 0:
            self._servoHandler.adjustCamera((self._aTrack,0))
            self._aTrack = 0

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
        # Move sensors until face is detected
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
                    self._servoHandler.setCamera(self._scanningPositions[self._scanningIndex], self._scanningSpeed)

                # If something is detected, stop moving to get a better look and move to case 2
                else:
                    face = self._sensorHandler.getFace()
                    if face != -1:
                        coords = (face["yaw_offset"], face["pitch_offset"])
                        #print("Stopping motion. Face detected: %s" % (coords,))
                        print("Stopping to see face",face)
                        self._servoHandler.stopTrack()
                        self._scanningMode = 1
                        self._scanningPositionTime = timer()

            # Tracker has stopped moving and it checking for targets
            ########################################################
            case 1:
                # Look for faces after a short delay to ensure sensors are stationary
                facesPresent = self._sensorHandler.facesDetected()
                if facesPresent and (timer() - self._scanningPositionTime) > self._scanningDelay and not self._servoHandler.inMotion():
                    face = self._sensorHandler.getFace()
                    if face != -1:
                        coords = (face["yaw_offset"], face["pitch_offset"])
                        #print("Face Detected! Moving to target: %s" % (coords,))
                        print("Face confirmed, moving..",face)
                        self._servoHandler.adjustCamera(coords)
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
                facesPresent = self._sensorHandler.facesDetected()
                if facesPresent and (timer() - self._scanningPositionTime) > self._scanningDelay and not self._servoHandler.inMotion():
                    face = self._sensorHandler.getFace()
                    if face != -1:
                        coords = (face["yaw_offset"], face["pitch_offset"])
                        self._scanningPositionTime = timer()
                        #print("Adjusting position, detection at: %s" % (coords,))
                        if coords[0] <= self._scanningThreshold and coords[1] <= self._scanningThreshold:
                            dist = self._sensorHandler.getDistance()
                            #print("Approx. Distance: %smm, confidence level: %s" % (dist, face["box_confidence"]))
                            self._matchCamera(distance = dist)
                            print("Aiming turrey...",face)
                        else:
                            self._servoHandler.adjustCamera(coords)
                            print("Adjusting aim..",face)
                elif not facesPresent and (timer() - self._scanningPositionTime) > self._scanningTimeout:
                    print("Must've been the wind...")
                    self._scanningMode = 0
                    self._scanningPositionTime = timer()
                


if __name__ == "__main__":
    turret = Turret()

    command =  ""
    while command not in ["exit", "close", "c"]:
        command = (input(">")).lower()
        match command:
            case "sleep":
                turret.setMode(_TurretMode.Sleep)
            case "scan":
                turret.setMode(_TurretMode.Scan)
            case "read ps":
                turret.setMode(_TurretMode.DebugPS)
            case "adjust":
                turret.setMode(_TurretMode.AdjustTrack)
                adjust = int(input(">>"))
                turret._aTrack = adjust
            case "agun":
                turret.setMode(_TurretMode.AdjustGun)
                adjust = int(input(">>"))
                turret._aGun = adjust

