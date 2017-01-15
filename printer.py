import serial
import time

def init():
	s = serial.Serial()
	s.port = "/dev/ttyACM0"
	s.baudrate = 9600
	s.bytesize = serial.EIGHTBITS
	s.parity = serial.PARITY_NONE
	s.stopbits = serial.STOPBITS_ONE
	s.timeout = 1

	s.open()
	s.write(serial.to_bytes([0x1D, 0x21, 0x11]))

#def change_size():
def underline_on():
	s.write(serial.to_bytes([0x1B, 0x2D, 1]))
def underline_off():
        s.write(serial.to_bytes([0x1B, 0x2D, 0]))

#change word size
def large():
	s.write(serial.to_bytes([0x1D, 0x21, 0x33]))
def mediun():
        s.write(serial.to_bytes([0x1D, 0x21, 0x22]))
def small():
        s.write(serial.to_bytes([0x1D, 0x21, 0x11]))
def defult():
        s.write(serial.to_bytes([0x1D, 0x21, 0x00]))

#double_strike >> twice dark
def double_strike_on(): 
	s.write(serial.to_bytes([0x1B, 0x47, 0x01]))
def double_strike_off():
        s.write(serial.to_bytes([0x1B, 0x47, 0x00]))

#emphasized >> "B" twice dark
def emphasized_on():
	s.write(serial.to_bytes([0x1B, 0x45, 0x01]))
def emphasized_off():
        s.write(serial.to_bytes([0x1B, 0x45, 0x00]))

#smoothing >> not sure how it work
def smoothing_on():
	s.write(serial.to_bytes([0x1D, 0x62, 0x01]))
def smoothing_off():
	s.write(serial.to_bytes([0x1D, 0x62, 0x00]))

#reverse >> reverse black and white
def reverse_on():
	s.write(serial.to_bytes([0x1D, 0x42, 0x01]))
def reverse_off():
	s.write(serial.to_bytes([0x1D, 0x42, 0x00]))

#upside-down
def upside_down_on():
	s.write(serial.to_bytes([0x1B, 0x7B, 0x01]))
def upside_down_off():
	s.write(serial.to_bytes([0x1B, 0x7B, 0x00]))

#clockwise (not for chinese)
def clockwise_on():
	s.write(serial.to_bytes([0x1B, 0x56, 0x01]))
def clockwise_off():
	s.write(serial.to_bytes([0x1B, 0x56, 0x00]))

#set_mode (no use)
def set_mode():
	s.write(serial.to_bytes([0x1B, 0x21, 0x80]))

#bar_code  >>  [0x1D, 0x6B, (mode),(code), 0]  /mode can be 0~6  
def bar_code():
	s.write(serial.to_bytes([0x1D, 0x6B, 6,36,43,45,47,0 ]))

def print_resp(insert,estimate_money,estimate_oil,cost,oil_add,type,rest):

	s = serial.Serial()
	s.port = "/dev/ttyACM0"
	s.baudrate = 9600
	s.bytesize = serial.EIGHTBITS
	s.parity = serial.PARITY_NONE
	s.stopbits = serial.STOPBITS_ONE
	s.timeout = 1

	s.open()
	s.write(serial.to_bytes([0x1D, 0x21, 0x11]))

	s.write(b'\xa7\xeb\xa4J\xa1G')
	s.write(str(insert).encode('big5'))

	s.write(b'\n\xb9w\xadp\xaa\xf7\xc3B\xa1G')
	s.write(str(estimate_money).encode('big5'))

	s.write(b'\n\xb9w\xadp\xa5[\xaao\xa1G')
	s.write(str(estimate_oil).encode('big5'))

	s.write(b'\n\xaa\xf7\xc3B\xa1G')
	s.write(str(cost).encode('big5'))

	s.write(b'\n\xa5[\xaao\xa1G')
	s.write(str(oil_add).encode('big5'))

	s.write(b'\n\xaao\xba\xd8\xa1G')
	s.write(str(type).encode('big5'))
	
	s.write(b'\n\xb5\xb2\xbel\xa1G')
	s.write(str(rest).encode('big5'))

	#cut paper
	s.write("\n\n\n\n\n".encode('big5'))
	s.write(serial.to_bytes([0x1D, 0x56, 0, 0]))




#for i in range(10):
	#s.write("皜祈岫??\n".encode('big5'))
#clockwise_on()
#s.write("13132132132312\n".encode('big5'))
#bar_code()
#s.write("皜祈岫??\n".encode('big5'))


#double_strike_on()
#s.write("皜祈岫??\n".encode('big5'))
#double_strike_off()
#s.write("皜祈岫??\n".encode('big5'))

#s.write("\n摰?憒喳末".encode('big5'))

#s.write("\n\n\n\n\n".encode('big5'))
#s.write(serial.to_bytes([0x1D, 0x56, 0, 0]))
