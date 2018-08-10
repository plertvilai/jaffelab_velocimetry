#!/usr/bin/python

#library for velocity sensor control

import io
import time
import cv2
import picamera
import numpy as np
import RPi.GPIO as GPIO

#------------------------pin assignment------------------------------#
button_pin = 5 #for push button
button_signal = 17 #for signal arduino the button pin
camera_pin = 27 #for signal camera status
shake_pin = 25 #for handshake signal
led_pin = 21 #onboard LED
light_pin = 12

class velocitySensor():

	def __init__(self):
		#GPIO
		self.buttonState = 0 #read button state at the beginning
		self.ledState = 0 #led pin state

		#file IO
		self.imageN = 30
		self.framerate = 50
		self.setNum = 0

		#image IO
		self.actualFPS = 0

		#camera
		self.camera = 0

	def initialize(self):
		'''Initialize the GPIO pins of the instrument.
		Needs to be run at first for GPIO to function properly.
		Then, read the configuration file and set varaibles accordingly.'''
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(button_pin, GPIO.IN)
		GPIO.setup(shake_pin, GPIO.OUT)
		GPIO.output(shake_pin, GPIO.HIGH)
		GPIO.setup(camera_pin, GPIO.OUT)
		GPIO.output(camera_pin, GPIO.LOW)
		GPIO.setup(led_pin, GPIO.OUT)
		GPIO.output(led_pin, GPIO.HIGH)
		GPIO.setup(light_pin, GPIO.OUT)
		GPIO.output(light_pin, GPIO.HIGH) #note that LED is active LOW, so writing HIGH turns LED off

		self.buttonState = GPIO.input(button_pin)
		self.ledState = 0

		#-----------------------Read configuration file-----------------------#
		file = open('/home/pi/velocimetry/config/velocimetry.config', 'r') 
		configStr = file.readlines() #read all lines from config file
		configInfo = range(len(configStr)) #initialize configuration information array
		for i in range(len(configStr)):
		    info = configStr[i]
		    configInfo[i] = info.split('=')[1]

		file.close()

		#parse into variables
		self.imageN = int(configInfo[0])
		self.framerate = int(configInfo[1])

		#read current set number
		file = open('/home/pi/velocimetry/config/setNum.txt', 'r') 
		self.setNum = int(file.readline())
		file.close()

		print 'ImageN = %d, framerate = %d, setNum = %d' %(self.imageN,self.framerate,self.setNum)

		
		return True

	def ledToggle(self):
		'''Toggle LED state'''
		if self.ledState: #if LED is on, then turns it off
			GPIO.output(light_pin, GPIO.HIGH)
			self.ledState = 0
		else: #otherwise turn it off
			GPIO.output(light_pin, GPIO.LOW)
			self.ledState = 1

	def burstShot(self,directory):
		'''Take burst shots and save images to files.'''
		self.ledToggle() #turn LED ON
		GPIO.output(camera_pin,GPIO.HIGH) #turn red indicator LED ON

		#taking pictures
		with picamera.PiCamera() as camera:
			camera.shutter_speed = 6000
			camera.resolution = (1280,720)
			camera.framerate = self.framerate
			time.sleep(2)
			outputs = [io.BytesIO() for i in range(self.imageN)]
			start = time.time()
			camera.capture_sequence(outputs,'jpeg',use_video_port=True)
			finish = time.time()
			self.actualFPS = 1.0*self.imageN/(finish-start)
			print 'Captured', self.imageN, 'images at', self.actualFPS , ' fps'

		#turn off camera signal
		GPIO.output(led_pin,GPIO.LOW)
		self.ledToggle() #turn LED off

		#-------------------Write images to files------------------------------#
		for i in range(self.imageN):
			frame = outputs[i]
			data = np.fromstring(frame.getvalue(), dtype=np.uint8)
			image = cv2.imdecode(data, 1)
			#print 'velocimetry/data/images/img%.2d_%.2d.tif'%(setNum,i)
			cv2.imwrite(directory+'img%.2d_%.2d.tif'%(self.setNum,i),image)

		return True

	def cameraInit(self):
		'''Initialize camera.'''
		self.camera = picamera.PiCamera()
		self.camera.shutter_speed = 3000
		self.camera.resolution = (1280,720)
		self.camera.framerate = self.framerate
		self.camera.start_preview()
		time.sleep(5)
		return True


	def cameraRelease(self):
		'''Release camera resources.'''
		print 'Closing camera'
		self.camera.stop_preview()
		self.camera.close()
		time.sleep(5)
		return True


	def videoRec(self,directory):
		'''Record video data.'''
		self.ledToggle() #turn LED ON
		GPIO.output(camera_pin,GPIO.HIGH) #turn red indicator LED ON
		#taking pictures
		
		self.camera.start_recording(directory+'vid%.4d.h264'%(self.setNum))
		time.sleep(0.5) #record for only 0.5 second
		self.camera.stop_recording()
		
		# with picamera.PiCamera() as camera:
		# 	camera.shutter_speed = 6000
		# 	camera.resolution = (1280,720)
		# 	camera.framerate = self.framerate
		# 	camera.start_preview()
		# 	camera.start_recording(directory+'vid%.4d.h264'%(self.setNum))
		# 	time.sleep(0.5) #record for only 0.5 second
		# 	camera.stop_recording()
		# 	camera.stop_preview()

		#turn off camera signal
		GPIO.output(led_pin,GPIO.LOW)
		self.ledToggle() #turn LED off


	def recordInfo(self,directory,pressure,temp):
		'''Record image info to files.'''
		#write framerate to file
		file = open(directory+'data/auxData.csv','a') 
		file.write('%.2f,%d,%.5f,%.3f,%.3f\n'%(time.time(),self.setNum,self.actualFPS,pressure,temp))

		#increment set number
		file = open(directory+'config/setNum.txt','w') 
		self.setNum = self.setNum+1
		file.write(str(self.setNum))
		file.close() 

		return True

	def checkButtonPress(self):
		'''Check whether the button is pressed.'''
		buttonPress = GPIO.input(button_pin) #read button
		if buttonPress and not self.buttonState: #if the button is pressed (from not being pressed)
			self.buttonState = 1 #change button state
			return True
		elif not buttonPress:
			self.buttonState = 0
			return False
		else:
			return False

	def checkButtonStat(self):
		'''Check whether the button is released.
		3 is the default state where button is not pressed.
		1 is when button is kept pressed.
		4 button release
		2 button initial press'''
		buttonPress = GPIO.input(button_pin) #read button
		if buttonPress and self.buttonState: #if the button is pressed (from being pressed)
			self.buttonState = 1 #change button state
			return 1
		elif buttonPress and not self.buttonState: #if the button is pressed (from not being pressed)
			self.buttonState = 1
			return 2
		elif not buttonPress and not self.buttonState: #if the button is not pressed (from not being pressed)
			self.buttonState = 0
			return 3
		elif not buttonPress and self.buttonState: #if the button is not pressed (from being pressed)
			self.buttonState = 0
			return 4
		else:
			return 5

	def readButton(self):
		return GPIO.input(button_pin)