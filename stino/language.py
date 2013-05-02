#-*- coding: utf-8 -*-
# stino/language.py

import os
import re

from . import const
from . import textutil
from . import fileutil

class Language:
	def __init__(self):
		self.settings = const.settings
		self.genAbvDict()
		self.genLanguageList()
		self.setDefaultLanguage()
		self.genDefaultTransDict()
		self.genTransDict()

	def update(self):
		self.genTransDict()

	def genAbvDict(self):
		self.abv_language_dict = {}
		self.abv_text_dict = {}
		config_root = const.config_root
		iso_file_path = os.path.join(config_root, 'ISO639_1')
		lines = fileutil.readFileLines(iso_file_path)
		for line in lines:
			line = line.strip()
			if line:
				info_list = line.split('=')
				lang_abv = info_list[0].strip()
				lang = info_list[1].strip()
				lang_text = info_list[2].strip()
				self.abv_language_dict[lang_abv] = lang
				self.abv_text_dict[lang_abv] = '%s (%s)' % (lang_text, lang)

	def genLanguageList(self):
		self.language_list = []
		self.language_text_list = []
		self.language_file_dict = {}
		self.language_text_dict = {}
		self.text_language_dict = {}
		language_root = const.language_root
		file_list = fileutil.listDir(language_root, with_dirs = False)
		for cur_file in file_list:
			if cur_file in self.abv_language_dict:
				language_abv = cur_file
				language = self.abv_language_dict[language_abv]
				language_text = self.abv_text_dict[language_abv]
				
				if not language in self.language_list:
					cur_file_path = os.path.join(language_root, cur_file)
					self.language_list.append(language)
					self.language_file_dict[language] = cur_file_path
					self.language_text_dict[language] = language_text
					self.text_language_dict[language_text] = language
		self.language_list.sort()
		for language in self.language_list:
			language_text = self.language_text_dict[language]
			self.language_text_list.append(language_text)

	def setDefaultLanguage(self):
		language = self.settings.get('language')
		if not language:
			language_abv = const.sys_language
			if language_abv in self.abv_language_dict:
				language = self.abv_language_dict[language_abv]
			else:
				language_abv = language_abv.split('_')[0].strip()
				if language_abv in self.abv_language_dict:
					language = self.abv_language_dict[language_abv]
		if not language in self.language_list:
			language = 'English'
		self.settings.set('language', language)

	def genDefaultTransDict(self):
		self.trans_dict = {}

		# pattern_text_list = [r"%\((.+?)\)s", r"display_text\s*?=\s*?'((?:[^'\\']|\\.)+?)'"]
		pattern_text_list = [r"%\((.+?)\)s"]
		pattern_list = []
		for pattern_text in pattern_text_list:
			pattern_list.append(re.compile(pattern_text, re.S))

		plugin_root = const.stino_root
		script_root = const.script_root
		template_root = const.template_root
		root_list = [plugin_root, script_root, template_root]

		for cur_dir in root_list:
			file_list = fileutil.listDir(cur_dir, with_dirs = False)
			for cur_file in file_list:
				if ('menu_' in cur_file.lower() and not 'sublime' in cur_file.lower()) \
					or (os.path.splitext(cur_file)[1].lower() == '.py'):
					cur_file_path = os.path.join(cur_dir, cur_file)
					text = fileutil.readFileText(cur_file_path)
					for pattern in pattern_list:
						key_list = pattern.findall(text)
						for key in key_list:
							if not key in self.trans_dict:
								self.trans_dict[key] = key

	def genTransDict(self):
		language = self.settings.get('language')
		language_file_path = self.getLanguageFile(language)
		if os.path.isfile(language_file_path):
			trans_block = []
			lines = fileutil.readFileLines(language_file_path)
			for line in lines:
				line = line.strip()
				if line and line[0] != '#':
					trans_block.append(line)
			info_block_list = textutil.splitToBlocks(trans_block, sep = 'msgid')
			for info_block in info_block_list:
				key = ''
				value = ''
				is_key_line = False
				is_value_line = False
				for line in info_block:
					if 'msgid' in line:
						is_key_line = True
					if 'msgstr' in line:
						is_key_line = False
						is_value_line = True
					if is_key_line:
						line = line.replace('msgid', '').strip()
						line = line[1:-1]
						key += line
					if is_value_line:
						line = line.replace('msgstr', '').strip()
						line = line[1:-1]
						value += line
				if key in self.trans_dict:
					self.trans_dict[key] = value

	def translate(self, display_text):
		display_text = display_text.replace('\n', '\\n')
		display_text = textutil.convertTextToUtf8(display_text)
		trans_text = display_text
		if display_text in self.trans_dict:
			trans_text = self.trans_dict[display_text]
		trans_text = trans_text.replace('\\n', '\n')
		return trans_text

	def getTransDict(self):
		return self.trans_dict

	def getLanguageList(self):
		return self.language_list

	def getLanguageTextList(self):
		return self.language_text_list

	def getLanguageFile(self, language):
		file_path = ''
		if language in self.language_file_dict:
			file_path = self.language_file_dict[language]
		return file_path

	def getLanguageTextFromLanguage(self, language):
		language_text = ''
		if language in self.language_text_dict:
			language_text = self.language_text_dict[language]
		return language_text

	def getLanguageFromLanguageText(self, language_text):
		language = ''
		if language_text in self.text_language_dict:
			language = self.text_language_dict[language_text]
		return language