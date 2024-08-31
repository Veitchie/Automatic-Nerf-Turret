from timeit import default_timer as timer

class Servo:
    """
    A custom servo clas built to expand the Adafruit ServoKit library
    """
    
    def __init__(self, servo,
        dom = 180, 
        minPulse = 500, maxPulse = 2500,
        minAngle = 0, maxAngle = 180,
        restAngle = 90,
        centreAngle = None,
        maxSpeed = 250,
        acceleration = 2000,
        adjustment = 0,
        invert = False,
        name = "generic-servo"):
        """
        Servo setup.
        
        Parameters:
            servo (servokit.servo[index]): The associated servo on the servokit. MANDATORY
            dom (int): The servos maximum range of motion.
            minPulse (int): Pulse width that achieves the servos minimum angle.
            maxPulse (int): Pulse width that achieves the servos maximum angle.
            restAngle (int): Resting angle of the servo.
            maxSpeed (int): Maximum speed limit of the servo (degrees per second).
            acceleration (int): Acceleration/decceleration rate (degrees per second per second).
            adjustment (int): Servo horn ange adjustment.
            invert (bool): Inverts the servo if it moves the wrong way.
        """

        if centreAngle is None:
            centreAngle = restAngle
        
        # Establish all parameters of the servo
        self.servo = servo
        self.dom = dom
        self.minPulse = minPulse
        self.maxPulse = maxPulse
        self.minAngle = minAngle
        self.maxAngle = maxAngle
        self.restAngle = restAngle
        self.centreAngle = centreAngle
        self.maxSpeed = maxSpeed
        self.acceleration = acceleration
        self.adjustment = adjustment
        self.invert = invert
        self.name = name
        
        # Set degrees of motion (pulse band is spread across this range of motion)
        self.servo.actuation_range = dom
        self.servo.set_pulse_width_range(minPulse, maxPulse)
        
        # Variables of the servo
        self.currentJump = 0
        self.currentSpeed = 0
        self.prevSpeed = 0
        self.speed = 0
        self.currentAngle = self.restAngle + self.adjustment
        self.targetAngle = self.currentAngle
        self.direction = 0
        self.atPos = False
        self.targetFrozen = False
        if self.invert:
            self.servo.angle = self.dom - self.restAngle
        else:
            self.servo.angle = self.restAngle
        
        self.timeAtLastUpdate = timer()
    
    
    def getDirection(self, current, target):
        if (current == target):
            return 0
        return (target - current) / abs(target - current)
    
    
    def setAngle(self, target, throttle = 1, fromCentre = False):
        """
        Returns:
            At position (boolean)
        """
        if fromCentre:
            target = target + self.centreAngle#(self.dom // 2)

        if target == self.targetAngle:
            self.atPos = True
            return True
        target = target
        target = min(target, self.maxAngle)
        target = max(target, self.minAngle)
        
        self.direction = self.getDirection(self.currentAngle, target)
        self.targetAngle = target
        self.speed = abs(throttle) * self.maxSpeed
        return self.atPos
    
    def stop(self):
        self.setAngle(self.currentAngle)
    
    def rest(self):
        self.setAngle(self.restAngle)
    
    
    def adjust(self, val):
        self.setAngle(self.targetAngle + val)
    
    
    def update(self):
        self.atPos = False
        
        currentUptime = timer()
    
        timeElapsed = currentUptime - self.timeAtLastUpdate
        self.timeAtLastUpdate = currentUptime
        
        targetAngle = self.targetAngle

        #if self.invert:
        #    targetAngle = self.dom - targetAngle
        
        if (self.currentAngle == targetAngle or abs(self.currentAngle - targetAngle) < 1):
            self.currentSpeed = 0
            self.currentAngle = targetAngle
            self.atPos = True
            #return True
        
        else:
        
            distanceToTarget = abs(targetAngle - self.currentAngle)
            
            decelerationDistance = ( self.prevSpeed ** 2 ) / ( 2 * self.acceleration )
            
            decel = False
            
            if (distanceToTarget > decelerationDistance):
            
                self.currentSpeed += self.acceleration * timeElapsed * self.direction  #Increase speed
                
            else:
                
                self.currentSpeed -= self.acceleration * timeElapsed * self.direction
                
                decel = True
            
            if (abs(self.currentSpeed) > self.speed):
                self.currentSpeed = self.speed * (self.currentSpeed / abs(self.currentSpeed))
            
            self.currentJump = self.currentSpeed * timeElapsed
            
            if (abs(self.currentJump) >= abs(self.currentAngle - targetAngle) ): # Check if the next planned move will take us past the target angle
            
                self.currentAngle = targetAngle
                
                self.currentSpeed = 0
            
            else:
                
                self.currentAngle += self.currentJump
                
                self.currentAngle = min(self.currentAngle, self.maxAngle)
                self.currentAngle = max(self.currentAngle, self.minAngle)
                

        #print("CustomServo-update: Moving %s to %s" % (self.name, self.currentAngle))
        if (self.invert):
            self.servo.angle = self.adjustment + self.dom - self.currentAngle # Move servo to currentAngle
        else:
            self.servo.angle = self.adjustment + self.currentAngle
        self.prevSpeed = self.currentSpeed
           
            
        return self.atPos
        
        
    def setAdjustment(self, angle):
        self.adjustment = angle
        self.setAngle(self.targetAngle)
        
    def getCurrentAngle(self, fromCentre = False):
        currentAngle = self.servo.angle
        if self.invert:
            currentAngle = self.dom - currentAngle - self.adjustment 
        if fromCentre:
            return currentAngle - self.centreAngle - self.adjustment 
        return currentAngle

    def getData(self):
        """ data = {
            "dom" : self.dom,
            "minPulse": self.minPulse,
            "maxPulse": self.maxPulse,
            "minAngle": self.minAngle,
            "maxAngle": self.maxAngle,
            "restAngle": self.restAngle,
            "maxSpeed": self.maxSpeed,
            "acceleration": self.acceleration,
            "adjustment": self.adjustment,
            "invert": self.invert,
            "name": self.name
        } """
        return vars(self)#data
    
    def atPosition(self):
        return self.atPos