#-*- coding: utf-8 -*-
# stino/const.py
# Global variants used by all codes are defined in this file.

# Part of the Stino project - https://github.com/Robot-Will/Stino
# Stino is Sublime Text plugin, which provides a Arduino-like IDE.
# Copyright (c) 2012-13 Robot Will

# This program is free software; you can redistribute it and/or modify
# it.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 

import inspect
import os
import sys

import locale
import codecs

import sublime

from . import setting

# Python Version
python_version_txt = sys.version[:3]
python_version = float(python_version_txt)

# Sublime Text Version
st_version = int(sublime.version())

# System platform may be "osx", "linux" or "windows"
sys_platform = sublime.platform()

# System Arch may be "x32" or "x64"
sys_arch = sublime.arch()

# System Encoding
if sys_platform == 'osx':
	sys_encoding = 'utf-8'
else:
	sys_encoding = codecs.lookup(locale.getpreferredencoding()).name

# System Language
sys_language = locale.getdefaultlocale()[0]
if sys_language:
	sys_language = sys_language.lower()
else:
	sys_language = 'en'

cur_file_path = inspect.stack()[0][1]
cur_folder_path = os.path.split(cur_file_path)[0]
stino_root = os.path.split(cur_folder_path)[0]
script_root = os.path.join(stino_root, 'stino')
template_root = os.path.join(stino_root, 'template')
language_root = os.path.join(stino_root, 'language')
config_root = os.path.join(stino_root, 'config')

#
arduino_ext_list = ['.ino', '.pde']
cpp_ext_list = ['.c', '.cc', '.cpp', '.cxx']
src_ext_list= arduino_ext_list + cpp_ext_list
src_header_ext_list = ['.h', '.hpp']
all_src_ext_list = src_ext_list + src_header_ext_list

sketchbook_function_dir_list = ['libraries', 'hardware', 'examples']

baudrate_list = ['300', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']

# Stino settings file
settings = setting.Setting(stino_root)