#-*- coding: utf-8 -*-
# stino/sketch.py

import sublime
import os

from . import const
from . import textutil
from . import fileutil
from . import parsearduino

def isSketchFolder(path):
	state = False
	src_ext_list = const.arduino_ext_list
	file_list = fileutil.listDir(path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in src_ext_list:
			state = True
			break
	return state

def genSketchInfo():
	sketch_list = []
	sketch_path_dict = {}

	sketchbook_root = fileutil.getSketchbookRoot()
	sketchbook_root = textutil.convertTextToUtf8(sketchbook_root)
	for (cur_path, sub_dirs, files) in os.walk(sketchbook_root):
		if cur_path == sketchbook_root:
			continue
		relative_path = cur_path.replace(sketchbook_root, '')
		if relative_path[0] == os.path.sep:
			relative_path = relative_path[1:]
		top_dir_name = relative_path.split(os.path.sep)[0]
		if top_dir_name in const.sketchbook_function_dir_list:
			continue
		if isSketchFolder(cur_path):
			sketch_name = relative_path.replace(os.path.sep, '/')
			sketch_list.append(sketch_name)
			sketch_path_dict[sketch_name] = cur_path
	sketch_info = (sketch_list, sketch_path_dict)
	return sketch_info

def genSketchList():
	sketch_info = genSketchInfo()
	sketch_list = sketch_info[0]
	return sketch_list

def createNewSketch(folder_path):
	filename = os.path.split(folder_path)[1]
	filename += '.ino'
	file_path = os.path.join(folder_path, filename)

	os.makedirs(folder_path)
	template_file_path = os.path.join(const.template_root, 'sketch')
	text = '// %s\n\n' % filename
	text += fileutil.readFileText(template_file_path)
	fileutil.writeFile(file_path, text)
	openSketch(folder_path)

def listSrcFile(folder_path, ext_list):
	path_list = []
	file_list = fileutil.listDir(folder_path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext.lower() in ext_list:
			cur_file_path = os.path.join(folder_path, cur_file)
			cur_file_path = cur_file_path.replace(os.path.sep, '/')
			path_list.append(cur_file_path)
	return path_list

def openSketch(folder_path):
	file_path_list = listSrcFile(folder_path, const.all_src_ext_list)
	sublime.run_command('new_window')
	window = sublime.windows()[-1]

	for cur_file_path in file_path_list:
		window.open_file(cur_file_path)

def createNewFile(window, file_path):
	filename = os.path.split(file_path)[1]
	text = '// %s\n\n' % filename
	fileutil.writeFile(file_path, text)
	window.open_file(file_path)

def isFile(path):
	return os.path.isfile(path)

def openFile(file_path):
	if fileutil.isPlainTextFile(file_path):
		window = sublime.active_window()
		window.open_file(file_path)
	else:
		os.popen(file_path)

def isArduinoSrcFile(file_path):
	state = False
	file_ext = os.path.splitext(file_path)[1]
	if file_ext.lower() in const.all_src_ext_list:
		state = True
	return state

def findSrcFile(folder_path, ext_list):
	file_path_list = []
	folder_path = textutil.convertTextToUtf8(folder_path)
	for (cur_path, sub_dirs, files) in os.walk(folder_path):
		if 'examples' in cur_path.lower():
			continue
		for cur_file in files:
			cur_ext = os.path.splitext(cur_file)[1]
			if cur_ext in ext_list:
				cur_file_path = os.path.join(cur_path, cur_file)
				cur_file_path = cur_file_path.replace(os.path.sep, '/')
				file_path_list.append(cur_file_path)
	return file_path_list

def listSubDirs(folder_path):
	sub_dir_list = []
	folder_path = textutil.convertTextToUtf8(folder_path)
	for (cur_path, sub_dirs, files) in os.walk(folder_path):
		if 'examples' in cur_path.lower():
			continue
		cur_path = cur_path.replace(os.path.sep, '/')
		sub_dir_list.append(cur_path)
	return sub_dir_list
