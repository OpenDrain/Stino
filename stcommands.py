#-*- coding: utf-8 -*-
# stino/stcommands.py

import sublime
import sublime_plugin
import stino

class StinoTestCommand(sublime_plugin.WindowCommand):
	def run(self):
		print stino.cur_language.getLanguageList()
		print stino.cur_language.getTransDict()