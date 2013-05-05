#-*- coding: utf-8 -*-
# stino/src.py

import sublime
import os
import re

from . import const
from . import textutil
from . import fileutil

def genSrcHeaderListFromSrc(src_text):
	src_header_list = []
	pattern_text = r'^\s*?#include\s+?["<](\S+?)[>"]'
	pattern = re.compile(pattern_text, re.M|re.S)
	src_header_list = pattern.findall(src_text)
	return src_header_list

def genSrcHeaderListFromView(view):
	view_text = textutil.getTextOfView(view)
	src_header_list = genSrcHeaderListFromSrc(view_text)
	return src_header_list

def genSrcHeaderListFromSrcFileList(src_file_list):
	src_header_list = []
	for src_file in src_file_list:
		src_text = fileutil.readFileText(src_file)
		cur_src_header_list = genSrcHeaderListFromSrc(src_text)
		for src_header in cur_src_header_list:
			if not src_header in src_header_list:
				src_header_list.append(src_header)
	return src_header_list

def getSrcHeaderListFromFolder(folder_path):
	src_header_list = []
	file_list = fileutil.listDir(folder_path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in const.src_header_ext_list:
			src_header_list.append(cur_file)
	return src_header_list

def genInsertionSrcHeaderList(folder_path, view):
	src_header_list = []
	src_header_list_from_view = genSrcHeaderListFromView(view)
	src_header_list_from_folder = getSrcHeaderListFromFolder(folder_path)
	for src_header in src_header_list_from_folder:
		if not src_header in src_header_list_from_view:
			src_header_list.append(src_header)
	return src_header_list

def genInsertionIncludeText(folder_path, view):
	insertion_include_text = ''
	src_header_list = genInsertionSrcHeaderList(folder_path, view)
	if src_header_list:
		include_text_list = [('#include <' + src_header + '>\n') for src_header in src_header_list]
		insertion_include_text += '\n'
		for include_text in include_text_list:
			insertion_include_text += include_text
		insertion_include_text += '\n'
	return insertion_include_text

def getInsertionIncludePosition(view):
	insertion_position = 0
	view_text = textutil.getTextOfView(view)
	pattern_text = r'^\s*?#include\s+?["<]\S+?[>"]'
	pattern = re.compile(pattern_text, re.M|re.S)
	match = pattern.search(view_text)
	if match:
		first_include_text = match.group()
		index = view_text.index(first_include_text)
		insertion_position = index
	return insertion_position

def insertIncludeText(folder_path, view):
	insertion_include_text = genInsertionIncludeText(folder_path, view)
	position = getInsertionIncludePosition(view)
	textutil.insertTextToView(view, insertion_include_text, position)

def hasSetup(src_text):
	state = False
	pattern_text = r'void\s+?(?:setup|loop)\s*?\(.*?\)(?=\s*?\{)'
	pattern = re.compile(pattern_text, re.M|re.S)
	func_list = pattern.findall(src_text)
	if len(func_list) >= 2:
		state = True 
	return state

def isSetupFile(src_path):
	state = False
	src_text = fileutil.readFileText(src_path)
	if hasSetup(src_text):
		state = True
	return state

def findSetupFile(ino_src_path_list):
	setup_src_file_path = ''
	for src_path in ino_src_path_list:
		if isSetupFile(src_path):
			setup_src_file_path = src_path
			break
	return setup_src_file_path

def removeComment(src_text):
	pattern_list = [r'//.*?$'] # single-line comment
	pattern_list += [r'/\*.*?\*/'] # multi-line comment
	for pattern_text in pattern_list:
		pattern = re.compile(pattern_text, re.M|re.S)
		simple_src_text = pattern.sub('', src_text)
	return simple_src_text

def regulariseBlank(text):
	pattern_text = r'\S+'
	word_list = re.findall(pattern_text, text)
	
	text = ''
	for word in word_list:
		text += word
		text += ' '
	text = text[:-1]
	return text

def regulariseFuctionText(function_text):
	function_text = function_text[:-1]
	text_list = function_text.split('(')
	function_name = text_list[0].strip()
	function_name = regulariseBlank(function_name)
	parameters = text_list[1].strip()
	parameters = regulariseBlank(parameters)
	function_text = function_name + ' (' + parameters + ')'
	return function_text

def genSrcDeclarationList(simple_src_text):
	src_declaration_list = []
	pattern_text = r'^\s*?[\w\[\]\*]+\s+[&\[\]\*\w\s]+\([&,\[\]\*\w\s]*\)(?=\s*?;)'
	pattern = re.compile(pattern_text, re.M|re.S)
	declaration_list = pattern.findall(simple_src_text)
	for declaration_text in declaration_list:
		declaration = regulariseFuctionText(declaration_text)
		if not ('if ' in declaration or 'else ' in declaration):
			src_declaration_list.append(declaration)
	return src_declaration_list

def genSrcFunctionList(simple_src_text):
	src_function_list = []
	pattern_text = r'^\s*?[\w\[\]\*]+\s+[&\[\]\*\w\s]+\([&,\[\]\*\w\s]*\)(?=\s*?\{)'
	pattern = re.compile(pattern_text, re.M|re.S)
	function_text_list = pattern.findall(simple_src_text)
	for function_text in function_text_list:
		function = regulariseFuctionText(function_text)
		if not ('if ' in function or 'else ' in function):
			src_function_list.append(function)
	return src_function_list

def removeExistDeclaration(src_function_list, src_declaration_list):
	declaration_list = []
	for function in src_function_list:
		if not function in src_declaration_list:
			if not function in declaration_list:
				declaration_list.append(function)
	return declaration_list

def genDeclarationList(ino_src_path_list):
	declaration_list = []
	for src_path in ino_src_path_list:
		src_text = fileutil.readFileText(src_path)
		simple_src_text = removeComment(src_text)
		src_function_list = genSrcFunctionList(simple_src_text)
		src_declaration_list = genSrcDeclarationList(simple_src_text)
		cur_declaration_list = removeExistDeclaration(src_function_list, src_declaration_list)
		declaration_list += cur_declaration_list
		print(src_path)
		print('function')
		print(src_function_list)
		print('declaration')
		print(src_declaration_list)
		print('simple')
		print(cur_declaration_list)
	return declaration_list

def findFirstFunction(src_text):
	pattern_text = r'^\s*?class\s+?\w+?(?=\s*?\{)|^\s*?[\w\[\]\*]+?\s+?[&\[\]\*\w\s]+?\([&,\[\]\*\w\s]*\)(?=\s*?\{)'
	pattern = re.compile(pattern_text, re.M|re.S)
	match = pattern.search(src_text)
	if match:
		first_function = match.group().strip()
		index = src_text.index(first_function)
	else:
		first_function = ''
		index = len(src_text) - 1
	return (first_function, index)

def splitByFirstFunction(src_text):
	(first_function, index) = findFirstFunction(src_text)
	print(first_function)
	print(index)
	header_text = src_text[:index]
	body_text = src_text[index:]
	return (header_text, body_text)

def insertDeclarationToSrcFile(src_file_path, declaration_list, arduino_version):
	org_src_text = fileutil.readFileText(src_file_path)

	if arduino_version < 100:
		include_text = '#include <WProgram.h>\n'
	else:
		include_text = '#include <Arduino.h>\n'

	declaration_text = ''
	for declaration in declaration_list:
		declaration_text += '%s;\n' % declaration
	declaration_text += '\n'

	(header_text, body_text) = splitByFirstFunction(org_src_text)

	src_text = '// %s\n' % src_file_path
	src_text += include_text
	src_text += header_text
	src_text += declaration_text
	src_text += body_text
	return src_text