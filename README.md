# Automatic NERF Turret

#### What's the idea?
To make an automated turret that can do these things:
* Automatically target at least anyone, ideally everyone but me
* Use an unmodified NERF Strife for the shooting, extra points if it's quick-release
* Account for distance real-time by aiming upwards
* 3D print most f not all of the body pieces and brackets

Extra points for me if I add anything else, this is a continuous project.

#### Why did I make this?
I've seen a few NERF turrets over the years, but they usually have the sensors mounted to the barrel which limits their actions, I thought it would be cool to not do that.

## CAD & Code
Both the individual 3d files and an Assembled .STEP file are provided for printing or modification.
Included in the .STEP are models for components like the servos and RPi, some are basic models I made myself while others I sourced online for reference. I have included an [External models](#extModels) section below for crediting and linking to any sources. 

<img src="./images/assembled_render.png" width="500" />

### External models <a id='extModels'></a>
* [SG90 - Micro Servo 9g - Tower Pro](https://grabcad.com/library/sg90-micro-servo-9g-tower-pro-1) (Modified - I increased the height to match my servos)
* [Raspberry Pi Camera Module v2.1](https://grabcad.com/library/raspberry-pi-camera-4) (Modified - Added ribbon cable)
* [LM2596 DC-DC Buck Converter](https://grabcad.com/library/lm2596-dc-dc-buck-converter-2)
* [Raspberry Pi 2 model B](https://grabcad.com/library/raspberry-pi-2-model-b-3d-cad-assembly-model-2)

## My reasoning's for certain decisions

#### Buying components vs. using what I have
My decisions about where to put money in this project seems confusing. I'm basing the build around an old NERF blaster without modifying it and I've limited my computing power to a Raspberry Pi 2, but I also bought a Person Sensor to do facial detection and high torque 35kg servos. The simple answer is I have a lot of random little things, like a Raspberry Pi 2, and I try to do workarounds with what I have first before buying something else; it's cheaper & easier to buy a Person Sensor and use an old RPi than it is to try and get a new one have you seen the prices?!

#### What's with the massive bearing?
The 6005 bearing is both overkill for the weight of a plastic NERF blaster, and the direction of forces on the bearing. My main reasons for using it is that it's centre diameter is nice and big, and it's significantly smoother than bare plastic.

### Components used
* VL53L0X LIDAR
* Person Sensor by Useful Sensors
* Raspberry Pi Camera Module v2.1
* 2 x DS3235SG 35Kg 270° Servos
* 4 x SG90 9g Servos
* Raspberry Pi 2 Model B
* LM2596 DC-DC Buck Converter
* 6005 25x47x12mm bearing
* 12v Switching Power Supply
* A variety of M3 & M4 bolts and nuts
* NERF Stryfe blaster

### Dependencies
* [Adafruit_CircuitPython_VL53L0X](https://github.com/adafruit/Adafruit_CircuitPython_VL53L0X)
* [Adafruit_CircuitPython_ServoKit](https://github.com/adafruit/Adafruit_CircuitPython_ServoKit)
