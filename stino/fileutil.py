#-*- coding: utf-8 -*-
# stino/fileutil.py

import os
import sublime

from . import const
from . import textutil

if const.sys_platform == 'windows':
	if const.python_version < 3:
		import _winreg as winreg
	else:
		import winreg

# List Dir
def isDirAccess(dir_path):
	state = False
	try:
		os.listdir(dir_path)
	except OSError:
		state = False
	else:
		state = True
	return state

def isFileAccess(file_path):
	state = False
	try:
		opened_file = open(file_path)
	except IOError:
		state = False
	else:
		opened_file.close()
		state = True	
	return state

def listDir(path, with_dirs = True, with_files = True):
	file_list = []
	path = textutil.convertTextToUtf8(path)
	if os.path.isdir(path):
		org_file_list = os.listdir(path)
		for cur_file in org_file_list:
			if cur_file[0] == '$' or cur_file[0] == '.':
				continue
			cur_file_path = os.path.join(path, cur_file)
			if os.path.isdir(cur_file_path):
				if with_dirs:
					if isDirAccess(cur_file_path):
						file_list.append(cur_file)
			else:
				if with_files:
					if isFileAccess(cur_file_path):
						file_list.append(cur_file)
	return file_list

# File Utilities
def isPlainTextFile(file_path):
	state = False
	opened_file = open(file_path, 'rb')
	text = opened_file.read(512)
	opened_file.close()
	
	length = len(text)
	if length > 0:
		white_list_char_count = 0
		black_list_char_count = 0
		for character in text:
			if type(character) == type(0):
				char_value = character
			else:
				char_value = ord(character)
			if (char_value == 9) or (char_value == 10) or (char_value == 13) or \
				((char_value >= 32) and (char_value <= 255)):
				white_list_char_count += 1
			elif (char_value <= 6) or ((char_value >= 14) and (char_value <= 31)):
				black_list_char_count += 1
		if black_list_char_count == 0:
			if white_list_char_count > 0:
				state = True
	else:
		state = True
	return state

def readFileLines(file_path):
	file_lines = []

	if isFileAccess(file_path):
		if isPlainTextFile(file_path):
			opened_file = open(file_path, 'rb')
			file_text = opened_file.read()
			opened_file.close()
			if const.python_version < 3:
				file_text = file_text.replace('\r\n', '\n')
				file_text = file_text.replace('\r', '\n')
				lines = file_text.split('\n')
			else:
				file_text = file_text.replace(b'\r\n', b'\n')
				file_text = file_text.replace(b'\r', b'\n')
				lines = file_text.split(b'\n')

			for line in lines:
				line = textutil.convertTextToUtf8(line)
				file_lines.append(line)
	return file_lines

def readFileText(file_path):
	file_text = ''
	lines = readFileLines(file_path)
	for line in lines:
		file_text += line
		file_text += '\n'
	return file_text

def writeFile(file_path, text, encoding = 'utf-8'):
	text = text.encode(encoding)
	f = open(file_path, 'wb')
	f.write(text)
	f.close()

# Directory Utilities
def getWinVolumeList():
	vol_list = []
	for label in range(67, 90):
		vol = chr(label) + ':\\'
		if os.path.isdir(vol):
			vol_list.append(vol)
	return vol_list

def getAppRootList():
	if const.sys_platform == 'windows':
		root_list = getWinVolumeList()
	elif const.sys_platform == 'linux':
		home_root = os.getenv('HOME')
		root_list = [home_root, '/usr', '/opt']
	elif const.sys_platform == 'osx':
		home_root = os.getenv('HOME')
		root_list = ['/Applications', home_root]
	app_root_list = textutil.convertListToUtf8(root_list)
	return app_root_list

def getHomeRootList():
	if const.sys_platform == 'windows':
		root_list = getWinVolumeList()
	else:
		home_root = os.getenv('HOME')
		root_list = [home_root]
	home_root_list = textutil.convertListToUtf8(root_list)
	return home_root_list

def getDocumentRoot():
	document_root = ''
	if const.sys_platform == 'windows':
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,\
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',)
		document_root = winreg.QueryValueEx(key, 'Personal')[0]
	else:
		home_root = os.getenv('HOME')
		if const.sys_platform == 'osx':
			document_root = os.path.join(home_root, 'Documents')
		else:
			document_root = home_root
	document_root = textutil.convertTextToUtf8(document_root)
	return document_root

def checkDir(dir_path):
	if os.path.isfile(dir_path):
		os.remove(dir_path)
	if not os.path.isdir(dir_path):
		os.makedirs(dir_path)

def checkSketchbookRoot(sketchbook_root):
	sub_dir_list = const.sketchbook_function_dir_list
	for sub_dir in sub_dir_list:
		sub_dir_path = os.path.join(sketchbook_root, sub_dir)
		checkDir(sub_dir_path)

def getDefaultSketchbookRoot():
	if const.sys_platform == 'linux':
		dir_name = 'sketchbook'
	else:
		dir_name = 'Arduino'
	document_root = getDocumentRoot()
	sketchbook_root = os.path.join(document_root, dir_name)
	return sketchbook_root

def setSketchbookRoot(sketchbook_root):
	const.settings.set('sketchbook_root', sketchbook_root)

def getSketchbookRoot():
	sketchbook_root = const.settings.get('sketchbook_root')
	if not (sketchbook_root and os.path.isdir(sketchbook_root)):
		sketchbook_root = getDefaultSketchbookRoot()
		setSketchbookRoot(sketchbook_root)
	checkSketchbookRoot(sketchbook_root)
	return sketchbook_root

def getRealArduinoRoot(path):
	if const.sys_platform == 'osx':
		path = os.path.join(path, 'Contents/Resources/JAVA')
	return path

def isArduinoRoot(path):
	state = False
	if path and os.path.isdir(path):
		path = getRealArduinoRoot(path)
		hardware_path = os.path.join(path, 'hardware')
		lib_path = os.path.join(path, 'lib')
		version_file_path = os.path.join(lib_path, 'version.txt')
		if os.path.isdir(hardware_path) and os.path.isfile(version_file_path):
			state = True
	return state

def getDefaultArduinoRoot():
	arduino_root = ''
	if const.sys_platform == 'osx':
		arduino_root = '/Applications/Arduino'
	elif const.sys_platform == 'linux':
		arduino_root = '/usr/share/arduino'
	if not isArduinoRoot(arduino_root):
		arduino_root = None
	return arduino_root

def getArduinoRoot():
	arduino_root = const.settings.get('arduino_root')
	if not isArduinoRoot(arduino_root):
		arduino_root = getDefaultArduinoRoot()
	if arduino_root:
		arduino_root = getRealArduinoRoot(arduino_root)
	return arduino_root

def regulariseFilename(filename):
	if filename:
		if filename[0] in '0123456789':
			filename = '_' + filename
		filename = filename.replace(' ', '_')
	return filename

def genFileListFromPathList(path_list, language):
	file_list = []
	for cur_path in path_list:
		if ('Stino_Button' + textutil.info_sep) in cur_path:
			parent_path = textutil.getInfoFromKey(cur_path)[1]
			display_text = 'Select Current Folder ({0})'
			caption = language.translate(display_text)
			caption = caption.replace('{0}', parent_path)
			file_list.append(caption)
		else:
			cur_file = os.path.split(cur_path)[1]
			if cur_file:
				file_list.append(cur_file)
			else:
				file_list.append(cur_path)
	return file_list

def genSubPathList(path, with_files = True, with_parent = True, with_button = False):
	path = os.path.normpath(path)
	file_list = listDir(path, with_files = with_files)
	if with_parent:
		file_list.insert(0, '..')
	path_list = [os.path.join(path, cur_file) for cur_file in file_list]
	if with_button:
		text = textutil.genKey(path, 'Stino_Button')
		path_list.insert(0, text)
	return path_list

def enterSubDir(top_path_list, level, index, sel_path, with_files = True, with_parent = True, with_button = False):
	cur_dir = os.path.split(sel_path)[1]
	if level > 0:
		if cur_dir == '..':
			level -= 1
		else:
			level += 1
	else:
		level += 1

	if level == 0:
		path_list = top_path_list
	else:
		path_list = genSubPathList(sel_path, with_files, with_parent, with_button)

	return (level, path_list)

def isButtonPress(text):
	state = False
	if not os.path.exists(text):
		if 'Stino_Button' in text:
			state = True
	return state

def openUrl(url):
	arduino_root = getArduinoRoot()
	if arduino_root:
		reference_path = os.path.join(arduino_root, 'reference')
		reference_path = reference_path.replace(os.path.sep, '/')
		url = 'file://%s/%s.html' % (reference_path, url)
	else:
		org_url = url.replace('index', 'HomePage')
		url = 'http://arduino.cc/en'
		if '_' in org_url or 'FAQ' in org_url:
			addr_list = org_url.split('_')
			for addr in addr_list:
				url += '/%s' % addr
		else:
			url += '/Reference/%s' % org_url
	sublime.run_command('open_url', {'url': url})

def openUrlList(url_list):
	for url in url_list:
		openUrl(url)

def copyFile(src_file_path, des_dir_path):
	src_filename = os.path.split(src_file_path)[1]
	des_file_path = os.path.join(des_dir_path, src_filename)
	text = readFileText(src_file_path)
	writeFile(des_file_path, text)

def getInfoBlock(file_path, info_value):
	info_block = []
	lines = readFileLines(file_path)
	info_block_list = textutil.splitToBlocks(lines, sep = '.name', none_sep = 'menu.')
	for cur_info_block in info_block_list:
		line = cur_info_block[0]
		(key, value) = textutil.getKeyValue(line)
		for line in cur_info_block[1:]:
			if '.container' in line:
				(key, value) = textutil.getKeyValue(line)
				break
		
		if value == info_value:
			info_block = cur_info_block
			break
	return info_block
