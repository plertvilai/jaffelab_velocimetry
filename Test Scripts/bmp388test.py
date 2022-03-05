import time
import bmp388

print("BMP388 Test Program ...\n")

bmp = bmp388.BMP388(address=0x77)
try:
    while True:
        time.sleep(0.5)
        temperature,pressure,altitude = bmp.get_temperature_and_pressure_and_altitude()
        print(' Temperature = %.1f Pressure = %.2f  Altitude =%.2f '%(temperature/100.0,pressure/100.0,altitude/100.0))
except IOError as e:
    print("IO error detected")
    print(e)

except KeyboardInterrupt:
    print("End of program")
    print("ctrl + c:")
    exit()