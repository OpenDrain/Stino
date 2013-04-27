#-*- coding: utf-8 -*-
# stino/serial.py

import os

from . import const

if const.sys_platform == 'windows':
	if const.python_version < 3:
		import _winreg as winreg
	else:
		import winreg

def getBaudrateList():
	return const.baudrate_list

def checkSelectedSerialPort(serial_port_list):
	serial_port = const.settings.get('serial_port')
	if serial_port_list:
		if not serial_port in serial_port_list:
			serial_port = serial_port_list[0]
	else:
		serial_port = ''
	const.settings.set('serial_port', serial_port)

def genSerialPortList():
	serial_port_list = []
	has_ports = False
	if const.sys_platform == "windows":
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path,)
			has_ports = True
		except WindowsError:
			pass

		if has_ports:
			for i in xrange(128):
				try:
					name,value,type = winreg.EnumValue(reg,i)
					serial_port_list.append(value)
				except WindowsError:
					pass
	else:
		if const.sys_platform == 'osx':
			dev_names = ['tty.', 'cu.']
		else:
			dev_names = ['ttyACM', 'ttyUSB']
		
		serial_port_list = []
		dev_path = '/dev'
		dev_file_list = os.listdir(dev_path)
		for dev_file in dev_file_list:
			for dev_name in dev_names:
				if dev_name in dev_file:
					dev_file_path = os.path.join(dev_path, dev_file)
					serial_port_list.append(dev_file_path)

	checkSelectedSerialPort(serial_port_list)
	return serial_port_list