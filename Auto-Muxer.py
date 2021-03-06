#!/usr/bin/python
# encoding: utf-8

# NOTE: ALL STRING RELATING TO INPUTS/OUTPUTS (LIKE BASE FOLDER, VIDEO, GROUP TAG, ASS, ETC.) MUST BE UNICODE STRING.
# Use u'your string' if you're using Python 2. All strings in Python 3 are Unicode by default.

# TODO:
# - merge batch mode & normal mode [easy][soon(tm)]
# - option to keep existing attachments, subtitles in video
# - verify video format when searching [low].
# - write a not-so-useless readme [high]
# - support winrar [low]
# - automatically raise source window size if | filesize(source) - filesize(target) | > 16 MiB. To a dynamic limit, though.
# - Deal with cases when both folder and filenames are non-ascii (using working dir)
# - Comment about how scripts work. Let's pray that I won't forget everything before even starting
#
# INCOMPLETE/ON PROGRESS:
#
# DONE:
# - writing logs [medium]
# - get ready to accept paramenters [high]
# - make searchForVer use v2 pattern [high]
# - support non-number episode [medium]
# - option to detect and remove previously muxed same-version files [low]
# - deal with patches for non-ascii filenames [high]:
#   + handle character encoding (output) mess (mostly for windows support--why do I even support windows?) [low]
#   + alternative applying scripts for Windows and non-ascii filenames: attempt to patch with temporary names and rename later [high]
#   + On Windows: works on Windows 7 x64, Python 2.7.6, 3.3.3.
#   + On Linux: works nicely on Python 2.7.5, 3.3.2 & LinuxMint 16.
# - support multiple subtitles [high]
# - accept paramenters [medium][after multiple subtitles supports]
# - accept option file [medium][after paramenters]
# - mux batch --batch 1-3
# - Escape filenames in batch scripts (bash scripts already escaped)
#		See http://www.robvanderwoude.com/escapechars.php http://ss64.com/nt/syntax-esc.html
# - Scripts also looking for source file in parent folder, and moving old file to parrent/old instead of parent/patch/old
# - Rewrite all applying script for batch a.k.a "apply all" scripts
# - Make a separated create patch script (not in repo)

import sys, os, time

programName = "Auto Muxer"
programVer = "0.7"
programAuthor = "dreamer2908"

# specify these 3 if application not found error occurs
mkvmergePath = 'mkvmerge'
xdelta3Path = 'xdelta3'
sevenzipPath = '7z'
repo, dummy = os.path.split(sys.argv[0])
commonPaths = [r'/bin', r'/sbin', r'/usr/bin/', r'/usr/sbin/', r'/usr/local/bin/', r'/usr/local/sbin/', r'C:\Program Files (x86)\MKVToolNix', r'C:\Program Files\MKVToolNix', r'C:\Program Files\7-Zip',  r'C:\Program Files (x86)\7-Zip', repo]

dontMux = False
stopAfterMuxing = False

testing = False
debug = False
verbose = True
python2 = False
win32 = False
initialized = False

plsWriteLogs = True
logFile = None
logFileName = u'muxing_log.txt'
logWriteCount = 0
preinitLog = u''

defaultTimer = None
cpuCount = 1
terminalSupportUnicode = False
nonAsciiParamsWorking = True

# basic inputs. ALL STRINGS MUST BE UNICODE STRINGS
batchMode = False
batchEps = []
episode = 1
version = 1
groupTag = u''
showName = u''
baseFolder = u''
subtitles = [] # format like this [(u"Pupa ? $2ep$.ass", u"Powered by Engrish(tm)", u"eng"), (u"Pupa ? $2ep$ [alt].ass", u"Powered by zZz(tm)", u"jpn")]
video = u"*premux*"
fonts = u"fonts" # the folder containing fonts inside base folder
chapters = u"*chapter*"
title = u"$show$ - $2ep$"
output = u''
output_v1 = u'[$tag$] $show$ - $2ep$ [$crc$].mkv'
output_v2 = u'[$tag$] $show$ - $2ep$v$ver$ [$crc$].mkv'
output_tmp = u'muxed.mkv'
previousVersion = u'[$tag$] $show$ - $2ep$v$lver$ [$crc$].mkv'
previousVersionFound = False
sameVersion = u''
sameVersionFound = False

# track languages and names
video_Name = u"H.264 720p"
video_Lang = u"jpn"
audio_Name = u"AAC LC 2.0"
audio_Lang = u"jpn"

# default sub name & lang for new subtitles
sub_Name = u"Powered by Engrish(tm)"
sub_Lang = u"eng"

patchv2_FolderName = u'patch_ep_$2ep$_v$lver$_to_v$ver$'
patchMux_FolderName = u'patch_ep_$2ep$_mux'
patchUndoMux_FolderName = u'patch_ep_$2ep$_undo_mux'
patchv2_Created = False
patchMux_Created = False
patchUndoMux_Created = False

subtitleArchive = u'[$tag$] $show$ - $2ep$ [sub].7z'
patchMuxArchive = patchMux_FolderName + '.7z'
patchv2Archive = patchv2_FolderName + '.7z'
patchAllArchive = u'patch_ep_$2ep$_all.7z'

plsAddCrc = True
plsCreatePatch_Mux = True
plsCreatePatch_UndoMux = False
plsCreatePatch_v2 = True
plsPackStuff = True
plsRemoveSameVersion = True

fontList = []
fontList_Name = []
muxParams = []

# replace $2ep$, $1ver$ with real value
def fillInValue(text):
	import re

	specialChars = r'.^$*+?{}, \[]|():=#!<'
	reg_Ep = re.compile(r'\$(\d)ep\$')
	reg_EpS = re.compile(r'\$ep\$')
	reg_Ver = re.compile(r'\$ver\$')
	reg_Lver = re.compile(r'\$lver\$')
	reg_Tag = re.compile(r'\$tag\$')
	reg_Show = re.compile(r'\$show\$')
	reg_Crc = re.compile(r'\$crc\$')
	regArray = [reg_Ep, reg_EpS, reg_Show, reg_Ver, reg_Lver, reg_Tag, reg_Crc]

	def regRepl(matchOjb):
		# return formatted episode number if it's a number; string as is otherwise
		if (matchOjb.re == reg_Ep):
			try:
				formatStr = '%0' + matchOjb.groups(1)[0] +'d'
				return formatStr % episode
			except:
				return '%s' % episode
		elif (matchOjb.re == reg_EpS):
			try:
				formatStr = '%02d'
				return formatStr % (episode)
			except:
				return '%s' % episode
		elif (matchOjb.re == reg_Lver):
			formatStr = '%d'
			return formatStr % (version - 1)
		elif (matchOjb.re == reg_Ver):
			formatStr = '%d'
			return formatStr % version
		elif (matchOjb.re == reg_Tag):
			return groupTag
		elif (matchOjb.re == reg_Show):
			return showName
		elif (matchOjb.re == reg_Crc): # addcrc will fill it in later
		# 	try:
		# 		return '%08X' % crc32
		# 	except:
		# 		return '%s' % crc32
			return '$crc$'

	for regObj in regArray:
		text = re.sub(regObj, regRepl, text)
	if debug:
		print(text)
	return text

def fillInInputs():
	global baseFolder, subtitles, video, fonts, chapters, title, output, output_v1, output_v2, previousVersion, patchv2_FolderName, patchMux_FolderName, patchUndoMux_FolderName, subtitleArchive, patchMuxArchive, patchv2Archive, patchAllArchive
	baseFolder = fillInValue(baseFolder)

	subtitles_new = []
	for s in subtitles:
		path, name, lang = s
		path = fillInValue(path)
		name = fillInValue(name)
		subtitles_new.append((path, name, lang))
	subtitles = subtitles_new

	video = fillInValue(video)
	fonts = fillInValue(fonts)
	chapters = fillInValue(chapters)
	title = fillInValue(title)
	patchv2_FolderName = fillInValue(patchv2_FolderName)
	patchMux_FolderName = fillInValue(patchMux_FolderName)
	patchUndoMux_FolderName = fillInValue(patchUndoMux_FolderName)
	subtitleArchive = fillInValue(subtitleArchive)
	patchMuxArchive = fillInValue(patchMuxArchive)
	patchv2Archive = fillInValue(patchv2Archive)
	patchAllArchive = fillInValue(patchAllArchive)
	output = fillInValue(output)
	output_v1 = fillInValue(output_v1)
	output_v2 = fillInValue(output_v2)
	previousVersion = fillInValue(previousVersion)

# detect mkvmerge, 7z, xdelta3 location
def detectPaths():
	import os, sys
	global mkvmergePath, xdelta3Path, sevenzipPath

	def is_exe(fpath):
		if os.path.isfile(fpath):
			if sys.platform != 'win32':
				return os.access(fpath, os.X_OK)
			else:
				if fpath.endswith('.exe') or fpath.endswith('.bat') or fpath.endswith('.com') or fpath.endswith('.cmd'):
					return True
		return False

	def search_exec(binName, firstTry = None):
		if hasattr(firstTry, 'startswith'):
			abspath = os.path.abspath(firstTry)
			if is_exe(abspath):
				return abspath
		# for win32 compatibility
		if sys.platform == 'win32' and not (binName.endswith('.exe') or binName.endswith('.bat') or binName.endswith('.com') or binName.endswith('.cmd')):
			binName += '.exe'
		# Check if it's in paths
		paths = os.environ["PATH"].split(os.pathsep) + commonPaths
		for path in paths:
			path = path.strip('"')
			abspath = os.path.join(path, binName)
			if is_exe(abspath):
				return abspath
		return None

	# try the specified paths
	mkvmergePath = search_exec('mkvmerge', mkvmergePath)
	xdelta3Path = search_exec('xdelta3', xdelta3Path)
	sevenzipPath = search_exec('7z', sevenzipPath)

	# failback to 7za if 7z not found. Not sure if this scenary even exists
	if sevenzipPath == None:
		sevenzipPath = search_exec('7za', '7za')

	if mkvmergePath == None or xdelta3Path == None or sevenzipPath == None:
		return False # not found
	return True # all OK

def isPureAscii(text):
	for c in text:
		code = ord(c)
		if code > 127:
			return False
	return True

def toAsciiBytes(text):
	asciiText = removeNonAscii(text)
	try:
		return asciiText.encode('ascii')
	except:
		return asciiText

# Kills non-ASCII characters
def removeNonAscii(original):
	result = ''
	for c in original:
		code = ord(c)
		if code < 128:
			result += c
		else:
			result += '?'
	return result

def printHacked(text):
	try:
		print(text)
	except:
		print(removeNonAscii(text))

def printAndLog(text):
	printHacked(text)
	if plsWriteLogs:
		writeToLog2(text)

def writeToLog3(mylist):
	tmp = ''
	for l in mylist:
		tmp += '"%s" ' % l
	writeToLog2(tmp)

def writeToLog2(text):
	writeToLog(text + '\n')

# Open the file in append mode and write text to it
# File handle is kept open because re-opening the file
# every single time something needs writing is a bad idea
def writeToLog(text):
	import codecs, sys, os
	global logFile, logWriteCount, preinitLog

	if not plsWriteLogs:
		return

	if not initialized:
		preinitLog += text
		return

	try:
		if logFile == None:
			logFile = codecs.open(logFileName, 'a', 'utf-8')
	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		print("Error! Can't open log file: %s" % error)

	try:
		logFile.write(text)
		logWriteCount += 1
	except Exception as e:
		if python2:
			# second attempt on Python 2
			try:
				logFile.write(removeNonAscii(text))
			except Exception as e:
				error = unicode(e)
				print("Error! Can't write to log file: %s" % error)
		else:
			error = str(e)
			print("Error! Can't write to log file: %s" % error)

	# Flush write buffer every a while
	try:
		if logWriteCount > 9:
			logFile.flush()
			logWriteCount = 0
	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		print("Error! Can't write to log file: %s" % error)

def getInputList():
	import sys, os
	global fontList, video, subtitles, chapters, previousVersion, previousVersionFound, output, sameVersion, sameVersionFound

	# Similar to fnmatch.filter, but [range] is not supported as it's useless for this purpose
	# Moreover, fnmatch.filter breaks when the pattern contains [Group tag], which is very common
	# It parses the pattern and converts it to regex, then use regex to match filenames
	# No, don't attempt to reinvent the wheel and write your own matching algo
	def patternMatching(filenames, pattern):
		import re

		matchingFname = []

		if not ('*' in pattern or  '?' in pattern):
			return []

		# Basically replaces "?" with ".", "*" with "(.*)", and then escapes all special characters
		# Finally, locks the end of pattern. pattern should be a unicode string, not byte string
		def convertPatternToRegex(pattern):
			specialChars = '.^$*+?{}, \\[]|():=#!<'
			regex = ''

			for i in range(len(pattern)):
				char = pattern[i]
				if char == '?':
					regex += '.'
				elif char == '*':
					regex += '(.*)'
				else:
					# escape stuff
					if char in specialChars:
						regex += '\\'
					regex += char
					if i == len(pattern) - 1: # end of pattern. Fixed a bug that made pattern blablah*.mkv match blablah.mkv.pass
						regex += '$'
			return regex

		regPattern = convertPatternToRegex(pattern)
		if debug:
			print(regPattern)

		# Ignore case if it's win32
		if win32:
			regObject = re.compile(regPattern, re.IGNORECASE)
		else:
			regObject = re.compile(regPattern)

		for fname in filenames:
			match = regObject.match(fname)
			if match:
				matchingFname.append(fname)

		if debug:
			print(matchingFname)

		return matchingFname

	# Return value: (Found filename / None if not found, Did the pattern work?)
	# It reads the base folder's content and returns the first one matching the input pattern
	# If none matches, it selects candidates based on their extentions and verifies their format
	# The first valid one is chosen as usual
	# Currently:
	# inputType: 1 = video, 2 = subtitles, 3 = chapters
	# Chapters: .txt and its content starts with 'CHAPTER'; or .xml and '<?xml'
	# Subtitles: .ass and '[Script Info]'
	# Video: ext the same as pattern, .mp4, .mkv. Format verification hasn't been implenented yet.
	def searchForInputs(baseFolder, pattern, inputType):
		import sys, os, fnmatch, codecs

		for (dirpath, dirnames, filenames) in os.walk(baseFolder):

			filenames1 = patternMatching(filenames, pattern)
			if len(filenames1) > 0:
				return filenames1[0], True

			if inputType == 3: # chapters
				filenames2 = fnmatch.filter(filenames, '*.txt') + fnmatch.filter(filenames, '*.xml') + fnmatch.filter(filenames, '*.TXT') + fnmatch.filter(filenames, '*.XML')
				for fname in filenames2:
					f = codecs.open(os.path.join(dirpath, fname), "r", "utf-8")
					content = f.readline()
					f.close()
					if fname.lower().endswith('.txt') and content.startswith(u'CHAPTER'):
						return fname, False
					elif fname.lower().endswith('.xml') and content.startswith(u'<?xml'):
						return fname, False
			elif inputType == 2: # subtitle
				filenames2 = fnmatch.filter(filenames, '*.ass') + fnmatch.filter(filenames, '*.ASS')
				for fname in filenames2:
					f = codecs.open(os.path.join(dirpath, fname), "r", "utf-8")
					content = f.readline()
					f.close()
					if fname.lower().endswith('.ass') and content.startswith(u'﻿[Script Info]'):
						return fname, False
			elif inputType == 1: # video
				namae, ext = os.path.splitext(pattern)
				# prefer file with the same ext as pattern
				# if valid ext should start with a dot
				if ext.startswith('.'):
					filenames3 = fnmatch.filter(filenames, '*' + ext)
				else:
					filenames3 = []
				filenames3 += fnmatch.filter(filenames, '*.mkv') + fnmatch.filter(filenames, '*.mp4')
				if len(filenames3) > 0:
					return filenames3[0], False
			break
		return None, False

	fillInInputs()
	printAndLog('Gathering inputs from folder "%s"...' % baseFolder)
	error = False
	warning = False
	searched = False

	if os.path.isfile(os.path.join(baseFolder, video)):
		printAndLog('Found video file: %s.' % video)
	else:
		result, pattern = searchForInputs(baseFolder, video, 1)
		if result == None:
			printAndLog('Video file not found.')
			error = True
		else:
			if not pattern:
				printAndLog('Video file "%s" not found, but found "%s".' % (video, result))
				searched = True
			else:
				printAndLog('Found video file: %s.' % result)
			video = result

	subtitles_new = []
	for i in range(len(subtitles)):
		fname, name, lang = subtitles[i]
		found = False
		if os.path.isfile(os.path.join(baseFolder, fname)):
			printAndLog('Found subtitle file #%d: %s.' % (i + 1, fname))
			found = True
		else:
			result, pattern = searchForInputs(baseFolder, fname, 2)
			if result == None:
				printAndLog('Subtitle file #%d "%s" not found.' % (i + 1, fname))
			else:
				if not pattern:
					printAndLog('Subtitle file #%d "%s" not found, but found "%s".' % (i + 1, fname, result))
					searched = True
				else:
					printAndLog('Found subtitle file #%d: %s.' % (i + 1, result))
				fname = result
				found = True
		if found:
			subtitles_new.append((fname, name, lang))
	if len(subtitles_new) > 0:
		subtitles = subtitles_new
	else:
		error = True

	if os.path.isfile(os.path.join(baseFolder, chapters)):
		printAndLog('Found chapter file: %s.' % chapters)
	else:
		result, pattern = searchForInputs(baseFolder, chapters, 3)
		if result == None:
			printAndLog('Chapter file not found.')
			warning = True
		else:
			if not pattern:
				printAndLog('Chapter file "%s" not found, but found "%s".' % (chapters, result))
				searched = True
			else:
				printAndLog('Found chapter file: %s.' % result)
			chapters = result

	# fonts. don't bother to verify them
	path = os.path.join(baseFolder, fonts)
	for (dirpath, dirnames, filenames) in os.walk(path):
		for fname in filenames:
			fontList.append(os.path.join(dirpath, fname))
			fontList_Name.append(fname)
	if len(fontList_Name) > 0:
		printAndLog('Found %d font file(s).' % len(fontList_Name))
		for name in fontList_Name:
			writeToLog('"' + name + '" ')
		writeToLog('\n')
	else:
		printAndLog('No font files found.')
		error = True

	# return an array of filename strings
	def searchForVers(baseFolder, wantedVer):
		for (dirpath, dirnames, filenames) in os.walk(baseFolder):
			if wantedVer != 1:
				if wantedVer < version:
					pattern = previousVersion.replace('$crc$', '*')
				else:
					pattern = output.replace('$crc$', '*')
			else:
				pattern = output_v1.replace('$crc$', '*')
			#printHacked('Version %d: %s' % (wantedVer, pattern))
			filenames2 = patternMatching(filenames, pattern)
			if len(filenames2) > 0:
				return filenames2
			break
		return ''
	# return the first matching one
	def searchForVer(baseFolder, wantedVer):
		filenames = searchForVers(baseFolder, wantedVer)
		if len(filenames) > 0:
			return filenames[0]
		else:
			return ''

	if version != 1:
		output = output_v2
	else:
		output = output_v1

	# previous version
	if plsCreatePatch_v2:# and version != 1:
		v1Filename = searchForVer(baseFolder, version - 1)
		if len(v1Filename) > 0:
			previousVersion = v1Filename
			previousVersionFound = True
			printAndLog('Found previous version: "%s".' % previousVersion)

	# same version
	if plsRemoveSameVersion:
		sameVersion = searchForVers(baseFolder, version)
		if sameVersion != '':
			sameVersionFound = True
			notice = 'Found same version: '
			for s in sameVersion:
				notice += '"%s" ' % s
			printAndLog(notice)

	if searched:
		printAndLog('Warning: Certain specified file(s) not found, but alternative(s) found. Please check if they are the correct ones.')

	if error:
		printAndLog('Error: Important input(s) not found. Job cancelled.\n')
		sys.exit(1)

	printAndLog(' ')

def generateMuxCmd():
	import os
	global muxParams

	muxParams = [mkvmergePath]
	printAndLog('Generating muxing command...')

	chapterFileExists = os.path.isfile(os.path.join(baseFolder, chapters))

	# output
	muxParams.append('-o')
	muxParams.append(os.path.join(baseFolder, output_tmp))

	# video
	tmp = ["--language", "0:%s" % video_Lang, "--track-name", "0:%s" % video_Name, "--default-track", "0:yes", "--forced-track", "0:no", "--language", "1:%s" % audio_Lang, "--track-name", "1:%s" % audio_Name, "--default-track", "1:yes", "--forced-track", "1:no", "-a", "1", "-d", "0" ] # copy audio track 1 & video track 0 from premux
	tmp += ["-S", "-T", "-M", "--no-global-tags"] # remove subtitle -S, track specific tags -T, attachments -M tags --no-global-tags
	if chapterFileExists:
		tmp.append("--no-chapters") # and chapters if we got chapters
	muxParams = muxParams + tmp
	muxParams.append(os.path.join(baseFolder, video))

	# subtitles
	for i in range(len(subtitles)):
		fname, name, lang = subtitles[i]
		muxParams += ["--language", "0:%s" % lang, "--track-name", "0:%s" % name]
		if i == 0:
			muxParams += ["--default-track", "0:yes"]
		muxParams += ["--forced-track", "0:no", "--compression", "0:zlib", "-s", "0"]
		muxParams += ["-D", "-A", "-T", "--no-global-tags", "--no-chapters"] # don't remove subtitle or attachments
		muxParams.append(os.path.join(baseFolder, fname))

	# track order
	# track 0 (video) from file #0 (premux) > track 1 (audio) > track 0 from file #1 (subtitle) > file #2 > file 3 > file #4
	# not really important as long as input files are added in a fixed order like this
	muxParams.append("--track-order")
	muxParams.append("0:0,0:1,1:0,2:0,3:0,4:0")

	# fonts
	for i in range(len(fontList)):
		tmp = ["--attachment-mime-type", "application/x-truetype-font", "--attachment-name"]
		muxParams = muxParams + tmp
		muxParams.append(fontList_Name[i])
		muxParams.append("--attach-file")
		muxParams.append(fontList[i])

	# video title
	muxParams.append("--title")
	muxParams.append(title)

	# chapters
	if chapterFileExists:
		muxParams.append("--chapters")
		muxParams.append(os.path.join(baseFolder, chapters))

	writeToLog3(muxParams)

# executes given task and return console output, return code and error message if any
def executeTask(params, taskName = ''):
	import subprocess, sys
	if taskName != '':
		printAndLog('Executing task "%s"...' % taskName)

	execOutput = ''
	returnCode = 0
	error = False
	writeToLog3(params)
	try:
		execOutput = subprocess.check_output(params)
	except subprocess.CalledProcessError as e:
		execOutput = e.output
		returnCode = e.returncode
		error = True
	if sys.stdout.encoding != None: # It's None when debugging in Sublime Text
		execOutput = execOutput.decode(sys.stdout.encoding)

	return execOutput, returnCode, error

def premuxCleanup():
	import shutil, os
	global plsRemoveSameVersion, sameVersionFound, sameVersion

	# sameVersion is an array of filename string
	if plsRemoveSameVersion and sameVersionFound:
		for s in sameVersion:
			victim = os.path.join(baseFolder, s)
			#print(victim)
			try:
				os.remove(victim)
			except:
				doNothing = 1

def addCrc32():
	import shutil, os
	global output

	# Opens the file in binary reading mode, reads data block by block and updates crc32 hash
	# The final crc32 got by hashing block by block is the same as hashing the whole file at once
	# Same for md4, md5, sha-1, etc.
	# Python 2.x might return negative crc32. Just add 2^32 to it in that case.
	# Comfirmed correct by hashing hundreds of files
	def getCrc32(fileName):
		import zlib, sys

		fileSize = os.path.getsize(fileName)
		blockSize = 2 * 1024 * 1024
		crc32 = 0

		try:
			fd = open(fileName, 'rb')
			while True:
				buffer = fd.read(blockSize)
				if len(buffer) == 0: # EOF or file empty. return hash
					fd.close()
					if python2 and crc32 < 0:
						crc32 += 2 ** 32
					return '%08X' % crc32, False
				crc32 = zlib.crc32(buffer, crc32)

		except Exception as e:
			if python2:
				error = unicode(e)
			else:
				error = str(e)
			return 0, error

	oldPath = os.path.join(baseFolder, output_tmp)

	if version == 1:
		newName = os.path.join(baseFolder, output)
	else:
		newName = os.path.join(baseFolder, output_v2)

	if plsAddCrc:
		hashS, error = getCrc32(oldPath)
		newName = newName.replace('$crc$', hashS)

	try:
		shutil.move(oldPath, newName)
		output = newName
	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		printAndLog("Couldn't added CRC-32: %s" % error)
		doNothing = 1

# Note about EOL: win32 uses \r\n, Linux/Unix/recent version of Mac OS uses \n, and old Mac uses \r.
# \n works for all platforms, but it might be funny if a win32 user tries to open it with a dumb editor like Notepad
# codecs.* keeps EOL intact, so as long as template files are in correct EOL, output files will be fine.
#
# Note about patches:
# xdelta3 typically saves paths of source/target files you give it. If you have a vcdiff file called changes.vcdiff
# and you run "xdelta3 -d changes.vcdiff" (no source/target specified), xdelta3 will use the filenames stored in changes.vcdiff.
# In early versions, it only saved filenames, no paths. Then, someone asked the author (politely) to keep full paths, so he did.
# See http://code.google.com/p/xdelta/issues/detail?id=38. He never marked it as done, though.
# Now you might see some patches with full paths inside, and ofc, you can't just do like above. You must type the full cmd line.
# "xdelta -d changes.vcdiff source.file target.file". To deal with this, I use paramenter "-A=target.file//source.file/"
# to set the application specific header in output vcdiff file to filenames only, no paths. Very few people know about this.
# You can put whatever funny things in that header, btw; output vcdiffs are still valid according to the standard (see rfc3284).
# Well, imo, it's OK to have full paths in vcdiff. It's just some people think they're better than the rest think the opposite.
#
# For pure ASCII filenames, patches should work fine, cross-platform. For non-ASCII filenames, well, they might not.
# You can put filenames in the script and use the full form of cmd line, but if the interpreter (e.g. MS command prompt)
# can't be into non-ascii encoding, you're done. Fortunately, sh, shell, dash, etc. in Linux/Unix/Mac can read UTF-8 just fine.
# The big problem is Windows, as usual - it's Microsoft after all.
# As said above, xdelta3 saves filenames, so you can use the short form. Looks good? It does *look* good, but the real life is
# not that simple. xdelta3 doesn't store and load filenames using the same encoding across all platforms: in Windows, it uses
# UTF-16 (wide char); in Unix/Linux, it uses UTF-8; in Mac, it might be UTF-8, too--I don't have Mac. This is a mess, really.
# Patches created on Unix won't work on Windows, and vise versa.
# However, I came with a few "solutions":
# - Encode the script in UTF-8 without BOM, and put "chcp 65001" at the beginning. This asks the command prompt to switch to
# UTF-8 encoding, and so, it reads UTF-8 encoded file fine. However, code page 65001 is buggy--even MS developers recommend
# against it; I have no idea if it works on many versions of Windows. Moreover, according to my own tests, calling xdelta3 with
# non-ascii inputs from an utf-8 batch script doesn't work: xdelta3 doesn't know how to decode the paramenters. However, renaming
# files works. So you can rename the source file if its name contains non-ascii chars; tell xdelta3 to output to a file with
# temporary, pure ascii name, and rename it later. It's what I'm using.
# - Alternative, make a Python script to apply. It's Python, so everything can be done nicely. Most Linux/Unix/Mac installation
# should have Python installed, so it's fine. On the other hand, most Windows ones don't. So bad.
# You can just throw 9001 scripts in and tell users to try until it works ┐(´～`；)┌
# Side note: thinking that "xdelta3 -d changes.vcdiff" is sufficient is simply naive, overwhelmingly naive.
def createPatch():
	import os, codecs, shutil

	forceNonAsciiMode = False

	# %^& must be escaped. \/<>"*:?| are forbidden in win32 filenames. []()!=,;`' work, so not needed
	def escapeStringForBatch(text):
		result = u''
		for char in text:
			if char == u'%':
				result += u'%%'
			elif char == u'&':
				result += u'^&'
			elif char == u'^':
				result += u'^^'
			else:
				result += char
		return result

	# single quotes are used, so the only character needing quoting is the single quote itself
	def escapseStringForBash(text):
		return text.replace("'", "'\"'\"'")

	def generateApplyScripts(outputFolder, sourceFile, targetFile):
		# As a side note, as long as the template apply_patch_* files have the correct EOL, the output files will also do. 
		# In current code, to be precise. I forgot what works and what doesn't.
		# Linux/Mac bash scripts can be UTF-8. Should work fine in recent distros for both pure ascii and non-ascii source/target.
		applyScripts = ['apply_patch_linux.sh', 'apply_patch_mac.command']
		for s in applyScripts:
			src = os.path.join(repo, s)
			targ = os.path.join(outputFolder, s)
			if os.path.isfile(src):
				f = codecs.open(src, "r", "utf-8")
				f2 = codecs.open(targ, 'w', 'utf-8')
				content = f.read()
				f.close()
				content = content.replace(u'&sourcefile&', escapseStringForBash(sourceFile)).replace(u'&targetfile&', escapseStringForBash(targetFile))
				f2.write(content)
				f2.close()

		# how_to_apply_this_patch.txt goes here, too
		applyScripts = ['how_to_apply_this_patch.txt']
		for s in applyScripts:
			src = os.path.join(repo, s)
			targ = os.path.join(outputFolder, s)
			if os.path.isfile(src):
				f = codecs.open(src, "r", "utf-8")
				f2 = codecs.open(targ, 'w', 'utf-8')
				content = f.read()
				f.close()
				content = content.replace(u'&sourcefile&', sourceFile).replace(u'&targetfile&', targetFile)
				f2.write(content)
				f2.close()

		# Windows script is a pain
		src = os.path.join(repo, 'apply_patch_windows.bat')
		targ = os.path.join(outputFolder, 'apply_patch_windows.bat')
		if os.path.isfile(src):
			f = codecs.open(src, "r", "utf-8")
			f2 = codecs.open(targ, 'w', 'utf-8')
			content = f.read()
			f.close()
			content = content.replace(u'&sourcefile&', escapeStringForBatch(sourceFile)).replace(u'&targetfile&', escapeStringForBatch(targetFile))
			if not (isPureAscii(sourceFile)) or forceNonAsciiMode:
				content = content.replace(u'set movesourcefile=0', u'set movesourcefile=1')
			if not (isPureAscii(targetFile)) or forceNonAsciiMode:
				content = content.replace(u'set movetargetfile=0', u'set movetargetfile=1')
			if isPureAscii(sourceFile) and isPureAscii(targetFile) and not forceNonAsciiMode:
				content = content.replace('chcp 65001', '') # don't switch to utf-8 code page in pure ascii mode
			f2.write(content)
			f2.close()

		# These alternative scripts only need copying as is
		applyScripts = ['apply_patch_linux_alternative.sh', 'apply_patch_mac_alternative.command', 'apply_patch_windows_alternative.bat']
		for s in applyScripts:
			src = os.path.join(repo, s)
			targ = os.path.join(outputFolder, s)
			if os.path.isfile(src):
				shutil.copy2(src, targ)

		binaries = ['xdelta3', 'xdelta3.exe', 'xdelta3.x86_64', 'xdelta3_mac']

		for b in binaries:
			src = os.path.join(repo, b)
			targ = os.path.join(outputFolder, b)
			shutil.copy2(src, targ)

	# See the wall of text above
	def createPatchSub(outputFolder, sourceFile, targetFile):
		def swap(a, b):
			return b, a

		if os.path.isdir(outputFolder):
			# try to clear the content of the folder if it exists
			for root, dirs, files in os.walk(outputFolder):
				for f in files:
					try:
						os.unlink(os.path.join(root, f))
					except:
						doNothing = 1
				for d in dirs:
					try:
						shutil.rmtree(os.path.join(root, d))
					except:
						doNothing = 1
		else:
			# or create it if it doesn't
			error = ''
			for n in range(10):
				try:
					os.makedirs(outputFolder)
					break
				except Exception as e:
					if python2:
						error = unicode(e)
					else:
						error = str(e)
					#print(error)
			if not os.path.isdir(outputFolder):
				print("Couldn't created folder '%s': %s" % (outputFolder, error))

		sourceFolder, sourceFileName = os.path.split(sourceFile)
		targetFolder, targetFileName = os.path.split(targetFile)

		xparams = [xdelta3Path]
		if nonAsciiParamsWorking:
			xparams.append('-A=%s//%s/' % (targetFileName, sourceFileName))
		else:
			xparams.append('-A=%s//%s/' % (removeNonAscii(targetFileName), removeNonAscii(sourceFileName))) # will make alternative scripts not working

		xparams += ['-D', '-R', '-f', '-e', '-s']


		# to deal with problem when xdelta3 can't open the file we give it because incorrect paramenter encoding
		# we temporarily rename it to something and rename it back later. Only needed in win32 (for now) or when not nonAsciiParamsWorking.
		# still breaks if the folder itself contains non-ascii chars
		sourceFileMoved = False
		targetFileMoved = False
		sourceFileTmp = os.path.join(sourceFolder, 'sourceFileTmp')
		targetFileTmp = os.path.join(targetFolder, 'targetFileTmp')
		if not isPureAscii(sourceFile) and (not nonAsciiParamsWorking or win32):
			try:
				shutil.move(sourceFile, sourceFileTmp)
				sourceFileMoved = True
				writeToLog2('Moved sourceFile to %s' % sourceFileTmp)
				sourceFileTmp, sourceFile = swap(sourceFileTmp, sourceFile)
			except:
				doNothing = 1
				writeToLog2("Couldn't moved sourceFile!")
		if not isPureAscii(targetFile) and (not nonAsciiParamsWorking or win32):
			try:
				shutil.move(targetFile, targetFileTmp)
				targetFileMoved = True
				writeToLog2('Moved targetFile to %s' % targetFileTmp)
				targetFileTmp, targetFile = swap(targetFileTmp, targetFile)
			except:
				doNothing = 1
				writeToLog2("Couldn't move targetFile!")

		xparams.append(sourceFile)
		xparams.append(targetFile)
		xparams.append(os.path.join(outputFolder, 'changes.vcdiff'))

		log, returnCode, error = executeTask(xparams)

		# move them back
		if sourceFileMoved:
			try:
				sourceFileTmp, sourceFile = swap(sourceFileTmp, sourceFile)
				shutil.move(sourceFileTmp, sourceFile)
				writeToLog2('Moved sourceFile back to %s' % sourceFile)
			except:
				doNothing = 1
				writeToLog2("Couldn't move sourceFile back!")

		if targetFileMoved:
			try:
				targetFileTmp, targetFile = swap(targetFileTmp, targetFile)
				shutil.move(targetFileTmp, targetFile)
				writeToLog2('Moved targetFile back to %s' % targetFile)
			except:
				doNothing = 1
				writeToLog2("Couldn't move targetFile back!")


		generateApplyScripts(outputFolder, sourceFileName, targetFileName)
		# return True if error occurs, and False if it works
		if not error:
			return False
		else:
			printAndLog(log)
			return True

	global patchv2_Created, patchMux_Created, patchUndoMux_Created
	patchv2_Created = False
	patchMux_Created = False
	patchUndoMux_Created = False

	sourceFile = os.path.join(baseFolder, video)
	oldVersion = os.path.join(baseFolder, previousVersion)

	if len(output) > 1 and len(patchMux_FolderName) > 0 and plsCreatePatch_Mux:
		outdir = os.path.join(baseFolder, patchMux_FolderName)
		error = createPatchSub(outdir, sourceFile, output)
		if not error:
			patchMux_Created = True

	if len(output) > 1 and len(patchUndoMux_FolderName) > 0 and plsCreatePatch_UndoMux:
		outdir = os.path.join(baseFolder, patchUndoMux_FolderName)
		error = createPatchSub(outdir, output, sourceFile)
		if not error:
			patchUndoMux_Created = True

	if len(output) > 1 and len(patchv2_FolderName) > 0 and plsCreatePatch_v2 and previousVersionFound:
		outdir = os.path.join(baseFolder, patchv2_FolderName)
		error = createPatchSub(outdir, oldVersion, output)
		if not error:
			patchv2_Created = True

def packFiles():
	import os

	if not plsPackStuff: return

	def packFilesSub(baseFolder, filenames, archive):
		# 7z [options] command input(s)
		zparams = [sevenzipPath, '-aoa', '-mx7', 'a']
		zoutput = os.path.join(baseFolder, archive)

		# don't need to check if fname is valid. 7z will just ignore invalid inputs
		zparams.append(zoutput)
		for fname in filenames:
			zparams.append(os.path.join(baseFolder, fname))

		# attempt to delete output file to prevent 7z from adding files to it
		for i in range(10): # give it 10 chances
			try:
				os.remove(zoutput)
				break
			except:
				doNothing = 1

		executeTask(zparams)

	if len(subtitleArchive) > 0:
		subs = [fonts]
		for s in subtitles:
			fname, name, lang = s
			subs.append(fname)
		packFilesSub(baseFolder, subs, subtitleArchive)
	if len(patchMuxArchive) > 0 and patchMux_Created:
		packFilesSub(baseFolder, [patchMux_FolderName], patchMuxArchive)
	if len(patchv2Archive) > 0 and version > 1 and patchv2_Created:
		packFilesSub(baseFolder, [patchv2_FolderName], patchv2Archive)
	if len(patchAllArchive) > 0 and (patchv2_Created or patchMux_Created or patchUndoMux_Created):
		fileList = []
		# only add to fileList if that type of patch is enabled as the folder might already exist
		if patchv2_Created: fileList.append(patchv2_FolderName)
		if patchMux_Created: fileList.append(patchMux_FolderName)
		if patchUndoMux_Created: fileList.append(patchUndoMux_FolderName)
		packFilesSub(baseFolder, fileList, patchAllArchive)

# ED2K is a pain because of its fixed-size chunk
# when multi-thread is emplemented, this shouldn't be a problem since we can use ED2K chunk size as block size
# without causing performance loss
def hasher(fileName):
	import math, os, sys, hashlib, zlib

	fileSize = os.path.getsize(fileName)
	blockSize = 2 * 1024 * 1024

	enableCrc = True
	enableMd4 = False
	enableMd5 = True
	enableSha1 = True
	enableSha256 = True
	enableSha512 = True
	enableEd2k = True

	crc32 = 0
	md4 = hashlib.new('md4')
	md5 = hashlib.md5()
	sha1 = hashlib.sha1()
	sha256 = hashlib.sha256()
	sha512 = hashlib.sha512()

	ed2kHash = bytearray()
	ed2kChunkSize = 9728000
	ed2kChunkHash = hashlib.new('md4')
	ed2kChunkRemain = ed2kChunkSize

	try:
		fd = open(fileName, 'rb')
		while True:
			buffer = fd.read(blockSize)
			if len(buffer) == 0: # EOF or file empty. return hashes
				fd.close()

				if ed2kChunkRemain < ed2kChunkSize:
					ed2kHash += ed2kChunkHash.digest()
				ed2kEndHash = hashlib.new('md4')
				if (fileSize % ed2kChunkSize == 0):
					ed2kHash += ed2kEndHash.digest()
				if fileSize >= ed2kChunkSize:
					ed2kEndHash.update(ed2kHash)
					ed2kHash = ed2kEndHash.hexdigest()
				elif fileSize > 0:
					ed2kHash = ed2kChunkHash.hexdigest()
				else:
					ed2kHash = ed2kEndHash.hexdigest()

				if python2 and crc32 < 0:
					crc32 += 2 ** 32
				return '%08X' % crc32, md4.hexdigest().upper(), md5.hexdigest().upper(), sha1.hexdigest().upper(), sha256.hexdigest().upper(), sha512.hexdigest().upper(), ed2kHash.upper(), False

			if enableCrc: crc32 = zlib.crc32(buffer, crc32)
			if enableMd4: md4.update(buffer)
			if enableMd5: md5.update(buffer)
			if enableSha1: sha1.update(buffer)
			if enableSha256: sha256.update(buffer)
			if enableSha512: sha512.update(buffer)

			if enableEd2k:
				dataLen = len(buffer)
				if dataLen < ed2kChunkRemain:
					ed2kChunkHash.update(buffer)
					ed2kChunkRemain -= dataLen
				elif dataLen == ed2kChunkRemain:
					ed2kChunkHash.update(buffer)
					ed2kHash += ed2kChunkHash.digest()
					ed2kChunkRemain = ed2kChunkSize
					ed2kChunkHash = hashlib.new('md4')
				else:
					ed2kChunkHash.update(buffer[0:ed2kChunkRemain])
					ed2kHash += ed2kChunkHash.digest()
					ed2kChunkHash = hashlib.new('md4')
					dataRemain = dataLen - ed2kChunkRemain
					chunkHashRepeat = int(math.floor(dataRemain / ed2kChunkSize))
					for i in range(chunkHashRepeat):
						ed2kChunkHash.update(buffer[ed2kChunkRemain + i * ed2kChunkSize : ed2kChunkRemain + i * ed2kChunkSize + ed2kChunkSize])
						ed2kHash += ed2kChunkHash.digest()
						ed2kChunkHash = hashlib.new('md4')
						hashCount += 1
					dataRemain = dataRemain - chunkHashRepeat * ed2kChunkSize
					ed2kChunkHash.update(buffer[-dataRemain:])
					ed2kChunkRemain = ed2kChunkSize - dataRemain

	except Exception as e:
		if python2:
			error = unicode(e)
		else:
			error = str(e)
		return '00000000', '', '', '', '', '', '', error

def printFileInfo():
	import os

	def byteToHumanSize(size):
		if size >= 1000 * 1024 * 1024:
			return '%0.3f GiB' % (size / (1024 ** 3))
		elif size >= 1000 * 1024:
			return '%0.3f MiB' % (size / 1024 ** 2)
		elif size >= 1000:
			return '%0.3f KiB' % (size / 1024)
		else:
			return '%s bytes' % size

	fileSize = os.path.getsize(output)
	dummy, name = os.path.split(output)
	crc32, md4, md5, sha1, sha256, sha512, ed2k, error = hasher(output)

	if error == False:
		printAndLog('Filename: %s' % name)
		printAndLog('Size: %s (%d bytes)' % (byteToHumanSize(fileSize), fileSize))
		printAndLog('CRC-32: %s' % crc32)
		printAndLog('MD5: %s' % md5)
		printAndLog('SHA-1: %s' % sha1)
		printAndLog('SHA-256: %s' % sha256)
		printAndLog('SHA-512: %s' % sha512)
		printAndLog('ED2K: %s' % ed2k)
	else:
		printAndLog(error)

# Calculate CPU time and average CPU usage
def getCpuStat(cpuOld, cpuNew, timeOld, timeNew):
	import sys

	cpuTime = float(cpuNew) - float(cpuOld)
	elapsedTime = float(timeNew) - float(timeOld)

	if cpuTime == 0:
		cpuTime = 0.001
		elapsedTime = cpuTime
	if elapsedTime == 0:
		elapsedTime = cpuTime

	cpuPercentage = 100 * cpuTime / elapsedTime

	# Devide CPU percentage by the number of CPUs if it's Windows
	# to match reference system monitors (Windows Task Manager, etc.)
	if sys.platform == 'win32':
		cpuPercentage = cpuPercentage / cpuCount

	return cpuTime, cpuPercentage, elapsedTime

# Detects the number of CPUs on a system
def getCpuCount():
	from multiprocessing import cpu_count
	cpuCount = cpu_count()
	if debug:
		print('CPU count = %d' % cpuCount)
	return cpuCount

# Test unicode support
def checkUnicodeSupport():
	try:
		text = u'「いなり、こんこん、恋いろは。」番宣ＰＶ'.encode(sys.stdout.encoding)
	except:
		return False
	return True

def initStuff():
	import sys
	global defaultTimer, terminalSupportUnicode, cpuCount, logFileName, python2, win32, nonAsciiParamsWorking, initialized

	initialized = True

	# if not logInAppFolder:
	# 	logFileName = os.path.join(baseFolder, logFileName)

	writeToLog2('------------------------------------------------------------------------------------------------------')
	writeToLog2('\nInitializing new session...\n')
	writeToLog2(preinitLog)
	writeToLog2('Searching for required applications...')

	foundAll = detectPaths()

	if not foundAll:
		printAndLog('Error: Not all required applications found.')
		if mkvmergePath == None:
			printAndLog('mkvmerge not found')
		else:
			writeToLog2('Found mkvmerge: %s' % mkvmergePath)
		if sevenzipPath == None:
			printAndLog('7z not found')
		else:
			writeToLog2('Found 7-zip: %s' % sevenzipPath)
		if xdelta3Path == None:
			printAndLog('xdelta3 not found')
		else:
			writeToLog2('Found xdelta3: %s' % mkvmergePath)
		sys.exit(1) # applications not found
	else:
		writeToLog2('Found mkvmerge: %s' % mkvmergePath)
		writeToLog2('Found 7-zip: %s' % sevenzipPath)
		writeToLog2('Found xdelta3: %s' % xdelta3Path)

	terminalSupportUnicode = checkUnicodeSupport()
	writeToLog2('Terminal supporting non-ASCII: %r' % terminalSupportUnicode)

	# Stats setup
	if sys.platform == 'win32':
	    # On Windows, the best timer is time.clock
	    defaultTimer = time.clock
	else:
	    # On most other platforms the best timer is time.time
	    defaultTimer = time.time

	cpuCount = getCpuCount()

	# python version
	if sys.version_info[0] < 3:
		python2 = True

	sVersion = 'Python version: %d.%d.%d\n' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
	if debug:
		printAndLog(sVersion)
	else:
		writeToLog2(sVersion)

	# platform
	if sys.platform == 'win32':
		win32 = True

	# test if non-ascii paramenters works
	try:
		tparams = [sevenzipPath, u'(✿◠‿◠)', u'「いなり、こんこん、恋いろは。」番宣ＰＶ']
		log, returnCode, error = executeTask(tparams)
		nonAsciiParamsWorking = True
	except (UnicodeEncodeError, UnicodeDecodeError):
		nonAsciiParamsWorking = False
	except:
		doNothing = 1

def checkSanity():
	doNothing = 1
	sane = True
	if not sane:
		printReadme()
		sys.exit(1)

def cleanUp():
	if logFile != None:
		logFile.close()

def printReadme():
	print(' ')
	print("%s v%s by %s" % (programName, version, author))
	print(' ')
	print("Sorry! Readme hasn't been written!")

# Arguments/paramenters and option files work as following:
# Args from sys.argv and option files are combined in ariving order.
# Options and their paramenters can be split into serveral parts.
# For example: python Auto-Muxer.py --episode 2 @option_file1 1 --basefolder @option_file2
# The last line of option_file1 is "--version"
# The first line of option_file2 is "F:\newlycomer\2013-fuyu\dunno\Pupa\$2ep$"
# parseArgs will combine them into --episode 2 [other options] --version 1 --basefolder "F:\newlycomer\2013-fuyu\dunno\Pupa\$2ep$" [other options]
# option file linked inside option file is also processed in the same way
# Finally, after everything is joined, parseArgsSub will parse them normally

def applyOptionFile(fname):
	parseArgsSub(parseOptionFile(fname))

def parseOptionFile(fname):
	import codecs, os

	if os.path.isfile(fname):
		f = codecs.open(fname, 'r', 'utf-8')
		args = []
		for line in f.readlines():
			line2 = line.strip(' \t\n\r\"')
			ll = len(line2)
			i = 0
			if ' ' in line2:
				# one option and its paramenter. more is forbidden
				while i < ll:
					if line2[i] == ' ':
						args.append(line2[0:i])
						if i < ll - 1:
							args.append(line2[i:].strip(' \t\n\r\"'))
						break
					i += 1
			else:
				# only one option in this line
				if not line2.startswith("@"):
					args.append(line2)
				else:
					args += parseOptionFile(line2[1:])
		#print(args)
		return args

def parseArgs():
	import sys, os

	args = []
	if len(sys.argv) > 1:
		for arg in sys.argv[1:]:
			if not arg.startswith("@"):
				args.append(toUnicodeStr(arg))
			else:
				args += parseOptionFile(arg[1:])

	parseArgsSub(args)
	writeToLog2("Input paramenters:")
	writeToLog3(args)

def parseArgsSub(args):
	global mkvmergePath, xdelta3Path, sevenzipPath
	global plsWriteLogs, logFileName
	global episode, version, groupTag, showName, batchEps, batchMode
	global baseFolder, subtitles, video, fonts, chapters, title, video_Name, video_Lang, audio_Name, audio_Lang, sub_Name, sub_Lang
	global output_v1, output_v2, output_tmp
	global patchv2_FolderName, patchMux_FolderName, patchUndoMux_FolderName
	global subtitleArchive, patchMuxArchive, patchv2Archive, patchAllArchive
	global plsAddCrc, plsCreatePatch_Mux, plsCreatePatch_UndoMux, plsCreatePatch_v2, plsPackStuff, plsRemoveSameVersion
	global dontMux, stopAfterMuxing, debug, verbose

	def parseInt(a, b):
		try:
			return int(args[i+1])
		except Exception as e:
			if python2:
				error = unicode(e)
			else:
				error = str(e)
			printAndLog("Can't parse option \"%s %s\": %s" % (a, b, error))
			return None

	argsCount = len(args)
	i = 0
	while i < argsCount:
		arg = args[i]
		argLen = len(arg)
		if argLen < 2:
			i += 1
			continue
		if arg.startswith('--') and argLen > 2:
			# parse -- long args
			arg = arg[2:].lower()
			# arg with value
			if arg == 'episode' and i < argsCount - 1:
				num = parseInt(arg, args[i+1])
				if num != None:
					episode = num
					i += 1
			elif arg == 'version' and i < argsCount - 1:
				num = parseInt(arg, args[i+1])
				if num != None:
					version = num
					i += 1
			elif arg == 'grouptag' and i < argsCount - 1:
				groupTag = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'showname' and i < argsCount - 1:
				showName = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'basefolder' and i < argsCount - 1:
				baseFolder = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'video' and i < argsCount - 1:
				video = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'fonts' and i < argsCount - 1:
				fonts = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'chapters' and i < argsCount - 1:
				chapters = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'title' and i < argsCount - 1:
				title = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'output_v1' and i < argsCount - 1:
				output_v1 = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'output_v2' and i < argsCount - 1:
				output_v2 = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'output_tmp' and i < argsCount - 1:
				output_tmp = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'title' and i < argsCount - 1:
				title = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'video_name' and i < argsCount - 1:
				video_Name = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'video_lang' and i < argsCount - 1:
				video_Lang = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'audio_name' and i < argsCount - 1:
				audio_Name = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'audio_lang' and i < argsCount - 1:
				audio_Lang = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'sub_name' and i < argsCount - 1:
				sub_Name = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'sub_lang' and i < argsCount - 1:
				sub_Lang = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'subtitle' and i < argsCount - 1:
				fname = toUnicodeStr(args[i+1])
				subtitles.append((fname, sub_Name, sub_Lang))
				i += 1
			elif arg == 'patchv2_foldername' and i < argsCount - 1:
				patchv2_FolderName = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'patchmux_foldername' and i < argsCount - 1:
				patchMux_FolderName = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'patchundomux_foldername' and i < argsCount - 1:
				patchUndoMux_FolderName = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'subtitlearchive' and i < argsCount - 1:
				subtitleArchive = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'patchmuxarchive' and i < argsCount - 1:
				patchMuxArchive = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'patchv2archive' and i < argsCount - 1:
				patchv2Archive = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'patchallarchive' and i < argsCount - 1:
				patchAllArchive = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'mkvmergepath' and i < argsCount - 1:
				mkvmergePath = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'xdelta3path' and i < argsCount - 1:
				xdelta3Path = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'sevenzippath' and i < argsCount - 1:
				sevenzipPath = toUnicodeStr(args[i+1])
				#print('sevenzipPath = %s' % sevenzipPath)
				i += 1
			elif arg == 'logfilename' and i < argsCount - 1:
				logFileName = toUnicodeStr(args[i+1])
				i += 1
			elif arg == 'batch' and i < argsCount - 1:
				batchMode = True
				eps = toUnicodeStr(args[i+1])
				i += 1
				tmp = eps.split('-')
				if len(tmp) > 1:
					start = int(tmp[0])
					end = int(tmp[1])
					for n in range(start, end + 1, 1):
						batchEps.append(n)
			# one without
			elif  arg == 'clear': # reset to "virgin" state
				video = u''
				subtitles = []
				fonts = u''
				groupTag = u''
				showname = u''
			elif  arg == 'plsaddcrc':
				plsAddCrc = True
			elif  arg == 'plscreatepatch_mux':
				plsCreatePatch_Mux = True
			elif  arg == 'plscreatepatch_undomux':
				plsCreatePatch_UndoMux = True
			elif  arg == 'plscreatepatch_v2':
				plsCreatePatch_v2 = True
			elif  arg == 'plspackstuff':
				plsPackStuff = True
			elif  arg == 'plsremovesameversion':
				plsRemoveSameVersion = True
			elif  arg == 'plswritelogs':
				plsWriteLogs = True
			elif  arg == 'dontmux':
				dontMux = True
			elif  arg == 'stopaftermuxing':
				stopAfterMuxing = True
			elif  arg == 'debug':
				debug = True
			elif  arg == 'verbose':
				verbose = True
			else:
				printAndLog('Unreconised paramenter: "%s"' % arg)

		elif arg.startswith('-'):
			# parse - short args
			arg = arg[1:].lower()
			if arg == 'patch':
				plsCreatePatch_v2 = True
				plsCreatePatch_Mux = True
				plsCreatePatch_UndoMux = True
			elif arg == 'crc':
				plsAddCrc = True
			elif arg == 'd':
				debug = True
			elif arg == 'v':
				verbose = True
			else:
				printAndLog('Unreconised paramenter: "%s"' % arg)
		else:
			printAndLog('Unreconised paramenter: "%s"' % arg)

		i += 1

	doNothing = 1

def toUnicodeStr(a):
	# TODO: do something
	return a

varsBackup = {}
def backupVars():
	global varsBackup, baseFolder, subtitles, video, fonts, chapters, title, output, output_v1, output_v2, previousVersion, patchv2_FolderName, patchMux_FolderName, patchUndoMux_FolderName, subtitleArchive, patchMuxArchive, patchv2Archive, patchAllArchive, fontList, fontList_Name, previousVersion, previousVersionFound, output, sameVersion, sameVersionFound
	varsBackup['baseFolder'] = baseFolder
	varsBackup['subtitles'] = subtitles
	varsBackup['video'] = video
	varsBackup['fonts'] = fonts
	varsBackup['chapters'] = chapters
	varsBackup['title'] = title
	varsBackup['output'] = output
	varsBackup['output_v1'] = output_v1
	varsBackup['output_v2'] = output_v2
	varsBackup['previousVersion'] = previousVersion
	varsBackup['patchv2_FolderName'] = patchv2_FolderName
	varsBackup['patchMux_FolderName'] = patchMux_FolderName
	varsBackup['patchUndoMux_FolderName'] = patchUndoMux_FolderName
	varsBackup['subtitleArchive'] = subtitleArchive
	varsBackup['patchMuxArchive'] = patchMuxArchive
	varsBackup['patchv2Archive'] = patchv2Archive
	varsBackup['patchAllArchive'] = patchAllArchive
	varsBackup['fontList'] = fontList
	varsBackup['fontList_Name'] = fontList_Name
	varsBackup['previousVersion'] = previousVersion
	varsBackup['previousVersionFound'] = previousVersionFound
	varsBackup['output'] = output
	varsBackup['sameVersion'] = sameVersion
	varsBackup['sameVersionFound'] = sameVersionFound

def restoreVars():	
	global varsBackup, baseFolder, subtitles, video, fonts, chapters, title, output, output_v1, output_v2, previousVersion, patchv2_FolderName, patchMux_FolderName, patchUndoMux_FolderName, subtitleArchive, patchMuxArchive, patchv2Archive, patchAllArchive, fontList, fontList_Name, previousVersion, previousVersionFound, output, sameVersion, sameVersionFound
	baseFolder = varsBackup['baseFolder']
	subtitles = varsBackup['subtitles']
	video = varsBackup['video']
	fonts = varsBackup['fonts']
	chapters = varsBackup['chapters']
	title = varsBackup['title']
	output = varsBackup['output']
	output_v1 = varsBackup['output_v1']
	output_v2 = varsBackup['output_v2']
	previousVersion = varsBackup['previousVersion']
	patchv2_FolderName = varsBackup['patchv2_FolderName']
	patchMux_FolderName = varsBackup['patchMux_FolderName']
	patchUndoMux_FolderName = varsBackup['patchUndoMux_FolderName']
	subtitleArchive = varsBackup['subtitleArchive']
	patchMuxArchive = varsBackup['patchMuxArchive']
	patchv2Archive = varsBackup['patchv2Archive']
	patchAllArchive = varsBackup['patchAllArchive']
	fontList = varsBackup['fontList']
	fontList_Name = varsBackup['fontList_Name']
	previousVersion = varsBackup['previousVersion']
	previousVersionFound = varsBackup['previousVersionFound']
	output = varsBackup['output']
	sameVersion = varsBackup['sameVersion']
	sameVersionFound = varsBackup['sameVersionFound']

def muxProcess():
	global dontmux, plsRemoveSameVersion, sameVersionFound, muxParams, stopAfterMuxing

	backupVars()

	getInputList()
	checkSanity()
	generateMuxCmd()

	if dontMux:
		return

	# run premuxing cleanup (same versions, etc.)
	if plsRemoveSameVersion and sameVersionFound:
		printAndLog('Removing same-version file(s)...')
		premuxCleanup()

	# Muxing
	startTime = defaultTimer()

	try:
		notice = 'Muxing episode %d version %d...' % (episode, version)
	except:
		notice = 'Muxing episode %s version %d' % (episode, version)
	printAndLog(notice)
	muxInfo, muxReturnCode, muxError = executeTask(muxParams)
	if muxError:
		printAndLog('Error occured!\n')
		printAndLog(muxInfo)

	endTime = defaultTimer()
	muxTime = endTime - startTime

	if stopAfterMuxing:
		printAndLog('\nStopped by user request.')
		sys.exit()

	# adding CRC-32
	printAndLog('Adding CRC-32...')
	startTime = defaultTimer()
	addCrc32()
	endTime = defaultTimer()
	crcTime = endTime - startTime

	# patches
	startTime = defaultTimer()
	printAndLog('Creating patches...')
	createPatch()
	endTime = defaultTimer()
	patchTime = endTime - startTime

	# packing
	startTime = defaultTimer()
	printAndLog('Packing subtitle and patches...')
	packFiles()
	endTime = defaultTimer()
	packTime = endTime - startTime

	# print file info
	startTime = defaultTimer()
	printAndLog('Getting file info...\n')
	printFileInfo()
	endTime = defaultTimer()
	infoTime = endTime - startTime

	printAndLog(' ') # new line.
	printAndLog('Muxing took %0.3f seconds.' % muxTime)
	printAndLog('Adding CRC-32 took %0.3f seconds.' % crcTime)
	printAndLog('Patching took %0.3f seconds.' % patchTime)
	printAndLog('Packing took %0.3f seconds.' % packTime)
	printAndLog('Getting info took %0.3f seconds.' % infoTime)
	printAndLog('\nTotal: %0.3f seconds.\n' % (muxTime + crcTime + patchTime + packTime + infoTime))

	restoreVars()

if testing:
	applyOptionFile('sample_option_file.txt')

parseArgs()
initStuff()

if batchMode:
	for i in batchEps:
		episode = i
		muxProcess()
else:
	muxProcess()

cleanUp()