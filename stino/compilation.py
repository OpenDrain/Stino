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
					print key
					value = ''
				info_value = info_value.replace(replace_text, value)
			info_dict[info_key] = info_value
	return info_dict

class Compilation:
	def __init__(self, arduino_info, sketch_folder_path):
		self.arduino_info = arduino_info
		self.sketch_name = src.getSketchNameFromFolder(sketch_folder_path)
		compilation_name = 'Compilation_' + self.sketch_name
		self.output_panel = stpanel.STPanel(compilation_name)
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

		self.build_path = './build'
		self.extra_compilation_flags = const.settings.get('extra_flags')
		self.arduino_root = const.settings.get('arduino_root')
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
		self.base_info_dict['build.path'] = self.build_path
		self.base_info_dict['software'] = 'ARDUINO'
		self.base_info_dict['runtime.ide.version'] = '%d' % arduino_version
		self.base_info_dict['source_file'] = '{source_file}'
		self.base_info_dict['object_file'] = '{object_file}'
		self.base_info_dict['object_files'] = '{object_files}'

	def isReady(self):
		state = False
		if self.platform_file_path:
			state = True
		return state

	def isDone(self):
		return self.is_finished

	def start(self):
		if self.isReady:
			self.output_panel.addText('Start compiling...')
			compilation_thread = threading.Thread(target=self.compile)
			compilation_thread.start()

	def compile(self):
		self.run_preprocess()
		sublime.set_timeout(self.run_compile, 0)

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

	def run_preprocess(self):
		self.info_dict = self.genInfoDict()
		for key in self.info_dict:
			if 'pattern' in key:
				print key
				print self.info_dict[key]

	def run_compile(self):
		self.is_finished = True

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

	

	
		
	