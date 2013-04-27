#-*- coding: utf-8 -*-
# stino/textutil.py

# from chardet import universaldetector

import sys
import re

import sublime

from . import const

info_sep = '$@@$'

def genKey(base_info, info):
	key = info + info_sep + base_info
	return key

def getInfoFromKey(key):
	info_list = key.split(info_sep)
	return info_list

def getTextOfView(view):
	view_text = view.substr(sublime.Region(0, view.size()))
	return view_text

def insertTextToView(view, text, position = -1):
	if position == -1:
		position = view.size()
	if const.st_version < 3000:
		edit = view.begin_edit()
		view.insert(edit, position, text)
		view.end_edit(edit)
	else:
		view.run_command('stino_insert_text', {'text': text, 'position': position})

def replaceTextOfView(view, text):
	if const.st_version < 3000:
		edit = view.begin_edit()
		view.replace(edit, sublime.Region(0, view.size()), '')
		view.end_edit(edit)
	else:
		view.run_command('stino_replace_text', {'text': text})

# 这个函数需要更多的判断来解码字符
def convertTextToUtf8(text):
	is_utf8 = False
	if const.python_version < 3:
		if type(text) == type(u'string'):
			is_utf8 = True
	else:
		if type(text) == type('string'):
			is_utf8 = True

	if not is_utf8:
		try:
			text = text.decode('utf-8')
		except UnicodeDecodeError:
			try:
				text = text.decode(const.sys_encoding)
			except UnicodeDecodeError:
				# from chardet import universaldetector
				print('Unable decode the text.')
				text = text.decode('utf-8', replace)
	return text

def convertListToUtf8(text_list):
	new_text_list = []
	for text in text_list:
		text = convertTextToUtf8(text)
		new_text_list.append(text)
	return new_text_list

def convertToLines(text):
	lines = text.split('\n')
	return lines

def getKeyValue(line):
	line = line.strip()
	if '=' in line:
		index = line.index('=')
		key = line[:index].strip()
		value = line[(index+1):].strip()
	else:
		key = ''
		value = ''
	return (key, value)

def splitToBlocks(lines, sep = '.name', none_sep = None, key_length = 0):
	block_list = []
	block = []
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			sep_condtion = sep in line
			none_sep_condition = True
			if none_sep:
				none_sep_condition = not none_sep in line
			length_condition = False
			if key_length > 0:
				if '=' in line:
					(key, value) = getKeyValue(line)
					key_list = key.split('.')
					length = len(key_list)
					if length == key_length:
						length_condition = True

			is_new_block = (sep_condtion and none_sep_condition) or length_condition
			if is_new_block:
				block_list.append(block)
				block = [line]
			else:
				block.append(line)
	block_list.append(block)
	block_list.pop(0)
	return block_list

def isLists(lists):
	state = False
	if lists:
		if type(lists[0]) == type([]):
			state = True
	return state

def simplifyLists(in_lists):
	out_list = []
	if isLists(in_lists):
		for in_list in in_lists:
			out_list += in_list
	else:
		out_list = in_lists
	return out_list

def getSelectedTextFromView(view):
	selected_text = ''
	region_list = view.sel()
	for region in region_list:
		selected_region = view.word(region)
		selected_text += view.substr(selected_region)
		selected_text += '\n'
	return selected_text

def getWordListFromText(text):
	pattern_text = r'\b\w+\b'
	pattern = re.compile(pattern_text)
	word_list = pattern.findall(text)
	return word_list

def removeRepeatItemFromList(info_list):
	simple_list = []
	for item in info_list:
		if not item in simple_list:
			simple_list.append(item)
	return simple_list

def removeWordsFromText(text, word_list):
	word_list.sort(key = len, reverse = True)
	for word in word_list:
		text = text.replace(word, '')
	text = re.sub(r'\s', '', text)
	return text

def getOperatorListFromText(text, word_list, keyword_operator_list):
	operator_list = []
	text = removeWordsFromText(text, word_list)
	for operator in keyword_operator_list:
		if operator in text:
			operator_list.append(operator)
	return operator_list

def getKeywordListFromText(text, keyword_operator_list):
	word_list = getWordListFromText(text)
	word_list = removeRepeatItemFromList(word_list)
	operator_list = getOperatorListFromText(text, word_list, keyword_operator_list)
	keyword_list = word_list + operator_list
	return keyword_list

def getRefList(keyword_list, arduino_info, platform):
	url_list = []
	ref_text = ''

	url = ''
	for keyword in keyword_list:
		if keyword in arduino_info.getKeywordList('common'):
			url = arduino_info.getKeywordRef('common', keyword)
		elif keyword in arduino_info.getKeywordList(platform):
			url = arduino_info.getKeywordRef(platform, keyword)

		if url:
			if url[0].isupper():
				if not url in url_list:
					url_list.append(url)
			else:
				text = '%s: %s\n' % (keyword, url)
				ref_text += text
	return (url_list, ref_text)

