#!/usr/bin/python
 
from velClass import *
import time


vel = velocitySensor()
vel.initialize()

while True:
   vel.ledToggle()
   time.sleep(1)