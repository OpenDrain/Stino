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