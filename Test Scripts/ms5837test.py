#!/usr/bin/python
import ms5837
import time

sensor = ms5837.MS5837_30BA()

sensor.setFluidDensity(ms5837.DENSITY_SALTWATER) #set fluid density to saltwater


# We must initialize the sensor before reading it
if not sensor.init():
        print("Sensor could not be initialized")
        exit(1)

# We have to read values from sensor to update pressure and temperature
if not sensor.read():
    print("Sensor read failed!")
    exit(1)

while(1):
	print("%.2f mbar  %.2f m  %.2f C"%(sensor.pressure(),sensor.depth(),sensor.temperature()))
	time.sleep(1)