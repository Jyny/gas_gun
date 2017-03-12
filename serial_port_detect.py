import serial.tools.list_ports

devs = serial.tools.list_ports.comports()

for dev in devs:
	print(dev.device)
	print(dev.hwid)

