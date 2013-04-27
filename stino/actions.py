#-*- coding: utf-8 -*-
# stino/actions.py

import os
import zipfile

from . import const
from . import globalvars
from . import textutil
from . import fileutil
from . import parsearduino

def changeArduinoRoot(arduino_root):
	pre_arduino_root = const.settings.get('arduino_root')
	const.settings.set('arduino_root', arduino_root)
	version_info = parsearduino.genVersionInfo()
	version_text = version_info[1]
	display_text = 'Arduino {0} is found at {1}.\n'
	globalvars.log_panel.addText(display_text, [version_text, arduino_root])

	if arduino_root != pre_arduino_root:
		globalvars.arduino_info.update()
		const.settings.set('full_compilation', True)
		globalvars.menu.update()
		# globalvars.status_info.update()
		
def changeSketchbookRoot(sketchbook_root):
	sketchbook_root = textutil.getInfoFromKey(sketchbook_root)[1]
	pre_sketchbook_root = const.settings.get('sketchbook_root')
	const.settings.set('sketchbook_root', sketchbook_root)
	display_text = 'Sketchbook folder has been changed to {0}.\n'
	globalvars.log_panel.addText(display_text, [sketchbook_root])

	if sketchbook_root != pre_sketchbook_root:
		globalvars.arduino_info.update()
		globalvars.menu.update()

def updateSerialMenu():
	globalvars.menu.update()
	globalvars.status_info.update()

def archiveSketch(zip_folder_path, sketch_folder_path):
	file_list = fileutil.listDir(sketch_folder_path, with_dirs = False)
	zip_folder_path = textutil.getInfoFromKey(zip_folder_path)[1]
	sketch_name = os.path.split(sketch_folder_path)[1]
	zip_file_name = sketch_name + '.zip'
	zip_file_path = os.path.join(zip_folder_path, zip_file_name)
	opened_zipfile = zipfile.ZipFile(zip_file_path, 'w' ,zipfile.ZIP_DEFLATED)
	os.chdir(sketch_folder_path)
	for cur_file in file_list:
		opened_zipfile.write(cur_file)
	opened_zipfile.close()

	display_text = 'Writing {0} completed.\n'
	globalvars.log_panel.addText(display_text, [zip_file_path])