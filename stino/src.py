#-*- coding: utf-8 -*-
# stino/src.py

import sublime
import os

from stino import osfile

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