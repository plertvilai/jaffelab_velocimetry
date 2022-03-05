import ms5837
import time
import bmx160
import bmp388
import math

#----- MS5837 Pressure Sensor ------#
sensor = ms5837.MS5837_30BA() # Default I2C bus is 1 (Raspberry Pi 3)
if not sensor.init():
	print("MS5837 sensor could not be initialized.")
	exit(1)
# We have to read values from sensor to update pressure and temperature
if not sensor.read():
	print("MS5837 sensor read failed!")
	exit(1)
sensor.setFluidDensity(ms5837.DENSITY_SALTWATER) #set fluid density to saltwater

#------BMP388 Internal temperature/pressure sensor ---------#
bmp = bmp388.BMP388(address=0x77)


#----- BMX160 IMU ----------#
imu = bmx160.bmx160()

imu.setParams(bmx160.ACCEL_MG_LSB_2G,bmx160.a_range2g,
	bmx160.GYRO_SENSITIVITY_250DPS,bmx160.g_rang250dps,bmx160.MAG_UT_LS)
imu.setup()
imu.calibration()
initialized = 1 # boolean for pitch/roll calculations
pitchA = 0
rollA = 0
pitchO = 0
rollO = 0
yawO = 0
yawM = 0


# data file and status file
status_file = '/home/pi/viv/status.txt'
data_file = '/home/pi/viv/env_data/%d.dat'%time.time()

# boolean to keep track of status
underwater = False # Trun true when the device is underwater
underater_thresh = 0.25 # threshold for considering that the device is underwater (unit meters)

#------- Main loop ------------------#

while(1):

	sensor.read() # read MS5837 pressure sensor

	if not underwater:
		if sensor.depth()>underater_thresh: # if the device is underwater, then start logging data
			print("Device is submersed at %d"%time.time())
			underwater = True
			# log timestamp to file
			f = open(status_file, "w")
			f.write("1")
			f.close()
			start_time = time.time()
		else:
			print("Device is on land. Depth reading = %.2f m"%sensor.depth())
			time.sleep(5)

		continue

	if sensor.depth()<underater_thresh: # if the device is no longer underwater
		print("Device is no longer submersed at %d"%time.time())
		underwater = False
		# log timestamp to file
		f = open(status_file, "w")
		f.write("0")
		f.close()

		continue

	# read data from BMP388
	temperature,pressure,altitude = bmp.get_temperature_and_pressure_and_altitude()

	# read data from the IMU
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
	imu_str =  "%5.2f,%5.2f,%5.2f,%5.1f,%5.1f,%5.1f,%5.1f,%5.1f,%5.1f,%5.1f,%5.1f,%5.1f\n" %(
		xAccl, yAccl, zAccl, zGyro, yGyro, xGyro, zMag, yMag, xMag, pitchO, rollO, yawO)
	start_time = time.time()

	# data from MS5837 pressure sensor. Pressure unit is in mbar
	pressure_str = '%.2f,%.3f,%.3f,'%(time.time(),sensor.pressure(),sensor.temperature())

	# data from BMP388. Pressure unit is in Pa
	bmp_str = '%.2f,%.2f,'%(temperature/100.0,pressure/100.0)

	# print the whole data to console
	print(pressure_str+bmp_str+imu_str)

	# write data to file
	f = open(data_file, "a")
	f.write(pressure_str+bmp_str+imu_str)
	f.close()

	time.sleep(0.1)

