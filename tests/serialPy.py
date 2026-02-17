import serial
import random
import time

ser = serial.Serial("/dev/cu.usbmodemDC5475C3BB642", 115200)

while True:
    angle = random.randint(0, 90)  # generate random angle between 0 and 90
    ser.write(str(angle).encode())  # send the angle to the serial port
    print(f"Sent: {angle}")  # print the sent angle
    time.sleep(1)  # wait for a second before generating next angle
