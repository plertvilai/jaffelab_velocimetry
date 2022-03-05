#!/usr/bin/python

import smbus
import time
from os.path import exists
import datetime
import math


# Configuration
MAG_CONF = 0x44
ACC_CONF = 0x40
GYR_CONF = 0x42

#Accelerometer ranges
ACC_RANGE = 0x41
a_range2g = (0b0011)
a_range4g = (0b0101)
a_range8g = (0b1000)
ACCEL_MG_LSB_2G =0.000061035
ACCEL_MG_LSB_4G =0.000122070
ACCEL_MG_LSB_8G =0.000244141
ACCEL_MG_LSB_16G=0.000488281

#Gyroscope ranges
GYR_RANGE = 0x43
g_rang125dps = 0x04
g_rang250dps = 0x03
g_rang500dps = 0x02
g_rang1000dps = 0x01
g_rang2000dps = 0x00
GYRO_SENSITIVITY_125DPS  =0.0038110
GYRO_SENSITIVITY_250DPS  =0.0076220
GYRO_SENSITIVITY_500DPS  =0.0152439
GYRO_SENSITIVITY_1000DPS =0.0304878
GYRO_SENSITIVITY_2000DPS =0.0609756            

#Magnetometer 
MAG_IF_0 = 0x4c
MAG_IF_1 = 0x4d
MAG_IF_2 = 0x4e
MAG_IF_3 = 0x4f
MAG_UT_LS = 0.3

# Accelerometer registers:
acc_z_15_8 = 0x17
acc_z_7_0 = 0x16
acc_y_15_8 = 0x15
acc_y_7_0 = 0x14
acc_x_15_8 = 0x13
acc_x_7_0 = 0x12

# Gyroscope  registers:
gyr_z_15_8 = 0x11
gyr_z_7_0 = 0x10
gyr_y_15_8 = 0x0F
gyr_y_7_0 = 0x0E
gyr_x_15_8 = 0x0D
gyr_x_7_0 = 0x0C

# Magnetometer  registers:
mag_z_15_8 = 0x09
mag_z_7_0 = 0x08
mag_y_15_8 = 0x07
mag_y_7_0 = 0x06
mag_x_15_8 = 0x05
mag_x_7_0 = 0x04



class bmx160():

	def __init__(self,address=0x68,bus=1):
		self.bus = smbus.SMBus(bus)
		self.address = address
		# Checking communication with sensor
		readtest= self.bus.read_byte_data(self.address, 0x00)

		#Configure Accelerometer
		
		self.reg1 = self.bus.read_byte_data(self.address,ACC_CONF)

		# Configure Gyroscope
		self.reg2 = self.bus.read_byte_data(self.address,GYR_CONF)

	def setParams(self,accelparam,a_range,gyroparam,g_rang,magparam):
		'''Set parameters for the IMU.'''
		self.accelparam = ACCEL_MG_LSB_2G
		self.a_range = a_range2g
		self.gyroparam = GYRO_SENSITIVITY_250DPS
		self.g_rang = g_rang250dps
		self.magparam = MAG_UT_LS

	def setup(self):
		# write(address, register, value)
		# write to each register to activate
		self.bus.write_byte_data(self.address,0x7e,0x11)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x7e,0x15)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x7e,0x19)
		time.sleep(0.1)

		#Write to IMU
		self.bus.write_byte_data(self.address,ACC_RANGE,self.a_range)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,GYR_RANGE,self.g_rang)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,GYR_CONF,0x28); #sets output data rate to 100 Hz
		time.sleep(0.1)

		# Interrupt and other configurations (double check)
		self.bus.write_byte_data(self.address,0x50,0b00000000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x51,0b00010000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x52,0b00000000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x53,0b10000000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x54,0b00000000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x55,0b00000000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x56,0b10001000)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x57,0b00000000)
		time.sleep(0.1)

		# Offset Compensation
		self.bus.write_byte_data(self.address,0x69,0b01111101)
		time.sleep(0.1)
		self.bus.write_byte_data(self.address,0x7e,0x03)
		time.sleep(0.1)

		# copy accelerometer reg1 to magnetometer
		self.bus.write_byte_data(self.address,MAG_CONF,self.reg1)
		self.bus.write_byte(self.address,0x04)
		time.sleep(0.1)        

		self.bus.write_byte_data(self.address,MAG_IF_0,0x80)
		self.bus.write_byte_data(self.address,MAG_IF_3,0x01)
		self.bus.write_byte_data(self.address,MAG_IF_2,0x4b)
		self.bus.write_byte_data(self.address,MAG_IF_3,0x04)
		self.bus.write_byte_data(self.address,MAG_IF_2,0x51)
		self.bus.write_byte_data(self.address,MAG_IF_3,0x0e)
		self.bus.write_byte_data(self.address,MAG_IF_2,0x52)
		self.bus.write_byte_data(self.address,MAG_IF_3,0x02)
		self.bus.write_byte_data(self.address,MAG_IF_2,0x4c)
		self.bus.write_byte_data(self.address,MAG_IF_1,0x42)
		self.bus.write_byte_data(self.address,MAG_CONF,0x08)
		self.bus.write_byte_data(self.address,MAG_IF_0,0x03)

		time.sleep(0.1)
		self.bus.write_byte_data(self.address,MAG_CONF,self.reg1)
		return
	def calibration(self):
		'''A function to perform calibration.
		This is a place holder for now.'''
		# calibration parameters
		self.zACal = 0.406751261177
		self.yACal = -1.04798875635
		self.xACal = -0.06669269
		self.zGCal = -0.16333946
		self.yGCal = -0.32911796
		self.xGCal = -0.24481864
		self.yMCal = -30.3612
		self.xMCal = -83.6755
		self.zMCal = 0

	def readAccel(self):
		# Read accelerometer data:
		self.az1 = self.bus.read_byte_data(self.address,acc_z_15_8)
		self.az2 = self.bus.read_byte_data(self.address,acc_z_7_0)
		self.ay1 = self.bus.read_byte_data(self.address,acc_y_15_8)
		self.ay2 = self.bus.read_byte_data(self.address,acc_y_7_0)
		self.ax1 = self.bus.read_byte_data(self.address,acc_x_15_8)
		self.ax2 = self.bus.read_byte_data(self.address,acc_x_7_0)
		return self.az1, self.az2, self.ay1, self.ay2, self.ax1, self.ax2
        
	def convertAccel(self,az1,az2,ay1,ay2,ax1,ax2):
		# Convert the data
		self.zAccl = self.az1 * 256 + self.az2
		self.yAccl = self.ay1 * 256 + self.ay2
		self.xAccl = self.ax1 * 256 + self.ax2

		if self.zAccl > 32767 :
			self.zAccl -= 65536
		if self.yAccl > 32767:
			self.yAccl -= 65536
		if self.xAccl > 32767:
			self.xAccl -= 65536
		                                        
		self.zAccl = self.zAccl*self.accelparam*9.807 - self.zACal
		self.yAccl = self.yAccl*self.accelparam*9.807 - self.yACal
		self.xAccl = self.xAccl*self.accelparam*9.807 - self.xACal
		return self.zAccl,self.yAccl,self.xAccl

	def readGyro(self):
		# Read gyroscope data:
		self.gz1 = self.bus.read_byte_data(self.address,gyr_z_15_8)
		self.gz2 = self.bus.read_byte_data(self.address,gyr_z_7_0)
		self.gy1 = self.bus.read_byte_data(self.address,gyr_y_15_8)
		self.gy2 = self.bus.read_byte_data(self.address,gyr_y_7_0)
		self.gx1 = self.bus.read_byte_data(self.address,gyr_x_15_8)
		self.gx2 = self.bus.read_byte_data(self.address,gyr_x_7_0)
		return self.gz1,self.gz2,self.gy1,self.gy2,self.gx1,self.gx2

	def convertGyro(self,gz1,gz2,gy1,gy2,gx1,gx2):
		# Convert the data
		self.zGyro = self.gz1 * 256 + self.gz2
		self.yGyro = self.gy1 * 256 + self.gy2
		self.xGyro = self.gx1 * 256 + self.gx2

		if self.zGyro > 32767 :
		    self.zGyro -= 65536
		if self.yGyro > 32767 :
			self.yGyro -= 65536
		if self.xGyro > 32767 :
			self.xGyro -= 65536
		        
		self.zGyro = self.zGyro*self.gyroparam - self.zGCal
		self.yGyro = self.yGyro*self.gyroparam - self.yGCal
		self.xGyro = self.xGyro*self.gyroparam - self.xGCal
		return self.zGyro,self.yGyro,self.xGyro

	def readMag(self):
		# Read magnetometer data:
		self.mz1 = self.bus.read_byte_data(self.address,mag_z_15_8)
		self.mz2 = self.bus.read_byte_data(self.address,mag_z_7_0)
		self.my1 = self.bus.read_byte_data(self.address,mag_y_15_8)
		self.my2 = self.bus.read_byte_data(self.address,mag_y_7_0)
		self.mx1 = self.bus.read_byte_data(self.address,mag_x_15_8)
		self.mx2 = self.bus.read_byte_data(self.address,mag_x_7_0)
		return self.mz1, self.mz2, self.my1, self.my2, self.mx1, self.mx2

	def convertMag(self,mz1,mz2,my1,my2,mx1,mx2):
		# Convert the data
		self.zMag = self.mz1 * 256 + self.mz2
		self.yMag = self.my1 * 256 + self.my2
		self.xMag = self.mx1 * 256 + self.mx2

		if self.zMag > 32767 :
			self.zMag -= 65536
		if self.yMag > 32767 :
			self.yMag -= 65536
		if self.xMag > 32767 :
			self.xMag -= 65536

		self.zMag = self.zMag*self.magparam - self.zMCal
		self.yMag = self.yMag*self.magparam - self.yMCal
		self.xMag = self.xMag*self.magparam - self.xMCal

		return self.zMag,self.yMag,self.xMag

	def calculatePRY(self,initialized,pitchA,rollA,pitchO,rollO,yawO,yawM,start_time):
		accVec = math.sqrt(self.xAccl*self.xAccl + self.yAccl*self.yAccl + self.zAccl*self.zAccl)
		rollA = math.asin(self.yAccl/accVec)*180/math.pi
		pitchA = math.asin(-self.xAccl/accVec)*180/math.pi

		if initialized:  #first value of 
			pitchO = pitchA
			rollO = rollA
			initialized = 0
			pitchI = 0
			rollI = 0
			                        
		pitchR = self.yGyro 
		rollR = self.xGyro

		dt = time.time() - start_time
		fGyr = 0.98 #fraction of gyroscope contribution
		pitchI += pitchR*dt
		rollI += rollR*dt
		self.pitchO = fGyr*(pitchO + pitchR*dt) + (1 - fGyr)*pitchA
		self.rollO = fGyr*(rollO + rollR*dt) + (1 - fGyr)*rollA
		self.yawO = fGyr*(yawO + self.zGyro*dt) + (1-fGyr)*yawM

		return self.pitchO, self.rollO, self.yawO

	# def calibrateMag(self):
	# 	# spin board
	# 	# record all mag readings every 1 second for 60 seconds
	# 	print("Calibrate the Magnetometer")
	# 	print("Begin spinning in xy-plane in 5 seconds")
	# 	time.sleep(5)

	# 	#Create and open file to log data
	# 	today = datetime.date.today()
	# 	todayS = str(today.year) + "_" + str(today.month) + "_" + str(today.day)+"_"
	# 	name = "/home/pi/magCal"+todayS
	# 	fcount = 0   # count files
	# 	filede = 1   # while file already exists
	# 	count = 0 
	# 	while filede:
	# 		if exists(name+str(fcount)+".csv") == 0:  #if file exists 
	# 			filede = 0
	# 			file = open(name+str(fcount)+".csv","w") 
	# 			file.write("H:M:S,Mz,My,Mx\n")
	# 			start_time = time.time()
	# 			timesum = 0
	# 			while count < 100:
	# 				now = datetime.datetime.now()
	# 				current_time = now.strftime("%H:%M:%S")

	# 				dt = time.time() - start_time
	# 				start_time = time.time()
	# 				timesum += dt

	# 				if timesum >= 1:
	# 					timesum = 0
	# 					(mz1,mz2,my1,my2,mx1,mx2) = readMag()
	# 					(zMag,yMag,xMag) = convertMag(mz1,mz2,my1,my2,mx1,mx2)
	# 					file.write(str(zMag) + "," + str(yMag) + "," + str(xMag) + "," + str(now.hour)  + "," + str(now.minute) + "," + str(now.second) + "\n")               
	# 					count += 1
	# 		else:
	# 			fcount += 1
	# 	return 


