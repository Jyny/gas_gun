import threading
import serial
import sys
import time

global data, sl
data = ''

sl = serial.Serial()
sl.port = '/dev/ttyACM1'
sl.baudrate = 9600
sl.open()
time.sleep(2)
sl.write('A'.encode())
sl.write('123'.encode())

def reads():
	global data
	while True:
		data = sl.readline().decode()
		print(data)
		sys.stdout.flush()

t = threading.Thread(target=reads)
t.start()
