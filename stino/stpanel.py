#-*- coding: utf-8 -*-
# stino/stpanel.py

import sublime
import threading
import time

from . import textutil

def isPanel(view):
	state = True
	file_name = view.file_name()
	name = view.name()
	if file_name or name:
		state = False
	return state

class STPanel:
	def __init__(self, language, name = 'stino_log'):
		self.is_ready = False
		self.language = language
		self.name = name
		self.window = None
		self.show_text = ''
		self.panel = None

	def addText(self, text, para_list = ()):
		if self.panel is None:
			window = sublime.active_window()
			if window is None:
				return
			else:
				self.panel = window.get_output_panel(self.name)
				self.toggleWordWrap()
		text = self.language.translate(text)

		index = 0
		for para in para_list:
			org_text = '{%d}' % index
			text = text.replace(org_text, para)
			index += 1

		text = text.replace('\r', '')

		self.show_text += text
		show_thread = threading.Thread(target=self.show)
		show_thread.start()

	def show(self):
		sublime.set_timeout(self.update, 0)

	def update(self):
		if self.show_text:
			textutil.insertTextToView(self.panel, self.show_text)
			self.panel.show(self.panel.size())
			self.show_text = ''

			window = sublime.active_window()
			panel_name = 'output.' + self.name
			window.run_command("show_panel", {"panel": panel_name})

	def clear(self):
		textutil.replaceTextOfView(self.panel)

	def toggleWordWrap(self):
		self.panel.run_command('toggle_setting', {'setting': 'word_wrap'})