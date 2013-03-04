#-*- coding: utf-8 -*-
# stino/language.py

import os
import re

from stino import const
from stino import osfile

def parseLanguageFromFile(file_path):
	language = ''
	language_text = ''
	lines = osfile.readFileLines(file_path)
	for line in lines:
		if '#' in line and 'LANGUAGE:' in line:
			language_text = line.split(':')[1].strip()
			language = language_text.split('(')[1]
			language = language.split(')')[0].strip()
			break
	return (language, language_text)

class Language:
	def __init__(self):
		self.genLanguageList()
		self.setDefaultLanguage()
		self.genDefaultTransDict()
		self.genDefaultLanguageFile()
		self.genTransDict()

	def genLanguageList(self):
		self.language_list = []
		self.language_file_dict = {}
		self.language_text_dict = {}
		self.text_language_dict = {}
		language_root = const.language_root
		file_list = osfile.listDir(language_root, with_dirs = False)
		for cur_file in file_list:
			if cur_file == 'default':
				continue
			cur_file_path = os.path.join(language_root, cur_file)
			(language, language_text) = parseLanguageFromFile(cur_file_path)
			if language:
				if not language in self.language_list:
					self.language_list.append(language)
					self.language_file_dict[language] = cur_file_path
					self.language_text_dict[language] = language_text
					self.text_language_dict[language_text] = language
		self.language_list.sort()

	def setDefaultLanguage(self):
		language = const.settings.get('language')
		if not language:
			language = const.sys_language
		if not language in self.language_list:
			language = language.split('_')[0].strip()
			if not language in self.language_list:
				language = 'en'
		const.settings.set('language', language)
		const.save_settings()

	def genDefaultTransDict(self):
		self.trans_dict = {}

		pattern_text = r'%\([\S\s]+?\)s'

		plugin_root = const.plugin_root
		script_root = const.script_root
		template_root = const.template_root
		root_list = [plugin_root, script_root, template_root]

		for cur_dir in root_list:
			file_list = osfile.listDir(cur_dir, with_dirs = False)
			for cur_file in file_list:
				if ('menu' in cur_file and not 'sublime' in cur_file) or (os.path.splitext(cur_file)[1] == '.py'):
					cur_file_path = os.path.join(cur_dir, cur_file)
					text = osfile.readFileText(cur_file_path)
					key_list = re.findall(pattern_text, text)
					for key in key_list:
						key = key[2:-2]
						if not key in self.trans_dict:
							value = key.replace('_', ' ')
							self.trans_dict[key] = value

	def genDefaultLanguageFile(self):
		template_root = const.template_root
		language_root = const.language_root
		template_file_path = os.path.join(template_root, 'language')
		text = osfile.readFileText(template_file_path)
		default_file_path = os.path.join(language_root, 'default')
		osfile.writeFile(default_file_path, text)

	def genTransDict(self):
		pass

	def update(self):
		self.genTransDict()

	def getTransDict(self):
		return self.trans_dict

	def getLanguageList(self):
		return self.language_list

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