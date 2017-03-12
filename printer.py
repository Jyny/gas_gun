import serial
import time

def print_resp(s, insert, estimate_money, estimate_oil, cost, oil_add, type, rest, num):
	'''
	s = serial.Serial()
	s.port = "/dev/ttyACM0"
	s.baudrate = 9600
	s.bytesize = serial.EIGHTBITS
	s.parity = serial.PARITY_NONE
	s.stopbits = serial.STOPBITS_ONE
	s.timeout = 1
	'''

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
	
	if num != '':
		s.write(b'\n\xb2\xce\xa4@\xbds\xb8\xb9\xa1G\n')
		s.write(str(num).encode('big5'))

	#cut paper
	s.write("\n\n\n\n\n".encode('big5'))
	s.write(serial.to_bytes([0x1D, 0x56, 0, 0]))
