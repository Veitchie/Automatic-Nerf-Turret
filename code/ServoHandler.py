from CustomServo import Servo
from adafruit_servokit import ServoKit
import threading
from timeit import default_timer as timer
import time

class ServoHandler:
    
    def __init__(self, debug = False):
        self.kit = ServoKit(channels=16)
        
        self.debug = debug
        
        self.gunYaw = Servo(self.kit.servo[0], 270, 400, 2500, 0, 270, 135, 250, 2000, -10)
        self.gunYPitch = Servo(self.kit.servo[1], 270, 400, 2500, 60, 120, 90, 250, 2000, 0)

        self._prime = Servo(self.kit.servo[2], 180, 500, 2500, 10, 170, 90, 250, 2000, 0)
        self._trigger = Servo(self.kit.servo[3], 180, 500, 2500, 10, 170, 130, 550, 2000, 0)
        
        self.trackYaw = Servo(self.kit.servo[4], 180, 500, 2500, 10, 170, 90, 250, 2000, 0, True, name = "trackYaw")
        self.trackPitch = Servo(self.kit.servo[5], 180, 500, 2500, 10, 170, 90, 250, 2000, 20, name = "trackPitch")
        
        self._primed = False
        self.__triggerPull = False
        self.__triggerDepressionDelay = 0.5
        self.__triggerPullAngle = 55
        self.__primeActiveAngle = 50
        self.__revTimer = timer()
        self.__spinupTime = 2
        self.__maxSpin = False
        self.__primeTimeout = 5

        self.enabled = False
        self.exit = False
        
        self.forwardOffset = 10
        self.rightOffset = 0
        self.heightOffset = 20
        
        self.timeAtLastUpdate = timer()
        self.updateTime = 0.01
        self.updateThread = threading.Thread(target=self.update, args=(), daemon=True)
        self.start()
    
    def enable(self):
        self.enabled = True
        
    def disable(self):
        self.enabled = False

    def start(self):
        self.exit = False
        self.updateThread.start()
        
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
            currentTime = timer()

            if (self.enabled):

                if self._primed:
                    elapsedTime = currentTime - self.__revTimer
                    if elapsedTime > self.__spinupTime:
                        self.__maxSpin = True
                    if self.__triggerPull:
                        timeSinceTriggerPull = currentTime - self.__triggerPullTime
                        if timeSinceTriggerPull > self.__triggerDepressionDelay:
                            self._trigger.rest()
                            self.__triggerPull = False
                        else:
                            self._trigger.setAngle(self.__triggerPullAngle)


                self.gunYaw.update()
                self.gunYPitch.update()
                self.trackYaw.update()
                self.trackPitch.update()
                self._prime.update()
                self._trigger.update()

            if (self.debug):
                print("ServoHandler: track-target-angle -> [%s,%s]" % (self.trackYaw.targetAngle,self.trackPitch.targetAngle))
            
    
    def inMotion(self):
        return not (self.trackYaw.atPos and self.trackPitch.atPos)
    
    def prime(self, noTimerUpdate = False):
        if not noTimerUpdate:
            self.__revTimer = timer()
        self._prime.setAngle(self.__primeActiveAngle)
        self._primed = True
        
    def unprime(self):
        self._primed = False
        self.__maxSpin = False
        self.__triggerPull = False
        self._prime.rest()

    def fire(self):
        self.prime(noTimerUpdate = True)
        if not self.__triggerPull:
            self.__triggerPullTime = timer()
        if self.__maxSpin:
            self.__triggerPull = True


if __name__ == '__main__':
    servoHandler = ServoHandler()
    servoHandler.enable()

    x = ""
    while not x == "c":
        x = input()
        if x == "p":
            servoHandler.unprime()
        if x == "":
            servoHandler.fire()
    servoHandler.unprime()

    time.sleep(1)