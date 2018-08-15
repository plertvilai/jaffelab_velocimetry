#!/usr/bin/python

#library for velocity sensor control

import io
import os
import time
import cv2
import picamera
import numpy as np
import RPi.GPIO as GPIO
import datetime as dt

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
		self.setNum = 0 #use for still images

		#get the next available video number
		i = 0
		while os.path.exists("/home/pi/velocimetry/data/video%.4d.h264" % i):
			i += 1
		self.vidNum = i

		#image IO
		self.actualFPS = 0

		#camera
		self.camera = 0

		#time keeping
		self.time = time.time()
		self.recStart = 0
		self.recEnd = 0

		#others
		self.mode = 0

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


	def cameraInit(self):
		'''Initialize camera.'''
		self.camera = picamera.PiCamera()
		self.camera.shutter_speed = 3000
		self.camera.resolution = (1280,720)
		self.camera.framerate = self.framerate
		time.sleep(5)
		return True


	def cameraRelease(self):
		'''Release camera resources.'''
		print 'Closing camera'
		self.camera.close()
		time.sleep(5)
		return True

	def burstShot(self,directory):
		'''Take burst shots and save images to files.'''
		self.ledToggle() #turn LED ON
		GPIO.output(camera_pin,GPIO.HIGH) #turn red indicator LED ON

		#taking pictures
		outputs = [io.BytesIO() for i in range(self.imageN)]
		start = time.time()
		self.camera.capture_sequence(outputs,'jpeg',use_video_port=True)
		finish = time.time()
		self.actualFPS = 1.0*self.imageN/(finish-start)
		print 'Captured', self.imageN, 'images at', self.actualFPS , ' fps'

		#turn off camera signal
		GPIO.output(led_pin,GPIO.LOW)
		self.ledToggle() #turn LED off

		#-------------------Write images to files------------------------------#
		for i in range(self.imageN-20):
			frame = outputs[i+20]
			data = np.fromstring(frame.getvalue(), dtype=np.uint8)
			np.save(directory+'img%.2d_%.2d.npy'%(self.setNum,i),data)

		return True



	def recordInfo(self,directory,pressure,temp,mode=0):
		'''Record image info to files.
		Mode == 0 -> video mode; else burst shot mode.'''

		if mode==0: #video mode
			#write framerate to file
			file = open(directory+'data/vidAux.csv','a') 
			file.write('%.3f,%.3f,%.3f\n'%(time.time(),pressure,temp))

		else: #burst shot mode
			file = open(directory+'data/stillAux.csv','a') 
			file.write('%.3f,%d,%.5f,%.3f,%.3f\n'%(time.time(),self.setNum,self.actualFPS,pressure,temp))
			#increment set number
			file = open(directory+'config/setNum.txt','w') 
			self.setNum = self.setNum+1
			file.write(str(self.setNum))
			file.close() 

		return True



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

	def videoRecInit(self,directory):
		'''Start video recording.'''
		self.ledToggle() #turn LED ON
		GPIO.output(camera_pin,GPIO.HIGH) #turn red indicator LED ON
		self.camera.start_preview()
		time.sleep(5) #wait for camera to stabilize
		self.recStart = time.time()
		#start recording with motion vector data as well
		self.camera.start_recording(directory+'video%.4d.h264'%(self.vidNum),motion_output=directory+'motion%.4d.data'%(self.vidNum))
		return True

	def videoRecClose(self,directory):
		'''End video recording. Record video info and increment vidNum.'''

		self.camera.stop_recording()
		self.camera.stop_preview()
		self.recEnd = time.time()
		#turn off camera signal
		GPIO.output(led_pin,GPIO.LOW)
		self.ledToggle() #turn LED off

		file = open(directory+'vidData.csv','a') 
		file.write('%.4d,%.2f,%.2f\n'%(self.vidNum,self.recStart,self.recEnd))

		self.vidNum = self.vidNum + 1 #increment video file name

		return True

	def checkTime(self,second):
		'''check whether time has passed in second.'''
		if time.time()-self.time>second:
			self.time = time.time()
			return True
		else:
			return False

	def videoRecCont(self):
		'''Perform video recording continuously without still image capturing.'''
		start = time.time()
		while (time.time()-start) < 0.5:
			self.camera.annotate_text = '%.3f' %time.time()
			self.camera.wait_recording(0.1)
		#self.camera.wait_recording(0.5)
		return True




	def buttonCommand(self,timeOut=3):
		'''Accept command from one button.
		The timeout is in second and default to 3s.'''
		start = time.time()
		count = 0
		while(time.time()-start<timeOut):
			if self.checkButtonStat() == 2: #if button is pressed from not pressed
				count = count+1
				time.sleep(0.3) #for debouncing
			time.sleep(0.1) 
		return count


#--------------Archived Functions (No longer used)--------------#
	# def initRecordFile(self,directory):
	# 	'''Initialize record file. 
	# 	Filename convention is video%.4d.h264 and is placed in the specified directory.'''

	# 	#first check all existing files in the directory
	# 	i = 0
	# 	while os.path.exists(directory+"video%.4d.h264" % i):
	# 		i += 1
	# 	self.vidNum = i
	# 	return True


	########## Original burst shot function in deployment 1
	########## Use opencv to decode and then re-encode image --> way too slow
	# def burstShot(self,directory):
	# 	'''Take burst shots and save images to files.'''
	# 	self.ledToggle() #turn LED ON
	# 	GPIO.output(camera_pin,GPIO.HIGH) #turn red indicator LED ON

	# 	#taking pictures
	# 	with picamera.PiCamera() as camera:
	# 		camera.shutter_speed = 6000
	# 		camera.resolution = (1280,720)
	# 		camera.framerate = self.framerate
	# 		time.sleep(2)
	# 		outputs = [io.BytesIO() for i in range(self.imageN)]
	# 		start = time.time()
	# 		camera.capture_sequence(outputs,'jpeg',use_video_port=True)
	# 		finish = time.time()
	# 		self.actualFPS = 1.0*self.imageN/(finish-start)
	# 		print 'Captured', self.imageN, 'images at', self.actualFPS , ' fps'

	# 	#turn off camera signal
	# 	GPIO.output(led_pin,GPIO.LOW)
	# 	self.ledToggle() #turn LED off

	# 	#-------------------Write images to files------------------------------#
	# 	for i in range(self.imageN):
	# 		frame = outputs[i]
	# 		data = np.fromstring(frame.getvalue(), dtype=np.uint8)
	# 		image = cv2.imdecode(data, 1)
	# 		#print 'velocimetry/data/images/img%.2d_%.2d.tif'%(setNum,i)
	# 		cv2.imwrite(directory+'img%.2d_%.2d.jpg'%(self.setNum,i),image)

	# 	return True


	########## Record multiple video files with very short length
	# def videoRec(self,directory):
	# 	'''Record video data.'''
	# 	self.ledToggle() #turn LED ON
	# 	GPIO.output(camera_pin,GPIO.HIGH) #turn red indicator LED ON
	# 	#taking pictures
		
	# 	self.camera.start_recording(directory+'vid%.4d.h264'%(self.setNum))
	# 	time.sleep(0.5) #record for only 0.5 second
	# 	self.camera.stop_recording()
		
	# 	# with picamera.PiCamera() as camera:
	# 	# 	camera.shutter_speed = 6000
	# 	# 	camera.resolution = (1280,720)
	# 	# 	camera.framerate = self.framerate
	# 	# 	camera.start_preview()
	# 	# 	camera.start_recording(directory+'vid%.4d.h264'%(self.setNum))
	# 	# 	time.sleep(0.5) #record for only 0.5 second
	# 	# 	camera.stop_recording()
	# 	# 	camera.stop_preview()

	# 	#turn off camera signal
	# 	GPIO.output(led_pin,GPIO.LOW)
	# 	self.ledToggle() #turn LED off



	########## Old button check function. Very simple; only return True if button is pressed from not pressed
	# def checkButtonPress(self):
	# 	'''Check whether the button is pressed.'''
	# 	buttonPress = GPIO.input(button_pin) #read button
	# 	if buttonPress and not self.buttonState: #if the button is pressed (from not being pressed)
	# 		self.buttonState = 1 #change button state
	# 		return True
	# 	elif not buttonPress:
	# 		self.buttonState = 0
	# 		return False
	# 	else:
	# 		return False

	########## Taking still images while recording
	########## when burst for several pictures, the video frames are dropped, so no longer used.
	# def videoRecStill(self,stillCap,directory=''):
	# 	'''Perform video recording continuously.
	# 	If stillCap <= 0, then no still images are recorded.
	# 	If stillCap > 0, then a set of 5 still images are recorded at the specify interval in seconds.'''
	# 	start = time.time()
	# 	while (time.time()-start) < 1:
	# 		self.camera.annotate_text = '%.3f' %time.time()
	# 		self.camera.wait_recording(0.1)

	# 	if stillCap <= 0:
	# 		return True
	# 	elif self.checkTime(stillCap):
	# 		start = time.time()
	# 		self.camera.capture_sequence([
	# 	        directory+'image%.4d_%.1d.jpg' % (self.setNum,i)
	# 	        for i in range(5)
	# 	        ], use_video_port=True)
	# 		stop = time.time()
	# 		self.actualFPS = 5.0/(stop-start) #get actual fps of still capturing
	# 		return True
	# 	else:
	# 		return False