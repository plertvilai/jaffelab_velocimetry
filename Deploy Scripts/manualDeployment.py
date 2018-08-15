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
import os

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

#vel.initRecordFile('/home/pi/velocimetry/data/') #initialize video file

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


def burstMode():
	'''For burst shot mode.'''
	#show info on OLED first
	oled.cls()
	oled.canvas.text((10,10), 'Burst Mode Active ...', fill=1)
	oled.display()

	vel.cameraInit() #initialize camera object

	while(1): #main loop for this mode
		buttonState = vel.checkButtonStat() #check button stat (should be either 1 or 4 here)

		if buttonState == 1: #if button is still pressed 
			sensor.read() #read pressure data
			vel.burstShot('/home/pi/velocimetry/data/') #take burst shots
			#record data to .csv file
			vel.recordInfo('/home/pi/velocimetry/',sensor.pressure(),sensor.temperature(ms5837.UNITS_Centigrade),mode=1) #set mode = 1 for burst shot

			#update OLED
			oled.cls()
			oled.canvas.text((10,0), 'Sensor Active...', fill=1)
			oled.canvas.text((10,10), 'Set # %d' %vel.setNum, fill=1)
			oled.canvas.text((10,20), 'fps = %.2f' %vel.actualFPS, fill=1)
			oled.canvas.text((10,30), 'Depth %.2f' %sensor.depth(), fill=1)
			oled.display()
		else: #if button is released
			vel.cameraRelease() #close camera
			return #go back to main loop


def videoMode():
	'''For video mode.'''
	#show info on OLED first
	#OLED is not updated in this mode to prevent frame drop
	oled.cls()
	oled.canvas.text((10,10), 'Video Mode Active ...', fill=1)
	oled.display()

	vel.cameraInit() #initialize camera object
	vel.videoRecInit('/home/pi/velocimetry/data/') #initialize video recording

	while(1): #main loop for this mode
		buttonState = vel.checkButtonStat() #check button stat (should be either 1 or 4 here)

		if buttonState == 1: #if button is still pressed 
			sensor.read() #read pressure data
			vel.videoRecCont() #continue to record video data
			vel.recordInfo('/home/pi/velocimetry/',sensor.pressure(),sensor.temperature(ms5837.UNITS_Centigrade),mode=0) #set mode=0 for video

		else: #if button is released
			vel.videoRecClose('/home/pi/velocimetry/data/') #stop video recording
			vel.cameraRelease() #close camera
			return #go back to main loop


#-------------------Main Loop of the program---------------------------#
while(1): 
	buttonState = vel.checkButtonStat() #check button stat (should be either 2 or 3 here)

	if buttonState == 2: #initial button press
		print 'Select Mode...'
		oled.cls()
		oled.canvas.text((10,10), 'Select Mode...', fill=1)
		oled.display()
		vel.mode = vel.buttonCommand(5) #select mode with one button

		if vel.mode == 4: #shutdown command
			oled.cls()
			oled.canvas.text((10,10), 'Shutting Down...', fill=1)
			oled.display()
			os.system("sudo shutdown -h now") #system shutdown
			break

		elif vel.mode == 0: #video mode
			videoMode()

		else: #burst shot mode
			burstMode()
	else: #if button remains unpressed
    	#show status on OLED
		oled.cls()
		#read pressure sensor while waiting
		if sensor.read():
			oled.canvas.text((10,0), 'Depth: %.2f m' %sensor.depth(), fill=1)
			oled.canvas.text((10,10), 'Temp: %.2f C' %sensor.temperature(ms5837.UNITS_Centigrade), fill=1)
			oled.canvas.text((10,20), 'Set: %.2f ' %vel.setNum, fill=1)
			oled.canvas.text((10,30), 'Vid: %.2f ' %vel.vidNum, fill=1)
			oled.display()
		else:
			oled.canvas.text((10,10), 'Pressure sensor fails', fill=1)
			oled.display()
		time.sleep(1)