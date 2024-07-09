from ServoHandler import ServoHandler
import time
import json

def inputValidation2(accept = "c", deny = "e", message = ""):
    printMsg = ""
    if ( not message == ""):
        printMsg = message + "\n>>>"
    else:
        printMsg = ">>>"
    val = input(printMsg).lower()
    if (val == accept.lower()):
        return 1
    elif (val == deny.lower()):
        return 0
    else:
        return -1
        
        
def inputValidation(responses = ["c","e"], printMsg = ">>>", lowerCase = True):
    
    userInput = input(printMsg)
    if lowerCase:
        userInput = userInput.lower()
    
    for i in range(len(responses)):
        if userInput == responses[i]:
            return i
    return -1

def inputLoop(responses = ["c","e"], printMsg = ">>>", lowerCase = True):
    validResponse = False
    
    while not validResponse:
        userInput = inputValidation(responses, printMsg, lowerCase)
        if userInput > -1:
            validResponse = True
            return userInput
        
def main():
    print("""
   _____                        _____          _ _   _                _____      _               
  / ____|                      |  __ \        (_) | (_)              / ____|    | |              
 | (___   ___ _ ____   _____   | |__) |__  ___ _| |_ _  ___  _ __   | (___   ___| |_ _   _ _ __  
  \___ \ / _ \ '__\ \ / / _ \  |  ___/ _ \/ __| | __| |/ _ \| '_ \   \___ \ / _ \ __| | | | '_ \ 
  ____) |  __/ |   \ V / (_) | | |  | (_) \__ \ | |_| | (_) | | | |  ____) |  __/ |_| |_| | |_) |
 |_____/ \___|_|    \_/ \___/  |_|   \___/|___/_|\__|_|\___/|_| |_| |_____/ \___|\__|\__,_| .__/ 
                                                                                          | |    
                                                                                          |_|  """)
    
    #Confirm they want to continue
    print("\nThis tool will enagage and move the ttached servo motors")
    print("Type 'c' to continue or type 'e' to exit, then press ENTER")
    if inputLoop() == 1:
        return
        
    #Set tracking servos to home positision
    print("\nSetting tracking servos to their resting positions...")
    time.sleep(3)
    servoHandler = ServoHandler()
    servoHandler.enable()
    print("\n// Take this oportunity to reseat your servo horns //")
    print("Type 'c' to continue or type 'e' to exit, then press ENTER")
    if inputLoop() == 1:
        return
    
    #tilt camera up
    print("\nThe tracking gimbal will now pivot upwards slightly...")
    time.sleep(3)
    servoHandler.adjustCamera(0,15)
    print("Did the gimbal move in the right direction? (upwards)")
    print("Type 'c' to confirm, or 'down' if the gimbal moved downwards instead, then press ENTER")
    userInput = inputLoop(["c","down"])
    if userInput == 1:
        print("PITCH NEEDS INVERTED")
    
    
    #turn camera right
    #turn camera left
    
    #Set home offsets
    
    #Save settings to text file
    
    
    #(post on lemmy for a pracitical guide to git)

def main2():

    if ( not inputValidation("c", "d", 'This is a Servo Configuration tool\nEnter "c" to continue.') == 1):
        print("Exiting")
    else:
        
        print("Please ensure all servos are at their approximate home positions")
        print('Once the servos are positioned, enter "c" to continue or enter "e" to exit the tool:')
        while (not inputValidation() == 1):
            print('Please enter either "c" to continue:')
        servoHandler = ServoHandler()
        servoHandler.enable()
        servoHandler.adjustCamera(0,15)
        while (not input(">>>") == "e"):
            print(".")
            
            
        #Confirm they want to continue
        
        #Set tracking servos to home positision
        
        #tilt camera up
        #tilt camera down
        
        #turn camera right
        #turn camera left
        
        #Set home offsets
        
        #Save settings to text file
        
        
        #(post on lemmy for a pracitical guide to git)

main()
#main2()