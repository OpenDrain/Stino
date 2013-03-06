#-*- coding: utf-8 -*-
# stino/stmenu.py

import os

from stino import const

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

	def update(self):
		pass

	def genOriginalMenuText(self):
		pass

	def genFullMenuText(self):
		pass

	def writeFile(self, display_text_dict):
		pass