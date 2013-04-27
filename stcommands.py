#-*- coding: utf-8 -*-
# stino/stcommands.py

import sys
import os
import inspect

import sublime
import sublime_plugin

# Get the path where Stino is.
plugin_path = inspect.stack()[0][1]
stino_root = os.path.split(plugin_path)[0]
sys.path.append(stino_root)

from stino import const
from stino import globalvars
from stino import textutil
from stino import fileutil
from stino import stpanel
from stino import sketch
from stino import src
from stino import actions

class StinoInsertTextCommand(sublime_plugin.TextCommand):
	def run(self, edit, position, text = ''):
		self.view.insert(edit, position, text)

class StinoReplaceTextCommand(sublime_plugin.TextCommand):
	def run(self, edit, text = ''):
		self.view.replace(edit, sublime.Region(0, self.view.size()), text)

class ShowFileExplorerPanelCommand(sublime_plugin.WindowCommand):
	def run(self, top_path_list, condition_mod, condition_func, function_mod, function_func, \
		with_files = True, with_button = False, extra_parameter = ''):
		self.level = 0
		self.top_path_list = top_path_list
		self.path_list = top_path_list
		self.condition_module = sys.modules['stino.' + condition_mod]
		self.condition_func = condition_func
		self.function_module = sys.modules['stino.' + function_mod]
		self.function_func = function_func
		self.with_files = with_files
		self.with_button = with_button
		self.extra_parameter = extra_parameter

		file_list = fileutil.genFileListFromPathList(self.path_list, globalvars.cur_language)
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if getattr(self.condition_module, self.condition_func)(sel_path):
			if self.extra_parameter:
				getattr(self.function_module, self.function_func)(sel_path, self.extra_parameter)
			else:
				getattr(self.function_module, self.function_func)(sel_path)
		else:		
			(self.level, self.path_list) = fileutil.enterSubDir(self.top_path_list, \
				self.level, index, sel_path, with_files = self.with_files, with_button = self.with_button)
			file_list = fileutil.genFileListFromPathList(self.path_list, globalvars.cur_language)
			sublime.set_timeout(lambda: self.window.show_quick_panel(file_list, self.on_done), 0)

class SelectItemCommand(sublime_plugin.WindowCommand):
	def run(self, command, parent_mod, list_func, parameter1, parameter2, parameter3):
		parent_mod = sys.modules['stino.' + parent_mod]
		attr_list = list_func.split('.')
		for attr in attr_list:
			func = getattr(parent_mod, attr)
			parent_mod = func
		self.parameter1 = parameter1
		self.parameter2 = parameter2
		self.parameter3 = parameter3
		self.command = command

		all_info_list = []
		self.menu_str_list = []

		if self.parameter1 and self.parameter3:
			info_list = func(self.parameter1, self.parameter2, self.parameter3)
			info_list = textutil.simplifyLists(info_list)
			for item in info_list:
				menu_str = textutil.genKey(self.parameter1, self.parameter2)
				menu_str = textutil.genKey( menu_str, self.parameter3)
				menu_str = textutil.genKey(menu_str, item)
				self.menu_str_list.append(menu_str)
			all_info_list = info_list
		elif self.parameter1:
			platform_list = ['common', self.parameter1]
			for platform in platform_list:
				info_list = func(platform)
				info_list = textutil.simplifyLists(info_list)
				for item in info_list:
					menu_str = textutil.genKey(platform, item)
					self.menu_str_list.append(menu_str)
				all_info_list += info_list
		else:
			info_list = func()
			self.menu_str_list = info_list
			all_info_list = info_list
		self.window.show_quick_panel(all_info_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return
			
		menu_str = self.menu_str_list[index]
		sublime.set_timeout(lambda: self.window.run_command(self.command, {'menu_str': menu_str}), 0)

class NotEnabledCommand(sublime_plugin.WindowCommand):
	def is_enabled(self):
		return False

class SketchListener(sublime_plugin.EventListener):
	def on_new(self, view):
		const.settings.set('show_arduino_menu', False)
		const.settings.set('show_serial_monitor_menu', False)
	# 	cur_menu.update()
	# 	serial_listener.stop()
	# 	status_info.setView(view)
	# 	status_info.update()

	def on_activated(self, view):
		if not stpanel.isPanel(view):
			pre_state = const.settings.get('show_arduino_menu')
			file_path = view.file_name()
			state = sketch.isArduinoSrcFile(file_path)
			if state:
				global_setting = const.settings.get('global_setting')
				if not global_setting:
					pre_setting_folder_path = const.settings.get('setting_folder_path')
					setting_folder_path = os.path.split(file_path)[0]
					
					if setting_folder_path != pre_setting_folder_path:
						const.settings.changeSettingFileFolder(setting_folder_path)
						globalvars.arduino_info.update()
						globalvars.menu.update()

			if state != pre_state:
				const.settings.set('show_arduino_menu', state)
				globalvars.menu.update()

	# 			if state:
	# 				serial_listener.start()
	# 			else:
	# 				serial_listener.stop()

	# 		pre_state = const.settings.get('show_serial_monitor_menu')
	# 		state = smonitor.isMonitorView(view)
	# 		if state != pre_state:
	# 			const.settings.set('show_serial_monitor_menu', state)
	# 			cur_menu.update()
	# 			view.window().run_command('send_to_serial')

	# 		status_info.setView(view)
	# 		status_info.update()

	# def on_close(self, view):
	# 	if smonitor.isMonitorView(view):
	# 		name = view.name()
	# 		serial_port = name.split('-')[1].strip()
	# 		if serial_port in serial_port_monitor_dict:
	# 			serial_monitor = serial_port_monitor_dict[serial_port]
	# 			serial_monitor.stop()
	# 			if serial_port in serial_port_in_use_list:
	# 				serial_port_in_use_list.remove(serial_port)

class ShowArduinoMenuCommand(sublime_plugin.WindowCommand):
	def run(self):
		show_arduino_menu = not const.settings.get('show_arduino_menu')
		const.settings.set('show_arduino_menu', show_arduino_menu)
		globalvars.menu.update()

	def is_checked(self):
		state = const.settings.get('show_arduino_menu')
		return state

class NewSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		display_text = 'Name for new sketch:'
		caption = globalvars.cur_language.translate(display_text)
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		if input_text:
			filename = fileutil.regulariseFilename(input_text)
			sketchbook_root = fileutil.getSketchbookRoot()
			file_path = os.path.join(sketchbook_root, filename)
			if os.path.exists(file_path):
				display_text = 'A sketch (or folder) named "{0}" already exists. Could not create the sketch.\n'
				globalvars.log_panel.addText(display_text, [filename])
			else:
				sketch.createNewSketch(file_path)
				globalvars.menu.update()

class OpenSketchCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		cur_sketch = menu_str
		sketch_info = sketch.genSketchInfo()
		sketch_path_dict = sketch_info[1]
		
		if cur_sketch in sketch_path_dict:
			sketch.openSketch(sketch_path_dict[cur_sketch])
		else:
			display_text = 'The selected sketch no longer exists. You may need to restart Sublime Text to update the sketchbook menu.\n'
			globalvars.log_panel.addText(display_text)

class SelectExampleCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(example, platform) = textutil.getInfoFromKey(menu_str)
		example_path = globalvars.arduino_info.getExamplePath(platform, example)
		dir_list = fileutil.listDir(example_path, with_files = False)
		dir_path_list = [os.path.join(example_path, cur_dir) for cur_dir in dir_list]
		self.window.run_command('show_file_explorer_panel', {'top_path_list':dir_path_list, \
				'condition_mod': 'sketch', 'condition_func':'isSketchFolder', 'function_mod': 'sketch', \
				'function_func':'openSketch'})

class NewToSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		display_text = 'Name for new file:'
		caption = globalvars.cur_language.translate(display_text)
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		if input_text:
			filename = fileutil.regulariseFilename(input_text)
			view_file_name = self.window.active_view().file_name()
			folder_path = os.path.split(view_file_name)[0]
			new_file_path = os.path.join(folder_path, filename)
			if os.path.exists(new_file_path):
				display_text = 'A file named "{0}" already exists. Could not create the file.\n'
				globalvars.log_panel.addText(display_text, [filename])
			else:
				sketch.createNewFile(self.window, new_file_path)

	def is_enabled(self):
		state = const.settings.get('show_arduino_menu', False)
		return state

class ImportLibraryCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		view = self.window.active_view()
		(library, platform) = textutil.getInfoFromKey(menu_str)
		library_path = globalvars.arduino_info.getLibraryPath(platform, library)
		if os.path.isdir(library_path):
			src.insertIncludeText(library_path, view)
		else:
			display_text = 'The selected library no longer exists. You may need to restart Sublime Text to update the import library menu.\n'
			globalvars.log_panel.addText(display_text)

	def is_enabled(self):
		state = const.settings.get('show_arduino_menu', False)
		return state

class ShowSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		filename = self.window.active_view().file_name()
		if filename:
			sketch_folder_path = os.path.split(filename)[0]
			dir_list = fileutil.listDir(sketch_folder_path)
			dir_path_list = [os.path.join(sketch_folder_path, cur_dir) for cur_dir in dir_list]
			self.window.run_command('show_file_explorer_panel', {'top_path_list':dir_path_list, \
				'condition_mod':'sketch', 'condition_func':'isFile', 'function_mod':'sketch', \
				'function_func':'openFile'})

	def is_enabled(self):
		state = const.settings.get('show_arduino_menu', False)
		return state

class ChangeExtraFlagsCommand(sublime_plugin.WindowCommand):
	def run(self):
		display_text = 'Extra compilation flags:'
		caption = globalvars.cur_language.translate(display_text)
		extra_flags = const.settings.get('extra_flags', '')
		self.window.show_input_panel(caption, extra_flags, self.on_done, None, None)

	def on_done(self, input_text):
		extra_flags = input_text
		const.settings.set('extra_flags', extra_flags)

	def description(self):
		extra_flags = const.settings.get('extra_flags', '')
		if not extra_flags:
			display_text = 'Add Extra Flags'
		else:
			display_text = 'Change Extra Flags'
		caption = globalvars.cur_language.translate(display_text)
		return caption

class CompileSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		# cur_compilation = compilation.Compilation(cur_language, arduino_info, \
		# 	cur_menu, filename)
		# cur_compilation.start()

	def is_enabled(self):
		state = const.settings.get('show_arduino_menu', False)
		return state

class UploadBinaryCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		# cur_upload = compilation.Upload(cur_language, arduino_info, cur_menu, \
		# 	filename, serial_port_in_use_list = serial_port_in_use_list, \
		# 	serial_port_monitor_dict = serial_port_monitor_dict)
		# cur_upload.start()

	# def is_enabled(self):
	# 	state = True
	# 	platform = const.settings.get('platform')
	# 	if 'AVR' in platform:
	# 		serial_port_list = smonitor.genSerialPortList()
	# 		if not serial_port_list:
	# 			state = False
	# 	show_state = const.settings.get('show_arduino_menu', False)
	# 	state = state and show_state
	# 	return state

class UploadUsingProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		# cur_upload = compilation.Upload(cur_language, arduino_info, \
		# 	cur_menu, filename, mode = 'upload_using_programmer')
		# cur_upload.start()

	def is_enabled(self):
		state = False
		platform = const.settings.get('platform')
		# programmer_lists = arduino_info.getProgrammerLists(platform)
		# if programmer_lists:
		# 	state = True
		# show_state = const.settings.get('show_arduino_menu', False)
		# state = state and show_state
		return state

class SelectBoardCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(board, platform) = textutil.getInfoFromKey(menu_str)
		pre_platform = const.settings.get('platform')
		pre_board = const.settings.get('board')
		if platform != pre_platform or board != pre_board:
			const.settings.set('platform', platform)
			const.settings.set('board', board)
			const.settings.set('full_compilation', True)
			globalvars.menu.update()
			# status_info.update()

	def is_checked(self, menu_str):
		state = False
		platform = const.settings.get('platform')
		board = const.settings.get('board')
		board_platform = textutil.genKey(platform, board)
		if menu_str == board_platform:
			state = True
		return state

class SelectBoardTypeCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(item, board_type, board, platform) = textutil.getInfoFromKey(menu_str)
		type_caption = globalvars.arduino_info.getPlatformTypeCaption(platform, board_type)
		pre_item = const.settings.get(type_caption)
		if not item == pre_item:
			const.settings.set(type_caption, item)
			const.settings.set('full_compilation', True)
			globalvars.menu.update()
			# status_info.update()

	def is_checked(self, menu_str):
		state = False
		(item, board_type, board, platform) = textutil.getInfoFromKey(menu_str)
		type_caption = globalvars.arduino_info.getPlatformTypeCaption(platform, board_type)
		pre_item = const.settings.get(type_caption)
		if item == pre_item:
			state = True
		return state

class SelectSerialPortCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		serial_port = menu_str
		pre_serial_port = const.settings.get('serial_port')
		if serial_port != pre_serial_port:
			const.settings.set('serial_port', serial_port)
			# status_info.update()

	def is_checked(self, menu_str):
		state = False
		serial_port = const.settings.get('serial_port')
		if menu_str == serial_port:
			state = True
		return state

class SelectBaudrateCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		baudrate = menu_str
		pre_baudrate = const.settings.get('baudrate')
		if baudrate != pre_baudrate:
			const.settings.set('baudrate', baudrate)
			# status_info.update()

	def is_checked(self, menu_str):
		state = False
		baudrate = const.settings.get('baudrate')
		if menu_str == baudrate:
			state = True
		return state

class StartSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		serial_port = const.settings.get('serial_port')
		if not serial_port in serial_port_in_use_list:
			serial_monitor = smonitor.SerialMonitor(serial_port)
			serial_port_in_use_list.append(serial_port)
			serial_port_monitor_dict[serial_port] = serial_monitor
		else:
			serial_monitor = serial_port_monitor_dict[serial_port]
		serial_monitor.start()
		self.window.run_command('send_to_serial')

	def is_enabled(self):
		state = False
		# serial_port = const.settings.get('serial_port')
		# serial_port_list = smonitor.genSerialPortList()
		# if serial_port in serial_port_list:
		# 	# if smonitor.isSerialPortAvailable(serial_port):
		# 	state = True
		return state

class StopSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		name = self.window.active_view().name()
		serial_port = name.split('-')[1].strip()
		serial_monitor = serial_port_monitor_dict[serial_port]
		serial_monitor.stop()
		if serial_port in serial_port_in_use_list:
			serial_port_in_use_list.remove(serial_port)

	def is_enabled(self):
		state = False
		# view = self.window.active_view()
		# if smonitor.isMonitorView(view):
		# 	name = view.name()
		# 	serial_port = name.split('-')[1].strip()
		# 	serial_port_list = serial_port_in_use_list
		# 	if serial_port in serial_port_list:
		# 		state = True
		return state

class SendToSerialCommand(sublime_plugin.WindowCommand):
	def run(self):
		caption = '%(Send)s'
		self.caption = caption % cur_language.getTransDict()
		self.window.show_input_panel(self.caption, '', self.on_done, None, None)
		
	def on_done(self, input_text):
		if input_text:
			view = self.window.active_view()
			if smonitor.isMonitorView(view):
				name = view.name()
				serial_port = name.split('-')[1].strip()
				if serial_port in serial_port_in_use_list:
					serial_monitor = serial_port_monitor_dict[serial_port]
					serial_monitor.send(input_text)
					self.window.show_input_panel(self.caption, '', self.on_done, None, None)

	def is_enabled(self):
		state = False
		# view = self.window.active_view()
		# if smonitor.isMonitorView(view):
		# 	name = view.name()
		# 	serial_port = name.split('-')[1].strip()
		# 	serial_port_list = serial_port_in_use_list
		# 	if serial_port in serial_port_list:
		# 		state = True
		return state

class SelectProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(programmer, platform) = textutil.getInfoFromKey(menu_str)
		pre_platform = const.settings.get('platform')
		pre_programmer = const.settings.get('programmer')
		if platform != pre_platform or programmer != pre_programmer:
			const.settings.set('programmer', programmer)
			# status_info.update()

	def is_checked(self, menu_str):
		state = False
		platform = const.settings.get('platform')
		programmer = const.settings.get('programmer')
		programmer_platform = textutil.genKey(platform, programmer)
		if menu_str == programmer_platform:
			state = True
		return state

class BurnBootloaderCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		# cur_burn = compilation.BurnBootloader(cur_language, arduino_info, cur_menu, filename)
		# cur_burn.start()

	def is_enabled(self):
		state = False
		platform = const.settings.get('platform')
		# programmer_lists = arduino_info.getProgrammerLists(platform)
		# if programmer_lists:
		# 	state = True
		# show_state = const.settings.get('show_arduino_menu', False)
		# state = state and show_state
		return state

class SelectLanguageCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		language = globalvars.cur_language.getLanguageFromLanguageText(menu_str)
		pre_language = const.settings.get('language')
		if language != pre_language:
			const.settings.set('language', language)
			globalvars.cur_language.update()
			globalvars.menu.changeLanguage()

	def is_checked(self, menu_str):
		state = False
		setting_language = const.settings.get('language')
		cur_language = globalvars.cur_language.getLanguageFromLanguageText(menu_str)
		if cur_language == setting_language:
			state = True
		return state

class ToggleGlobalSettingCommand(sublime_plugin.WindowCommand):
	def run(self):
		global_setting = not const.settings.get('global_setting', True)
		file_path = self.window.active_view().file_name()
		setting_folder_path = os.path.split(file_path)[0]
		const.settings.changeState(global_setting, setting_folder_path)
		globalvars.arduino_info.update()
		globalvars.menu.update()
		# status_info.update()
		
	def is_checked(self):
		state = const.settings.get('global_setting', True)
		return state

	def is_enabled(self):
		state = const.settings.get('show_arduino_menu', False)
		return state

class SelectArduinoFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		app_root_list = fileutil.getAppRootList()
		self.window.run_command('show_file_explorer_panel', {'top_path_list':app_root_list, \
			'condition_mod':'fileutil', 'condition_func':'isArduinoRoot', 'function_mod':'actions', \
			'function_func':'changeArduinoRoot', 'with_files': False})

class ChangeSketchbookFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		home_root_list = fileutil.getHomeRootList()
		self.window.run_command('show_file_explorer_panel', {'top_path_list':home_root_list, \
			'condition_mod':'fileutil', 'condition_func':'isButtonPress', 'function_mod':'actions', \
			'function_func':'changeSketchbookRoot', 'with_files': False, 'with_button': True})

class ToggleFullCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		full_compilation = not const.settings.get('full_compilation', False)
		const.settings.set('full_compilation', full_compilation)

	def is_checked(self):
		state = const.settings.get('full_compilation', False)
		return state

class ToggleVerboseCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_compilation = not const.settings.get('verbose_compilation', False)
		const.settings.set('verbose_compilation', verbose_compilation)

	def is_checked(self):
		state = const.settings.get('verbose_compilation', False)
		return state

class ToggleVerboseUploadCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_upload = not const.settings.get('verbose_upload', False)
		const.settings.set('verbose_upload', verbose_upload)

	def is_checked(self):
		state = const.settings.get('verbose_upload', False)
		return state

class ToggleVerifyCodeCommand(sublime_plugin.WindowCommand):
	def run(self):
		verify_code = not const.settings.get('verify_code', False)
		const.settings.set('verify_code', verify_code)

	def is_checked(self):
		state = const.settings.get('verify_code', False)
		return state

class AutoFormatCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.run_command('reindent', {'single_line': False})
		display_text = 'Auto Format finished.\n'
		state = globalvars.log_panel.addText(display_text)

class ArchiveSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		filename = self.window.active_view().file_name()
		if filename:
			sketch_folder_path = os.path.split(filename)[0]
			home_root_list = fileutil.getHomeRootList()
			self.window.run_command('show_file_explorer_panel', {'top_path_list':home_root_list, \
				'condition_mod':'fileutil', 'condition_func':'isButtonPress', 'function_mod':'actions', \
				'function_func':'archiveSketch', 'with_files': False, 'with_button': True, \
				'extra_parameter': sketch_folder_path})

class FixEncodingCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		filename = view.file_name()
		if filename:
			state = True
			if view.is_dirty():
				display_text = 'Discard all changes and reload sketch?\n'
				msg = globalvars.cur_language.translate(display_text)
				state = sublime.ok_cancel_dialog(msg)
		
			if state:
				file_text = fileutil.readFileText(filename)
				textutil.replaceTextOfView(view, file_text)

class OpenRefCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		fileutil.openUrl(menu_str)

class FindInReferenceCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		selected_text = textutil.getSelectedTextFromView(view)

		platform = const.settings.get('platform')
		common_keyword_operator_list = globalvars.arduino_info.getOperatorList('common')
		platform_keyword_operator_list = globalvars.arduino_info.getOperatorList(platform)
		keyword_operator_list = common_keyword_operator_list + platform_keyword_operator_list

		keyword_list = textutil.getKeywordListFromText(selected_text, keyword_operator_list)
		(url_list, ref_text) = textutil.getRefList(keyword_list, globalvars.arduino_info, platform)
		if url_list:
			fileutil.openUrlList(url_list)
		if ref_text:
			globalvars.log_panel.addText(ref_text)
		if not (url_list or ref_text):
			display_text = 'No reference available.\n'
			globalvars.log_panel.addText(display_text)

class AboutStinoCommand(sublime_plugin.WindowCommand):
	def run(self):
		display_text = 'Stino'
		msg = globalvars.cur_language.translate(display_text)
		sublime.message_dialog(msg)
