#-*- coding: utf-8 -*-
# stino/utils.py

info_sep = '$@@$'

def genKey(info, base_info):
	key = info + info_sep + base_info
	return key

def getInfoFromKey(key):
	info_list = key.split(info_sep)
	return info_list

def convertAsciiToUtf8(txt):
	if not isinstance(txt, unicode):
		try:
			txt = txt.decode('utf-8')
		except UnicodeDecodeError:
			from chardet import universaldetector
			detector = universaldetector.UniversalDetector()
			detector.feed(txt)
			detector.close()
			result = detector.result
			encoding = result['encoding']
			if encoding:
				try:
					txt = txt.decode(encoding)
				except UnicodeDecodeError:
					txt = splitTextToConvertToUtf8(txt, encoding)
			else:
				txt = splitTextToConvertToUtf8(txt, 'utf-8')
	return txt

def splitTextToConvertToUtf8(txt, encoding):
	if len(txt) == 1:
		txt = txt.decode(encoding, 'replace')
	else:
		if '\n' in txt:
			lines = convertTextToLines(txt)
			txt = ''
			for line in lines:
				line = convertAsciiToUtf8(line)
				txt += line
				txt += '\n'
		else:
			org_txt = txt
			txt = ''
			for character in org_txt:
				character = convertAsciiToUtf8(character)
				txt += character
	return txt

def convertTextToLines(txt):
	lines = txt.split('\n')
	return lines

def getKeyValue(line):
	line = line.strip()
	if '=' in line:
		index = line.index('=')
		key = line[:index].strip()
		value = line[(index+1):].strip()
	else:
		key = ''
		value = ''
	return (key, value)

def splitToBlocks(lines, sep = '.name', none_sep = None, key_length = 0):
	block_list = []
	block = []
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			sep_condtion = sep in line
			none_sep_condition = True
			if none_sep:
				none_sep_condition = not none_sep in line
			length_condition = False
			if key_length > 0:
				if '=' in line:
					(key, value) = getKeyValue(line)
					key_list = key.split('.')
					length = len(key_list)
					if length == key_length:
						length_condition = True

			is_new_block = (sep_condtion and none_sep_condition) or length_condition
			if is_new_block:
				block_list.append(block)
				block = [line]
			else:
				block.append(line)
	block_list.append(block)
	block_list.pop(0)
	return block_list

def getTypeInfoBlock(board_info_block, board_type):
	info_block = []
	for line in board_info_block:
		if board_type in line:
			info_block.append(line)
	return info_block

def isLists(lists):
	state = False
	if lists:
		if isinstance(lists[0], list):
			state = True
	return state

def simplifyLists(lists):
	simple_list = []
	for cur_list in lists:
		simple_list += cur_list
	return simple_list
