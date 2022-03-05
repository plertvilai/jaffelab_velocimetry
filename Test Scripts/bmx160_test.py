#!/usr/bin/python

import bmx160
import time
import math

imu = bmx160.bmx160()

imu.setParams(bmx160.ACCEL_MG_LSB_2G,bmx160.a_range2g,
	bmx160.GYRO_SENSITIVITY_250DPS,bmx160.g_rang250dps,bmx160.MAG_UT_LS)

imu.setup()
imu.calibration()


fname = "/home/pi/viv/imu_test.dat"
fcount = 0   # count files
filede = 1   # while file already exists
initialized = 1 # boolean for pitch/roll calculations
pitchA = 0
rollA = 0
pitchO = 0
rollO = 0
yawO = 0
yawM = 0

print("Test script for BMX160 IMU")
print("Press CTRL+C to stop the program.")
time.sleep(5)

start_time = time.time()

while(True):
	#READ ACCELEROMETER
	(az1,az2,ay1,ay2,ax1,ax2)  = imu.readAccel()        
	#CONVERT ACCELEROMETER
	(zAccl,yAccl,xAccl) = imu.convertAccel(az1,az2,ay1,ay2,ax1,ax2)

	#READ GYROSCOPE
	(gz1,gz2,gy1,gy2,gx1,gx2) = imu.readGyro()
	#CONVERT GYROSCOPE
	(zGyro,yGyro,xGyro) = imu.convertGyro(gz1,gz2,gy1,gy2,gx1,gx2)
	                                
	#READ MAGNETOMETER
	(mz1,mz2,my1,my2,mx1,mx2) = imu.readMag()
	#CONVERT MAGNETOMETER
	(zMag,yMag,xMag) = imu.convertMag(mz1,mz2,my1,my2,mx1,mx2)


	yawM = math.atan2(yMag,xMag)*180/math.pi

	#CALCULATE PITCH AND ROLL
	(pitchO,rollO,yawO) = imu.calculatePRY(initialized,pitchA,rollA,pitchO,rollO,yawO,yawM,start_time)

	
	# data string
	imuStr =  "%.2f,%5.2f %5.2f %5.2f  %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f %5.1f\n" %( start_time,
		xAccl, yAccl, zAccl, zGyro, yGyro, xGyro, zMag, yMag, xMag, pitchO, rollO, yawO)
	start_time = time.time()
	
	print(imuStr)

	f = open(fname, "a")
	f.write(imuStr)
	f.close()

	time.sleep(1)