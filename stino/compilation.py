#-*- coding: utf-8 -*-
# stino/compilation.py

import os
import json
import time
import datetime
import threading
import re

from . import const
from . import fileutil
from . import textutil
from . import stpanel
from . import sketch
from . import src
from . import parsearduino

ram_size_file_path = os.path.join(const.config_root, 'ram_size')
ram_size_text = fileutil.readFileText(ram_size_file_path)
ram_size_dict = json.loads(ram_size_text)

def getPlatformFilename(platform, board):
	platform_filename = ''
	platform_info_dict = {}
	
	platform_info_file = os.path.join(const.config_root, 'compilation_command_platform')
	platform_info_text = fileutil.readFileText(platform_info_file)
	if platform_info_text:
		platform_info_dict = json.loads(platform_info_text)
	if platform in platform_info_dict:
		platform_filename = platform_info_dict[platform]
	else:
		platform_info_file = os.path.join(const.config_root, 'compilation_command_board')
		platform_info_text = fileutil.readFileText(platform_info_file)
		if platform_info_text:
			platform_info_dict = json.loads(platform_info_text)
		if board in platform_info_dict:
			platform_filename = platform_info_dict[board]
	return platform_filename

def getBuildPath(sketch_name):
	build_folder_path =const.settings.get('build_folder', '')
	if not os.path.isdir(build_folder_path):
		document_root = fileutil.getDocumentRoot()
		build_folder_path = os.path.join(document_root, 'Arduino_Build')
	build_path = os.path.join(build_folder_path, sketch_name)
	fileutil.checkDir(build_path)
	build_path =build_path.replace(os.path.sep, '/')
	return build_path

def initInfoDict(base_info_dict, arduino_info, platform_file_path):
	(board_info_key_list, board_info_dict) = parsearduino.genBoardInfoDict(arduino_info)
	(programmer_info_key_list, programmer_info_dict) = parsearduino.genProgrammerInfoDict(arduino_info)

	info_key_list =  board_info_key_list + programmer_info_key_list
	info_dict = base_info_dict
	info_dict.update(board_info_dict)
	info_dict.update(programmer_info_dict)

	if 'build.vid' in info_key_list:
		if not 'build.extra_flags' in info_key_list:
			info_key_list.append('build.extra_flags')
			info_dict['build.extra_flags'] = '-DUSB_VID={build.vid} -DUSB_PID={build.pid}'
	
	(platform_info_key_list, platform_info_dict) = parsearduino.genPlatformInfoDict(platform_file_path)
	for info_key in platform_info_key_list:
		if info_key in info_key_list:
			if not info_dict[info_key]:
				info_dict[info_key] = platform_info_dict[info_key]
		else:
			info_key_list.append(info_key)
			info_dict[info_key] = platform_info_dict[info_key]
	return (info_key_list, info_dict)

def copyHFilesToBuildFolder(build_path, h_src_path_list):
	for h_src_path in h_src_path_list:
		fileutil.copyFile(h_src_path, build_path)

def getLibraryPathList(arduino_info, platform):
	library_path_list = []
	platform_list = ['common', platform]

	for platform in platform_list:
		library_lists = arduino_info.getLibraryLists(platform)
		simple_library_list = textutil.simplifyLists(library_lists)
		for library in simple_library_list:
			library_path = arduino_info.getLibraryPath(platform, library)
			if not library_path in library_path_list:
				library_path_list.append(library_path)
	return library_path_list

def getIncludeLibraryPathList(library_path_list, src_header_list):
	include_library_path_list = []
	for library_path in library_path_list:
		cur_src_header_list = src.getSrcHeaderListFromFolder(library_path)
		for src_header in cur_src_header_list:
			if src_header in src_header_list:
				include_library_path_list.append(library_path)
				break
	return include_library_path_list

def findSrcFileFromPathList(path_list, ext_list):
	src_path_list = []
	for path in path_list:
		src_path_list += sketch.findSrcFile(path, ext_list)
	return src_path_list

def listSubDirsFromPathList(path_list):
	sub_dir_list = []
	for path in path_list:
		sub_dir_list += sketch.listSubDirs(path)
	return sub_dir_list

def genMainSrcFile(ino_src_path_list, build_path, sketch_name, arduino_version):
	main_src_name = sketch_name + '.cpp'
	main_src_path = os.path.join(build_path, main_src_name)
	main_src_path = main_src_path.replace(os.path.sep, '/')

	declaration_list = src.genDeclarationList(ino_src_path_list)
	
	setup_src_file_path = src.findSetupFile(ino_src_path_list)
	if setup_src_file_path:
		ino_src_path_list.remove(setup_src_file_path)
	else:
		setup_src_file_path = ino_src_path_list[0]
		ino_src_path_list = ino_src_path_list[1:]

	setup_src_text = src.insertDeclarationToSrcFile(setup_src_file_path, declaration_list, arduino_version)

	main_src_text = setup_src_text
	for src_path in ino_src_path_list:
		main_src_text += '\n// %s\n' % src_path
		main_src_text += fileutil.readFileText(src_path)
	fileutil.writeFile(main_src_path, main_src_text)
	return main_src_path

def genIncludesText(include_folder_list):
	includes_text = ''
	for include_folder in include_folder_list:
		includes_text += '"-I%s" ' % include_folder
	includes_text = includes_text[:-1]
	return includes_text

def regulariseDictValue(info_dict, info_key_list):
	pattern_text = r'\{\S+?}'
	for info_key in info_key_list:
		info_value = info_dict[info_key]
		key_list = re.findall(pattern_text, info_value)
		if key_list:
			key_list = [key[1:-1] for key in key_list]
			for key in key_list:
				replace_text = '{' + key + '}'
				if key in info_dict:
					value = info_dict[key]
				else:
					value = ''
				info_value = info_value.replace(replace_text, value)
			info_dict[info_key] = info_value
	return info_dict

def genSrcCompilationCommandInfo(info_dict, build_path, src_path_list):
	command_list = []
	obj_path_list = []
	for src_path in src_path_list:
		filename = os.path.split(src_path)[1]
		filename += '.o'
		obj_path = os.path.join(build_path, filename)
		obj_path = obj_path.replace(os.path.sep, '/')
		obj_path_list.append(obj_path)

		src_ext = os.path.splitext(src_path)[1]
		if src_ext.lower() in ['.c', '.cc']:
			pattern = 'recipe.c.o.pattern'
		elif src_ext.lower() in ['.cpp', '.cxx']:
			pattern = 'recipe.cpp.o.pattern'
		elif src_ext.lower() in ['.s']:
			pattern = 'recipe.S.o.pattern'
		command_text = info_dict[pattern]
		command_text = command_text.replace('{source_file}', src_path)
		command_text = command_text.replace('{object_file}', obj_path)
		command_list.append(command_text)
	return (obj_path_list, command_list)

def genArCommandInfo(info_dict, ar_file_path, core_obj_path_list):
	command_list = []
	ar_file_path_list = [ar_file_path]

	object_files = ''
	for sketch_obj_path in core_obj_path_list:
		object_files += '"%s" ' % sketch_obj_path
	object_files = object_files[:-1]

	pattern = 'recipe.ar.pattern'
	command_text = self.info_dict[pattern]
	command_text = command_text.replace('"{object_file}"', object_files)
	command_list.append(command_text)
	return (ar_file_path_list, command_list)

def genElfCommandInfo(info_dict, elf_file_path, sketch_obj_path_list):
	command_list = []
	elf_file_path_list = [elf_file_path]

	object_files = ''
	for sketch_obj_path in sketch_obj_path_list:
		object_files += '"%s" ' % sketch_obj_path
	object_files = object_files[:-1]

	pattern = 'recipe.c.combine.pattern'
	command_text = info_dict[pattern]
	command_text = command_text.replace('{object_files}', object_files)
	command_list.append(command_text)
	return (elf_file_path_list, command_list)

def genEepCommandInfo(info_dict, eep_file_path):
	command_list = []
	eep_file_path_list = [eep_file_path]

	pattern = 'recipe.objcopy.eep.pattern'
	command_text = info_dict[pattern]
	command_list.append(command_text)
	return (eep_file_path_list, command_list)

def genHexCommandInfo(info_dict, hex_filename):
	command_list = []

	pattern = 'recipe.objcopy.hex.pattern'
	command_text = info_dict[pattern]
	ext = command_text[-5:-1]
	hex_file_path = hex_filename + ext
	hex_file_path_list = [hex_file_path]

	pattern = 'recipe.objcopy.hex.pattern'
	command_text = info_dict[pattern]
	command_list.append(command_text)
	return (hex_file_path_list, command_list)

def genSizeCommandList(info_dict):
	command_list = []

	pattern = 'recipe.size.pattern'
	command_text = info_dict[pattern]
	command_list.append(command_text)
	command_text = command_text.replace('-A', '')
	command_text = command_text.replace('.hex', '.elf')
	command_list.append(command_text)
	return command_list

class Compilation:
	def __init__(self, language, arduino_info, menu, file_path, is_run_cmd = True):
		self.language = language
		self.arduino_info = arduino_info
		self.menu = menu
		self.is_run_cmd = is_run_cmd

		self.sketch_folder_path = os.path.split(file_path)[0]
		self.sketch_name = os.path.split(self.sketch_folder_path)[1]

		now_time = datetime.datetime.now()
		time_str = str(now_time.microsecond)

		compilation_name = 'Compilation_' + self.sketch_name + '_' + time_str
		self.output_panel = stpanel.STPanel(self.language, compilation_name)

		self.error_messages = ['', \
			'[Stino - I do not know how to compile the sketch.]\n', \
			'']

		self.error_code = 0
		self.is_finished = False

		self.platform = const.settings.get('platform')
		self.board = const.settings.get('board')
		self.programmer = const.settings.get('programmer')

		self.src_cores_path = self.arduino_info.getSrcCoresPath(self.platform)
		self.platform_core_root = os.path.split(self.src_cores_path)[0]

		self.platform_file_path = os.path.join(self.platform_core_root, 'platform.txt')
		
		if not os.path.isfile(self.platform_file_path):
			platform_filename = getPlatformFilename(self.platform, self.board)
			self.platform_file_path = os.path.join(const.compilation_root, platform_filename)

		print(self.platform_file_path)
		if not self.platform_file_path:
			self.error_code = 1
		else:
			self.full_compilation = const.settings.get('full_compilation')
			self.verbose_compilation = const.settings.get('verbose_compilation')
			self.verbose_upload = const.settings.get('verbose_upload')
			self.verify_code = const.settings.get('verify_code')

			serial_port = const.settings.get('serial_port')

			self.extra_compilation_flags = const.settings.get('extra_flags', '')
			self.arduino_root = fileutil.getArduinoRoot()
			self.sketchbook_root = fileutil.getSketchbookRoot()

			self.variant_path = os.path.join(self.platform_core_root, 'variants')
			self.variant_folder_path = self.variant_path

			build_system_path = os.path.join(self.platform_core_root, 'system')
			
			self.arduino_version = self.arduino_info.getVersion()
			
			self.archive_file = 'core.a'
			self.hex_file_path = ''
			
			self.src_cores_path = self.src_cores_path.replace(os.path.sep, '/')
			self.platform_core_root = self.platform_core_root.replace(os.path.sep, '/')
			self.arduino_root = self.arduino_root.replace(os.path.sep, '/')
			self.library_path_list = getLibraryPathList(self.arduino_info, self.platform)

			self.base_info_dict = {}
			self.base_info_dict['runtime.ide.path'] = self.arduino_root
			self.base_info_dict['build.project_name'] = self.sketch_name
			self.base_info_dict['serial.port'] = serial_port
			self.base_info_dict['serial.port.file'] = serial_port
			self.base_info_dict['archive_file'] = self.archive_file
			self.base_info_dict['build.system.path'] = build_system_path
			self.base_info_dict['software'] = 'ARDUINO'
			self.base_info_dict['runtime.ide.version'] = '%d' % self.arduino_version
			self.base_info_dict['source_file'] = '{source_file}'
			self.base_info_dict['object_file'] = '{object_file}'
			self.base_info_dict['object_files'] = '{object_files}'
			self.base_info_dict['includes'] = '{includes}'

	def start(self):
		if self.error_code == 0:
			self.starttime = datetime.datetime.now()
			compilation_thread = threading.Thread(target=self.compile)
			compilation_thread.start()
		else:
			self.is_finished = True

	def compile(self):
		display_text = 'Gathering compilation infomation...\n'
		self.output_panel.addText(display_text)
		self.preCompilationProcess()
		if self.is_run_cmd:
			self.runCompile()
		self.is_finished = True

	def preCompilationProcess(self):
		self.build_path = getBuildPath(self.sketch_name)
		self.base_info_dict['build.path'] = self.build_path

		(self.info_key_list, self.info_dict) = initInfoDict(self.base_info_dict, \
			self.arduino_info, self.platform_file_path)

		self.ino_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.arduino_ext_list)
		self.cpp_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.cpp_ext_list)
		self.s_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.s_ext_list)
		self.h_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.src_header_ext_list)

		# copyHFilesToBuildFolder(self.build_path, self.h_src_path_list)
		self.main_src_path = genMainSrcFile(self.ino_src_path_list, self.build_path, \
			self.sketch_name, self.arduino_version)

		all_src_path_list = self.ino_src_path_list + self.cpp_src_path_list + self.h_src_path_list
		src_header_list = src.genSrcHeaderListFromSrcFileList(all_src_path_list)
		include_library_path_list = getIncludeLibraryPathList(self.library_path_list, src_header_list)
		
		build_core = self.info_dict['build.core']
		src_build_core_path = os.path.join(self.src_cores_path, build_core)

		build_core_path_list = [src_build_core_path] + include_library_path_list
		self.core_src_path_list = findSrcFileFromPathList(build_core_path_list, const.cpp_ext_list)
		self.include_folder_list = [self.sketch_folder_path]
		self.include_folder_list += listSubDirsFromPathList(build_core_path_list)
		if 'build.variant' in self.info_dict:
			board_file_path = self.arduino_info.getBoardFile(self.platform, self.board)
			board_folder_path = os.path.split(board_file_path)[0]
			variant_folder_path = os.path.join(board_folder_path, 'variants')
			variant_folder_path = os.path.join(variant_folder_path, self.info_dict['build.variant'])
			if not os.path.isdir:
				board_folder_path = self.platform_core_root
				variant_folder_path = os.path.join(board_folder_path, 'variants')
				variant_folder_path = os.path.join(variant_folder_path, self.info_dict['build.variant'])
			variant_folder_path = variant_folder_path.replace(os.path.sep, '/')
			self.include_folder_list.append(variant_folder_path)
		self.includes_text = genIncludesText(self.include_folder_list)
		self.info_dict['includes'] = self.includes_text

		self.completeInfoDict()
		self.genCompilationCommandsInfo()

	def runCompile(self):
		if self.error_code == 0:
			pass

	def completeInfoDict(self):
		self.info_dict['compiler.c.flags'] += ' '
		self.info_dict['compiler.c.flags'] += self.extra_compilation_flags
		self.info_dict['compiler.cpp.flags'] += ' '
		self.info_dict['compiler.cpp.flags'] += self.extra_compilation_flags

		if 'build.variant' in self.info_dict:
			variant_folder = self.info_dict['build.variant']
			variant_folder_path = os.path.join(self.variant_path, variant_folder)
			self.variant_folder_path = variant_folder_path.replace(os.path.sep, '/')
			self.info_dict['build.variant.path'] = self.variant_folder_path
		else:
			core_folder = self.info_dict['build.core']
			core_folder_path = os.path.join(self.src_cores_path, core_folder)
			core_folder_path = core_folder_path.replace(os.path.sep, '/')
			self.info_dict['build.variant.path'] = core_folder_path

		if not 'compiler.path' in self.info_dict:
			compiler_path = os.path.join(self.arduino_root, 'hardware/tools/avr/bin/')
			compiler_path = compiler_path.replace(os.path.sep, '/')
			self.info_dict['compiler.path'] = compiler_path

		compiler_path = self.info_dict['compiler.path']
		compiler_path = compiler_path.replace('{runtime.ide.path}', self.arduino_root)
		compiler_path = compiler_path.replace('/', os.path.sep)
		if not os.path.isdir(compiler_path):
			compiler_path = ''
		self.info_dict['compiler.path'] = compiler_path

		if 'teensy' in self.platform:
			if 'build.elide_constructors' in self.info_dict:
				if self.info_dict['build.elide_constructors'] == 'true':
					self.info_dict['build.elide_constructors'] = '-felide-constructors'
				else:
					self.info_dict['build.elide_constructors'] = ''
			if 'build.cpu' in self.info_dict:
				self.info_dict['build.mcu'] = self.info_dict['build.cpu']
			if 'build.gnu0x' in self.info_dict:
				if self.info_dict['build.gnu0x'] == 'true':
					self.info_dict['build.gnu0x'] = '-std=gnu++0x'
				else:
					self.info_dict['build.gnu0x'] = ''
			if 'build.cpp0x' in self.info_dict:
				if self.info_dict['build.cpp0x'] == 'true':
					self.info_dict['build.cpp0x'] = '-std=c++0x'
				else:
					self.info_dict['build.cpp0x'] = ''

		if not 'upload.maximum_ram_size' in self.info_dict:
			if self.info_dict['build.mcu'] in ram_size_dict:
				self.info_dict['upload.maximum_ram_size'] = ram_size_dict[self.info_dict['build.mcu']]
			else:
				self.info_dict['upload.maximum_ram_size'] = ''

		if 'cmd.path.linux' in self.info_dict:
			if const.sys_platform == 'linux':
				self.info_dict['cmd.path'] = self.info_dict['cmd.path.linux']
				self.info_dict['config.path'] = self.info_dict['config.path.linux']

		if not self.verbose_upload:
			if 'upload.quiet' in self.info_dict:
				self.info_dict['upload.verbose'] = self.info_dict['upload.quiet']
			if 'program.quiet' in self.info_dict:
				self.info_dict['program.verbose'] = self.info_dict['program.quiet']
			if 'erase.quiet' in self.info_dict:
				self.info_dict['erase.verbose'] = self.info_dict['erase.quiet']
			if 'bootloader.quiet' in self.info_dict:
				self.info_dict['bootloader.verbose'] = self.info_dict['bootloader.quiet']

		if 'AVR' in self.platform:
			if not self.verify_code:
				if 'upload.quiet' in self.info_dict:
					self.info_dict['upload.verbose'] += ' -V'
				if 'program.quiet' in self.info_dict:
					self.info_dict['program.verbose'] += ' -V'
				if 'erase.quiet' in self.info_dict:
					self.info_dict['erase.verbose'] += ' -V'
				if 'bootloader.quiet' in self.info_dict:
					self.info_dict['bootloader.verbose'] += ' -V'

		self.info_dict = regulariseDictValue(self.info_dict, self.info_key_list)

	def genCompilationCommandsInfo(self):
		(sketch_obj_path_list, sketch_command_list) = genSrcCompilationCommandInfo(self.sketch_src_path_list)