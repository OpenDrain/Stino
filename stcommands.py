#-*- coding: utf-8 -*-
# stino/stcommands.py

import sublime
import sublime_plugin
import stino
import time

class SketchListener(sublime_plugin.EventListener):
	def on_new(self, view):
		pass

	def on_activated(self, view):
		pass

	def on_close(self, view):
		pass

class ShowArduinoMenuCommand(sublime_plugin.WindowCommand):
	def run(self):
		show_arduino_menu = not stino.const.settings.get('show_arduino_menu')
		stino.const.settings.set('show_arduino_menu', show_arduino_menu)
		stino.const.save_settings()
		stino.cur_menu.update()

	def is_checked(self):
		state = stino.const.settings.get('show_arduino_menu')
		return state

class NewSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class OpenSketchCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		sketch = menu_str
		sketch_path = stino.arduino_info.getSketchPath(sketch)
		print sketch_path

class NewToSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class ImportLibraryCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(library, platform) = stino.utils.getInfoFromKey(menu_str)
		library_path = stino.arduino_info.getLibraryPath(platform, library)
		print library_path

class ShowSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class CompileSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class UploadBinaryCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class UploadUsingProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class SelectBoardCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(board, platform) = stino.utils.getInfoFromKey(menu_str)
		pre_platform = stino.const.settings.get('platform')
		pre_board = stino.const.settings.get('board')
		if platform != pre_platform or board != pre_board:
			stino.const.settings.set('platform', platform)
			stino.const.settings.set('board', board)
			stino.const.save_settings()
			stino.cur_menu.update()

	def is_checked(self, menu_str):
		state = False
		platform = stino.const.settings.get('platform')
		board = stino.const.settings.get('board')
		board_platform = stino.utils.genKey(board, platform)
		if menu_str == board_platform:
			state = True
		return state

class SelectBoardTypeCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(item, board_type, board, platform) = stino.utils.getInfoFromKey(menu_str)
		type_caption = stino.arduino_info.getPlatformTypeCaption(platform, board_type)
		pre_item = stino.const.settings.get(type_caption)
		if not item == pre_item:
			stino.const.settings.set(type_caption, item)
			stino.const.save_settings()

	def is_checked(self, menu_str):
		state = False
		(item, board_type, board, platform) = stino.utils.getInfoFromKey(menu_str)
		type_caption = stino.arduino_info.getPlatformTypeCaption(platform, board_type)
		pre_item = stino.const.settings.get(type_caption)
		if item == pre_item:
			state = True
		return state
