#-*- coding: utf-8 -*-
# stino/stcommands.py

import sublime
import sublime_plugin
import os
import stino
import time

class ShowFileExplorerPanelCommand(sublime_plugin.WindowCommand):
	def run(self, top_path_list, condition_mod, condition_func, function_mod, function_func, \
		with_files = True, with_button = False):
		self.level = 0
		self.top_path_list = top_path_list
		self.path_list = top_path_list
		self.condition_module = getattr(stino, condition_mod)
		self.condition_func = condition_func
		self.function_module = getattr(stino, function_mod)
		self.function_func = function_func
		self.with_files = with_files
		self.with_button = with_button

		file_list = stino.osfile.genFileListFromPathList(self.path_list)
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if getattr(self.condition_module, self.condition_func)(sel_path):
			getattr(self.function_module, self.function_func)(sel_path)
		else:		
			(self.level, self.path_list) = stino.osfile.enterSubDir(self.top_path_list, \
				self.level, index, sel_path, with_files = self.with_files, with_button = self.with_button)
			file_list = stino.osfile.genFileListFromPathList(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

class NotEnabled(sublime_plugin.WindowCommand):
	def is_enabled(self):
		return False

class SketchListener(sublime_plugin.EventListener):
	def on_new(self, view):
		stino.const.settings.set('show_arduino_menu', False)
		stino.const.settings.set('show_serial_monitor_menu', False)
		stino.const.save_settings()
		stino.cur_menu.update()
		stino.serial_listener.stop()

	def on_activated(self, view):
		if not stino.stpanel.isPanel(view):
			pre_state = stino.const.settings.get('show_arduino_menu')
			filename = view.file_name()
			
			sketch = view
			if filename:
				if not view.is_dirty():
					sketch = filename

			state = stino.src.isSketch(sketch)
			if state != pre_state:
				stino.const.settings.set('show_arduino_menu', state)
				stino.const.save_settings()
				stino.cur_menu.update()

				if state:
					stino.serial_listener.start()
				else:
					stino.serial_listener.stop()

			pre_state = stino.const.settings.get('show_serial_monitor_menu')
			state = stino.smonitor.isMonitorView(view)
			if state != pre_state:
				stino.const.settings.set('show_serial_monitor_menu', state)
				stino.const.save_settings()
				stino.cur_menu.update()

	def on_close(self, view):
		if stino.smonitor.isMonitorView(view):
			print 'Close Serial Monitor'

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
		text = '%(Name_for_new_sketch:)s'
		caption = text % stino.cur_language.getTransDict()
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		if input_text:
			filename = stino.osfile.regulariseFilename(input_text)
			if stino.osfile.existsInSketchbook(filename):
				text = 'Sketch %s exists, please use another file name.' % filename
				stino.log_panel.addText(text)
			else:
				stino.src.createNewSketch(filename)
				stino.arduino_info.sketchbookUpdate()
				stino.cur_menu.update()

class OpenSketchCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		stino.src.openSketch(menu_str)

class NewToSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		text = '%(Name_for_new_file:)s'
		caption = text % stino.cur_language.getTransDict()
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		if input_text:
			filename = stino.osfile.regulariseFilename(input_text)
			view_file_name = self.window.active_view().file_name()
			folder_path = os.path.split(view_file_name)[0]
			new_file_path = os.path.join(folder_path, filename)
			if os.path.exists(new_file_path):
				text = 'File %s exists, please use another file name.' % filename
				stino.log_panel.addText(text)
			else:
				stino.src.createNewFile(self.window, new_file_path)

class ImportLibraryCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		view = self.window.active_view()
		(library, platform) = stino.utils.getInfoFromKey(menu_str)
		library_path = stino.arduino_info.getLibraryPath(platform, library)
		stino.src.insertLibraries(library_path, view)

class ShowSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		filename = self.window.active_view().file_name()
		if filename:
			sketch_folder_path = stino.src.getSketchFolderPath(filename)
			self.window.run_command('show_file_explorer_panel', {'top_path_list':[sketch_folder_path], \
				'condition_mod':'osfile', 'condition_func':'isFile', 'function_mod':'osfile', \
				'function_func':'openFile'})

class ChangeExtraFlagsCommand(sublime_plugin.WindowCommand):
	def run(self):
		text = '%(Name_for_new_sketch:)s'
		caption = text % stino.cur_language.getTransDict()
		extra_flags = stino.const.settings.get('extra_flags')
		if (not extra_flags) or (len(extra_flags) < 2):
			extra_flags = '-D'
		self.window.show_input_panel(caption, extra_flags, self.on_done, None, None)

	def on_done(self, input_text):
		extra_flags = input_text
		if (not extra_flags) or (len(extra_flags) < 2):
			extra_flags = '-D'
		stino.const.settings.set('extra_flags', extra_flags)
		stino.const.save_settings()

	def description(self):
		extra_flags = stino.const.settings.get('extra_flags')
		if (not extra_flags) or (len(extra_flags) < 2):
			caption = '%(Add_Extra_Flags)s'
		else:
			caption = '%(Change_Extra_Flags)s'
		caption = caption % stino.cur_language.getTransDict()
		return caption

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

class SelectSerialPortCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		serial_port = menu_str
		pre_serial_port = stino.const.settings.get('serial_port')
		if serial_port != pre_serial_port:
			stino.const.settings.set('serial_port', serial_port)
			stino.const.save_settings()

	def is_checked(self, menu_str):
		state = False
		serial_port = stino.const.settings.get('serial_port')
		if menu_str == serial_port:
			state = True
		return state

class SelectBaudrateCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		baudrate = menu_str
		pre_baudrate = stino.const.settings.get('baudrate')
		if baudrate != pre_baudrate:
			stino.const.settings.set('baudrate', baudrate)
			stino.const.save_settings()

	def is_checked(self, menu_str):
		state = False
		baudrate = stino.const.settings.get('baudrate')
		if menu_str == baudrate:
			state = True
		return state

class StartSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

	def is_enabled(self):
		state = True
		return state

class StopSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

	def is_enabled(self):
		state = True
		return state

class SendToSerialCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

	def is_enabled(self):
		state = True
		return state

class SelectProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(programmer, platform) = stino.utils.getInfoFromKey(menu_str)
		pre_programmer = stino.const.settings.get('programmer')
		if platform != pre_platform:
			stino.const.settings.set('programmer', programmer)
			stino.const.save_settings()

	def is_checked(self, menu_str):
		state = False
		platform = stino.const.settings.get('platform')
		programmer = stino.const.settings.get('programmer')
		programmer_platform = stino.utils.genKey(programmer, platform)
		if menu_str == programmer_platform:
			state = True
		return state

class BurnBootloaderCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

	def is_enabled(self):
		state = True
		return state

class SelectLanguageCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		language = menu_str
		pre_language = stino.const.settings.get('language')
		if language != pre_language:
			stino.const.settings.set('language', language)
			stino.const.save_settings()
			stino.cur_language.update()
			stino.cur_menu.languageUpdate()

	def is_checked(self, menu_str):
		state = False
		language = stino.const.settings.get('language')
		if menu_str == language:
			state = True
		return state

class SelectArduinoFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		app_root_list = stino.osfile.getAppRootList()
		self.window.run_command('show_file_explorer_panel', {'top_path_list':app_root_list, \
			'condition_mod':'arduino', 'condition_func':'isArduinoRoot', 'function_mod':'actions', \
			'function_func':'changeArduinoRoot', 'with_files': False})

class ChangeSketchbookFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		home_root_list = stino.osfile.getHomeRootList()
		self.window.run_command('show_file_explorer_panel', {'top_path_list':home_root_list, \
			'condition_mod':'osfile', 'condition_func':'isButtonPress', 'function_mod':'actions', \
			'function_func':'changeSketchbookRoot', 'with_files': False, 'with_button': True})

class ToggleFullCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		full_compilation = not stino.const.settings.get('full_compilation')
		stino.const.settings.set('full_compilation', full_compilation)
		stino.const.save_settings()

	def is_checked(self):
		state = stino.const.settings.get('full_compilation')
		return state

class ToggleVerboseCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_compilation = not stino.const.settings.get('verbose_compilation')
		stino.const.settings.set('verbose_compilation', verbose_compilation)
		stino.const.save_settings()

	def is_checked(self):
		state = stino.const.settings.get('verbose_compilation')
		return state

class ToggleVerboseUploadCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_upload = not stino.const.settings.get('verbose_upload')
		stino.const.settings.set('verbose_upload', verbose_upload)
		stino.const.save_settings()

	def is_checked(self):
		state = stino.const.settings.get('verbose_upload')
		return state

class ToggleVerifyCodeCommand(sublime_plugin.WindowCommand):
	def run(self):
		verify_code = not stino.const.settings.get('verify_code')
		stino.const.settings.set('verify_code', verify_code)
		stino.const.save_settings()

	def is_checked(self):
		state = stino.const.settings.get('verify_code')
		return state

class AutoFormatCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class ArchiveSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class FixEncodingCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class SelectExampleCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(example, platform) = stino.utils.getInfoFromKey(menu_str)
		example_path = stino.arduino_info.getExamplePath(platform, example)
		print example_path

class OpenRefCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		stino.osfile.openUrl(menu_str)

class FindInReferenceCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

class AboutStinoCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass