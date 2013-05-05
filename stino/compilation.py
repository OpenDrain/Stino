#-*- coding: utf-8 -*-
# stino/compilation.py

import os
import json
import time
import datetime
import threading
import re
import subprocess
import shlex

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

def formatNumber(number):
	length = len(number)
	number_str = number[::-1]
	seq = 1
	new_number = ''
	for digit in number_str:
		if seq % 3 == 0:
			if seq != length:
				digit = ',' + digit
		new_number = digit + new_number
		seq += 1
	return new_number

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

	src_path_list = ino_src_path_list[:]
	declaration_list = src.genDeclarationList(src_path_list)
	
	setup_src_file_path = src.findSetupFile(src_path_list)
	if setup_src_file_path:
		src_path_list.remove(setup_src_file_path)
	else:
		setup_src_file_path = src_path_list[0]
		src_path_list = src_path_list[1:]

	setup_src_text = src.insertDeclarationToSrcFile(setup_src_file_path, declaration_list, arduino_version)

	main_src_text = setup_src_text
	for src_path in src_path_list:
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
		if pattern in info_dict:
			command_text = info_dict[pattern]
		else:
			command_text = ''
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
	command_text = info_dict[pattern]
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

def genCommandArgs(command):
	if const.python_version < 3:
		command = command.encode(const.sys_encoding)
		if const.sys_platform == 'windows':
			command = command.replace('/"', '"')
			command = command.replace('/', os.path.sep)
			std_args = '"' + command + '"'
		else:
			std_args = command
	else:
		std_args = shlex.split(command)
	return std_args

def getFlashSizeInfo(size_text, info_dict):
	flash_size = 0.00
	pattern_text = info_dict['recipe.size.regex']
	pattern = re.compile(pattern_text, re.S)
	lines = textutil.convertToLines(size_text)
	for line in lines:
		match = pattern.search(line)
		if match:
			flash_size = int(match.groups()[0])
	return flash_size

def getRamSizeInfo(size_text):
	size_line = size_text.split('\n')[-2].strip()
	info_list = re.findall(r'\S+', size_line)
	text_size = int(info_list[0])
	data_size = int(info_list[1])
	bss_size = int(info_list[2])
	flash_size = text_size + data_size
	ram_size = data_size + bss_size
	return ram_size

def getSizeInfoText(size_text, info_dict, language, mode):
	if mode == 'flash_size':
		size = getFlashSizeInfo(size_text, info_dict)
		size_key = 'upload.maximum_size'
		display_text = 'Binary sketch size: {1} bytes (of a {2} byte maximum, {3}%).\n'
	elif mode == 'ram_size':
		size = getRamSizeInfo(size_text)
		size_key = 'upload.maximum_ram_size'
		display_text = 'Estimated memory use: {1} bytes (of a {2} byte maximum, {3}%).\n'

	if size_key in info_dict:
		upload_maximum_size_text = info_dict[size_key]
	else:
		upload_maximum_size_text = ''
	
	size_text = str(size)
	size_text = formatNumber(size_text)

	if upload_maximum_size_text:
		upload_maximum_size = float(upload_maximum_size_text)
		size_percentage = (size / upload_maximum_size) * 100
		upload_maximum_size_text = formatNumber(upload_maximum_size_text)
	else:
		upload_maximum_size_text = '%(unknown)s'
		size_percentage = 0.00
	
	size_info_text = language.translate(display_text)
	size_info_text = size_info_text.replace('{1}', size_text)
	size_info_text = size_info_text.replace('{2}', upload_maximum_size_text)
	size_info_text = size_info_text.replace('{3}', '%.2f' % size_percentage)
	return size_info_text

def runCommand(command, command_type, info_dict, language, output_panel, verbose_output):
	args = genCommandArgs(command)
	compilation_process = subprocess.Popen(args, stdout = subprocess.PIPE, stderr = subprocess.PIPE, shell = True)
	result = compilation_process.communicate()
	return_code = compilation_process.returncode
	stdout = result[0]
	stderr = result[1]
				
	if verbose_output:
		output_panel.addText(command)
		output_panel.addText('\n')
		if stdout:
			output_panel.addText(stdout.decode(const.sys_encoding, 'replace'))

	if command_type == 'flash_size' or command_type == 'ram_size':
		size_text = stdout.decode(const.sys_encoding, 'replace')
		size_info_text = getSizeInfoText(size_text, info_dict, language, mode = command_type)
		output_panel.addText(size_info_text)

	if stderr:
		output_panel.addText(stderr.decode(const.sys_encoding, 'replace'))
	return return_code

def resetSerialPort(serial_port):
	ser = serial.Serial()
	ser.port = serial_port
	ser.baudrate = 1200
	ser.open()
	ser.close()

def diffSerialPort(list_before, list_now):
	for serial_port in list_before:
		if serial_port in list_now:
			list_now.remove(serial_port)
	return list_now

def getNewSerialPort(serial_port):
	# ser = serial.Serial()
	# ser.port = serial_port
	# ser.baudrate = 1200
	# ser.open()
	# ser.close()

	# if const.sys_platform != 'osx':
	# 	time.sleep(0.3)

	# serial_port_list.remove(serial_port)
	# new_serial_port_list = smonitor.genSerialPortList()

	# index = 0
	# while serial_port in new_serial_port_list:
	# 	time.sleep(0.5)
	# 	new_serial_port_list = smonitor.genSerialPortList()
	# 	index += 1
	# 	if index > 20:
	# 		break
	
	# for serial_port in serial_port_list:
	# 	if serial_port in new_serial_port_list:
	# 		new_serial_port_list.remove(serial_port)
	
	# index = 0
	# while not new_serial_port_list:
	# 	time.sleep(0.5)
	# 	new_serial_port_list = smonitor.genSerialPortList()
	# 	for serial_port in serial_port_list:
	# 		if serial_port in new_serial_port_list:
	# 			new_serial_port_list.remove(serial_port)

	# 	index += 1
	# 	if index > 40:
	# 		break
	
	# if new_serial_port_list:
	# 	new_serial_port = new_serial_port_list[0]
	# else:
	# 	new_serial_port = ''

	caterina_upload_port = ''

	serial_port_list_before = smonitor.genSerialPortList()
	if serial_port in serial_port_list_before:
		resetSerialPort(serial_port)
		if const.sys_platform != 'osx':
			time.sleep(0.3)

	elapsed = 0
	while elapsed < 10:
		serial_port_list_now = smonitor.genSerialPortList()
		serial_port_list_diff = diffSerialPort(serial_port_list_before, serial_port_list_now)
		print elapsed
		print 'before: ', serial_port_list_before
		print 'now: ', serial_port_list_now
		print 'diff: ', serial_port_list_diff
		if serial_port_list_diff:
			caterina_upload_port = serial_port_list_diff[0]
			print 'New serial port was found.'
			print caterina_upload_port
			break
		# serial_port_list_before = serial_port_list_now
		time.sleep(0.25)
		elapsed += 0.25

		if ((((const.sys_platform != 'windows') and (elapsed > 0.5)) or (elapsed > 5)) \
			and (serial_port in serial_port_list_now)):
			caterina_upload_port = serial_port
			print 'Timeout.'
			break
	return caterina_upload_port

class Compilation:
	def __init__(self, language, arduino_info, file_path, is_run_cmd = True):
		self.language = language
		self.arduino_info = arduino_info
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
		self.preCompilationProcess()
		if self.is_run_cmd:
			self.runCompile()
		self.is_finished = True

	def preCompilationProcess(self):
		display_text = 'Gathering compilation infomation...\n'
		self.output_panel.addText(display_text)

		self.build_path = getBuildPath(self.sketch_name)
		self.base_info_dict['build.path'] = self.build_path

		(self.info_key_list, self.info_dict) = initInfoDict(self.base_info_dict, \
			self.arduino_info, self.platform_file_path)

		if self.is_run_cmd:
			self.ino_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.arduino_ext_list)
			self.cpp_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.cpp_ext_list)
			self.s_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.s_ext_list)
			self.h_src_path_list = sketch.listSrcFile(self.sketch_folder_path, const.src_header_ext_list)

			copyHFilesToBuildFolder(self.build_path, self.h_src_path_list)
			self.main_src_path = genMainSrcFile(self.ino_src_path_list, self.build_path, \
				self.sketch_name, self.arduino_version)

			all_src_path_list = self.ino_src_path_list + self.cpp_src_path_list + self.h_src_path_list
			src_header_list = src.genSrcHeaderListFromSrcFileList(all_src_path_list)

			include_library_path_list = getIncludeLibraryPathList(self.library_path_list, src_header_list)

			build_core = self.info_dict['build.core']
			board_file_path = self.arduino_info.getBoardFile(self.platform, self.board)
			board_folder_path = os.path.split(board_file_path)[0]
			board_cores_path = os.path.join(board_folder_path, 'cores')
			src_build_core_path = os.path.join(board_cores_path, build_core)
			if not os.path.isdir(src_build_core_path):
				src_build_core_path = os.path.join(self.src_cores_path, build_core)

			build_core_path_list = [src_build_core_path] + include_library_path_list
			self.core_src_path_list = findSrcFileFromPathList(build_core_path_list, const.cpp_ext_list)

			self.include_folder_list = [self.build_path]
			self.include_folder_list += listSubDirsFromPathList(build_core_path_list)
			if 'build.variant' in self.info_dict:
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
			self.cleanObjFiles()
			self.runCompilationCommands()

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
		(sketch_obj_path_list, sketch_command_list) = genSrcCompilationCommandInfo(self.info_dict, \
			self.build_path, [self.main_src_path])
		(cpp_obj_path_list, cpp_command_list) = genSrcCompilationCommandInfo(self.info_dict, \
			self.build_path, self.cpp_src_path_list)
		(s_obj_path_list, s_command_list) = genSrcCompilationCommandInfo(self.info_dict, \
			self.build_path, self.s_src_path_list)
		(core_obj_path_list, core_command_list) = genSrcCompilationCommandInfo(self.info_dict, \
			self.build_path, self.core_src_path_list)

		ar_file_path = self.build_path + '/' + self.archive_file
		elf_file_path = self.build_path + '/' + self.sketch_name + '.elf'
		eep_file_path = self.build_path + '/' + self.sketch_name + '.eep'
		hex_file_path = self.build_path + '/' + self.sketch_name
		src_obj_path_list = sketch_obj_path_list + cpp_obj_path_list + s_obj_path_list

		(ar_file_path_list, ar_command_list) = genArCommandInfo(self.info_dict, ar_file_path, \
			core_obj_path_list)
		(elf_file_path_list, elf_command_list) = genElfCommandInfo(self.info_dict, elf_file_path, \
			src_obj_path_list)
		(eep_file_path_list, eep_command_list) = genEepCommandInfo(self.info_dict, eep_file_path)
		(hex_file_path_list, hex_command_list) = genHexCommandInfo(self.info_dict, hex_file_path)
		size_command_list = genSizeCommandList(self.info_dict)

		hex_file_path = hex_file_path_list[0]
		
		if not os.path.isfile(ar_file_path):
			self.full_compilation = True

		self.created_file_list = []
		self.compilation_command_list = []
		self.created_file_list += sketch_obj_path_list
		self.compilation_command_list += sketch_command_list
		self.created_file_list += cpp_obj_path_list
		self.compilation_command_list += cpp_command_list
		self.created_file_list += s_obj_path_list
		self.compilation_command_list += s_command_list
		if self.full_compilation:
			self.created_file_list += core_obj_path_list
			self.compilation_command_list += core_command_list
			self.created_file_list += ar_file_path_list
			self.compilation_command_list += ar_command_list
		self.created_file_list += elf_file_path_list
		self.compilation_command_list += elf_command_list
		if self.info_dict['recipe.objcopy.eep.pattern']:
			self.created_file_list += eep_file_path_list
			self.compilation_command_list += eep_command_list
		self.created_file_list += hex_file_path_list
		self.compilation_command_list += hex_command_list
		self.created_file_list += ['flash_size', 'ram_size']
		self.compilation_command_list += size_command_list

	def cleanObjFiles(self):
		display_text = 'Cleaning...\n'
		self.output_panel.addText(display_text)
		for file_path in self.created_file_list:
			if os.path.isfile(file_path):
				os.remove(file_path)

	def runCompilationCommands(self):
		compilation_info = zip(self.created_file_list, self.compilation_command_list)
		for (created_file, compilation_command) in compilation_info:
			command_type = ''
			if created_file:
				if created_file == 'flash_size':
					command_type = 'flash_size'
				elif created_file == 'ram_size':
					command_type = 'ram_size'
				else:
					display_text = 'Creating {0}...\n'
					self.output_panel.addText(display_text, [created_file])
			return_code = runCommand(compilation_command, command_type, self.info_dict, \
				self.language, self.output_panel, self.verbose_compilation)
			if return_code != 0:
				self.error_code = 2
				break
		
		if self.error_code > 0:
			display_text = '[Stino - Error while compiling.]\n'
			self.output_panel.addText(display_text)
		else:
			self.endtime = datetime.datetime.now()
			interval = (self.endtime - self.starttime).microseconds * 1e-6
			display_text = '[Stino - Done compiling.]\n'
			self.output_panel.addText(display_text)

	def getHexFilePath(self):
		return self.hex_file_path

	def isTerminatedWithError(self):
		if self.error_code == 0:
			state = False
		else:
			state = True
		return state

	def getOutputPanel(self):
		return self.output_panel

	def getInfoDict(self):
		return self.info_dict

class Upload:
	def __init__(self, language, arduino_info, file_path, mode = 'upload', \
		serial_port_in_use_list = None, serial_port_monitor_dict = None):
		self.language = language
		self.board = const.settings.get('Board')
		self.cur_compilation = Compilation(language, arduino_info, file_path)
		self.output_panel = self.cur_compilation.getOutputPanel()
		self.error_code = 0
		self.is_finished = False
		self.mode = mode
		self.board = const.settings.get('board')
		self.verbose_upload = const.settings.get('verbose_upload')
		
		self.serial_port_in_use_list = serial_port_in_use_list
		self.serial_port_monitor_dict = serial_port_monitor_dict
		self.serial_port = const.settings.get('serial_port')
		
		self.serial_monitor_is_running = False
		if self.serial_port_in_use_list:
			if self.serial_port in self.serial_port_in_use_list:
				self.serial_monitor = self.serial_port_monitor_dict[self.serial_port]
				self.serial_monitor_is_running = True

	def start(self):
		self.cur_compilation.start()
		upload_thread = threading.Thread(target=self.upload)
		upload_thread.start()

	def upload(self):
		while not self.cur_compilation.is_finished:
			time.sleep(0.5)
		if self.cur_compilation.isTerminatedWithError():
			self.error_code = 1
		else:
			self.info_dict = self.cur_compilation.getInfoDict()
			self.hex_file_path = self.cur_compilation.getHexFilePath()
			display_text = 'Uploading {0} to {1}...\n'
			self.output_panel.addText(display_text, [self.hex_file_path, self.board])
			if self.mode == 'upload':
				upload_command = self.info_dict['upload.pattern']
				if self.serial_monitor_is_running:
					self.serial_monitor.stop()
					time.sleep(0.1)
				bootloader_path = self.info_dict['bootloader.path']
				if 'caterina' in bootloader_path:
					display_text = 'Forcing reset using 1200bps open/close on port.\n'
					self.output_panel.addText(display_text)
					new_serial_port = getNewSerialPort(self.serial_port)
					if new_serial_port:
						upload_command = upload_command.replace(self.serial_port, new_serial_port)
						self.serial_port = new_serial_port
					else:
						upload_command = ''
						display_text = 'Couldn\'t find a Leonardo on the selected port. Check that you have the\ncorrect port selected.  If it is correct, try pressing the board\'s reset\nbutton after initiating the upload.\n'
						self.output_panel.addText(display_text)
			elif self.mode == 'upload_using_programmer':
				if 'program.pattern' in self.info_dict:
					upload_command = self.info_dict['program.pattern']
			else:
				upload_command = ''
			if upload_command:
				termination_with_error = False
				command_list = [upload_command]
				if 'reboot.pattern' in self.info_dict:
					reboot_command = self.info_dict['reboot.pattern']
					command_list.append(reboot_command)
				for command in command_list:
					command_type = ''
					return_code = runCommand(command, command_type, self.info_dict, \
						self.language, self.output_panel, self.verbose_upload)
					if return_code != 0:
						termination_with_error = True
						break
				if termination_with_error:
					self.error_code = 2
					display_text = '[Stino - Error while uploading.]\n'
					self.output_panel.addText(display_text)
				else:
					display_text = '[Stino - Done uploading.]\n'
					self.output_panel.addText(display_text)
				if self.mode == 'upload':
					if self.serial_monitor_is_running:
						self.serial_monitor.setSerialPort(self.serial_port)
						sublime.set_timeout(self.serial_monitor.start, 0)
			else:
				self.error_code = 3
		self.is_finished = True

class BurnBootloader:
	def __init__(self, language, arduino_info, file_path):
		self.language = language
		self.board = const.settings.get('board')
		self.cur_compilation = Compilation(language, arduino_info, file_path, is_run_cmd = False)
		self.output_panel = self.cur_compilation.getOutputPanel()
		self.error_code = 0
		self.is_finished = False
		self.verbose_upload = const.settings.get('verbose_upload')

	def start(self):
		self.cur_compilation.start()
		upload_thread = threading.Thread(target=self.burn)
		upload_thread.start()

	def burn(self):
		while not self.cur_compilation.is_finished:
			time.sleep(0.5)
		if self.cur_compilation.isTerminatedWithError():
			self.error_code = 1
		else:
			self.info_dict = self.cur_compilation.getInfoDict()
			if 'bootloader.file' in self.info_dict:
				display_text = 'Burning bootloader {0} to {1} (this may take a minute)...\n'
				self.output_panel.addText(display_text, [os.path.split(self.info_dict['bootloader.file'])[1], self.board])
				termination_with_error = False
				erase_command = self.info_dict['erase.pattern']
				burn_command = self.info_dict['bootloader.pattern']
				command_list = [erase_command, burn_command]
				for command in command_list:
					command_type = ''
					return_code = runCommand(command, command_type, self.info_dict, \
						self.language, self.output_panel, self.verbose_upload)
					if return_code != 0:
						termination_with_error = True
						break
				if termination_with_error:
					self.error_code = 2
					display_text = '[Stino - Error while burning bootloader.]\n'
					msg = self.language.translate(display_text)
					self.output_panel.addText(msg)
				else:
					display_text = '[Stino - Done burning bootloader.]\n'
					msg = self.language.translate(display_text)
					self.output_panel.addText(msg)
			else:
				self.error_code = 3
		self.is_finished = True