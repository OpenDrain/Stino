#-*- coding: utf-8 -*-
# stino/arduino.py

import os

from stino import utils
from stino import const
from stino import osfile

def getRealPath(path):
	if const.sys_platform == 'osx':
		path = os.path.join(path, 'Contents/Resources/JAVA')
	return path

def isArduinoRoot(path):
	state = False
	if path and os.path.isdir(path):
		path = getRealPath(path)
		hardware_path = os.path.join(path, 'hardware')
		lib_path = os.path.join(path, 'lib')
		version_file_path = os.path.join(lib_path, 'version.txt')
		if os.path.isdir(hardware_path) and os.path.isfile(version_file_path):
			state = True
	return state

def isCoreRoot(path):
	state = False
	if os.path.isdir(path):
		cores_path = os.path.join(path, 'cores')
		boards_file_path = os.path.join(path, 'boards.txt')
		if os.path.isdir(cores_path) or os.path.isfile(boards_file_path):
			state = True
	return state

def getPlatformFromFile(platform_file_path):
	lines = osfile.readFileLines(platform_file_path)
	for line in lines:
		if 'name' in line:
			(key, value) = utils.getKeyValue(line)
			platform = value
			break
	return platform

def getPlatformFromCoreRoot(core_root):
	platform = 'Arduino AVR Boards'
	platform_file_path = os.path.join(core_root, 'platform.txt')
	if os.path.isfile(platform_file_path):
		platform = getPlatformFromFile(platform_file_path)
	else:
		cores_path = os.path.join(core_root, 'cores')
		if os.path.isdir(cores_path):
			core_root_folder_name = os.path.split(core_root)[1]
			platform = core_root_folder_name + ' Boards'
	return platform

class Arduino:
	def __init__(self):
		pass

	def isReady(self):
		state = False
		arduino_root = self.getArduinoRoot()
		if arduino_root:
			state = True
		return state

	def genCoreRootList(self):
		core_root_list = []
		arduino_root = self.getArduinoRoot()
		sketchbook_root = self.getSketchbookRoot()
		path_list = [arduino_root, sketchbook_root]
		for path in path_list:
			hardware_path = os.path.join(path, 'hardware')
			dir_list = osfile.listDir(hardware_path, with_files = False)
			for cur_dir in dir_list:
				if cur_dir == 'tools':
					continue
				cur_dir_path = os.path.join(hardware_path, cur_dir)
				if isCoreRoot(cur_dir_path):
					core_root_list.append(cur_dir_path)
				else:
					subdir_list = osfile.listDir(cur_dir_path)
					for cur_subdir in subdir_list:
						cur_subdir_path = os.path.join(cur_dir_path, cur_subdir)
						if isCoreRoot(cur_subdir_path):
							core_root_list.append(cur_subdir_path)
		return core_root_list

	def genPlatformList(self):
		self.platform_list = []
		self.platform_core_root_dict = {}

		core_root_list = self.genCoreRootList()
		for core_root in core_root_list:
			platform = getPlatformFromCoreRoot(core_root)
			if not platform in self.platform_list:
				self.platform_list.append(platform)
		return self.platform_list

	def genPlatformBoardList(self):
		pass

	def setArduinoRoot(self, arduino_root):
		const.settings.set('arduino_root', arduino_root)
		const.save_settings()

	def getArduinoRoot(self):
		arduino_root = const.settings.get('arduino_root')
		if not isArduinoRoot(arduino_root):
			arduino_root = None
		return arduino_root

	def setSketchbookRoot(self, sketchbook_root):
		const.settings.set('sketchbook_root', sketchbook_root)
		const.save_settings()

	def getSketchbookRoot(self):
		sketchbook_root = const.settings.get('sketchbook_root')
		if not (sketchbook_root and os.path.isdir(sketchbook_root)):
			sketchbook_root = self.getDefaultSketchbookRoot()
			self.setSketchbookRoot(sketchbook_root)
		return sketchbook_root

	def getDefaultSketchbookRoot(self):
		if const.sys_platform == 'windows':
			import _winreg
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,\
	            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',)
			document_root = _winreg.QueryValueEx(key, 'Personal')[0]
			sketchbook_root = os.path.join(document_root, 'Arduino')
		elif const.sys_platform == 'linux':
			home_root = os.getenv('HOME')
			sketchbook_root = os.path.join(home_root, 'sketchbook')
		elif const.sys_platform == 'osx':
			home_root = os.getenv('HOME')
			document_root = os.path.join(home_path, 'Documents')
			sketchbook_root = os.path.join(document_root, 'Arduino')

		libraries_path = os.path.join(sketchbook_root, 'libraries')
		hardware_path = os.path.join(sketchbook_root, 'hardware')
		path_list = [sketchbook_root, libraries_path, hardware_path]
		for path in path_list:
			if not os.path.exists(path):
				os.mkdir(path)
		return sketchbook_root