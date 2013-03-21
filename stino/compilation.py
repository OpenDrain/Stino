#-*- coding: utf-8 -*-
# stino/compilation.py

import sublime
import threading
import time
import os
import re

from stino import const
from stino import osfile
from stino import utils
from stino import src
from stino import stpanel
from stino import arduino

def isWriteAccess(folder_path):
	state = True
	filename = 'write_test.stino'
	file_path = os.path.join(folder_path, filename)
	try:
		opened_file = open(file_path, 'w')
		opened_file.write('test')
	except IOError:
		state = False
	else:
		opened_file.close()
		os.remove(file_path)
	return state

def findSrcFiles(path):
	file_path_list = []
	build_folder_path = os.path.join(path, 'build')
	for (cur_path, sub_dirs, files) in os.walk(path):
		if build_folder_path in cur_path:
			continue
		for cur_file in files:
			cur_ext = os.path.splitext(cur_file)[1]
			if cur_ext in src.src_ext_list:
				cur_file_path = os.path.join(cur_path, cur_file)
				file_path_list.append(cur_file_path)
	return file_path_list

def findMainSrcFile(src_path_list):
	main_src_path = ''
	main_src_number = 0
	for src_path in src_path_list:
		src_text = osfile.readFileText(src_path)
		if src.isMainSrcText(src_text):
			main_src_path = src_path
			main_src_number += 1
	return (main_src_number, main_src_path)

def getPlatformFilePath(platform, board):
	platform_file_path = ''
	platform_file = ''
	if 'Arduino AVR' in platform:
		platform_file = 'arduino_avr.txt'
	elif 'teensy' in platform:
		if '3.0' in board:
			platform_file = 'teensy_arm.txt'
		else:
			platform_file = 'teensy_avr.txt'
	if platform_file:
		platform_file_path = os.path.join(const.compilation_script_root, platform_file)
	return platform_file_path

def getBoardInfoBlock150(board_file_path, board):
	board_info_block = []
	lines = osfile.readFileLines(board_file_path)
	info_block_list = utils.splitToBlocks(lines, sep = '.name')
	for info_block in info_block_list:
		for line in info_block:
			if '.name' in line:
				(key, board_name) = utils.getKeyValue(line)
			if '.container' in line:
				(key, board_name) = utils.getKeyValue(line)
				break
		if board_name == board:
			board_info_block = info_block
			break
	return board_info_block

def getBoardInfoBlock(board_file_path, board):
	board_info_block = []
	lines = osfile.readFileLines(board_file_path)
	info_block_list = utils.splitToBlocks(lines, sep = '.name', none_sep = 'menu.')
	for info_block in info_block_list:
		board_name_line = info_block[0]
		(key, board_name) = utils.getKeyValue(board_name_line)
		if board_name == board:
			board_info_block = info_block
			break
	return board_info_block

def getBoardCommonInfoBlock(board_info_block):
	board_common_info_block = []
	for line in board_info_block:
		if 'menu.' in line:
			break
		board_common_info_block.append(line)
	return board_common_info_block

def getBoardTypeInfoBlock(board_info_block, board_type):
	board_type_info_block = []
	for line in board_info_block:
		if board_type in line:
			board_type_info_block.append(line)
	return board_type_info_block

def genOptionInfoBlockList(info_block):
	block_list = utils.splitToBlocks(info_block, sep = '.name', key_length = 4)
	name_key_list = []
	for block in block_list:
		name_line = block[0]
		(key, value) = utils.getKeyValue(name_line)
		key = key.replace('.name', '.')
		name_key_list.append(key)

	option_info_block_list = []
	for name_key in name_key_list:
		option_info_block = []
		for line in info_block:
			if name_key in line:
				option_info_block.append(line)
		option_info_block_list.append(option_info_block)
	return option_info_block_list

def removeOptionInfoFromBlock(board_info_block, board_type_value_dict):
	info_block_list = []
	board_common_info_block = getBoardCommonInfoBlock(board_info_block)
	info_block_list.append(board_common_info_block)

	for board_type in board_type_value_dict:
		value = board_type_value_dict[board_type]
		board_type_info_block = getBoardTypeInfoBlock(board_info_block, board_type)
		option_info_block_list = genOptionInfoBlockList(board_type_info_block) 
		for option_info_block in option_info_block_list:
			name_line = option_info_block[0]
			(key, name) = utils.getKeyValue(name_line)
			if name == value:
				info_block_list.append(option_info_block)
				break
	return info_block_list                                                                                               

def genBoardInfoBlockList(board_file_path, board, board_type_value_dict):
	info_block_list = []
	if arduino.isBoard150(board_file_path):
		board_info_block = getBoardInfoBlock150(board_file_path, board)
		info_block_list.append(board_info_block)
	else:
		board_info_block = getBoardInfoBlock(board_file_path, board)
		if board_type_value_dict:
			info_block_list = removeOptionInfoFromBlock(board_info_block, board_type_value_dict)
		else:
			info_block_list.append(board_info_block)
	return info_block_list

def genInfoDictFromBlock(info_block):
	info_key_list = []
	info_dict = {}
	name_line = info_block[0]
	(name_key, name) = utils.getKeyValue(name_line)
	name_key = name_key.replace('.name', '.')
	for line in info_block[1:]:
		(key, value) = utils.getKeyValue(line)
		key = key.replace(name_key, '')
		info_key_list.append(key)
		info_dict[key] = value
	return (info_key_list, info_dict)

def getBoardInfoDict(info_block_list):
	board_info_key_list = []
	board_info_dict = {}
	for info_block in info_block_list:
		(info_key_list, info_dict) = genInfoDictFromBlock(info_block)
		board_info_key_list += info_key_list
		board_info_dict = dict(board_info_dict, **info_dict)
	return (board_info_key_list, board_info_dict)

def parseBoradInfo(board_file_path, board, board_type_value_dict):
	info_block_list = genBoardInfoBlockList(board_file_path, board, board_type_value_dict)
	(board_info_key_list, board_info_dict) = getBoardInfoDict(info_block_list)
	return (board_info_key_list, board_info_dict)

def getProgrammerInfoBlock(programmer_file_path, programmer):
	lines = osfile.readFileLines(programmer_file_path)
	info_block_list = utils.splitToBlocks(lines, sep = '.name')
	for info_block in info_block_list:
		programmer_name_line = info_block[0]
		(key, programmer_name) = utils.getKeyValue(programmer_name_line)
		if programmer_name == programmer:
			programmer_info_block = info_block
			break
	return programmer_info_block

def parseProgrammerInfo(programmer_file_path, programmer):
	programmer_info_dict = {}
	programmer_info_key_list = []
	if programmer_file_path:
		programmer_info_block = getProgrammerInfoBlock(programmer_file_path, programmer)
		(programmer_info_key_list, programmer_info_dict) = genInfoDictFromBlock(programmer_info_block)
	return (programmer_info_key_list, programmer_info_dict)

def regulariseToolsKey(key):
	info_list = key.split('.')
	new_key = ''
	for info in info_list[2:]:
		new_key += info
		new_key += '.'
	new_key = new_key[:-1]
	new_key = new_key.replace('params.', '')
	return new_key

def parsePlatformInfo(platform_file_path):
	platform_info_key_list = []
	platform_info_dict = {}
	lines = osfile.readFileLines(platform_file_path)
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			if 'build.extra_flags=' in line:
				continue
			(key, value) = utils.getKeyValue(line)
			if 'tools.' in key:
				key = regulariseToolsKey(key)
			platform_info_key_list.append(key)
			platform_info_dict[key] = value
	return (platform_info_key_list, platform_info_dict)

def regulariseDictValue(info_dict, info_key_list):
	pattern_text = r'\{\S+?}'
	for info_key in info_key_list:
		info_value = info_dict[info_key]
		key_list = re.findall(pattern_text, info_value)
		if key_list:
			key_list = [key[1:-1] for key in key_list]
			for key in key_list:
				replace_text = '{' + key + '}'
				if key in info_dict:
					value = info_dict[key]
				else:
					value = ''
				info_value = info_value.replace(replace_text, value)
			info_dict[info_key] = info_value
	return info_dict

class Compilation:
	def __init__(self, arduino_info, file_path):
		self.arduino_info = arduino_info
		self.sketch_folder_path = src.getSketchFolderPath(file_path)
		self.sketch_name = src.getSketchNameFromFolder(self.sketch_folder_path)
		compilation_name = 'Compilation_' + self.sketch_name
		self.output_panel = stpanel.STPanel(compilation_name)
		self.error_code = 0
		self.is_finished = False

		self.platform = const.settings.get('platform')
		self.board = const.settings.get('board')
		self.programmer = const.settings.get('programmer')

		self.cores_path = self.arduino_info.getCoresPath(self.platform)
		self.core_root = os.path.split(self.cores_path)[0]
		self.platform_file_path = os.path.join(self.core_root, 'platform.txt')
		if not os.path.isfile(self.platform_file_path):
			self.platform_file_path = getPlatformFilePath(self.platform, self.board)

		self.board_type_list = self.arduino_info.getBoardTypeList(self.platform, self.board)
		self.board_type_value_dict = {}
		for board_type in self.board_type_list:
			board_type_caption = self.arduino_info.getPlatformTypeCaption(self.platform, board_type)
			self.board_type_value_dict[board_type] = const.settings.get(board_type_caption)

		self.extra_compilation_flags = const.settings.get('extra_flags')
		self.arduino_root = const.settings.get('arduino_root')
		self.sketchbook_root = const.settings.get('sketchbook_root')
		serial_port = const.settings.get('serial_port')
		variant_path = os.path.join(self.core_root, 'variants')
		build_system_path = os.path.join(self.core_root, 'system')
		arduino_version = self.arduino_info.getVersion()
		
		self.base_info_dict = {}
		self.base_info_dict['runtime.ide.path'] = self.arduino_root
		self.base_info_dict['build.project_name'] = self.sketch_name
		self.base_info_dict['serial.port'] = serial_port
		self.base_info_dict['serial.port.file'] = serial_port
		self.base_info_dict['archive_file'] = 'core.a'
		self.base_info_dict['build.variant.path'] = variant_path
		self.base_info_dict['build.system.path'] = build_system_path
		self.base_info_dict['software'] = 'ARDUINO'
		self.base_info_dict['runtime.ide.version'] = '%d' % arduino_version
		self.base_info_dict['source_file'] = '{source_file}'
		self.base_info_dict['object_file'] = '{object_file}'
		self.base_info_dict['object_files'] = '{object_files}'
		self.base_info_dict['includes'] = '{includes}'

	def isReady(self):
		state = False
		self.error_code = 1
		if self.platform_file_path:
			state = True
			self.error_code = 0
		return state

	def isDone(self):
		return self.is_finished

	def start(self):
		if self.isReady:
			self.output_panel.clear()
			self.output_panel.addText('Start compiling...\n')
			compilation_thread = threading.Thread(target=self.compile)
			compilation_thread.start()

	def compile(self):
		self.post_compilation_process()
		sublime.set_timeout(self.run_compile, 0)

	def post_compilation_process(self):
		(main_src_number, main_src_path) = self.genMainSrcFileInfo()
		if main_src_number == 0:
			self.error_code = 2
			msg = 'Error: No main source file (containing setup() and loop() functions) was found.\n'
			self.output_panel.addText(msg)
		elif main_src_number > 1:
			self.error_code = 3
			msg = 'Error: More than one (%d) main source files (containing setup() and loop() functions) were found.\n' % main_src_number
			self.output_panel.addText(msg)
		else:
			self.checkBuildPath()
			self.info_dict = self.genInfoDict()
			self.core_src_path_list = self.genCoreSrcPathList()
			self.genHeaderList()


	def run_compile(self):
		if self.error_code == 0:
			self.is_finished = True

	def checkBuildPath(self):
		self.build_path = os.path.join(self.sketchbook_root, 'build')
		self.build_path = os.path.join(self.build_path, self.sketch_name)
		self.base_info_dict['build.path'] = self.build_path
		if os.path.isfile(self.build_path):
			os.remove(self.build_path)
		if not os.path.exists(self.build_path):
			os.makedirs(self.build_path)

	def genInfoDict(self):
		(board_info_key_list, board_info_dict) = self.genBoardInfo()
		(programmer_info_key_list, programmer_info_dict) = self.genProgrammerInfo()
		(platform_info_key_list, platform_info_dict) = self.genPlatformInfo()

		info_dict = self.base_info_dict
		info_key_list = board_info_key_list + programmer_info_key_list + platform_info_key_list
		info_dict = dict(info_dict, **board_info_dict)
		info_dict = dict(info_dict, **programmer_info_dict)
		info_dict = dict(info_dict, **platform_info_dict)

		info_dict['compiler.c.flags'] += ' '
		info_dict['compiler.c.flags'] += self.extra_compilation_flags
		info_dict['compiler.cpp.flags'] += ' '
		info_dict['compiler.cpp.flags'] += self.extra_compilation_flags

		if not 'compiler.path' in info_dict:
			compiler_path = os.path.join(self.arduino_root, '/tools/avr/bin')
			info_dict['compiler.path'] = compiler_path

		info_dict = regulariseDictValue(info_dict, info_key_list)
		return info_dict

	def genBoardInfo(self):
		board_file_path = self.arduino_info.getBoardFile(self.platform, self.board)
		board_info_dict = parseBoradInfo(board_file_path, self.board, self.board_type_value_dict)
		return board_info_dict
		
	def genProgrammerInfo(self):
		programmer_file_path = self.arduino_info.getProgrammerFile(self.platform, self.programmer)
		programmer_info_dict = parseProgrammerInfo(programmer_file_path, self.programmer)
		return programmer_info_dict

	def genPlatformInfo(self):
		platform_info_dict = parsePlatformInfo(self.platform_file_path)
		return platform_info_dict

	def genSketchSrcPathList(self):
		os.chdir(self.sketch_folder_path)
		sketch_src_path_list = findSrcFiles('.')
		return sketch_src_path_list

	def genCoreSrcPathList(self):
		core_folder = self.info_dict['build.core']
		core_folder_path = os.path.join(self.cores_path, core_folder)
		core_src_path_list = findSrcFiles(core_folder_path)
		return core_src_path_list

	def genMainSrcFileInfo(self):
		self.sketch_src_path_list = self.genSketchSrcPathList()
		os.chdir(self.sketch_folder_path)
		(main_src_number, main_src_path) = findMainSrcFile(self.sketch_src_path_list)
		return (main_src_number, main_src_path)

	def genHeaderList(self):
		os.chdir(self.sketch_folder_path)
		for sketch_src_path in self.sketch_src_path_list:
			src_text = osfile.readFileText(sketch_src_path)
			header_list = src.genHeaderListFromSketchText(src_text)
			print header_list
	