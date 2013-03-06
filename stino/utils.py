#-*- coding: utf-8 -*-
# stino/utils.py

def convertAsciiToUtf8(txt):
	if not isinstance(txt, unicode):
		try:
			txt = txt.decode('utf-8')
		except UnicodeDecodeError:
			import chardet
			detector = chardet.universaldetector()
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

def splitToBlocks(lines, sep = '.name'):
	block_list = []
	block = []
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			if sep in line:
				block_list.append(block)
				block = [line]
			else:
				block.append(line)
	block_list.append(block)
	block_list.pop(0)
	return block_list