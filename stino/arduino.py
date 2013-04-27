#-*- coding: utf-8 -*-
# stino/arduino.py

import os

from . import const
from . import textutil
from . import fileutil
from . import parsearduino

class Arduino:
	def __init__(self):
		self.update()

	def update(self):
		version_info = parsearduino.genVersionInfo()
		platform_info = parsearduino.genPlatformInfo()
		board_info = parsearduino.genPlatformBoardInfo(platform_info)
		programmer_info = parsearduino.genPlatformProgrammerInfo(platform_info)
		library_info = parsearduino.genPlatformLibraryInfo(platform_info)
		example_info = parsearduino.genPlatformExampleInfo(platform_info, library_info)
		keyword_info = parsearduino.genPlatformKeywordInfo(platform_info, library_info)
		platform_operator_list_dict = parsearduino.genPlatformOperatorInfo(platform_info, keyword_info)
		
		self.version = version_info[0]
		self.version_text = version_info[1]

		self.platform_list = platform_info[0]
		self.platform_core_root_list_dict = platform_info[1]
		self.platform_src_cores_path_dict = platform_info[2]

		self.platform_board_lists_dict = board_info[0]
		self.board_file_dict = board_info[1]
		self.board_type_list_dict = board_info[2]
		self.board_item_list_dict = board_info[3]
		self.type_caption_dict = board_info[4]

		self.platform_programmer_lists_dict = programmer_info[0]
		self.programmer_file_dict = programmer_info[1]

		self.platform_library_lists_dict = library_info[0]
		self.library_path_dict = library_info[1]

		self.platform_example_lists_dict = example_info[0]
		self.example_path_dict = example_info[1]

		self.platform_keyword_list_dict = keyword_info[0]
		self.keyword_type_dict = keyword_info[1]
		self.keyword_ref_dict = keyword_info[2]

		self.platform_operator_list_dict = platform_operator_list_dict

	def isReady(self):
		state = False
		if self.platform_list:
			state = True
		return state

	def getVersion(self):
		return self.version

	def getVersionText(self):
		return self.version_text

	def getPlatformList(self):
		return self.platform_list

	def getSrcCoresPath(self, platform):
		cores_path = ''
		if platform in self.platform_src_cores_path_dict:
			cores_path = self.platform_src_cores_path_dict[platform]
		return cores_path

	def getBoardLists(self, platform):
		board_lists = []
		if platform in self.platform_board_lists_dict:
			board_lists = self.platform_board_lists_dict[platform]
		return board_lists

	def getBoardFile(self, platform, board):
		file_path = ''
		key = textutil.genKey(platform, board)
		if key in self.board_file_dict:
			file_path = self.board_file_dict[key]
		return file_path

	def getBoardTypeList(self, platform, board):
		type_list = []
		key = textutil.genKey(platform, board)
		if key in self.board_type_list_dict:
			type_list = self.board_type_list_dict[key]
		return type_list

	def getBoardItemList(self, platform, board, board_type):
		item_list = []
		board_key = textutil.genKey(platform, board)
		type_key = textutil.genKey(board_key, board_type)
		if type_key in self.board_item_list_dict:
			item_list = self.board_item_list_dict[type_key]
		return item_list

	def getPlatformTypeCaption(self, platform, board_type):
		caption = ''
		key = textutil.genKey(platform, board_type)
		if key in self.type_caption_dict:
			caption = self.type_caption_dict[key]
		return caption

	def getProgrammerLists(self, platform):
		programmer_lists = []
		if platform in self.platform_programmer_lists_dict:
			programmer_lists = self.platform_programmer_lists_dict[platform]
		return programmer_lists

	def getProgrammerFile(self, platform, programmer):
		file_path = ''
		key = textutil.genKey(platform, programmer)
		if key in self.programmer_file_dict:
			file_path = self.programmer_file_dict[key]
		return file_path

	def getLibraryLists(self, platform):
		library_lists = []
		if platform in self.platform_library_lists_dict:
			library_lists = self.platform_library_lists_dict[platform]
		return library_lists

	def getLibraryPath(self, platform, library):
		path = ''
		key = textutil.genKey(platform, library)
		if key in self.library_path_dict:
			path = self.library_path_dict[key]
		return path

	def getExampleLists(self, platform):
		example_lists = []
		if platform in self.platform_example_lists_dict:
			example_lists = self.platform_example_lists_dict[platform]
		return example_lists

	def getExamplePath(self, platform, example):
		path = ''
		key = textutil.genKey(platform, example)
		if key in self.example_path_dict:
			path = self.example_path_dict[key]
		return path

	def getKeywordList(self, platform):
		keyword_list = []
		if platform in self.platform_keyword_list_dict:
			keyword_list = self.platform_keyword_list_dict[platform]
		return keyword_list

	def getKeywordType(self, platform, keyword):
		keyword_type = ''
		key = textutil.genKey(platform, keyword)
		if key in self.keyword_type_dict:
			keyword_type = self.keyword_type_dict[key]
		return keyword_type

	def getKeywordRef(self, platform, keyword):
		keyword_ref = ''
		key = textutil.genKey(platform, keyword)
		if key in self.keyword_ref_dict:
			keyword_ref = self.keyword_ref_dict[key]
		return keyword_ref

	def getOperatorList(self, platform):
		operator_list = []
		if platform in self.platform_operator_list_dict:
			operator_list = self.platform_operator_list_dict[platform]
		return operator_list