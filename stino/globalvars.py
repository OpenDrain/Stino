#-*- coding: utf-8 -*-
# stino/globalvars.py
# Define global variants

from . import language

from . import status
from . import stpanel

from . import arduino
from . import stsyntax
from . import stmenu
from . import stcommand
from . import stcompletion
from . import smonitor

cur_language = language.Language()
log_panel = stpanel.STPanel(cur_language)

arduino_info = arduino.Arduino()
menu = stmenu.STMenu(cur_language, arduino_info)
command = stcommand.STCommand(cur_language, arduino_info)
syntax = stsyntax.STSyntax(arduino_info)
completion = stcompletion.STCompletion(arduino_info)


# status = status.Status()
# serial_listener = smonitor.SerialPortListener()
# serial_port_in_use_list = []
# serial_port_monitor_dict = {}


