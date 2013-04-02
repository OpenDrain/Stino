#-*- coding: utf-8 -*-
# stino/stcommands.py

import sublime
import sublime_plugin
import os
import stino
import time

class ShowFileExplorerPanelCommand(sublime_plugin.WindowCommand):
	def run(self, top_path_list, condition_mod, condition_func, function_mod, function_func, \
		with_files = True, with_button = False, extra_parameter = ''):
		self.level = 0
		self.top_path_list = top_path_list
		self.path_list = top_path_list
		self.condition_module = getattr(stino, condition_mod)
		self.condition_func = condition_func
		self.function_module = getattr(stino, function_mod)
		self.function_func = function_func
		self.with_files = with_files
		self.with_button = with_button
		self.extra_parameter = extra_parameter

		file_list = stino.osfile.genFileListFromPathList(self.path_list, stino.cur_language)
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
			(self.level, self.path_list) = stino.osfile.enterSubDir(self.top_path_list, \
				self.level, index, sel_path, with_files = self.with_files, with_button = self.with_button)
			file_list = stino.osfile.genFileListFromPathList(self.path_list, stino.cur_language)
			self.window.show_quick_panel(file_list, self.on_done)

class SelectItemCommand(sublime_plugin.WindowCommand):
	def run(self, command, parent_mod, list_func, parameter1, parameter2, parameter3):
		parent_mod = getattr(stino, parent_mod) 
		func = getattr(parent_mod, list_func)
		self.parameter1 = parameter1
		self.parameter2 = parameter2
		self.parameter3 = parameter3
		self.command = command
		if self.parameter1 and self.parameter3:
			self.info_list = func(self.parameter1, self.parameter2, self.parameter3)
		elif self.parameter1:
			self.info_list = func(self.parameter1)
		else:
			self.info_list = func()
		if stino.utils.isLists(self.info_list):
			self.info_list = stino.utils.simplifyLists(self.info_list)
		self.window.show_quick_panel(self.info_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return
			
		sel_item = self.info_list[index]
		if self.parameter1 and self.parameter3:
			menu_str = stino.utils.genKey(self.parameter2, self.parameter1)
			menu_str = stino.utils.genKey(self.parameter3, menu_str)
			menu_str = stino.utils.genKey(sel_item, menu_str)
		elif self.parameter1:
			menu_str = stino.utils.genKey(sel_item, self.parameter1)
		else:
			menu_str = sel_item

		self.window.run_command(self.command, {'menu_str': menu_str})

class NotEnabledCommand(sublime_plugin.WindowCommand):
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
				view.window().run_command('send_to_serial')

	def on_close(self, view):
		if stino.smonitor.isMonitorView(view):
			name = view.name()
			serial_port = name.split('-')[1].strip()
			if serial_port in stino.serial_port_monitor_dict:
				serial_monitor = stino.serial_port_monitor_dict[serial_port]
				serial_monitor.stop()
				if serial_port in stino.serial_port_in_use_list:
					stino.serial_port_in_use_list.remove(serial_port)

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
		caption = '%(Name_for_new_sketch:)s'
		caption = caption % stino.cur_language.getTransDict()
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		if input_text:
			filename = stino.osfile.regulariseFilename(input_text)
			if stino.osfile.existsInSketchbook(filename):
				display_text = 'Sketch {1} exists, please use another file name.\n'
				msg = stino.cur_language.translate(display_text)
				msg = msg.replace('{1}', filename)
				stino.log_panel.addText(msg)
			else:
				stino.src.createNewSketch(filename)
				stino.arduino_info.sketchbookUpdate()
				stino.cur_menu.update()

class OpenSketchCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		stino.src.openSketch(menu_str)

	def is_enabled(self):
		state = stino.const.settings.get('show_arduino_menu', False)
		return state

class NewToSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		caption = '%(Name_for_new_file:)s'
		caption = caption % stino.cur_language.getTransDict()
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		if input_text:
			filename = stino.osfile.regulariseFilename(input_text)
			view_file_name = self.window.active_view().file_name()
			folder_path = os.path.split(view_file_name)[0]
			new_file_path = os.path.join(folder_path, filename)
			if os.path.exists(new_file_path):
				display_text = 'File {1} exists, please use another file name.\n'
				msg = stino.cur_language.translate(display_text)
				msg = msg.replace('{1}', filename)
				stino.log_panel.addText(msg)
			else:
				stino.src.createNewFile(self.window, new_file_path)

	def is_enabled(self):
		state = stino.const.settings.get('show_arduino_menu', False)
		return state

class ImportLibraryCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		view = self.window.active_view()
		(library, platform) = stino.utils.getInfoFromKey(menu_str)
		library_path = stino.arduino_info.getLibraryPath(platform, library)
		stino.src.insertLibraries(library_path, view)

	def is_enabled(self):
		state = stino.const.settings.get('show_arduino_menu', False)
		return state

class ShowSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		filename = self.window.active_view().file_name()
		if filename:
			# sketch_folder_path = stino.src.getSketchFolderPath(filename)
			sketch_folder_path = os.path.split(filename)[0]
			self.window.run_command('show_file_explorer_panel', {'top_path_list':[sketch_folder_path], \
				'condition_mod':'osfile', 'condition_func':'isFile', 'function_mod':'osfile', \
				'function_func':'openFile'})

	def is_enabled(self):
		state = stino.const.settings.get('show_arduino_menu', False)
		return state

class ChangeExtraFlagsCommand(sublime_plugin.WindowCommand):
	def run(self):
		caption = '%(Extra compilation flags:)s'
		caption = caption % stino.cur_language.getTransDict()
		extra_flags = stino.const.settings.get('extra_flags')
		if (not extra_flags) or (len(extra_flags) < 2):
			extra_flags = '-D'
		self.window.show_input_panel(caption, extra_flags, self.on_done, None, None)

	def on_done(self, input_text):
		extra_flags = input_text
		if (not extra_flags) or (len(extra_flags) < 3):
			extra_flags = ''
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
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		cur_compilation = stino.compilation.Compilation(stino.cur_language, stino.arduino_info, \
			stino.cur_menu, filename)
		cur_compilation.start()

	def is_enabled(self):
		state = stino.const.settings.get('show_arduino_menu', False)
		return state

class UploadBinaryCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		cur_upload = stino.compilation.Upload(stino.cur_language, stino.arduino_info, stino.cur_menu, \
			filename, serial_port_in_use_list = stino.serial_port_in_use_list, \
			serial_port_monitor_dict = stino.serial_port_monitor_dict)
		cur_upload.start()

	def is_enabled(self):
		state = True
		platform = stino.const.settings.get('platform')
		if 'AVR' in platform:
			serial_port_list = stino.smonitor.genSerialPortList()
			if not serial_port_list:
				state = False
		show_state = stino.const.settings.get('show_arduino_menu', False)
		state = state and show_state
		return state

class UploadUsingProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		cur_upload = stino.compilation.Upload(stino.cur_language, stino.arduino_info, \
			stino.cur_menu, filename, mode = 'upload_using_programmer')
		cur_upload.start()

	def is_enabled(self):
		state = False
		platform = stino.const.settings.get('platform')
		programmer_lists = stino.arduino_info.getProgrammerLists(platform)
		if programmer_lists:
			state = True
		show_state = stino.const.settings.get('show_arduino_menu', False)
		state = state and show_state
		return state

class SelectBoardCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(board, platform) = stino.utils.getInfoFromKey(menu_str)
		pre_platform = stino.const.settings.get('platform')
		pre_board = stino.const.settings.get('board')
		if platform != pre_platform or board != pre_board:
			stino.const.settings.set('platform', platform)
			stino.const.settings.set('board', board)
			stino.const.settings.set('full_compilation', True)
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
			stino.const.settings.set('full_compilation', True)
			stino.const.save_settings()
			stino.cur_menu.commandUpdate()

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
		serial_port = stino.const.settings.get('serial_port')
		if not serial_port in stino.serial_port_in_use_list:
			serial_monitor = stino.smonitor.SerialMonitor(serial_port)
			stino.serial_port_in_use_list.append(serial_port)
			stino.serial_port_monitor_dict[serial_port] = serial_monitor
		else:
			serial_monitor = stino.serial_port_monitor_dict[serial_port]
		serial_monitor.start()
		self.window.run_command('send_to_serial')

	def is_enabled(self):
		state = False
		serial_port = stino.const.settings.get('serial_port')
		serial_port_list = stino.smonitor.genSerialPortList()
		if serial_port in serial_port_list:
			if stino.smonitor.isSerialPortAvailable(serial_port):
				state = True
		return state

class StopSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		name = self.window.active_view().name()
		serial_port = name.split('-')[1].strip()
		serial_monitor = stino.serial_port_monitor_dict[serial_port]
		serial_monitor.stop()
		if serial_port in stino.serial_port_in_use_list:
			stino.serial_port_in_use_list.remove(serial_port)

	def is_enabled(self):
		state = False
		view = self.window.active_view()
		if stino.smonitor.isMonitorView(view):
			name = view.name()
			serial_port = name.split('-')[1].strip()
			serial_port_list = stino.serial_port_in_use_list
			if serial_port in serial_port_list:
				state = True
		return state

class SendToSerialCommand(sublime_plugin.WindowCommand):
	def run(self):
		caption = '%(Send:)s'
		self.caption = caption % stino.cur_language.getTransDict()
		self.window.show_input_panel(self.caption, '', self.on_done, None, None)
		
	def on_done(self, input_text):
		if input_text:
			view = self.window.active_view()
			if stino.smonitor.isMonitorView(view):
				name = view.name()
				serial_port = name.split('-')[1].strip()
				if serial_port in stino.serial_port_in_use_list:
					serial_monitor = stino.serial_port_monitor_dict[serial_port]
					serial_monitor.send(input_text)
					self.window.show_input_panel(self.caption, '', self.on_done, None, None)

	def is_enabled(self):
		state = False
		view = self.window.active_view()
		if stino.smonitor.isMonitorView(view):
			name = view.name()
			serial_port = name.split('-')[1].strip()
			serial_port_list = stino.serial_port_in_use_list
			if serial_port in serial_port_list:
				state = True
		return state

class SelectProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(programmer, platform) = stino.utils.getInfoFromKey(menu_str)
		pre_platform = stino.const.settings.get('platform')
		pre_programmer = stino.const.settings.get('programmer')
		if platform != pre_platform or programmer != pre_programmer:
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
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		cur_burn = stino.compilation.BurnBootloader(stino.cur_language, stino.arduino_info, stino.cur_menu, filename)
		cur_burn.start()

	def is_enabled(self):
		state = False
		platform = stino.const.settings.get('platform')
		programmer_lists = stino.arduino_info.getProgrammerLists(platform)
		if programmer_lists:
			state = True
		show_state = stino.const.settings.get('show_arduino_menu', False)
		state = state and show_state
		return state

class SelectLanguageCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		language = stino.cur_language.getLanguageFromLanguageText(menu_str)
		pre_language = stino.const.settings.get('language')
		if language != pre_language:
			stino.const.settings.set('language', language)
			stino.const.save_settings()
			stino.cur_language.update()
			stino.cur_menu.languageUpdate()

	def is_checked(self, menu_str):
		state = False
		setting_language = stino.const.settings.get('language')
		cur_language = stino.cur_language.getLanguageFromLanguageText(menu_str)
		if cur_language == setting_language:
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
		stino.cur_menu.commandUpdate()

	def is_checked(self):
		state = stino.const.settings.get('full_compilation')
		return state

class ToggleVerboseCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_compilation = not stino.const.settings.get('verbose_compilation')
		stino.const.settings.set('verbose_compilation', verbose_compilation)
		stino.const.save_settings()
		stino.cur_menu.commandUpdate()

	def is_checked(self):
		state = stino.const.settings.get('verbose_compilation')
		return state

class ToggleVerboseUploadCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_upload = not stino.const.settings.get('verbose_upload')
		stino.const.settings.set('verbose_upload', verbose_upload)
		stino.const.save_settings()
		stino.cur_menu.commandUpdate()

	def is_checked(self):
		state = stino.const.settings.get('verbose_upload')
		return state

class ToggleVerifyCodeCommand(sublime_plugin.WindowCommand):
	def run(self):
		verify_code = not stino.const.settings.get('verify_code')
		stino.const.settings.set('verify_code', verify_code)
		stino.const.save_settings()
		stino.cur_menu.commandUpdate()

	def is_checked(self):
		state = stino.const.settings.get('verify_code')
		return state

class AutoFormatCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.run_command('reindent', {'single_line': False})

class ArchiveSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		filename = self.window.active_view().file_name()
		if filename:
			sketch_folder_path = stino.src.getSketchFolderPath(filename)
			home_root_list = stino.osfile.getHomeRootList()
			self.window.run_command('show_file_explorer_panel', {'top_path_list':home_root_list, \
				'condition_mod':'osfile', 'condition_func':'isButtonPress', 'function_mod':'actions', \
				'function_func':'getArchiveFolderPath', 'with_files': False, 'with_button': True, \
				'extra_parameter': sketch_folder_path})

class FixEncodingCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		filename = view.file_name()
		if filename:
			state = True
			if view.is_dirty():
				display_text = 'Discard all changes and reload sketch?\n'
				msg = stino.cur_language.translate(display_text)
				state = sublime.ok_cancel_dialog(msg)
		
			if state:
				content = stino.osfile.readFileText(filename)
				edit = view.begin_edit()
				view.replace(edit, sublime.Region(0, view.size()), content)
				view.end_edit(edit)

class SelectExampleCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		(example, platform) = stino.utils.getInfoFromKey(menu_str)
		example_path = stino.arduino_info.getExamplePath(platform, example)
		self.window.run_command('show_file_explorer_panel', {'top_path_list':[example_path], \
				'condition_mod':'arduino', 'condition_func':'isSketchFolder', 'function_mod':'src', \
				'function_func':'openExample'})

class OpenRefCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		stino.osfile.openUrl(menu_str)

class FindInReferenceCommand(sublime_plugin.WindowCommand):
	def run(self):
		view = self.window.active_view()
		selected_text = stino.utils.getSelectedTextFromView(view)
		platform = stino.const.settings.get('platform')
		keyword_operator_list = stino.arduino_info.getOperatorList(platform)
		keyword_list = stino.utils.getKeywordListFromText(selected_text, keyword_operator_list)
		(ref_list, msg_text) = stino.utils.getRefList(keyword_list, stino.arduino_info, platform)
		stino.osfile.openUrlList(ref_list)
		stino.log_panel.addText(msg_text)

class AboutStinoCommand(sublime_plugin.WindowCommand):
	def run(self):
		display_text = 'Stino'
		msg = stino.cur_language.translate(display_text)
		sublime.message_dialog(msg)