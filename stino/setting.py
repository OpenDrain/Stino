#-*- coding: utf-8 -*-
# stino/const.py

import os
import json

global_setting_key_list = ['stino_root', 'global_setting', 'show_arduino_menu',\
	 'show_serial_monitor_menu', 'language', 'setting_folder_path']

class Setting:
	def __init__(self, stino_root):
		self.setting_filename = 'Stino.settings'
		self.global_settings_dict = {}
		self.settings_dict = {}

		self.stino_root = stino_root
		self.global_setting_file_path = os.path.join(self.stino_root, self.setting_filename)
		
		# Fisrt, read the global settings.
		self.use_global_setting = True
		self.readSettingFile()

		# If 'global_setting' is not set, use global settings.
		self.use_global_setting = self.get('global_setting')
		if self.use_global_setting is None:
			self.use_global_setting = True
			self.set('global_setting', self.use_global_setting)

		# Set working settings_file path.
		self.setting_folder_path = self.get('setting_folder_path', '')
		if not os.path.isdir(self.setting_folder_path):
			self.setting_file_path = self.global_setting_file_path
		else:
			self.setting_file_path = os.path.join(self.setting_folder_path, self.setting_filename)
		
		# Finally, read settings.
		self.readSettingFile()

	def isGlobalKey(self, key):
		state = True
		if not self.use_global_setting:
			if not key in global_setting_key_list:
				state = False
		return state

	def get(self, key, default_value = None):
		settings_dict = self.global_settings_dict
		if not self.isGlobalKey(key):
			settings_dict = self.settings_dict

		if key in settings_dict:
			value = settings_dict[key]
		else:
			value = default_value
		return value

	def set(self, key, value):
		if self.isGlobalKey(key):
			self.global_settings_dict[key] = value
		else:
			self.settings_dict[key] = value
		self.saveSettingFile()

	def readSettingFile(self):
		if self.use_global_setting:
			setting_file_path = self.global_setting_file_path
		else:
			setting_file_path = self.setting_file_path

		if os.path.isfile(setting_file_path):
			opened_file = open(setting_file_path, 'r')
			settings_text = opened_file.read()
			opened_file.close()

			settings_dict = json.loads(settings_text)

			if self.use_global_setting:
				self.global_settings_dict = settings_dict
			else:
				self.settings_dict = settings_dict
		else:
			self.saveSettingFile()

	def saveSettingFile(self):
		if self.use_global_setting:
			settings_dict = self.global_settings_dict
			setting_file_path = self.global_setting_file_path
		else:
			settings_dict = self.settings_dict
			setting_file_path = self.setting_file_path

		settings_text = json.dumps(settings_dict, sort_keys = True, indent = 4)
		opened_file = open(setting_file_path, 'w')
		opened_file.write(settings_text)
		opened_file.close()

	def changeSettingFileFolder(self, setting_folder_path):
		if os.path.isdir(setting_folder_path):
			self.set('setting_folder_path', setting_folder_path)
			self.setting_file_path = os.path.join(setting_folder_path, self.setting_filename)
			if not os.path.isfile(self.setting_file_path):
				self.saveSettingFile()
			self.readSettingFile()

	def changeState(self, state, setting_folder_path):
		self.use_global_setting = state
		self.set('global_setting', self.use_global_setting)
		if not self.use_global_setting:
			self.changeSettingFileFolder(setting_folder_path)

