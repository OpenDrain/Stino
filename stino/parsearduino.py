#-*- coding: utf-8 -*-
# stino/parsearduino.py

import os
import re

from . import const
from . import textutil
from . import fileutil

def isPlatformCoreRoot(path):
	state = False
	if os.path.isdir(path):
		cores_path = os.path.join(path, 'cores')
		boards_file_path = os.path.join(path, 'boards.txt')
		if os.path.isdir(cores_path) or os.path.isfile(boards_file_path):
			state = True
	return state

def findPlatformCoreRootList(path):
	platform_core_root_list = []
	dir_list = fileutil.listDir(path, with_files = False)
	for cur_dir in dir_list:
		if cur_dir.lower() == 'tools':
			continue
		cur_dir_path = os.path.join(path, cur_dir)
		if isPlatformCoreRoot(cur_dir_path):
			platform_core_root_list.append(cur_dir_path)
		else:
			platform_core_root_list += findPlatformCoreRootList(cur_dir_path)
	return platform_core_root_list

def getPlatformFromFile(platform_file_path):
	lines = fileutil.readFileLines(platform_file_path)
	for line in lines:
		if 'name=' in line:
			(key, platform) = textutil.getKeyValue(line)
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
			arduino_path = os.path.join(cores_path, 'arduino')
			if not os.path.isdir(arduino_path):
				core_root_folder_name = os.path.split(core_root)[1]
				core_root_folder_name = core_root_folder_name[0].upper() + core_root_folder_name[1:].lower()
				platform = core_root_folder_name + ' Boards'
	platform = platform.replace('Boards', 'Board')
	return platform

def findSrcCoresPath(core_root_list):
	src_cores_path = ''
	for core_root in core_root_list:
		path = os.path.join(core_root, 'cores')
		if os.path.isdir(path):
			dir_list = fileutil.listDir(path, with_files = False)
			if dir_list:
				src_cores_path = path
				break
	return src_cores_path

def isBoard150(boards_file_path):
	state = False
	text = fileutil.readFileText(boards_file_path)
	if '.container=' in text:
		state = True
	return state

def parseBoardFile150(platform, boards_file_path):
	board_list = []
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}

	board_type = 'menu.cpu'
	board_type_list = [board_type]
	type_key = textutil.genKey(platform, board_type)
	type_caption_dict = {type_key:'Processor'}

	lines = fileutil.readFileLines(boards_file_path)
	board_info_block_list = textutil.splitToBlocks(lines, sep = '.name')
	for board_info_block in board_info_block_list:
		cpu = ''
		for line in board_info_block:
			if '.name' in line:
				(key, board) = textutil.getKeyValue(line)
			if '.cpu' in line:
				(key, cpu) = textutil.getKeyValue(line)
			if '.container' in line:
				(key, board) = textutil.getKeyValue(line)
				break

		board_key = textutil.genKey(platform, board)
		key = textutil.genKey(board_key, board_type)

		if not board in board_list:
			board_list.append(board)

			board_file_dict[board_key] = boards_file_path
			if cpu:
				board_type_list_dict[board_key] = board_type_list
				board_item_list_dict[key] = [cpu]
		else:
			if cpu and (not cpu in board_item_list_dict[key]):
				board_item_list_dict[key].append(cpu)
	board_info = (board_list, board_file_dict, board_type_list_dict, \
		board_item_list_dict, type_caption_dict)
	return board_info

def splitBoardsFile(boards_file_path):
	boards_file_header_block = []
	boards_file_body_block = []
	lines = fileutil.readFileLines(boards_file_path)
	is_header = True
	for line in lines:
		if '.name=' in line:
			is_header = False
		if is_header:
			boards_file_header_block.append(line)
		else:
			boards_file_body_block.append(line)
	return (boards_file_header_block, boards_file_body_block)

def parseBoardHeader(boards_file_header_block):
	board_type_list = []
	board_type_caption_dict = {}
	for line in boards_file_header_block:
		line = line.strip()
		if line and (not '#' in line):
			if '=' in line:
				(board_type, board_type_caption) = textutil.getKeyValue(line)
				if not board_type in board_type_list:
					board_type_list.append(board_type)
					board_type_caption_dict[board_type] = board_type_caption
	return (board_type_list, board_type_caption_dict)

def getTypeInfoBlock(board_info_block, board_type):
	info_block = []
	for line in board_info_block:
		if board_type in line:
			info_block.append(line)
	return info_block

def parseBoardFile(platform, boards_file_path):
	board_list = []
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}
	type_caption_dict = {}

	(boards_file_header_block, boards_file_body_block) = splitBoardsFile(boards_file_path)
	(board_type_list, board_type_caption_dict) = parseBoardHeader(boards_file_header_block)

	for board_type in board_type_caption_dict:
		type_key = textutil.genKey(platform, board_type)
		type_caption_dict[type_key] = board_type_caption_dict[board_type]

	board_info_block_list = textutil.splitToBlocks(boards_file_body_block, \
		sep = '.name', none_sep = 'menu.')
	for board_info_block in board_info_block_list:
		board_name_line = board_info_block[0]
		(key, board) = textutil.getKeyValue(board_name_line)
		if not board in board_list:
			board_list.append(board)

			board_key = textutil.genKey(platform, board)
			board_file_dict[board_key] = boards_file_path
			board_type_list_dict[board_key] = []

			for board_type in board_type_list:
				item_list = []
				board_type_info_block = getTypeInfoBlock(board_info_block, board_type)
				item_blocks = textutil.splitToBlocks(board_type_info_block, \
					sep = '.name', key_length = 4)
				for item_block in item_blocks:
					item_name_line = item_block[0]
					(key, item) = textutil.getKeyValue(item_name_line)
					if not item in item_list:
						item_list.append(item)
				if item_list:
					board_type_list_dict[board_key].append(board_type)
					key = textutil.genKey(board_key, board_type)
					board_item_list_dict[key] = item_list
	board_info = (board_list, board_file_dict, board_type_list_dict, \
		board_item_list_dict, type_caption_dict)
	return board_info

def parseBoardInfo(platform, core_root):
	board_list = []
	boards_file_path = os.path.join(core_root, 'boards.txt')
	if os.path.isfile(boards_file_path):
		if isBoard150(boards_file_path):
			board_info = parseBoardFile150(platform, boards_file_path)
		else:
			board_info = parseBoardFile(platform, boards_file_path)
	return board_info

def parseProgrammerInfo(platform, core_root):
	programmer_list = []
	programmer_file_dict = {}
	programmers_file_path = os.path.join(core_root, 'programmers.txt')
	if os.path.isfile(programmers_file_path):
		lines = fileutil.readFileLines(programmers_file_path)
		programmer_info_block_list = textutil.splitToBlocks(lines, sep = '.name')
		for programmer_info_block in programmer_info_block_list:
			programmer_name_line = programmer_info_block[0]
			(key, programmer) = textutil.getKeyValue(programmer_name_line)
			if not programmer in programmer_list:
				programmer_list.append(programmer)

				programmer_key = textutil.genKey(platform, programmer)
				programmer_file_dict[programmer_key] = programmers_file_path
	return (programmer_list, programmer_file_dict)

def isLibraryFolder(path):
	state = False
	header_ext_list = const.src_header_ext_list
	file_list = fileutil.listDir(path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in header_ext_list:
			state = True
			break
	return state

def parseLibraryInfo(platform, root):
	library_list = []
	library_path_dict = {}
	libraries_path = os.path.join(root, 'libraries')
	dir_list = fileutil.listDir(libraries_path, with_files = False)
	for cur_dir in dir_list:
		cur_dir_path = os.path.join(libraries_path, cur_dir)
		if isLibraryFolder(cur_dir_path):
			library_list.append(cur_dir)
			key = textutil.genKey(platform, cur_dir)
			library_path_dict[key] = cur_dir_path
	return (library_list, library_path_dict)

def parseExampleInfo(platform, root):
	example_list = []
	example_path_dict = {}
	examples_path = os.path.join(root, 'examples')
	dir_list = fileutil.listDir(examples_path, with_files = False)
	for cur_dir in dir_list:
		example_list.append(cur_dir)
		key = textutil.genKey(platform, cur_dir)
		cur_dir_path = os.path.join(examples_path, cur_dir)
		example_path_dict[key] = cur_dir_path
	return (example_list, example_path_dict)

def parseLibraryExampleInfo(platform, library_path_list):
	example_list = []
	example_path_dict = {}
	for library_path in library_path_list:
		examples_path = os.path.join(library_path, 'examples')
		if os.path.isdir(examples_path):
			example_name = os.path.split(library_path)[1]
			example_list.append(example_name)
			key = textutil.genKey(platform, example_name)
			example_path_dict[key] = examples_path
	return (example_list, example_path_dict)

def parseKeywordListFromFile(keywords_file_path):
	keyword_list = []
	keyword_type_dict = {}
	keyword_ref_dict = {}
	lines = fileutil.readFileLines(keywords_file_path)
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			word_list = re.findall(r'\S+', line)
			if len(word_list) > 1:
				keyword = word_list[0]
				if len(word_list) == 3:
					keyword_type = word_list[1]
					keyword_ref = word_list[2]
				elif len(word_list) == 2:
					if 'LITERAL' in word_list[1] or 'KEYWORD' in word_list[1]:
						keyword_type = word_list[1]
						keyword_ref = ''
					else:
						keyword_type = ''
						keyword_ref = word_list[1]
				if not keyword in keyword_list:
					keyword_list.append(keyword)
					keyword_type_dict[keyword] = keyword_type
					keyword_ref_dict[keyword] = keyword_ref
	return (keyword_list, keyword_type_dict, keyword_ref_dict)

def parseKeywordList(platform, lib_path_list):
	keyword_list = []
	keyword_type_dict = {}
	keyword_ref_dict = {}

	for lib_path in lib_path_list:
		keywords_file_path = os.path.join(lib_path, 'keywords.txt')
		if os.path.isfile(keywords_file_path):
			(keyword_list_form_file, keyword_type_dict_from_file, keyword_ref_dict_from_file) = parseKeywordListFromFile(keywords_file_path)
			for keyword in keyword_list_form_file:
				if not keyword in keyword_list:
					keyword_list.append(keyword)
					key = textutil.genKey(platform, keyword)
					keyword_type_dict[key] = keyword_type_dict_from_file[keyword]
					keyword_ref_dict[key] = keyword_ref_dict_from_file[keyword]
	return (keyword_list, keyword_type_dict, keyword_ref_dict)

def convertTextToVersion(version_text):
	number_patter_text = r'[\d.]+'
	number_pattern = re.compile(number_patter_text)
	match = number_pattern.search(version_text)
	if match:
		version_text = match.group()
		number_list = version_text.split('.')
		
		version = 0
		power = 0
		for number in number_list:
			number = int(number)
			version += number * (10 ** power)
			power -= 1
		version *= 100
		version = int(version)
	else:
		version = 100
		version_text = '1.0.0'
	return (version, version_text)

def genPlatformCoreRootList():
	sketchbook_root = fileutil.getSketchbookRoot()
	arduino_root = fileutil.getArduinoRoot()
	root_list = [sketchbook_root]
	if arduino_root:
		root_list.append(arduino_root)

	platform_core_root_list = []
	for root in root_list:
		hardware_dir_path = os.path.join(root, 'hardware')
		platform_core_root_list += findPlatformCoreRootList(hardware_dir_path)
	return platform_core_root_list

def genPlatformInfo():
	platform_list = []
	platform_core_root_list_dict = {}
	platform_src_cores_path_dict = {}

	platform_core_root_list = genPlatformCoreRootList()
	for platform_core_root in platform_core_root_list:
		platform = getPlatformFromCoreRoot(platform_core_root)
		if not platform in platform_list:
			platform_list.append(platform)
			platform_core_root_list_dict[platform] = [platform_core_root]
		else:
			platform_core_root_list_dict[platform].append(platform_core_root)

	for platform in platform_list:
		platform_core_root_list = platform_core_root_list_dict[platform]
		src_cores_path = findSrcCoresPath(platform_core_root_list)
		platform_src_cores_path_dict[platform] = src_cores_path

	for platform in platform_src_cores_path_dict:
		src_cores_path = platform_src_cores_path_dict[platform]
		if not src_cores_path:
			platform_list.remove(platform)
	platform_info = (platform_list, platform_core_root_list_dict, platform_src_cores_path_dict)
	return platform_info

def genPlatformBoardInfo(platform_info):
	platform_list = platform_info[0]
	platform_core_root_list_dict = platform_info[1]

	platform_board_lists_dict = {}
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}
	type_caption_dict = {}

	for platform in platform_list:
		platform_board_lists_dict[platform] = []
		board_type_list_dict[platform] = []
		platform_core_root_list = platform_core_root_list_dict[platform]
		for platform_core_root in platform_core_root_list:
			board_info = parseBoardInfo(platform, platform_core_root)
			
			board_list = board_info[0]
			if board_list:
				cur_board_file_dict = board_info[1]
				cur_board_type_list_dict = board_info[2]
				cur_board_item_list_dict = board_info[3]
				cur_type_caption_dict = board_info[4]

				platform_board_lists_dict[platform].append(board_list)
				board_file_dict.update(cur_board_file_dict)
				board_type_list_dict.update(cur_board_type_list_dict)
				board_item_list_dict.update(cur_board_item_list_dict)
				type_caption_dict.update(cur_type_caption_dict)
	board_info = (platform_board_lists_dict, board_file_dict, board_type_list_dict, \
		board_item_list_dict, type_caption_dict)
	return board_info

def genPlatformProgrammerInfo(platform_info):
	platform_list = platform_info[0]
	platform_core_root_list_dict = platform_info[1]

	platform_programmer_lists_dict = {}
	programmer_file_dict = {}

	for platform in platform_list:
		platform_programmer_lists_dict[platform] = []
		platform_core_root_list = platform_core_root_list_dict[platform]
		for platform_core_root in platform_core_root_list:
			(programmer_list, cur_programmer_file_dict) = parseProgrammerInfo(platform, platform_core_root)
			if programmer_list:
				platform_programmer_lists_dict[platform].append(programmer_list)
				programmer_file_dict.update(cur_programmer_file_dict)
	programmer_info = (platform_programmer_lists_dict, programmer_file_dict)
	return programmer_info

def genPlatformLibraryInfoFromRootList(platform, root_list):
	library_lists = []
	library_path_dict = {}
	for root in root_list:
		(library_list, cur_library_path_dict) = parseLibraryInfo(platform, root)
		if library_list:
			library_lists.append(library_list)
			library_path_dict.update(cur_library_path_dict)
	library_info = (library_lists, library_path_dict)
	return library_info

def genPlatformLibraryInfo(platform_info):
	platform_list = platform_info[0]
	platform_core_root_list_dict = platform_info[1]

	platform_library_lists_dict = {}
	library_path_dict = {}

	arduino_root = fileutil.getArduinoRoot()
	sketchbook_root = fileutil.getSketchbookRoot()

	root_list = [sketchbook_root]
	if arduino_root:
		root_list.append(arduino_root)
	cur_library_info = genPlatformLibraryInfoFromRootList('common', root_list)
	platform_library_lists_dict['common'] = cur_library_info[0]
	library_path_dict.update(cur_library_info[1])

	for platform in platform_list:
		platform_library_lists_dict[platform] = []
		platform_core_root_list = platform_core_root_list_dict[platform]
		root_list = [sketchbook_root]

		root_list = platform_core_root_list
		cur_library_info = genPlatformLibraryInfoFromRootList(platform, root_list)
		platform_library_lists_dict[platform] = cur_library_info[0]
		library_path_dict.update(cur_library_info[1])
	library_info = (platform_library_lists_dict, library_path_dict)
	return library_info

def genPlatformExampleInfoFromLibraryLists(platform, library_lists, library_path_dict):
	example_lists = []
	example_path_dict = {}
	for library_list in library_lists:
		library_path_list = [library_path_dict[textutil.genKey(platform, library)] for library in library_list]
		(example_list, cur_example_path_dict) = parseLibraryExampleInfo(platform, library_path_list)
		if example_list:
			example_lists.append(example_list)
			example_path_dict.update(cur_example_path_dict)
	example_info = (example_lists, example_path_dict)
	return example_info

def genPlatformExampleInfo(platform_info, library_info):
	platform_list = platform_info[0]
	platform_core_root_list_dict = platform_info[1]
	platform_library_lists_dict = library_info[0]
	library_path_dict = library_info[1]

	platform_example_lists_dict = {}
	example_path_dict = {}

	platform_example_lists_dict['common'] = []
	arduino_root = fileutil.getArduinoRoot()
	sketchbook_root = fileutil.getSketchbookRoot()
	root_list = [sketchbook_root]
	if arduino_root:
		root_list.append(arduino_root)
	for root in root_list:
		(example_list, cur_example_path_dict) = parseExampleInfo('common', root)
		if example_list:
			platform_example_lists_dict['common'].append(example_list)
			example_path_dict.update(cur_example_path_dict)

	library_lists = platform_library_lists_dict['common']
	cur_example_info = genPlatformExampleInfoFromLibraryLists('common', library_lists, library_path_dict)
	platform_example_lists_dict['common'] += cur_example_info[0]
	example_path_dict.update(cur_example_info[1])
	
	for platform in platform_list:
		platform_example_lists_dict[platform] = []
		
		library_lists = platform_library_lists_dict[platform]
		cur_example_info = genPlatformExampleInfoFromLibraryLists(platform, library_lists, library_path_dict)
		platform_example_lists_dict[platform] = cur_example_info[0]
		example_path_dict.update(cur_example_info[1])
	example_info = (platform_example_lists_dict, example_path_dict)
	return example_info

def genPlatformKeywordInfo(platform_info, library_info):
	platform_list = platform_info[0]
	platform_core_root_list_dict = platform_info[1]
	platform_library_lists_dict = library_info[0]
	library_path_dict = library_info[1]

	platform_keyword_list_dict = {}
	keyword_type_dict = {}
	keyword_ref_dict = {}

	arduino_root = fileutil.getArduinoRoot()
	if arduino_root:
		lib_path_list = [os.path.join(arduino_root, 'lib')]
	else:
		lib_path_list = []
	(keyword_list, cur_keyword_type_dict, cur_keyword_ref_dict) = parseKeywordList('common', lib_path_list)
	platform_keyword_list_dict['common'] = keyword_list
	keyword_type_dict.update(cur_keyword_type_dict)
	keyword_ref_dict.update(cur_keyword_ref_dict)

	for platform in platform_list:
		lib_path_list = []
		library_lists = platform_library_lists_dict[platform]
		for library_list in library_lists:
			library_path_list = [library_path_dict[textutil.genKey(platform, library)] for library in library_list]
			lib_path_list += library_path_list
		(keyword_list, cur_keyword_type_dict, cur_keyword_ref_dict) = parseKeywordList(platform, lib_path_list)
		platform_keyword_list_dict[platform] = keyword_list
		keyword_type_dict.update(cur_keyword_type_dict)
		keyword_ref_dict.update(cur_keyword_ref_dict)
	keyword_info = (platform_keyword_list_dict, keyword_type_dict, keyword_ref_dict)
	return keyword_info

def genPlatformOperatorInfo(platform_info, keyword_info):
	platform_list = platform_info[0]
	platform_core_root_list_dict = platform_info[1]
	platform_keyword_list_dict = keyword_info[0]
	keyword_type_dict = keyword_info[1]
	keyword_ref_dict = keyword_info[2]

	platform_operator_list_dict = {}
	
	platform_list = ['common'] + platform_list
	for platform in platform_list:
		operator_list =[]
		keyword_list = platform_keyword_list_dict[platform]
		for keyword in keyword_list:
			keyword_type = keyword_type_dict[textutil.genKey(platform, keyword)]
			keyword_ref = keyword_ref_dict[textutil.genKey(platform, keyword)]
			if (not keyword_type) and keyword_ref:
				operator_list.append(keyword)
		platform_operator_list_dict[platform] = operator_list
	return platform_operator_list_dict

def genVersionInfo():
	version_text = '1.0.0'
	arduino_root = fileutil.getArduinoRoot()
	lib_path = os.path.join(arduino_root, 'lib')
	version_file_path = os.path.join(lib_path, 'version.txt')
	if os.path.isfile(version_file_path):
		lines = fileutil.readFileLines(version_file_path)
		for line in lines:
			line = line.strip()
			if line:
				version_text = line
				break
	(version, version_text) = convertTextToVersion(version_text)
	version_info = (version, version_text)
	return  version_info

def getCommonInfoBlock(board_info_block):
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

def genTypeInfoBlockList(info_block):
	block_list = textutil.splitToBlocks(info_block, sep = '.name', key_length = 4)
	name_key_list = []
	for block in block_list:
		name_line = block[0]
		(key, value) = textutil.getKeyValue(name_line)
		key = key.replace('.name', '.')
		name_key_list.append(key)

	type_info_block_list = []
	for name_key in name_key_list:
		type_info_block = []
		for line in info_block:
			if name_key in line:
				type_info_block.append(line)
		type_info_block_list.append(type_info_block)
	return type_info_block_list

def removeInfo(type_info_block, board_type_value):
	block = []
	block_list = genTypeInfoBlockList(type_info_block)
	for cur_block in block_list:
		line = cur_block[0]
		(key, value) = textutil.getKeyValue(line)
		if value == board_type_value:
			block = cur_block
	return block

def splitInfoBlock(info_block, board_type_value_dict):
	info_blocks = []
	common_info_block = getCommonInfoBlock(info_block)
	info_blocks.append(common_info_block)

	for board_type in board_type_value_dict:
		board_type_value = board_type_value_dict[board_type]
		type_info_block = getBoardTypeInfoBlock(info_block, board_type)
		type_info_block = removeInfo(type_info_block, board_type_value)
		info_blocks.append(type_info_block)
	return info_blocks

def genBoardInfoDict(arduino_info):
	info_key_list = []
	info_dict = {}
	platform = const.settings.get('platform')
	board = const.settings.get('board')
	board_file_path = arduino_info.getBoardFile(platform, board)
	if os.path.isfile(board_file_path):
		info_block = fileutil.getInfoBlock(board_file_path, board)

		board_type_list = arduino_info.getBoardTypeList(platform, board)
		board_type_value_dict = {}
		for board_type in board_type_list:
			board_type_caption = arduino_info.getPlatformTypeCaption(platform, board_type)
			board_type_value_dict[board_type] = const.settings.get(board_type_caption)

		info_blocks = splitInfoBlock(info_block, board_type_value_dict)
		
		for info_block in info_blocks:
			(cur_info_key_list, cur_info_dict) = textutil.genInfoDictFromBlock(info_block)
			info_key_list += cur_info_key_list
			info_dict.update(cur_info_dict)
	return (info_key_list, info_dict)

def genProgrammerInfoDict(arduino_info):
	info_key_list = []
	info_dict = {}
	platform = const.settings.get('platform')
	programmer = const.settings.get('programmer')
	programmer_file_path = arduino_info.getProgrammerFile(platform, programmer)
	if os.path.isfile(programmer_file_path):
		info_block = fileutil.getInfoBlock(programmer_file_path, programmer)
		(info_key_list, info_dict) = textutil.genInfoDictFromBlock(info_block)
	return (info_key_list, info_dict)

def regulariseToolsKey(key):
	info_list = key.split('.')
	new_key = ''
	for info in info_list[2:]:
		new_key += info
		new_key += '.'
	new_key = new_key[:-1]
	new_key = new_key.replace('params.', '')
	return new_key

def genPlatformInfoDict(platform_file_path):
	platform_info_key_list = []
	platform_info_dict = {}
	lines = fileutil.readFileLines(platform_file_path)
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			(key, value) = textutil.getKeyValue(line)
			if 'tools.' in key:
				key = regulariseToolsKey(key)
			platform_info_key_list.append(key)
			platform_info_dict[key] = value
	return (platform_info_key_list, platform_info_dict)