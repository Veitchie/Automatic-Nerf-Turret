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
        
        # Establish all parameters of the servo
        self.servo = servo
        self.dom = dom
        self.minPulse = minPulse
        self.maxPulse = maxPulse
        self.minAngle = minAngle
        self.maxAngle = maxAngle
        self.restAngle = restAngle
        self.maxSpeed = maxSpeed
        self.invert = invert
        self.name = name
        
        # Set degrees of motion (pulse band is spread across this range of motion)
        self.servo.actuation_range = dom
        self.servo.set_pulse_width_range(minPulse, maxPulse)
        
        # Variables of the servo
        self.acceleration = acceleration
        self.currentJump = 0
        self.currentSpeed = 0
        self.prevSpeed = 0
        self.currentAngle = self.restAngle
        self.targetAngle = self.currentAngle
        self.servo.angle = self.restAngle
        self.direction = 0
        self.adjustment = adjustment
        self.atPos = False
        self.targetFrozen = False
        
        self.timeAtLastUpdate = timer()
    
    
    def getDirection(self, current, target):
        if (current == target):
            return 0
        return (target - current) / abs(target - current)
    
    
    def setAngle(self, target):
        """
        Returns:
            self.update() : If the Update thread crashes, this will continue to move the servo without acceleration
        """
        target = target + self.adjustment
        target = min(target, self.maxAngle)
        target = max(target, self.minAngle)
        
        if (self.invert):
            target = self.dom - target
        
        self.direction = self.getDirection(self.currentAngle, target)
        self.targetAngle = target
        #print("CustomServo-setAngle: Setting %s's targetAngle to %s" % (self.name,target))
        self.atPos = False
        return self.update()
    
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
        
        if (self.currentAngle == targetAngle or abs(self.currentAngle - targetAngle) < 1):
            self.currentSpeed = 0
            
            self.atPos = True
            return True
        
        else:
        
            distanceToTarget = abs(targetAngle - self.currentAngle)
            
            decelerationDistance = ( self.prevSpeed ** 2 ) / ( 2 * self.acceleration )
            
            decel = False
            
            if (distanceToTarget > decelerationDistance):
            
                self.currentSpeed += self.acceleration * timeElapsed * self.direction  #Increase speed
                
            else:
                
                self.currentSpeed -= self.acceleration * timeElapsed * self.direction
                
                decel = True
            
            if (abs(self.currentSpeed) > self.maxSpeed):
                self.currentSpeed = self.maxSpeed * (self.currentSpeed / abs(self.currentSpeed))
            
            self.currentJump = self.currentSpeed * timeElapsed
            
            if (abs(self.currentJump) >= abs(self.currentAngle - targetAngle) ): # Check if the next planned move will take us past the target angle
            
                self.currentAngle = targetAngle
                
                self.currentSpeed = 0
            
            else:
                
                self.currentAngle += self.currentJump
                
                self.currentAngle = min(self.currentAngle, self.maxAngle)
                self.currentAngle = max(self.currentAngle, self.minAngle)
                

        #print("CustomServo-update: Moving %s to %s" % (self.name, self.currentAngle))
        self.servo.angle = self.currentAngle # Move servo to currentAngle
        self.prevSpeed = self.currentSpeed
           
            
        return self.atPos
        
        
    def setAdjustment(self, angle):
        self.adjustment = angle
        self.setAngle(self.targetAngle)
        
    def getCurrentAngle(self):
        if (self.invert):
            return self.dom - self.servo.angle
        return self.servo.angle
