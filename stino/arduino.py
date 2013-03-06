#-*- coding: utf-8 -*-
# stino/arduino.py

import os

from stino import utils
from stino import const
from stino import osfile

def genKey(info, base_info):
	key = info + const.info_sep + base_info
	return key

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
				
def parseBoardFile150(platform, boards_file_path):
	board_list = []
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}

	board_type = 'menu.cpu'
	board_type_list = [board_type]
	type_key = genKey(board_type, platform)
	type_caption_dict = {type_key:'Processor'}

	lines = osfile.readFileLines(boards_file_path)
	board_info_block_list = utils.splitToBlocks(lines, sep = '.name')
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

		board_key = genKey(board, platform)
		key = genKey(board_type, board_key)

		if not board in board_list:
			board_list.append(board)

			board_file_dict[board_key] = boards_file_path
			if cpu:
				board_type_list_dict[board_key] = board_type_list
				board_item_list_dict[key] = [cpu]
		else:
			if cpu and (not cpu in board_item_list_dict[key]):
				board_item_list_dict[key].append(cpu)
	return (board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict)

def parseBoardFile(platform, boards_file_path):
	board_list = []
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}
	type_caption_dict = {}

	(boards_file_header_block, boards_file_body_block) = splitBoardsFile(boards_file_path)
	(board_type_list, board_type_caption_dict) = parseBoardHeader(boards_file_header_block)

	for board_type in board_type_caption_dict:
		type_key = genKey(board_type, platform)
		type_caption_dict[type_key] = board_type_caption_dict[board_type]

	board_info_block_list = utils.splitToBlocks(boards_file_body_block, sep = '.name')
	for board_info_block in board_info_block_list:
		board_name_line = board_info_block[0]
		(key, board) = utils.getKeyValue(board_name_line)
		if not board in board_list:
			board_list.append(board)

			board_key = genKey(board, platform)
			board_file_dict[board_key] = boards_file_path
			board_type_list_dict[board_key] = []

			for board_type in board_type_list:
				item_list = []
				board_type_info_block = utils.getTypeInfoBlock(board_info_block, board_type)
				item_blocks = utils.splitToBlocks(board_type_info_block, sep = '.name', key_length = 4)
				for item_block in item_blocks:
					item_name_line = item_block[0]
					(key, item) = utils.getKeyValue(item_name_line)
					if not item in item_list:
						item_list.append(item)
				if item_list:
					board_type_list_dict[board_key].append(board_type)
					key = genKey(board_type, board_key)
					board_item_list_dict[key] = item_list
	return (board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict)

def parseBoardInfo(platform, core_root):
	board_list = []
	boards_file_path = os.path.join(core_root, 'boards.txt')
	if os.path.isfile(boards_file_path):
		if isBoard150(boards_file_path):
			(board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict) = parseBoardFile150(platform, boards_file_path)
		else:
			(board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict) = parseBoardFile(platform, boards_file_path)
	return (board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict)

def parseProgrammerInfo(platform, core_root):
	programmer_list = []
	programmer_file_dict = {}
	programmers_file_path = os.path.join(core_root, 'programmers.txt')
	if os.path.isfile(programmers_file_path):
		lines = osfile.readFileLines(programmers_file_path)
		programmer_info_block_list = utils.splitToBlocks(lines, sep = '.name')
		for programmer_info_block in programmer_info_block_list:
			programmer_name_line = programmer_info_block[0]
			(key, programmer) = utils.getKeyValue(programmer_name_line)
			if not programmer in programmer_list:
				programmer_list.append(programmer)

				programmer_key = genKey(programmer, platform)
				programmer_file_dict[programmer_key] = programmers_file_path
	return (programmer_list, programmer_file_dict)

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

	def genPlatformBoardLists(self):
		self.platform_board_lists_dict = {}
		self.board_file_dict = {}
		self.board_type_list_dict = {}
		self.board_item_list_dict = {}
		self.type_caption_dict = {}

		platform_list = self.genPlatformList()
		for platform in platform_list:
			self.platform_board_lists_dict[platform] = []
			self.board_type_list_dict[platform] = []
			core_root_list = self.getCoreRootList(platform)
			for core_root in core_root_list:
				(board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict) = parseBoardInfo(platform, core_root)
				if board_list:
					self.platform_board_lists_dict[platform].append(board_list)
					self.board_file_dict = dict(self.board_file_dict, **board_file_dict)
					self.board_type_list_dict = dict(self.board_type_list_dict, **board_type_list_dict)
					self.board_item_list_dict = dict(self.board_item_list_dict, **board_item_list_dict)
					self.type_caption_dict = dict(self.type_caption_dict, **type_caption_dict)
		print self.platform_board_lists_dict
		print self.board_file_dict
		print self.board_type_list_dict
		print self.board_item_list_dict
		print self.type_caption_dict

	def genPlatformProgrammerLists(self):
		self.platform_programmer_lists_dict = {}
		self.programmer_file_dict = {}
		platform_list = self.getPlatformList()
		for platform in platform_list:
			self.platform_programmer_lists_dict[platform] = []
			core_root_list = self.getCoreRootList(platform)
			for core_root in core_root_list:
				(programmer_list, programmer_file_dict) = parseProgrammerInfo(platform, core_root)
				if programmer_list:
					self.platform_programmer_lists_dict[platform].append(programmer_list)
					self.programmer_file_dict = dict(self.programmer_file_dict, **programmer_file_dict)

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

	def getPlatformList(self):
		return self.platform_list

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

	def getBoardLists(self, platform):
		board_lists = []
		if platform in self.platform_list:
			board_lists = self.platform_board_lists_dict[platform]
		return board_lists

	def getBoardFile(self, platform, board):
		file_path = ''
		key = genKey(board, platform)
		if key in self.board_file_dict:
			file_path = self.board_file_dict[key]
		return file_path

	def getBoardTypeList(self, platform, board):
		type_list = []
		key = genKey(board, platform)
		if key in self.board_type_list_dict:
			type_list = self.board_type_list_dict[key]
		return type_list

	def getBoardItemList(self, platform, board, board_type):
		item_list = []
		board_key = genKey(board, platform)
		type_key = genKey(board_type, board_key)
		if type_key in self.board_item_list_dict:
			item_list = self.board_item_list_dict[type_key]
		return item_list

	def getPlatformTypeCaption(self, platform, board_type):
		caption = ''
		key = genKey(board_type, platform)
		if key in self.type_caption_dict:
			caption = self.type_caption_dict[key]
		return caption

	def getProgrammerLists(self, platform):
		programmer_lists = []
		if platform in self.platform_list:
			programmer_lists = self.platform_programmer_lists_dict[platform]
		return programmer_lists

	def getProgrammerFile(self, platform, programmer):
		file_path = ''
		key = genKey(programmer, platform)
		if key in self.programmer_file_dict:
			file_path = self.programmer_file_dict[programmer]
		return file_path

