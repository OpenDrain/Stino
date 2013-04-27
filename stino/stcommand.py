#-*- coding: utf-8 -*-
# stino/stcommand.py

import os

from . import const
from . import fileutil
from . import stmenu
from . import sketch
from . import serial

def genSelectCommandText(caption, command, parent_mod, list_func, parameter1 = '', \
	parameter2 = '', parameter3 = ''):
	command_text = '    { "caption": "Stino: %s", "command": "select_item", "args": \
	{"command": "%s", "parent_mod": "%s", "list_func": "%s", "parameter1": "%s", \
	"parameter2": "%s", "parameter3": "%s"}},\n' % (caption, command, parent_mod, \
	list_func, parameter1, parameter2, parameter3)
	return command_text

def genOpenSketchCommandText(arduino_info):
	command_text = ''
	sketch_list = sketch.genSketchList()
	if sketch_list:
		command_caption = '%(Open)s %(Sketch)s'
		command = 'open_sketch'
		parent_mod = 'sketch'
		list_func = 'genSketchList'
		command_text = genSelectCommandText(command_caption, command, parent_mod, list_func)
	return command_text

def genSelectExampleCommandText(arduino_info):
	command_text = ''
	platform_list = ['common']
	platform = const.settings.get('platform')
	if platform:
		platform_list.append(platform)

	example_lists = []
	for platform in platform_list:
		cur_lists = arduino_info.getExampleLists(platform)
		example_lists += cur_lists

	if example_lists:
		command_caption = '%(Open)s %(Examples)s'
		command = 'select_example'
		parent_mod = 'globalvars'
		list_func = 'arduino_info.getExampleLists'
		command_text = genSelectCommandText(command_caption, command, parent_mod, list_func, parameter1 = platform)
	return command_text

def genImportLibraryCommandText(arduino_info):
	command_text = ''
	platform_list = ['common']
	platform = const.settings.get('platform')
	if platform:
		platform_list.append(platform)

	library_lists = []
	for platform in platform_list:
		cur_lists = arduino_info.getLibraryLists(platform)
		library_lists += cur_lists
	
	if library_lists:
		command_caption = '%(Import Library...)s'
		command = 'import_library'
		parent_mod = 'globalvars'
		list_func = 'arduino_info.getLibraryLists'
		command_text = genSelectCommandText(command_caption, command, parent_mod, \
			list_func, parameter1 = platform)
	return command_text

def genSelectBoardCommandText(arduino_info):
	command_text = ''

	command = 'select_board'
	parent_mod = 'globalvars'
	list_func = 'arduino_info.getBoardLists'
	platform_list = arduino_info.getPlatformList()
	for platform in platform_list:
		command_caption = '%(Select)s ' + stmenu.replaceMenuCaption(platform)
		command_text += genSelectCommandText(command_caption, command, parent_mod, \
			list_func, parameter1 = platform)
	return command_text

def genSelectBoardTypeCommandText(arduino_info):
	command_text = ''
	command = 'select_board_type'
	parent_mod = 'globalvars'
	list_func = 'arduino_info.getBoardItemList'

	platform = const.settings.get('platform')
	board = const.settings.get('board')
	board_type_list = arduino_info.getBoardTypeList(platform, board)
	for board_type in board_type_list:
		board_type_caption = arduino_info.getPlatformTypeCaption(platform, board_type)
		board_type_caption = stmenu.replaceMenuCaption(board_type_caption)
		command_caption = '%(Select)s ' + board_type_caption
		command_text += genSelectCommandText(command_caption, command, parent_mod, \
			list_func, parameter1 = platform, parameter2 = board, parameter3 = board_type)
	return command_text

def genSelectSerialPortCommandText():
	command_text = ''
	serial_port_list = serial.genSerialPortList()
	if serial_port_list:
		command_caption = '%(Select)s ' + '%(Serial_Port)s'
		command = 'select_serial_port'
		parent_mod = 'serial'
		list_func = 'genSerialPortList'
		command_text = genSelectCommandText(command_caption, command, parent_mod, list_func)
	return command_text

def genSelectBaudrateCommandText():
	command_caption = '%(Select)s ' + '%(Baudrate)s'
	command = 'select_baudrate'
	parent_mod = 'serial'
	list_func = 'getBaudrateList'
	command_text = genSelectCommandText(command_caption, command, parent_mod, list_func)
	return command_text

def genSelectProgrammerCommandText(arduino_info):
	command_text = ''
	platform = const.settings.get('platform')
	programmer_lists = arduino_info.getProgrammerLists(platform)
	if programmer_lists:
		command_caption = '%(Select)s ' + '%(Programmer)s'
		command = 'select_programmer'
		parent_mod = 'globalvars'
		list_func = 'arduino_info.getProgrammerLists'
		command_text = genSelectCommandText(command_caption, command, parent_mod, \
			list_func, parameter1 = platform)
	return command_text

def genSelectLanguageCommandText(language):
	command_text = ''
	language_list = language.getLanguageTextList()
	if language_list:
		command_caption = '%(Select)s ' + '%(Language)s'
		command = 'select_language'
		parent_mod = 'globalvars'
		list_func = 'cur_language.getLanguageTextList'
		command_text = genSelectCommandText(command_caption, command, parent_mod, list_func)
	return command_text

def genCommandText(arduino_info, language):
	text = ''
	text += genOpenSketchCommandText(arduino_info)
	text += genSelectExampleCommandText(arduino_info)
	text += genImportLibraryCommandText(arduino_info)
	text += genSelectBoardCommandText(arduino_info)
	text += genSelectBoardTypeCommandText(arduino_info)
	text += genSelectSerialPortCommandText()
	text += genSelectBaudrateCommandText()
	text += genSelectProgrammerCommandText(arduino_info)
	text += genSelectLanguageCommandText(language)

	temp_file = os.path.join(const.template_root, 'commands')
	command_text = fileutil.readFileText(temp_file)
	command_text = command_text.replace('(_$item$_)', text)
	return command_text

def writeCompletionFile(file_path, file_text, language):
	file_text = file_text % language.getTransDict()
	fileutil.writeFile(file_path, file_text)

class STCommand:
	def __init__(self, language, arduino_info):
		self.language = language
		self.arduino_info = arduino_info
		self.file_path = os.path.join(const.stino_root, 'Stino.sublime-commands')
		self.update()

	def update(self):
		file_text = genCommandText(self.arduino_info, self.language)
		writeCompletionFile(self.file_path, file_text, self.language)