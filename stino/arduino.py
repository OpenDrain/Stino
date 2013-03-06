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
		if 'name=' in line:
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

def findCoresPath(core_root_list):
	cores_path = ''
	for core_root in core_root_list:
		path = os.path.join(core_root, 'cores')
		if os.path.isdir(path):
			cores_path = path
			break
	return cores_path

def splitBoardsFile(boards_file_path):
	boards_file_header_block = []
	boards_file_body_block = []
	lines = osfile.readFileLines(boards_file_path)
	is_header = True
	for line in lines:
		if '.name' in line:
			is_header = False
		if is_header:
			boards_file_header_block.append(line)
		else:
			boards_file_body_block.append(line)
	return (boards_file_header_block, boards_file_body_block)

def isBoard150(boards_file_path):
	state = False
	text = osfile.readFileText(boards_file_path)
	if '.container=' in text:
		state = True
	return state

def parseBoardHeader(boards_file_header_block):
	board_type_list = []
	board_type_caption_dict = {}
	for line in boards_file_header_block:
		line = line.strip()
		if line and (not '#' in line):
			if '=' in line:
				(board_type, board_type_caption) = utils.getKeyValue(line)
				if not board_type in board_type_list:
					board_type_list.append(board_type)
					board_type_caption_dict[board_type] = board_type_caption
	return (board_type_list, board_type_caption_dict)
				
def parseBoardBody150(boards_file_body_block):
	print 'board150'
	board_list = []
	board_info_block_list = utils.splitToBlocks(boards_file_body_block, sep = '.name')
	for board_info_block in board_info_block_list:
		cpu = ''
		for line in board_info_block:
			if '.name' in line:
				(key, board) = utils.getKeyValue(line)
			if '.cpu' in line:
				(key, cpu) = utils.getKeyValue(line)
			if '.container' in line:
				(key, board) = utils.getKeyValue(line)
				break
		if not board in board_list:
			board_list.append(board)
		else:
			pass
	return board_list

def parseBoardBody(boards_file_body_block, board_type_list):
	board_list = []
	board_info_block_list = utils.splitToBlocks(boards_file_body_block, sep = '.name')
	for board_info_block in board_info_block_list:
		board_name_line = board_info_block[0]
		(key, board) = utils.getKeyValue(board_name_line)
		if not board in board_list:
			board_list.append(board)
	return board_list

def parseBoardInfo(platform, core_root):
	board_list = []
	boards_file_path = os.path.join(core_root, 'boards.txt')
	if os.path.isfile(boards_file_path):
		(boards_file_header_block, boards_file_body_block) = splitBoardsFile(boards_file_path)
		if isBoard150(boards_file_path):
			board_type_list = ['menu.cpu']
			board_type_caption_dict = {'menu.cpu':'Processor'}
			board_list = parseBoardBody150(boards_file_body_block)
		else:
			(board_type_list, board_type_caption_dict) = parseBoardHeader(boards_file_header_block)
			board_list = parseBoardBody(boards_file_body_block, board_type_list)
	return board_list

def parseProgrammerInfo(core_root):
	programmer_list = []
	programmers_file_path = os.path.join(core_root, 'programmers.txt')
	if os.path.isfile(programmers_file_path):
		lines = osfile.readFileLines(programmers_file_path)
		programmer_info_block_list = utils.splitToBlocks(lines, sep = '.name')
		for programmer_info_block in programmer_info_block_list:
			programmer_name_line = programmer_info_block[0]
			(key, programmer) = utils.getKeyValue(programmer_name_line)
			programmer_list.append(programmer)
	return programmer_list

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
		self.platform_core_root_list_dict = {}
		self.platform_cores_path_dict = {}

		core_root_list = self.genCoreRootList()
		for core_root in core_root_list:
			platform = getPlatformFromCoreRoot(core_root)
			if not platform in self.platform_list:
				self.platform_list.append(platform)
				self.platform_core_root_list_dict[platform] = [core_root]
			else:
				self.platform_core_root_list_dict[platform].append(core_root)
		
		for platform in self.platform_list:
			core_root_list = self.getCoreRootList(platform)
			cores_path = findCoresPath(core_root_list)
			self.platform_cores_path_dict[platform] = cores_path

		for platform in self.platform_cores_path_dict:
			cores_path = self.getCoresPath(platform)
			if not cores_path:
				self.platform_list.remove(platform)
		return self.platform_list

	def genPlatformBoardList(self):
		platform_list = self.genPlatformList()
		for platform in platform_list:
			core_root_list = self.getCoreRootList(platform)
			for core_root in core_root_list:
				board_list = parseBoardInfo(platform, core_root)
				print board_list

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

	def getCoreRootList(self, platform):
		core_root_list = []
		if platform in self.platform_list:
			core_root_list = self.platform_core_root_list_dict[platform]
		return core_root_list

	def getCoresPath(self, platform):
		cores_path = ''
		if platform in self.platform_list:
			cores_path = self.platform_cores_path_dict[platform]
		return cores_path