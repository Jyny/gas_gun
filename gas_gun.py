from collections import deque
from pygame.locals import *
from sys import stdout
import pygame, sys, os
import RPi.GPIO as GPIO
import time

BLACK = (  0,   0,   0)
WHITE = (255, 255, 255)
RED   = (255,   0,   0)
GREEN = (  0, 255,   0)
BLUE  = (  0,   0, 255)
GBLUE  = (  0, 255, 255)
YELLOW = (255, 255,   0)
PERPLE  = (255,   0, 255)

# screen settings
global x_min, x_max, y_min, y_max
x_min = 218
y_min = 454
x_max = 3894
y_max = 3795

global x, y
x = -1
y = -1

# exec_stat variables
global money_input, money_expect_cost, money_cost, exec_stat
global gas_expect_out, gas_out, gas_class, gas_info, mode, uni_unm
uni_unm = ''
mode = 0
gas_class = ''
gas_info = {'92':35.62, '95':37.15, '98':39.19}
money_expect_cost = 0
gas_expect_out = 0
money_cost = 0
gas_out = 0
money_input = 0
exec_stat = 0

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
	def __init__(self, butt_id, x1, x2, y1, y2, color, text):
		self.id = butt_id
		self.x1 = x1
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2
		self.color = color
		self.text = text
		self.size = 20
		self.dark = 40

	def draw(self, screen):
		dark = (
			self.color[0]-self.dark if self.color[0] > self.dark else self.color[0],
			self.color[1]-self.dark if self.color[1] > self.dark else self.color[1],
			self.color[2]-self.dark if self.color[2] > self.dark else self.color[2])
		pygame.draw.rect(screen, dark, [self.x1, self.y1, self.x2-self.x1, self.y2-self.y1])
		pygame.draw.rect(screen, self.color, [self.x1+2, self.y1+2, self.x2-self.x1-4, self.y2-self.y1-4])
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', self.size).render(self.text, False, BLACK)
		text_rect = text.get_rect(center=((self.x1+self.x2)/2, (self.y1+self.y2)/2))
		screen.blit(text, text_rect)
	
	def is_click(self, x, y):
		if( x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2):
			return True
		else:
			return False

	def blink(self, screen):
		dark = (
			self.color[0]-self.dark if self.color[0] > self.dark else self.color[0],
			self.color[1]-self.dark if self.color[1] > self.dark else self.color[1],
			self.color[2]-self.dark if self.color[2] > self.dark else self.color[2])
		pygame.draw.rect(screen, YELLOW, [self.x1, self.y1, self.x2-self.x1, self.y2-self.y1])
		pygame.draw.rect(screen, dark, [self.x1+2, self.y1+2, self.x2-self.x1-4, self.y2-self.y1-4])
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', self.size).render(self.text, False, BLACK)
		text_rect = text.get_rect(center=((self.x1+self.x2)/2, (self.y1+self.y2)/2))
		screen.blit(text, text_rect)
		
class setting_button:
	def __init__(self, butt_id, x1, x2, y1, y2, text):
		self.id = butt_id
		self.x1 = x1
		self.x2 = x2
		self.y1 = y1
		self.y2 = y2
		self.color = BLUE
		self.text = text
		self.size = 20
		self.dark = 40
		self.stat = 0

	def draw(self, screen):
		dark = (
			self.color[0]-self.dark if self.color[0] > self.dark else self.color[0],
			self.color[1]-self.dark if self.color[1] > self.dark else self.color[1],
			self.color[2]-self.dark if self.color[2] > self.dark else self.color[2])
		pygame.draw.rect(screen,
			(YELLOW if self.stat == 1 else dark),
			[self.x1, self.y1, self.x2-self.x1, self.y2-self.y1])
		pygame.draw.rect(screen,
			(GBLUE if self.stat == 1 else BLUE),
			[self.x1+2, self.y1+2, self.x2-self.x1-4, self.y2-self.y1-4])
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', self.size).render(self.text, False, BLACK)
		text_rect = text.get_rect(center=((self.x1+self.x2)/2, (self.y1+self.y2)/2))
		screen.blit(text, text_rect)
	
	def is_click(self, x, y):
		if( x >= self.x1 and x <= self.x2 and y >= self.y1 and y <= self.y2):
			return True
		else:
			return False

	def blink(self, screen):
		dark = (
			self.color[0]-self.dark if self.color[0] > self.dark else self.color[0],
			self.color[1]-self.dark if self.color[1] > self.dark else self.color[1],
			self.color[2]-self.dark if self.color[2] > self.dark else self.color[2])
		pygame.draw.rect(screen, YELLOW, [self.x1, self.y1, self.x2-self.x1, self.y2-self.y1])
		pygame.draw.rect(screen, dark, [self.x1+2, self.y1+2, self.x2-self.x1-4, self.y2-self.y1-4])
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', self.size).render(self.text, False, BLACK)
		text_rect = text.get_rect(center=((self.x1+self.x2)/2, (self.y1+self.y2)/2))
		screen.blit(text, text_rect)
	
	def set_stat(self, stat):
		if(stat == 1):
			self.stat = 1
		else:
			self.stat = 0

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
	pygame.draw.rect(screen, WHITE, [0, y, 479,  1])
	pygame.draw.rect(screen, WHITE, [x, 0,   1,271])

def button_show():
	global exec_stat
	global x, y

	if exec_stat == 0:
		x, y = read_touch()
		if x == -1 and y == -1:
			return
		else:
			exec_stat += 1

	for butt in buttons:
		if butt.is_click(x, y):
			butt.blink(screen)
			butt_press_handler(butt.id)
		else:
			butt.draw(screen)
			butt_click_handler(butt.id)

	for butt in setting_butts:
		if butt.is_click(x, y):
			butt.blink(screen)
			butt_press_handler(butt.id)
		else:
			butt.draw(screen)
			butt_click_handler(butt.id)

	pygame.draw.rect(screen, WHITE, [  0, 42,291,229])

def butt_press_handler(butt_id):
	if(butt_id not in butt_press_event):
		butt_press_event.append(butt_id)

def butt_click_handler(butt_id):
	if(butt_id in butt_press_event):
		butt_press_event.remove(butt_id)
		butt_click_event.append(butt_id)

def clear():
	global money_input, money_expect_cost, money_cost, exec_stat
	global gas_expect_out, gas_out, gas_class, gas_info, mode, uni_unm
	gas_class = ''
	money_expect_cost = 0
	gas_expect_out = 0
	money_cost = 0
	gas_out = 0
	money_input = 0
	exec_stat = 0

def butt_event_handler():
	global exec_stat
	while(len(butt_click_event)>0):
		butt = butt_click_event.popleft()
		if butt == 10:
			pass
		if butt == 11:
			if exec_stat < 5:
				exec_stat += 1
		if butt == 12:
			if exec_stat >= 5:
				clear()
			elif exec_stat > 1:
				exec_stat -= 1

def UI_show():
	global money_input, money_expect_cost, money_cost, exec_stat
	global gas_expect_out, gas_out, gas_class, gas_info, mode, uni_unm
	if exec_stat == 0:
		img = pygame.image.load('./gas_station.jpg')
		img_rect = img.get_rect(center=(240, 136))
		screen.blit(img, img_rect)
	if exec_stat == 1:
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 30).render(str(exec_stat), False, BLACK)
		text_rect = text.get_rect(center=(145, 114))
		screen.blit(text, text_rect)
	if exec_stat == 2:
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 30).render(str(exec_stat), False, BLACK)
		text_rect = text.get_rect(center=(145, 114))
		screen.blit(text, text_rect)
	if exec_stat == 3:
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 30).render(str(exec_stat), False, BLACK)
		text_rect = text.get_rect(center=(145, 114))
		screen.blit(text, text_rect)
	if exec_stat == 4:
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 30).render(str(exec_stat), False, BLACK)
		text_rect = text.get_rect(center=(145, 114))
		screen.blit(text, text_rect)
	if exec_stat == 5:
		text = pygame.font.Font('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 30).render(str(exec_stat), False, BLACK)
		text_rect = text.get_rect(center=(145, 114))
		screen.blit(text, text_rect)

# init
xpt2046 = XPT2046()

os.environ["SDL_FBDEV"] = "/dev/fb0"
pygame.init()
pygame.mouse.set_visible(False)

					# resolution 0-479 0-271
screen = pygame.display.set_mode([640, 480])

# init tests
#screen_test(0.1)
#calibration_touch()

# init buttons 
buttons = []
buttons.append(button(0, 356,415,212,271, PERPLE, '0'))
start_button = button(11, 294,353,212,271, GREEN, 'START')
end_button = button(12, 418,477,212,271, RED, 'END')
start_button.size = 18
end_button.size = 18
buttons.append(start_button)
buttons.append(end_button)
buttons.append(button(10, 418,477,  0, 29, WHITE, b'\xe2\x86\x90'.decode()))
buttons.append(button(1, 294,353, 32, 89, PERPLE, '1'))
buttons.append(button(2, 356,415, 32, 89, PERPLE, '2'))
buttons.append(button(3, 418,477, 32, 89, PERPLE, '3'))
buttons.append(button(4, 294,353, 92,149, PERPLE, '4'))
buttons.append(button(5, 356,415, 92,149, PERPLE, '5'))
buttons.append(button(6, 418,477, 92,149, PERPLE, '6'))
buttons.append(button(7, 294,353,152,209, PERPLE, '7'))
buttons.append(button(8, 356,415,152,209, PERPLE, '8'))
buttons.append(button(9, 418,477,152,209, PERPLE, '9'))

setting_butts = []
setting_butts.append(setting_button(14,   2,144, 0, 39, b'\xe8\xa8\xad\xe5\xae\x9a\xe6\xb2\xb9\xe9\x87\x8f'.decode()))
setting_butts.append(setting_button(15, 145,291, 0, 39, b'\xe8\xa8\xad\xe5\xae\x9a\xe9\x87\x91\xe9\xa1\x8d'.decode()))
setting_butts.append(setting_button(13, 294,415,  0, 29, b'\xe7\xb5\xb1\xe4\xb8\x80\xe7\xb7\xa8\xe8\x99\x9f'.decode()))

# event queue
butt_press_event = deque()
butt_click_event = deque()

#main
while True:
	x, y = read_touch()
	screen.fill(BLACK)
	button_show()
	butt_event_handler()
	UI_show()
	#draw_corss(x, y)
	pygame.display.update()
	pygame.display.flip()
	#stdout.write ("\r" + ('1 ' if x != -1 and y != -1 else '0 ') + "X:{:5d}".format(x) + " Y:{:5d}".format(y))
	##stdout.flush ()
