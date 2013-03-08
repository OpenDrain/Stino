#-*- coding: utf-8 -*-
# stino/stmenu.py

import os

from stino import utils
from stino import const
from stino import osfile
from stino import smonitor

class STMenu:
	def __init__(self, language, arduino_info):
		self.language = language
		self.arduino_info = arduino_info

		self.plugin_root = const.plugin_root
		self.template_root = const.template_root

		self.main_menu_file = os.path.join(self.plugin_root, 'Main.sublime-menu')
		self.commands_file = os.path.join(self.plugin_root, 'Stino.sublime-commands')
		self.completions_file = os.path.join(self.plugin_root, 'Stino.sublime-completions')
		self.syntax_file = os.path.join(self.plugin_root, 'Arduino.tmLanguage')

		self.original_menu_text = ''
		self.full_menu_text = ''
		self.update()

	def update(self):
		self.genOriginalMenuText()
		self.genFullMenuText()
		self.writeMainMenuFile()

	def genOriginalMenuText(self):
		show_arduino_menu = const.settings.get('show_arduino_menu')
		show_serial_monitor_menu = const.settings.get('show_serial_monitor_menu')

		preference_menu_file = os.path.join(self.template_root, 'menu_preference')
		serial_monitor_menu_file = os.path.join(self.template_root, 'menu_serial')
		menu_text = osfile.readFileText(preference_menu_file)

		if show_arduino_menu:
			if self.arduino_info.isReady():
				arduino_menu_file_name = 'menu_full'
			else:
				arduino_menu_file_name = 'menu_mini'
			arduino_menu_file = os.path.join(self.template_root, arduino_menu_file_name)
			menu_text += ',\n'
			menu_text += osfile.readFileText(arduino_menu_file)

		if show_serial_monitor_menu:
			menu_text += ',\n'
			menu_text += osfile.readFileText(serial_monitor_menu_file)

		menu_text += '\n]'
		self.original_menu_text = menu_text

	def genSubMenuBlock(self, menu_caption, item_lists, command, menu_base = None, checkbox = False):
		submenu_text = '{"caption": "%s", "command": "not_enable"},' % menu_caption
		if item_lists:
			submenu_text = ''
			submenu_text += '{\n'
			submenu_text += '\t'*4
			submenu_text += '"caption": "%s",\n' % menu_caption
			submenu_text += '\t'*4
			submenu_text += '"id": "%s",\n' % command
			submenu_text += '\t'*4
			submenu_text += '"children":\n'
			submenu_text += '\t'*4
			submenu_text += '[\n'
			for item_list in item_lists:
				for item in item_list:
					if menu_base:
						menu_str = utils.genKey(item, menu_base)
					else:
						menu_str = item
					submenu_text += '\t'*5
					submenu_text += '{"caption": "%s", "command": "%s", "args": {"menu_str": "%s"}' % (item, command, menu_str)
					if checkbox:
						submenu_text += ', "checkbox": true'
					submenu_text += '},\n'
				submenu_text += '\t'*5
				submenu_text += '{"caption": "-"},\n'
			submenu_text = submenu_text[:-2] + '\n'
			submenu_text += '\t'*4
			submenu_text += ']\n'
			submenu_text += '\t'*3
			submenu_text += '},\n'
		return submenu_text

	def genSketchbookMenuText(self):
		sketch_list = self.arduino_info.getSketchList()
		menu_caption = '%(Sketchbook)s'
		command = 'open_sketch'
		menu_text = self.genSubMenuBlock(menu_caption, [sketch_list], command)
		return menu_text

	def genLibraryMenuText(self):
		platform = self.getPlatform()
		library_lists = self.arduino_info.getLibraryLists(platform)
		menu_caption = '%(Import_Library...)s'
		command = 'import_library'
		menu_text = self.genSubMenuBlock(menu_caption, library_lists, command, menu_base = platform)
		return menu_text

	def genBoardMenuText(self):
		menu_text = ''
		command = 'select_board'
		platform_list = self.arduino_info.getPlatformList()
		for platform in platform_list:
			board_lists = self.arduino_info.getBoardLists(platform)
			menu_caption = platform
			menu_text += self.genSubMenuBlock(menu_caption, board_lists, command, menu_base = platform, checkbox = True)
		return menu_text

	def genBoardOptionMenuText(self):
		menu_text = ''
		command = 'select_board_type'
		platform = self.getPlatform()
		board = self.getBoard()
		board_type_list = self.arduino_info.getBoardTypeList(platform, board)
		for board_type in board_type_list:
			item_list = self.arduino_info.getBoardItemList(platform, board, board_type)
			menu_caption = self.arduino_info.getPlatformTypeCaption(platform, board_type)
			board_key = utils.genKey(board, platform)
			type_key = utils.genKey(board_type, board_key)
			menu_text += self.genSubMenuBlock(menu_caption, [item_list], command, menu_base = type_key, checkbox = True)

			type_value = const.settings.get(menu_caption)
			if not type_value in item_list:
				type_value = item_list[0]
				const.settings.set(menu_caption, type_value)
				const.save_settings()
		return menu_text

	def genSerialMenuText(self):
		serial_port_list = smonitor.genSerialPortList()
		menu_caption = '%(Serial_Port)s'
		command = 'select_serial_port'
		serial_port_lists = []
		if serial_port_list:
			serial_port_lists.append(serial_port_list)
		menu_text = self.genSubMenuBlock(menu_caption, serial_port_lists, command, checkbox = True)
		serial_port = const.settings.get('serial_port')
		if not serial_port in serial_port_list:
			if serial_port_list:
				serial_port = serial_port_list[0]
			else:
				serial_port = 'No_Serial_Port'
			const.settings.set('serial_port', serial_port)
			const.save_settings()
		return menu_text

	def genBaudrateMenuText(self):
		baudrate_list = smonitor.getBaudrateList()
		menu_caption = '%(Baudrate)s'
		command = 'select_baudrate'
		menu_text = self.genSubMenuBlock(menu_caption, [baudrate_list], command, checkbox = True)
		baudrate = const.settings.get('baudrate')
		if not baudrate in baudrate_list:
			baudrate = '9600'
			const.settings.set('baudrate', baudrate)
			const.save_settings()
		return menu_text

	def genProgrammerMenuText(self):
		platform = self.getPlatform()
		programmer_lists = self.arduino_info.getProgrammerLists(platform)
		menu_caption = '%(Programmer)s'
		command = 'select_programmer'
		menu_text = self.genSubMenuBlock(menu_caption, programmer_lists, command, menu_base = platform, checkbox = True)
		if programmer_lists:
			all_programer_list = utils.simplifyLists(programmer_lists)
			programmer = const.settings.get('programmer')
			if not programmer in all_programer_list:
				programmer = all_programer_list[0]
				const.settings.set('programmer', programmer)
				const.save_settings()
		return menu_text

	def genLanguageMenuText(self):
		language_list = self.language.getLanguageList()
		menu_caption = '%(Language)s'
		command = 'select_language'
		menu_text = self.genSubMenuBlock(menu_caption, [language_list], command, checkbox = True)
		return menu_text

	def genExampleMenuText(self):
		platform = self.getPlatform()
		example_lists = self.arduino_info.getExampleLists(platform)
		menu_caption = '%(Examples)s'
		command = 'select_example'
		menu_text = self.genSubMenuBlock(menu_caption, example_lists, command, menu_base = platform)
		return menu_text

	def genFullMenuText(self):
		self.full_menu_text = self.getOriginMenuText()

		language_menu_text = self.genLanguageMenuText()
		serial_menu_text = self.genSerialMenuText()
		baudrate_menu_text = self.genBaudrateMenuText()
		sketchbook_menu_text = self.genSketchbookMenuText()

		self.full_menu_text = self.full_menu_text.replace('{"caption": "Sketchbook->"},', sketchbook_menu_text)
		self.full_menu_text = self.full_menu_text.replace('{"caption": "Serial_Port->"},', serial_menu_text)
		self.full_menu_text = self.full_menu_text.replace('{"caption": "Baudrate->"},', baudrate_menu_text)
		self.full_menu_text = self.full_menu_text.replace('{"caption": "Language->"},', language_menu_text)

		if self.arduino_info.isReady():
			library_menu_text = self.genLibraryMenuText()
			board_menu_text = self.genBoardMenuText()
			board_option_menu_text = self.genBoardOptionMenuText()
			programmer_menu_text = self.genProgrammerMenuText()
			example_menu_text = self.genExampleMenuText()

			self.full_menu_text = self.full_menu_text.replace('{"caption": "Import_Library->"},', library_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Board->"},', board_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Board_Option->"},', board_option_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Programmer->"},', programmer_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Examples->"},', example_menu_text)

	def writeMainMenuFile(self):
		menu_text = self.getFullMneuText() % self.language.getTransDict()
		osfile.writeFile(self.main_menu_file, menu_text)

	def getPlatform(self):
		platform = const.settings.get('platform')
		platform_list = self.arduino_info.getPlatformList()
		if not platform in platform_list:
			platform = platform_list[0]
			const.settings.set('platform', platform)
			const.save_settings()
		return platform

	def getBoard(self):
		board = const.settings.get('board')
		platform = self.getPlatform()
		board_lists = self.arduino_info.getBoardLists(platform)
		all_board_list = utils.simplifyLists(board_lists)
		if not board in all_board_list:
			board = all_board_list[0]
			const.settings.set('board', board)
			const.save_settings()
		return board

	def getOriginMenuText(self):
		if not self.original_menu_text:
			self.genOriginalMenuText()
		return self.original_menu_text

	def getFullMneuText(self):
		if not self.full_menu_text:
			self.genFullMenuText()
		return self.full_menu_text