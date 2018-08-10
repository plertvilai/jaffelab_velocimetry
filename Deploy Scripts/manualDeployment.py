#!/usr/bin/python

#manual deployment code for fiedl testing
#updated August 1, 2018
#P. Lertvilai

from velClass import *
import ms5837
import time
from lib_oled96 import ssd1306
from time import sleep
from smbus import SMBus


#-------------------Initialization-----------------------------------#
### OLED
i2cbus = SMBus(1)        # 1 = Raspberry Pi but NOT early REV1 board
oled = ssd1306(i2cbus)   # create oled object, nominating the correct I2C bus, default address

oled.canvas.text((10,0),    'Initializing', fill=1)
oled.display()


#velocity sensor
vel = velocitySensor() #init velocity sensor functions
if not vel.initialize():
	print "velocity sensor fails to initialize."
	oled.canvas.text((10,10),    'Velocity sensor fails', fill=1)
	oled.display()
	exit(1)

oled.canvas.text((10,10),    'Velocity sensor...', fill=1)
oled.display()


### Pressure Sensor
sensor = ms5837.MS5837_30BA() # Default I2C bus is 1 (Raspberry Pi 3)
# We must initialize the sensor before reading it
if not sensor.init():
        print "Sensor could not be initialized"
        exit(1)

# We have to read values from sensor to update pressure and temperature
if not sensor.read():
    print "Sensor read failed!"
    exit(1)
sensor.setFluidDensity(ms5837.DENSITY_SALTWATER) #set fluid density to saltwater

oled.canvas.text((10,20),    'Pressure sensor...', fill=1)
oled.display()

print 'Initialization success!'
oled.canvas.text((10,30),    'Init success!!', fill=1)
oled.display()
time.sleep(2)
oled.cls()

while(1):
	#while(not vel.checkButtonPress()): #use this for discrete data collection when button is pushed
	buttonState = vel.checkButtonStat()
	print buttonState
	if buttonState == 3: #button not pressed
		oled.cls()
		#read pressure sensor while waiting
		if sensor.read():
			oled.canvas.text((10,0), 'Depth: %.2f m' %sensor.depth(), fill=1)
			oled.canvas.text((10,10), 'Temp: %.2f C' %sensor.temperature(ms5837.UNITS_Centigrade), fill=1)
			oled.canvas.text((10,20), 'Set: %.2f ' %vel.setNum, fill=1)
			oled.canvas.text((10,30), 'FPS: %.2f ' %vel.actualFPS, fill=1)
			oled.display()
		else:
			oled.canvas.text((10,10), 'Pressure sensor fails', fill=1)
			oled.display()
		time.sleep(1)
	
	elif buttonState == 2:  #button pressed from not pressed
		vel.cameraInit()

	elif buttonState == 4: #button released from pressed
		vel.cameraRelease()

	else: #button pressed from pressed

		oled.cls()
		#after the button is pressed, perform image acquisition
		sensor.read() #read pressure data
		oled.canvas.text((10,0), 'Sensor Active...', fill=1)
		oled.canvas.text((10,10), 'Set # %d' %vel.setNum, fill=1)
		oled.canvas.text((10,20), 'fps = %.2f' %vel.actualFPS, fill=1)
		oled.canvas.text((10,30), 'Depth %.2f' %sensor.depth(), fill=1)
		oled.display()

		vel.videoRec('/home/pi/velocimetry/data/')
		
		#oled.display()

		#record pressure in mbar and temperature in degree C
		vel.recordInfo('/home/pi/velocimetry/',sensor.pressure(),sensor.temperature(ms5837.UNITS_Centigrade))
