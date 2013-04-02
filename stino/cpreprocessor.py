#-*- coding: utf-8 -*-
# stino/cpreprocessor.py

import os
import re

from stino import utils
from stino import osfile
from stino import src

def getTextFromBlock(block):
	text = ''
	for line in block:
		text += line
		text += '\n'
	return text

def checkDir(dir_path):
	if os.path.isfile(dir_path):
		os.remove(dir_path)
	if not os.path.isdir(dir_path):
		os.makedirs(dir_path)

def createTempSrcFiles(temp_folder_path, path_list):
	temp_path_list = []
	for path in path_list:
		filename = os.path.split(path)[1]
		temp_path = os.path.join(temp_folder_path, filename)
		text = osfile.readFileText(path)
		text = src.removeComments(text)
		osfile.writeFile(temp_path, text)
		temp_path_list.append(temp_path)
	return temp_path_list

def getMacroDictFromCommand(command):
	macro_value_dict = {}
	pattern_text = r'\S+'
	pattern = re.compile(pattern_text)
	word_list = pattern.findall(command)
	for word in word_list:
		if len(word) > 2:
			if word[:2] == '-D':
				word = word[2:]
				if '=' in word:
					(macro, value) = utils.getKeyValue(word)
					macro_value_dict[macro] = value
				else:
					macro = word
					macro_value_dict[macro] = ''
	return macro_value_dict

def hasMacroBlock(src_text):
	state = False
	if '#if' in src_text:
		state = True
	return state

def getMacroBlockTextList(src_text):
	src_lines = utils.convertTextToLines(src_text)
	level = 0

	text_list = []
	for line in src_lines:
		if level > 0:
			text += line
			text += '\n'
			if '#if' in line:
				level += 1
			if '#endif' in line:
				level -= 1
			if level == 0:
				text_list.append(text)
		else:
			if '#if' in line:
				text = line
				text += '\n'
				level += 1
	return text_list

def splitHeaderPathList(header_path_list):
	none_macro_header_path_list = []
	macro_header_path_list = []
	for header_path in header_path_list:
		header_text = osfile.readFileText(header_path)
		if hasMacroBlock(header_text):
			macro_header_path_list.append(header_path)
		else:
			none_macro_header_path_list.append(header_path)
	return (macro_header_path_list, none_macro_header_path_list)

def getMacroDictFromText(text):
	blank_pattern_text = r'\S+'
	blank_pattern = re.compile(blank_pattern_text)
	macro_value_dict = {}
	text = text.replace('\\\n', ' ')
	lines = utils.convertTextToLines(text)
	for line in lines:
		line = line.strip()
		if '#define' in line:
			macro = ''
			value = ''
			word_list = blank_pattern.findall(line)
			if len(word_list) > 1:
				macro = word_list[1]
			if len(word_list) > 2:
				value_word_list = word_list[2:]
				for value_word in value_word_list:
					value += '%s ' % value_word
				value = value[:-1]
			if macro:
				macro_value_dict[macro] = value
		elif '#undef' in line:
			macro = ''
			word_list = blank_pattern.findall(line)
			if len(word_list) > 1:
				macro = word_list[1]
				if macro in macro_value_dict:
					macro_value_dict.pop(macro)
	return macro_value_dict

def getMacroDictFromFileList(file_path_list):
	macro_value_dict = {}
	for file_path in file_path_list:
		file_text = osfile.readFileText(file_path)
		cur_macro_value_dict = getMacroDictFromText(file_text)
		macro_value_dict.update(cur_macro_value_dict)
	return macro_value_dict

def splitTextByFirstMacro(text):
	index = text.index('#if')
	none_macro_text = text[:index]
	macro_text = text[index:]
	return (none_macro_text, macro_text)

def getFirstMacroBlock(text):
	fisrt_macro_block = []
	lines = utils.convertTextToLines(text)
	level = 0
	for line in lines:
		if level > 0:
			fisrt_macro_block.append(line)
			if '#if' in line:
				level += 1
			if '#endif' in line:
				level -= 1
			if level == 0:
				break
		else:
			if '#if' in line:
				fisrt_macro_block.append(line)
				level += 1
	fisrt_macro_block = fisrt_macro_block[:-1]
	return fisrt_macro_block

def splitMacroElseBlcokList(macro_block):
	macro_else_block_list = []
	else_block = []
	level = 0
	for line in macro_block:
		if level > 0:
			if '#endif' in line:
				level -= 1
			if level == 1:
				if ('#elif' in line) or ('#else' in line):
					macro_else_block_list.append(else_block)
					else_block = []
			else_block.append(line)
			if '#if' in line:
				level += 1
		else:
			if '#if' in line:
				else_block.append(line)
				level += 1
	macro_else_block_list.append(else_block)
	return macro_else_block_list

def getConditionCommand(condition_line):
	blank_pattern_text = r'\S+'
	blank_pattern = re.compile(blank_pattern_text)
	word_list = blank_pattern.findall(condition_line)
	condition_command = word_list[0]
	return condition_command

def getCompareList(statement):
	blank_pattern_text = r'\S+'
	blank_pattern = re.compile(blank_pattern_text)
	word_list = blank_pattern.findall(statement)
	return word_list

def parseDefineConditionStatemnet(define_statement, macro_value_dict):
	if '(' in define_statement:
		def_macro = define_statement.split('(')[1]
		def_macro = def_macro.replace(')', '')
	else:
		blank_pattern_text = r'\S+'
		blank_pattern = re.compile(blank_pattern_text)
		word_list = blank_pattern.findall(define_statement)
		def_macro = word_list[-1]
	def_macro = def_macro.strip()
	state = (def_macro in macro_value_dict)
	return state

def parseCompareConditionStatemnet(compare_statement, macro_value_dict):
	state = False
	compare_list = getCompareList(compare_statement)
	if len(compare_list) == 3:
		def_macro = compare_list[0]
		compare_operator = compare_list[1]
		compare_value = int(compare_list[2])
		if def_macro in macro_value_dict:
			def_macro_value = int(macro_value_dict[def_macro])
			if compare_operator == '==':
				state = (def_macro_value == compare_value)
			elif compare_operator == '!=':
				state = (def_macro_value != compare_value)
			elif compare_operator == '>':
				state = (def_macro_value > compare_value)
			elif compare_operator == '<':
				state = (def_macro_value < compare_value)
			elif compare_operator == '>=':
				state = (def_macro_value >= compare_value)
			elif compare_operator == '<=':
				state = (def_macro_value <= compare_value)
	return state

def parseSimpleConditionStatemnet(statement, macro_value_dict):
	if 'define' in statement:
		state = parseDefineConditionStatemnet(statement, macro_value_dict)
	else:
		state = parseCompareConditionStatemnet(statement, macro_value_dict)
	return state

def parseComplexConditionStatemnet(statement, macro_value_dict):
	parenthesis_list = ['(', ')']
	logic_list = ['||', '&&']
	for op in (parenthesis_list + logic_list):
		replace_text = '\n%s\n' % op
		statement = statement.replace(op, replace_text)
	lines = utils.convertTextToLines(statement)
	
	simple_bool_list = []
	logic_op = ''
	statement = ''
	parenthesis_level = 0
	start_parsing = False
	for line in lines:
		line = line.strip()
		if not line:
			continue
		if parenthesis_level > 0:
			statement += '%s ' % line
			if '(' in line:
				parenthesis_level += 1
			elif ')' in line:
				parenthesis_level -= 1
		else:
			if ('||' in line) or ('&&' in line):
				logic_op = line
				start_parsing = True
			else:
				statement += '%s ' % line
				if '(' in line:
					parenthesis_level += 1
			
		if start_parsing:
			cur_state = parseConditionStatemnet(statement, macro_value_dict)
			simple_bool_list.append(cur_state)
			statement = ''
			start_parsing = False
	if statement:
		cur_state = parseConditionStatemnet(statement, macro_value_dict)
		simple_bool_list.append(cur_state)

	if logic_op == '||':
		state = (simple_bool_list[0] or simple_bool_list[1])
	else:
		state = (simple_bool_list[0] and simple_bool_list[1])
	if len(simple_bool_list) > 2:
		for simple_bool in simple_bool_list[2:]:
			if logic_op == '||':
				state = (state or simple_bool)
			else:
				state = (state and simple_bool)
	return state

def parseConditionStatemnet(statement, macro_value_dict):
	statement = src.regulariseBlank(statement)
	is_reverse = False
	if statement[0] == '!':
		is_reverse = True
		statement = statement[1:]
	if statement[0] == '(':
		statement = statement[1:-1]
	if ('||' in statement) or ('&&' in statement):
		state = parseComplexConditionStatemnet(statement, macro_value_dict)
	else:
		state = parseSimpleConditionStatemnet(statement, macro_value_dict)
	if is_reverse:
		state = not state
	return state

def isCondition(condition_line, macro_value_dict):
	# print condition_line
	state = False
	condition_command = getConditionCommand(condition_line)
	condition_statement = condition_line.replace(condition_command, '').strip()
	if condition_command == '#if' or condition_command == '#elif':
		state = parseConditionStatemnet(condition_statement, macro_value_dict)
	elif condition_command == '#ifdef' or condition_command == '#ifndef':
		if condition_statement:
			if condition_command == '#ifdef':
				state = (condition_statement in macro_value_dict)
			else:
				state = (condition_statement in macro_value_dict)
	elif condition_command == '#ifndef':
		def_macro = getDefMacro(condition_line)
		state = (def_macro and (not def_macro in macro_value_dict))
	elif condition_command == '#else':
		state = True
	# print state
	return state

def simplifyMacroBlock(macro_block, macro_value_dict):
	simple_macro_block = []
	condition_line = macro_block[0]
	
	macro_else_block_list = splitMacroElseBlcokList(macro_block)
	for else_block in macro_else_block_list:
		condition_line = else_block[0]
		if isCondition(condition_line, macro_value_dict):
			simple_macro_block = else_block[1:]
			break
	return simple_macro_block

def removeFileMacroBlock(file_path_list, macro_value_dict):
	for file_path in file_path_list:
		file_text = osfile.readFileText(file_path)
		simple_text = ''
		process_text = file_text
		# print file_path
		while '#if' in process_text:
			(none_macro_text, process_text) = splitTextByFirstMacro(process_text)
			cur_macro_value_dict = getMacroDictFromText(none_macro_text)
			macro_value_dict.update(cur_macro_value_dict)
			simple_text += none_macro_text
			fisrt_macro_block = getFirstMacroBlock(process_text)
			simple_macro_block = simplifyMacroBlock(fisrt_macro_block, macro_value_dict)
			fisrt_macro_text = getTextFromBlock(fisrt_macro_block)
 			simple_macro_text = getTextFromBlock(simple_macro_block)
			process_text = process_text.replace(fisrt_macro_text, simple_macro_text)
		cur_macro_value_dict = getMacroDictFromText(process_text)
		macro_value_dict.update(cur_macro_value_dict)

		simple_text += process_text
		simple_text = simple_text.replace('#endif', '')
		osfile.writeFile(file_path, simple_text)
	return macro_value_dict

def getHeaderMacroDict(command, header_path_list):
	all_macro_value_dict = {}
	macro_value_dict = getMacroDictFromCommand(command)
	all_macro_value_dict.update(macro_value_dict)
	(macro_header_path_list, none_macro_header_path_list) = splitHeaderPathList(header_path_list)
	macro_value_dict = getMacroDictFromFileList(none_macro_header_path_list)
	all_macro_value_dict.update(macro_value_dict)
	all_macro_value_dict = removeFileMacroBlock(macro_header_path_list, all_macro_value_dict)
	return all_macro_value_dict

def collapseBrace(src_path_list):
	# define_pattern_text = r'^\s*#define\.*?$'
	# define_pattern = re.compile(define_pattern_text, re.M|re.S)
	for src_path in src_path_list:
		src_text = osfile.readFileText(src_path)
		# src_text = define_pattern.sub('', src_text)
		src_text = src_text.replace('{', '\n{\n')
		src_text = src_text.replace('}', '\n}\n')
		lines = utils.convertTextToLines(src_text)
		brace_level = 0
		simple_text = ''
		for line in lines:
			line = line.strip()
			if line:
				if '}' in line:
					brace_level -= 1
				if brace_level == 0:
					simple_text += line
					simple_text += '\n'
				if '{' in line:
					brace_level += 1
		osfile.writeFile(src_path, simple_text)
		print '%s done.' % src_path

def findMainSrcPath(src_path_list, src_folder_path):
	main_src_path = ''
	for src_path in src_path_list:
		src_text = osfile.readFileText(src_path)
		if src.isMainSrcText(src_text):
			filename = os.path.split(src_path)[1]
			main_src_path = os.path.join(src_folder_path, filename)
			main_src_path = main_src_path.replace(os.path.sep, '/')
			break
	return main_src_path

class CPreprocessor:
	def __init__(self, build_path, compilation_command, header_path_list, src_path_list):
		build_path = build_path.replace('/', os.path.sep)
		self.compilation_command = compilation_command
		if src_path_list:
			self.src_folder_path = os.path.split(src_path_list[0])[0]
		else:
			 self.src_folder_path = ''
		self.temp_path = os.path.join(build_path, 'temp')
		checkDir(self.temp_path)
		self.header_path_list = createTempSrcFiles(self.temp_path, header_path_list)
		self.src_path_list = createTempSrcFiles(self.temp_path, src_path_list)
		self.main_src_path = ''
		
	def run(self):
		macro_value_dict = getHeaderMacroDict(self.compilation_command, self.header_path_list)
		removeFileMacroBlock(self.src_path_list, macro_value_dict)
		collapseBrace(self.src_path_list)
		self.main_src_path = findMainSrcPath(self.src_path_list, self.src_folder_path)

	def getMainSrcPath(self):
		return self.main_src_path

	def getTempSrcPathList(self):
		return self.src_path_list
