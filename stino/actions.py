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