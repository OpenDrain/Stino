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
		self.initiatePanel()

	def initiatePanel(self):
		init_thread = threading.Thread(target=self.waitForWindowReady)
		init_thread.start()

	def getWindow(self):
		self.window = sublime.active_window()

	def setPanel(self):
		self.panel = self.window.get_output_panel(self.name)

	def waitForWindowReady(self):
		ready = False
		while not ready:
			sublime.set_timeout(self.getWindow, 0)
			if not (self.window is None):
				ready = True
			else:
				time.sleep(0.5)
		sublime.set_timeout(self.setPanel, 0)

	def addText(self, text, para_list = ()):
		text = self.language.translate(text)

		index = 0
		for para in para_list:
			org_text = '{%d}' % index
			text = text.replace(org_text, para)
			index += 1

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