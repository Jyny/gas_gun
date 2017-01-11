from pygame.locals import *
from sys import stdout
import pygame, sys, os
import RPi.GPIO as GPIO
import time

global x_min, x_max, y_min, y_max

class SPIManager(object):
	
	SPI_MOSI = 10
	SPI_MISO = 9
	SPI_SCLK = 11
	SPI_CE0 = 7
		
	def __init__(self):
		self.SPISetupGPIO();
	
	def SPISetupGPIO(self):
		GPIO.setmode(GPIO.BCM)
	
		GPIO.setup(SPIManager.SPI_MOSI, GPIO.OUT)
		GPIO.output(SPIManager.SPI_MOSI, GPIO.LOW)
	
		GPIO.setup(SPIManager.SPI_MISO, GPIO.IN)
	
		GPIO.setup(SPIManager.SPI_SCLK, GPIO.OUT)
		GPIO.output(SPIManager.SPI_SCLK, GPIO.LOW)
	
		GPIO.setup(SPIManager.SPI_CE0, GPIO.OUT)
		GPIO.output(SPIManager.SPI_CE0, GPIO.HIGH)
	
	
	def SPISelect(self):
		GPIO.output(SPIManager.SPI_CE0, GPIO.LOW)
		
	def SPIUnSelect(self):
		GPIO.output(SPIManager.SPI_CE0, GPIO.HIGH)
	
	def SPIPulseClock(self):		
		GPIO.output(SPIManager.SPI_SCLK, GPIO.HIGH)	
		GPIO.output(SPIManager.SPI_SCLK, GPIO.LOW)
		
	def SPISend(self, data):
		currentMOSIstate = False
		
		for i in range (len(data)):
			byteToSend = data[i]
			for j in range (8):

				desiredState = False
				if (byteToSend & 0x80) > 0 :
					desiredState = True

				if desiredState == True and currentMOSIstate == False :	
					GPIO.output(SPIManager.SPI_MOSI, GPIO.HIGH)
					currentMOSIstate = True
				elif desiredState == False and currentMOSIstate == True :
					GPIO.output(SPIManager.SPI_MOSI, GPIO.LOW)
					currentMOSIstate = False
				
				# Pulse the clock.
				self.SPIPulseClock()

				# Shift to the next bit.
				byteToSend <<= 1;
		if currentMOSIstate == True :
			GPIO.output(SPIManager.SPI_MOSI, GPIO.LOW)

		
	def SPIReceive(self, numBits):
		numBytes = (numBits + 7) // 8

		buffer = bytearray()

		# Array is filled in received byte order.
		# Any padding bits are the least significant bits, of the last byte.

		currentBit = 0;
		for i in range (numBytes):
			receiveByte = 0x00
			for j in range(8):
				# Shift to the next bit.
				receiveByte <<= 1

				# Skip padding bits
				currentBit += 1				
				if currentBit > numBits:
					continue

				# Set the clock high.
				GPIO.output(SPIManager.SPI_SCLK, GPIO.HIGH)

				# Read the value.
				bit = GPIO.input(SPIManager.SPI_MISO)

				# Set the clock low.
				GPIO.output(SPIManager.SPI_SCLK, GPIO.LOW)
				
				# Set the received bit.
				if bit == True : 
					receiveByte |= 1
				
			buffer.append(receiveByte)

		return buffer;

class XPT2046(object):
	
	StartBit = 0b10000000 
	
	class ChannelSelect(object):
		X_POSITION = 0b01010000
		Y_POSITION = 0b00010000
		Z1_POSITION = 0b00110000
		Z2_POSITION = 0b01000000
		TEMPERATURE_0 = 0b00000000
		TEMPERATURE_1 = 0b01110000
		BATTERY_VOLTAGE = 0b00100000
		AUXILIARY = 0b01100000

	class ConversionSelect(object):
		_8_BIT = 0b00001000
		_12_BIT = 0b00000000
	
	def __init__(self):
		self._ConversionSelect = XPT2046.ConversionSelect._12_BIT
		self._SPIManager = SPIManager()
		
	def setMode(self, conversionSelect):
		self._ConversionSelect = conversionSelect
	
	def makeControlByte(self, channelSelect):
		# @@TODO Other elements in control byte.
		return XPT2046.StartBit | channelSelect | self._ConversionSelect
	
	def readValue(self, channelSelect):
		controlByte = self.makeControlByte(channelSelect)
		msg = bytearray()
		msg.append(controlByte)
		self._SPIManager.SPISelect()
		self._SPIManager.SPISend(msg)
		
		# Skip the 'busy' bit.
		self._SPIManager.SPIPulseClock();
		
		responseValue = 0
		
		if self._ConversionSelect == XPT2046.ConversionSelect._12_BIT:
			responseData = self._SPIManager.SPIReceive(12)
			responseValue = (responseData[0] << 4) | (responseData[1] >> 4) 
		else:
			responseData = self._SPIManager.SPIReceive(8)
			responseValue = responseData[0]
			
		self._SPIManager.SPIUnSelect()
		return responseValue
		
		
	def readX(self):
		return self.readValue(XPT2046.ChannelSelect.X_POSITION)
		
	def readY(self):
		return self.readValue(XPT2046.ChannelSelect.Y_POSITION)
		
	def readZ1(self):
		return self.readValue(XPT2046.ChannelSelect.Z1_POSITION)

	def readZ2(self):
		return self.readValue(XPT2046.ChannelSelect.Z2_POSITION)

	def readBatteryVoltage(self):
		return self.readValue(XPT2046.ChannelSelect.BATTERY_VOLTAGE)

	def readTemperature0(self):
		return self.readValue(XPT2046.ChannelSelect.TEMPERATURE_0)

	def readTemperature1(self):
		return self.readValue(XPT2046.ChannelSelect.TEMPERATURE_1)

	def readAuxiliary(self):
		return self.readValue(XPT2046.ChannelSelect.AUXILIARY)

	def readTouchPressure(self):
		# Formula (option 1) according to the datasheet (12bit conversion)
		# RTouch = RX-Plate.(XPosition/4096).((Z1/Z2)-1)
		# Not sure of the correct value of RX-Plate.
		# Assuming the ratio is sufficient.
		# Empirically this function seems to yield a values in the range of 0.4
		# for a firm touch, and 1.75 for a light touch.

		x = self.readX();
		z1 = self.readZ1();
		z2 = self.readZ2();
		
		# Avoid division by zero exception
		if (z1 == 0) :
			z1 = 1
		
		xDivisor = 4096;
		if (self._ConversionSelect == XPT2046.ConversionSelect._8_BIT) :
			xDivisor = 256;

		result = ( x / xDivisor) * (( z2 / z1) - 1);
		return result;# Copyright 2012 Matthew Lowden

class button:
	def __init__(x1, x2, y1, y2, color):
		self.x1 = x1
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2
	

def screen_test(sec):
	screen.fill(WHITE)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(BLACK)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(RED)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(BLUE)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(GREEN)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(GBLUE)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(YELLOW)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(PERPLE)
	pygame.display.update()
	time.sleep(sec)
	screen.fill(WHITE)
	pygame.display.update()
	time.sleep(sec)

def test_point():
	screen.fill(WHITE)
	pygame.draw.rect(screen, BLACK, [  8,  8, 6, 6])
	pygame.draw.rect(screen, BLACK, [466,  8, 6, 6])
	pygame.draw.rect(screen, BLACK, [  8,258, 6, 6])
	pygame.draw.rect(screen, BLACK, [466,258, 6, 6])
	pygame.draw.rect(screen, BLACK, [237,133, 6, 6])
	pygame.draw.rect(screen, GREEN, [  9,  9, 4, 4])
	pygame.draw.rect(screen, GREEN, [467,  9, 4, 4])
	pygame.draw.rect(screen, GREEN, [  9,259, 4, 4])
	pygame.draw.rect(screen, GREEN, [467,259, 4, 4])
	pygame.draw.rect(screen, GREEN, [238,134, 4, 4])
	pygame.draw.rect(screen, BLUE, [ 10, 10, 2, 2])
	pygame.draw.rect(screen, BLUE, [468, 10, 2, 2])
	pygame.draw.rect(screen, BLUE, [ 10,260, 2, 2])
	pygame.draw.rect(screen, BLUE, [468,260, 2, 2])
	pygame.draw.rect(screen, BLUE, [239,135, 2, 2])
	pygame.draw.rect(screen, RED, [  0,  0, 2, 2])
	pygame.draw.rect(screen, RED, [478,  0, 2, 2])
	pygame.draw.rect(screen, RED, [  0,270, 2, 2])
	pygame.draw.rect(screen, RED, [478,270, 2, 2])
	pygame.draw.rect(screen, RED, [239,135, 2, 2])

def raw_touch():
	i = 0
	j = 0
	x = 0
	y = 0
	while(i<3 and j<3):
		x_read = int(xpt2046.readX())
		y_read = int(xpt2046.readY())
		if(x_read != 0 and y_read != 4095):
			x += x_read
			y += y_read
			i += 1
		else:
			j += 1
	return (-1, -1) if i<3 else (int(x/i), int(y/i))

def read_touch():
	global x_min, x_max, y_min, y_max
	x_rate = 459/(x_max-x_min)
	y_rate = 251/(y_max-y_min)
	x_adj = (469-x_max*x_rate + 10-x_min*x_rate)/2
	y_adj = (261-y_max*y_rate + 10-y_min*y_rate)/2
	x_read, y_read = raw_touch()
	if(x_read != -1 and y_read != -1):
		return int(x_read*x_rate+x_adj), int(y_read*y_rate+y_adj)
	else:
		return -1, -1

def calibration_touch():
	global x_min, x_max, y_min, y_max
	i = 0
	while(1):
		screen.fill(WHITE)
		pygame.draw.rect(screen, BLACK, [  8,  8, 6, 6])
		pygame.draw.rect(screen, GREEN, [  9,  9, 4, 4])
		pygame.draw.rect(screen, BLUE, [ 10, 10, 2, 2])
		pygame.display.update()
		x_read, y_read = raw_touch()
		if(x_read != -1 and y_read != -1):
			x_min, y_min = x_read, y_read
			i = 1
		elif(i == 1):
			break
	i = 0
	while(1):
		screen.fill(WHITE)
		pygame.draw.rect(screen, BLACK, [466, 8, 6, 6])
		pygame.draw.rect(screen, GREEN, [467, 9, 4, 4])
		pygame.draw.rect(screen, BLUE, [468, 10, 2, 2])
		pygame.display.update()
		x_read, y_read = raw_touch()
		if(x_read != -1 and y_read != -1):
			x_max, y_min = x_read, int((y_read+y_min)/2)
			i = 1
		elif(i == 1):
			break
	i = 0
	while(1):
		screen.fill(WHITE)
		pygame.draw.rect(screen, BLACK, [  8,258, 6, 6])
		pygame.draw.rect(screen, GREEN, [  9,259, 4, 4])
		pygame.draw.rect(screen, BLUE, [ 10,260, 2, 2])
		pygame.display.update()
		x_read, y_read = raw_touch()
		if(x_read != -1 and y_read != -1):
			x_min, y_max = int((x_read+x_min)/2), y_read
			i = 1
		elif(i == 1):
			break
	i = 0
	while(1):
		screen.fill(WHITE)
		pygame.draw.rect(screen, BLACK, [466,258, 6, 6])
		pygame.draw.rect(screen, GREEN, [467,259, 4, 4])
		pygame.draw.rect(screen, BLUE, [468,260, 2, 2])
		pygame.display.update()
		x_read, y_read = raw_touch()
		if(x_read != -1 and y_read != -1):
			x_max, y_max = int((x_read+x_max)/2), int((y_read+y_max)/2)
			i = 1
		elif(i == 1):
			break
	print(x_min, y_min, x_max, y_max)

def draw_corss(x, y):
	pygame.draw.rect(screen, BLACK, [0, y, 479,  1])
	pygame.draw.rect(screen, BLACK, [x, 0,   1,271])

#init
xpt2046 = XPT2046()

os.environ["SDL_FBDEV"] = "/dev/fb0"
pygame.init()
pygame.mouse.set_visible(False)

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
GBLUE  = (  0, 255, 255)
YELLOW = (255, 255,   0)
PERPLE  = (255,   0, 255)

					# resolution 0-479 0-271
screen = pygame.display.set_mode([640, 480])
screen_test(0.1)
calibration_touch()

#main
while True:
	x, y = read_touch()
	screen.fill(WHITE)
	draw_corss(x, y)
	pygame.display.update()
	stdout.write ("\r" + ('1 ' if x != -1 and y != -1 else '0 ') + "X:{:5d}".format(x) + " Y:{:5d}".format(y))
	stdout.flush ()
