#-*- coding: utf-8 -*-
# stino/stmenu.py

import os

from . import const
from . import fileutil
from . import textutil
from . import sketch
from . import serial

def replaceMenuCaption(menu_caption):
	menu_caption = menu_caption.replace('Board', '%(Board)s')
	menu_caption = menu_caption.replace('Processor', '%(Processor)s')
	menu_caption = menu_caption.replace('Type', '%(Type)s')
	menu_caption = menu_caption.replace('Speed', '%(Speed)s')
	menu_caption = menu_caption.replace('Keyboard Layout', '%(Keyboard_Layout)s')
	return menu_caption

def genSubMenuBlockHead(menu_caption, command):
	submenu_text = '\t'*3
	submenu_text += '{\n'
	submenu_text += '\t'*4
	submenu_text += '"caption": "%s",\n' % menu_caption
	submenu_text += '\t'*4
	submenu_text += '"id": "%s",\n' % command
	submenu_text += '\t'*4
	submenu_text += '"children":\n'
	submenu_text += '\t'*4
	submenu_text += '[\n'
	return submenu_text

def genSubMenuBlockTail():
	submenu_text = '\t'*4
	submenu_text += ']\n'
	submenu_text += '\t'*3
	submenu_text += '},\n'
	return submenu_text

def genSubMenuBlock(menu_caption, item_lists, command, menu_base = None, checkbox = False, mode = 'all'):
	if mode == 'all':
		submenu_text = '{"caption": "%s", "command": "not_enabled"},' % menu_caption
		if not item_lists:
			return submenu_text
	submenu_text = ''
	if mode == 'head' or mode == 'all':
		submenu_text += genSubMenuBlockHead(menu_caption, command)
	if mode == 'body' or mode == 'head' or mode == 'tail' or mode == 'all':
		for item_list in item_lists:
			for item in item_list:
				if menu_base:
					menu_str = textutil.genKey(menu_base, item)
				else:
					menu_str = item
				submenu_text += '\t'*5
				submenu_text += '{"caption": "%s", "command": "%s", "args": {"menu_str": "%s"}' \
					% (item, command, menu_str)
				if checkbox:
					submenu_text += ', "checkbox": true'
				submenu_text += '},\n'
			submenu_text += '\t'*5
			submenu_text += '{"caption": "-"},\n'
	if mode == 'tail' or mode == 'all':
		if item_lists:
			submenu_text = submenu_text[:-2] + '\n'
		submenu_text += genSubMenuBlockTail()
	return submenu_text

def checkSelectedMenuItem(menu_lists, item_name, menu_base = None):
	menu_list = textutil.simplifyLists(menu_lists)
	item_value = const.settings.get(item_name)
	if not item_value in menu_list:
		pass

def genSketchbookMenuText():
	menu_caption = '%(Sketchbook)s'
	command = 'open_sketch'
	sketch_info = sketch.genSketchInfo()
	sketch_list = sketch_info[0]
	menu_text = genSubMenuBlock(menu_caption, [sketch_list], command)
	return menu_text

def genExampleMenuText(arduino_info):
	menu_caption = '%(Examples)s'
	command = 'select_example'
	platform = const.settings.get('platform')
	common_example_lists = arduino_info.getExampleLists('common')
	platform_example_lists = arduino_info.getExampleLists(platform)
	all_example_lists = common_example_lists + platform_example_lists
	if all_example_lists:
		menu_text = genSubMenuBlock(menu_caption, common_example_lists, command, menu_base = 'common', mode = 'head')
		menu_text += genSubMenuBlock(menu_caption, platform_example_lists, command, menu_base = platform, mode = 'tail')
	else:
		menu_text = '{"caption": "%s", "command": "not_enabled"},' % menu_caption
	return menu_text

def genLibraryMenuText(arduino_info):
	menu_caption = '%(Import Library...)s'
	command = 'import_library'
	platform = const.settings.get('platform')
	common_library_lists = arduino_info.getLibraryLists('common')
	platform_library_lists = arduino_info.getLibraryLists(platform)
	all_library_lists = common_library_lists + platform_library_lists
	if all_library_lists:
		menu_text = genSubMenuBlock(menu_caption, common_library_lists, command, menu_base = 'common', mode = 'head')
		menu_text += genSubMenuBlock(menu_caption, platform_library_lists, command, menu_base = platform, mode = 'tail')
	else:
		menu_text = '{"caption": "%s", "command": "not_enabled"},' % menu_caption
	return menu_text

def genSerialMenuText():
	menu_caption = '%(Serial Port)s'
	command = 'select_serial_port'
	serial_port_list = serial.genSerialPortList()
	serial_port_lists = []
	if serial_port_list:
		serial_port_lists.append(serial_port_list)
	menu_text = genSubMenuBlock(menu_caption, serial_port_lists, command, checkbox = True)
	return menu_text

def genBaudrateMenuText():
	menu_caption = '%(Baudrate)s'
	command = 'select_baudrate'
	baudrate_list = const.baudrate_list
	menu_text = genSubMenuBlock(menu_caption, [baudrate_list], command, checkbox = True)
	return menu_text

def genLanguageMenuText(language):
	menu_caption = '%(Language)s'
	command = 'select_language'
	language_list = language.getLanguageTextList()
	menu_text = genSubMenuBlock(menu_caption, [language_list], command, checkbox = True)
	return menu_text

def genBoardMenuText(arduino_info):
	menu_text = ''
	command = 'select_board'
	platform_list = arduino_info.getPlatformList()
	for platform in platform_list:
		board_lists = arduino_info.getBoardLists(platform)
		menu_caption = replaceMenuCaption(platform)
		menu_text += genSubMenuBlock(menu_caption, board_lists, command, menu_base = platform, checkbox = True)
	return menu_text

def genBoardOptionMenuText(arduino_info):
	menu_text = ''
	command = 'select_board_type'
	platform = const.settings.get('platform')
	board = const.settings.get('board')
	board_type_list = arduino_info.getBoardTypeList(platform, board)
	for board_type in board_type_list:
		item_list = arduino_info.getBoardItemList(platform, board, board_type)
		type_caption = arduino_info.getPlatformTypeCaption(platform, board_type)
		menu_caption = replaceMenuCaption(type_caption)
		board_key = textutil.genKey(platform, board)
		type_key = textutil.genKey(board_key, board_type)
		menu_text += genSubMenuBlock(menu_caption, [item_list], command, menu_base = type_key, checkbox = True)
	return menu_text

def genProgrammerMenuText(arduino_info):
	menu_caption = '%(Programmer)s'
	command = 'select_programmer'
	platform = const.settings.get('platform')
	programmer_lists = arduino_info.getProgrammerLists(platform)
	menu_text = genSubMenuBlock(menu_caption, programmer_lists, command, menu_base = platform, checkbox = True)
	return menu_text

def genMiniMenuText(arduino_info):
	show_arduino_menu = const.settings.get('show_arduino_menu')
	show_serial_monitor_menu = const.settings.get('show_serial_monitor_menu')

	preference_menu_file = os.path.join(const.template_root, 'menu_preference')
	arduino_menu_file = os.path.join(const.template_root, 'menu_arduino')
	serial_monitor_menu_file = os.path.join(const.template_root, 'menu_serial')

	menu_text = fileutil.readFileText(preference_menu_file)

	if show_arduino_menu:		
		menu_text += ',\n'
		menu_text += fileutil.readFileText(arduino_menu_file)

	if show_serial_monitor_menu:
		menu_text += ',\n'
		menu_text += osfile.readFileText(serial_monitor_menu_file)

	menu_text += '\n]'
	return menu_text

def genMenuText(arduino_info, language):
	menu_text = genMiniMenuText(arduino_info)

	show_arduino_menu = const.settings.get('show_arduino_menu')
	if show_arduino_menu:
		sketchbook_menu_text = genSketchbookMenuText()
		example_menu_text = genExampleMenuText(arduino_info)
		library_menu_text = genLibraryMenuText(arduino_info)
		board_menu_text = genBoardMenuText(arduino_info)
		board_option_menu_text = genBoardOptionMenuText(arduino_info)
		serial_menu_text = genSerialMenuText()
		baudrate_menu_text = genBaudrateMenuText()
		programmer_menu_text = genProgrammerMenuText(arduino_info)
		language_menu_text = genLanguageMenuText(language)

		menu_text = menu_text.replace('{"caption": "Sketchbook->"},', sketchbook_menu_text)
		menu_text = menu_text.replace('{"caption": "Examples->"},', example_menu_text)
		menu_text = menu_text.replace('{"caption": "Import Library->"},', library_menu_text)
		menu_text = menu_text.replace('{"caption": "Board->"},', board_menu_text)
		menu_text = menu_text.replace('{"caption": "Board Option->"},', board_option_menu_text)
		menu_text = menu_text.replace('{"caption": "Serial Port->"},', serial_menu_text)
		menu_text = menu_text.replace('{"caption": "Baudrate->"},', baudrate_menu_text)
		menu_text = menu_text.replace('{"caption": "Programmer->"},', programmer_menu_text)
		menu_text = menu_text.replace('{"caption": "Language->"},', language_menu_text)
	return menu_text

def writeMenuFile(menu_file_path, menu_text, language):
	menu_text = menu_text % language.getTransDict()
	fileutil.writeFile(menu_file_path, menu_text)

def checkSelectedPlatform(arduino_info):
	platform = const.settings.get('platform')
	platform_list = arduino_info.getPlatformList()
	if platform_list:
		if not platform in platform_list:
			platform = platform_list[0]
	else:
		platform = ''
	const.settings.set('platform', platform)

def checkSelectedBoard(arduino_info):
	platform = const.settings.get('platform')
	board = const.settings.get('board')
	board_lists = arduino_info.getBoardLists(platform)
	board_list = textutil.simplifyLists(board_lists)
	if board_list:
		if not board in board_list:
			board = board_list[0]
	else:
		board = ''
	const.settings.set('board', board)

def checkSelectedBoardOption(arduino_info):
	platform = const.settings.get('platform')
	board = const.settings.get('board')
	board_type_list = arduino_info.getBoardTypeList(platform, board)
	for board_type in board_type_list:
		item_list = arduino_info.getBoardItemList(platform, board, board_type)
		type_caption = arduino_info.getPlatformTypeCaption(platform, board_type)
		type_value = const.settings.get(type_caption)
		if item_list:
			if not type_value in item_list:
				type_value = item_list[0]
		else:
			type_value = ''
		const.settings.set(type_caption, type_value)

def checkSelectedProgrammer(arduino_info):
	platform = const.settings.get('platform')
	programmer = const.settings.get('programmer')
	programmer_lists = arduino_info.getProgrammerLists(platform)
	programmer_list = textutil.simplifyLists(programmer_lists)
	if programmer_list:
		if not programmer in programmer_list:
			programmer = programmer_list[0]
	else:
		programmer = ''
	const.settings.set('programmer', programmer)

def checkSelectedBaudrate():
	baudrate = const.settings.get('baudrate')
	if not baudrate in const.baudrate_list:
		baudrate = '9600'
	const.settings.set('baudrate', baudrate)

def checkSelectedValue(arduino_info):
	checkSelectedPlatform(arduino_info)
	checkSelectedBoard(arduino_info)
	checkSelectedBoardOption(arduino_info)
	checkSelectedProgrammer(arduino_info)
	checkSelectedBaudrate()

class STMenu:
	def __init__(self, language, arduino_info):
		self.language = language
		self.arduino_info = arduino_info
		self.menu_file_path = os.path.join(const.stino_root, 'Main.sublime-menu')
		self.update()

	def update(self):
		checkSelectedValue(self.arduino_info)
		self.menu_text = genMenuText(self.arduino_info, self.language)
		writeMenuFile(self.menu_file_path, self.menu_text, self.language)

	def changeLanguage(self):
		writeMenuFile(self.menu_file_path, self.menu_text, self.language)