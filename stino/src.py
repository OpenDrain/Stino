#-*- coding: utf-8 -*-
# stino/src.py

import sublime
import os

from stino import osfile
from stino import const

header_ext_list = ['.h', '.hpp']
arduino_ext_list = ['.ino', '.pde']
src_ext_list = ['.ino', '.pde', '.c', '.cc', '.cpp', '.cxx']

def isSketch(sketch):
	state = False
	sketch_ext = ''
	sketch_text = ''
	if isinstance(sketch, file):
		sketch_ext = os.path.splitext(sketch)[1]
	elif isinstance(sketch, type(sublime.active_window().active_view())):
		sketch_name = sketch.file_name()
		if sketch_name:
			sketch_ext = os.path.splitext(sketch_name)[1]
	
	if sketch_ext in arduino_ext_list:
		state = True
	else:
		if isinstance(sketch, file):
			if sketch_ext in src_ext_list:
				sketch_text = osfile.readFileText(sketch)
		elif isinstance(sketch, type(sublime.active_window().active_view())):
			region = sublime.Region(0, sketch.size())
			sketch_text = sketch.substr(region)
	
	if sketch_text:
		state = isMainSketch(sketch_text)
	return state

def isMainSketch(sketch):
	state = False
	sketch_text = ''
	if isinstance(sketch, file):
		sketch_text = osfile.readFileText(sketch)
	elif isinstance(sketch, basestring):
		sketch_text = sketch

	if sketch_text:
		pass
	return state

def createNewSketch(filename):
	sketchbook_root = const.settings.get('sketchbook_root')
	folder_path = os.path.join(sketchbook_root, filename)
	file_path = os.path.join(folder_path, filename)
	file_path += '.ino'

	template_file_path = os.path.join(const.template_root, 'sketch')
	os.mkdir(folder_path)
	text = osfile.readFileText(template_file_path)
	osfile.writeFile(file_path, text)
	openSketch(filename)

def openSketch(sketch):
	sketchbook_root = const.settings.get('sketchbook_root')
	folder_path = os.path.join(sketchbook_root, sketch)
	full_file_list = osfile.listDir(folder_path, with_dirs = False)

	file_list = []
	for cur_file in full_file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in src_ext_list:
			file_list.append(cur_file)

	file_path_list = [os.path.join(folder_path, cur_file) for cur_file in file_list]

	sublime.run_command('new_window')
	window = sublime.windows()[-1]

	for cur_file_path in file_path_list:
		window.open_file(cur_file_path)

def createNewFile(window, file_path):
	filename = os.path.split(file_path)[1]
	text = '// %s\n\n' % filename
	osfile.writeFile(file_path, text)
	window.open_file(file_path)