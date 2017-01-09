from sys import stdout
import RPi.GPIO as GPIO
import time

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

#main
try:
	xpt2046 = XPT2046()
	while True:
		x = xpt2046.readX()
		y = xpt2046.readY()
		stdout.write ("\r" + "X:%5s" % x + " Y:%5s" % y)
		stdout.flush ()
except KeyboardInterrupt:
	stdout.write ("\n")
except Exception:
	raise
