#-*- coding: utf-8 -*-
# stino/stsyntax.py

import os

from . import const
from . import fileutil

def classifyKeyword(arduino_info):
	constant_list = []
	keyword_list = []
	function_list = []
	
	platform_list = ['common']
	platform = const.settings.get('platform')
	if platform:
		platform_list.append(platform)

	for platform in platform_list:
		all_keyword_list = arduino_info.getKeywordList(platform)
		for keyword in all_keyword_list:
			if len(keyword) > 1:
				keyword_type = arduino_info.getKeywordType(platform, keyword)
				if keyword_type:
					if 'LITERAL' in keyword_type:
						constant_list.append(keyword)
					elif keyword_type == 'KEYWORD1':
						keyword_list.append(keyword)
					else:
						function_list.append(keyword)
	return (constant_list, keyword_list, function_list)

def genDictBlock(info_list, description):
	dict_text = ''
	if info_list:
		dict_text += '\t' * 2
		dict_text += '<dict>\n'
		dict_text += '\t' * 3
		dict_text += '<key>match</key>\n'
		dict_text += '\t' * 3
		dict_text += '<string>\\b('
		for item in info_list:
			dict_text += item
			dict_text += '|'
		dict_text = dict_text[:-1]
		dict_text += ')\\b</string>\n'
		dict_text += '\t' * 3
		dict_text += '<key>name</key>\n'
		dict_text += '\t' * 3
		dict_text += '<string>'
		dict_text += description
		dict_text += '</string>\n'
		dict_text += '\t' * 2
		dict_text += '</dict>'
	return dict_text


def genSyntaxText(arduino_info):
	(constant_list, keyword_list, function_list) = classifyKeyword(arduino_info)
	
	text = ''
	text += genDictBlock(constant_list, 'constant.arduino')
	text += genDictBlock(keyword_list, 'storage.modifier.arduino')
	text += genDictBlock(function_list, 'support.function.arduino')

	temp_file = os.path.join(const.template_root, 'syntax')
	syntax_text = fileutil.readFileText(temp_file)
	syntax_text = syntax_text.replace('(_$dict$_)', text)
	return syntax_text

def writeSyntaxFile(syntax_file, syntax_text):
	fileutil.writeFile(syntax_file, syntax_text)

class STSyntax:
	def __init__(self, arduino_info):
		self.arduino_info = arduino_info
		self.syntax_file_path = os.path.join(const.stino_root, 'Arduino.tmLanguage')
		self.update()

	def update(self):
		file_text = genSyntaxText(self.arduino_info)
		writeSyntaxFile(self.syntax_file_path, file_text)
		
