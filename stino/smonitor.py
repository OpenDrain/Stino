#-*- coding: utf-8 -*-
# stino/smonitor.py

import sublime
import os
import serial
import threading
import time

from stino import const
from stino import stpanel

if const.sys_platform == 'windows':
	import _winreg

def getBaudrateList():
	baudrate_list = ['300', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']
	return baudrate_list

def genSerialPortList():
	serial_port_list = []
	has_ports = False
	if const.sys_platform == "windows":
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path,)
			has_ports = True
		except WindowsError:
			pass

		if has_ports:
			for i in xrange(128):
				try:
					name,value,type = _winreg.EnumValue(reg,i)
					serial_port_list.append(value)
				except WindowsError:
					pass
	else:
		if const.sys_platform == 'osx':
			dev_names = ['tty.*', 'cu.*']
		else:
			dev_names = ['ttyACM', 'ttyUSB']
		for dev_name in dev_names:
			cmd = 'ls /dev | grep %s' % dev_name
			serial_port_list += ['/dev/' + f.strip() for f in os.popen(cmd).readlines()]
	return serial_port_list

def isMonitorView(view):
	state = ''
	name = view.name()
	if name:
		if 'Serial Monitor - ' in name:
			state = True
	return state

class SerialPortListener:
	def __init__(self):
		self.serial_list = []
		self.is_alive = False

	def start(self):
		if not self.is_alive:
			self.is_alive = True
			listener_thread = threading.Thread(target=self.update)
			listener_thread.start()

	def update(self):
		while self.is_alive:
			self.serial_list = genSerialPortList()
			time.sleep(0.5)

	def stop(self):
		if self.is_alive:
			self.is_alive = False

	def getSerialList(self):
		return self.serial_list

class SerialMonitor:
	def __init__(self, serial_port):
		self.serial_port = serial_port
		self.name = 'Serial Monitor - ' + self.serial_port
		self.view = stpanel.MonitorView(self.name)
		self.is_alive = False

	def start(self):
		if not self.is_alive:
			self.is_alive = True
			monitor_thread = threading.Thread(target=self.receive)
			monitor_thread.start()

	def stop(self):
		if self.is_alive:
			self.is_alive = False

	def receive(self):
		while self.is_alive:
			time.sleep(2)
			time.sleep(0.1)

	def send(self, text):
		pass