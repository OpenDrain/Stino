#-*- coding: utf-8 -*-
# stino/stcompletion.py

import os

from . import const
from . import fileutil

def genCompletionText(arduino_info):
	completions_text = '{\n'
	completions_text += '\t"scope": "source.arduino",\n'
	completions_text += '\t"completions":\n'
	completions_text += '\t[\n'

	platform_list = ['common']
	platform = const.settings.get('platform')
	if platform:
		platform_list.append(platform)

	for platform in platform_list:
		all_keyword_list = arduino_info.getKeywordList(platform)
		for keyword in all_keyword_list:
			if arduino_info.getKeywordType(platform, keyword):
				completions_text += '\t\t"%s",\n' % keyword
	completions_text = completions_text[:-2] + '\n'
	completions_text += '\t]\n'
	completions_text += '}'
	return completions_text

def writeCompletionFile(file_path, file_text):
	fileutil.writeFile(file_path, file_text)

class STCompletion:
	def __init__(self, arduino_info):
		self.arduino_info = arduino_info
		self.file_path = os.path.join(const.stino_root, 'Stino.sublime-completions')
		self.update()

	def update(self):
		file_text = genCompletionText(self.arduino_info)
		writeCompletionFile(self.file_path, file_text)