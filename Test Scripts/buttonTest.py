#!/usr/bin/python

import time
import RPi.GPIO as GPIO

button_pin = 5 #for push button

GPIO.setmode(GPIO.BCM)
GPIO.setup(button_pin, GPIO.IN)

while(1):
	print GPIO.input(button_pin)
	time.sleep(1)