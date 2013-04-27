#-*- coding: utf-8 -*-
# stino/status.py

class Status:
	def __init__(self, settings, arduino_info, language):
		self.settings = settings
		self.arduino_info = arduino_info
		self.language = language

		self.view = None
		self.global_setting = True
		self.arduino_version_text = ''
		self.board = ''
		self.board_option_list = []
		self.programmer = ''
		self.serial_port = ''
		self.baudrate = ''

		self.loadInfo()

	def update(self):
		text = ''
		show_arduino_menu = self.settings.get('show_arduino_menu')
		if show_arduino_menu and self.arduino_info.isReady():
			self.loadInfo()
			if self.global_setting:
				text += '%(Global Setting)s - '
			text += 'Arduino %s' % self.arduino_version_text
			text += ', %s' % self.board
			for board_option in self.board_option_list:
				text += ', %s' % board_option
			if self.serial_port:
				text += ', %s' % self.serial_port
				text += ', %s bps' % self.baudrate
			if self.programmer:
				text += ', %s' % self.programmer
			text = text % self.language.getTransDict()
		if self.view:
			self.view.set_status('Stino_status', text)

	def loadInfo(self):
		if self.arduino_info.isReady():
			self.global_setting = self.settings.get('global_setting')
			self.arduino_version_text = self.arduino_info.getVersionText()
			self.board = self.settings.get('board')
			self.programmer = self.settings.get('programmer')
			self.serial_port = self.settings.get('serial_port')
			self.baudrate = self.settings.get('baudrate')

			platform = self.settings.get('platform')
			board_type_list = self.arduino_info.getBoardTypeList(platform, self.board)
			for board_type in board_type_list:
				type_caption = self.arduino_info.getPlatformTypeCaption(platform, board_type)
				type_value = self.settings.get(type_caption)
				self.board_option_list.append(type_value)

	def setView(self, view):
		self.view = view