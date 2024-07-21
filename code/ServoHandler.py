from CustomServo import Servo
from adafruit_servokit import ServoKit
import threading
from timeit import default_timer as timer

class ServoHandler:
    
    def __init__(self, debug = False):
        self.kit = ServoKit(channels=16)
        
        self.debug = debug
        
        self.gunYaw = Servo(self.kit.servo[0], 270, 400, 2500, 0, 270, 135, 250, 2000, -10)
        self.gunYPitch = Servo(self.kit.servo[1], 270, 400, 2500, 60, 120, 90, 250, 2000, 0)

        self._prime = Servo(self.kit.servo[2], 180, 500, 2500, 10, 170, 90, 250, 2000, 0)
        
        self.trackYaw = Servo(self.kit.servo[4], 180, 500, 2500, 10, 170, 90, 250, 2000, 0, True, name = "trackYaw")
        self.trackPitch = Servo(self.kit.servo[5], 180, 500, 2500, 10, 170, 90, 250, 2000, 20, name = "trackPitch")
        
        self._primed = False
        self.__primeActiveAngle = 70
        self.__revTimer = timer()
        self.__spinupTime = 3
        self.__maxSpin = False
        self.__primeTimeout = 5
        self.__revThread = threading.Thread(target=self.revBarrel, args=(), daemon=False)

        self.enabled = False
        self.exit = False
        
        self.forwardOffset = 10
        self.rightOffset = 0
        self.heightOffset = 20
        
        self.timeAtLastUpdate = timer()
        self.updateTime = 0.01
        self.updateThread = threading.Thread(target=self.update, args=(), daemon=True)
        self.updateThread.start()
    
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False
        
    def stop(self):
        self.exit = True
    
    def moveTurret(self, angles):
        self.gunYaw.setAngle(angles[0])
        self.gunYPitch.setAngle(angles[1])
        
    def adjustCamera(self, angles):
        self.trackYaw.adjust(angles[0])
        self.trackPitch.adjust(angles[1])
        
    def setCamera(self, angles):
        self.trackYaw.setAngle(angles[0])
        self.trackPitch.setAngle(angles[1])
    
    def fromCentre(self, angles):
        self.trackYaw.setAngle(self.trackYaw.getCurrentAngle() - self.trackYaw.adjustment + angles[0])
        self.trackPitch.setAngle(self.trackPitch.getCurrentAngle() - self.trackPitch.adjustment + angles[1])
        
    
    def update(self):
        while (not self.exit):
            if (self.enabled):
                self.gunYaw.update()
                self.gunYPitch.update()
                self.trackYaw.update()
                self.trackPitch.update()
                self._prime.update()
            if (self.debug):
                print("ServoHandler: track-target-angle -> [%s,%s]" % (self.trackYaw.targetAngle,self.trackPitch.targetAngle))
            
            
            currentUptime = timer()
            timeElapsed = currentUptime - self.timeAtLastUpdate
            
            while (timeElapsed < self.updateTime):
                currentUptime = timer()
                timeElapsed = currentUptime - self.timeAtLastUpdate
            self.timeAtLastUpdate = timer()
            
    
    def inMotion(self):
        return not (self.trackYaw.atPos and self.trackPitch.atPos)
    
    def prime(self):
        self.__revTimer = timer()
        if not self._primed:
            self.__revThread.start()
            self._primed = True

    def revBarrel(self):
        self._prime.setAngle(self.__primeActiveAngle)
        while self._primed:
            currentTime = timer()
            if (currentTime - self.__revTimer > self.__primeTimeout):
                self.unprime()
            if currentTime > self.__spinupTime:
                self.__maxSpin = True
        
    def unprime(self):
        self._primed = False
        self._prime.rest()


if __name__ == '__main__':
    servoHandler = ServoHandler()
    servoHandler.enable()
    servoHandler.prime()