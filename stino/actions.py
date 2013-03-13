#-*- coding: utf-8 -*-
# stino/actions.py

import stino

def changeArduinoRoot(arduino_root):
	pre_arduino_root = stino.const.settings.get('arduino_root')
	stino.arduino_info.setArduinoRoot(arduino_root)
	stino.arduino_info.genVersion()
	version_text = stino.arduino_info.getVersionText()
	log_text = 'Arduino %s is found at %s.\n' % (version_text, arduino_root)
	stino.log_panel.addText(log_text)

	if arduino_root != pre_arduino_root:
		stino.arduino_info.update()
		stino.cur_menu.update()
		stino.const.settings.set('full_compilation', True)
		stino.const.save_settings()

def changeSketchbookRoot(sketchbook_root):
	sketchbook_root = stino.utils.getInfoFromKey(sketchbook_root)[1]
	pre_sketchbook_root = stino.const.settings.get('sketchbook_root')
	stino.arduino_info.setSketchbookRoot(sketchbook_root)
	log_text = 'Sketchbook folder have switched to %s.\n' % sketchbook_root
	stino.log_panel.addText(log_text)

	if sketchbook_root != pre_sketchbook_root:
		stino.arduino_info.sketchbookUpdate()
		stino.cur_menu.update()

def updateSerialMenu():
	stino.cur_menu.update()