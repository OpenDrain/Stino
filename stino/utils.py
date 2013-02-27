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