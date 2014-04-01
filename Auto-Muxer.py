#!/usr/bin/python
# encoding: utf-8

# TODO: 
# - verify video format when searching [low].
# - write a not-so-useless readme [medium]
# - support multiple subtitles [medium]
# - deal with patches for non-ascii filenames [medium]
# - option to detect and remove previous muxed file, patches, blablah [low]
# - handle character encoding mess (mostly for windows support--why do I even support windows?) [low]
# - support winrar [low]
# DONE:
# - writing logs [medium]
# - get ready to accept paramenters [high]
# - make searchForVer use v2 pattern [high]
# - support non-number episode [medium]

import sys, os, time

programName = "Auto Muxer"
programVer = "0.4"
programAuthor = "dreamer2908"

# specify these 3 if application not found error occurs
mkvmergePath = 'mkvmerge'
xdelta3Path = 'xdelta3'
sevenzipPath = '7z'
repo, dummy = os.path.split(sys.argv[0])
commonPaths = [r'/bin', r'/sbin', r'/usr/bin/', r'/usr/sbin/', r'/usr/local/bin/', r'/usr/local/sbin/', r'C:\Program Files (x86)\MKVToolNix', r'C:\Program Files\MKVToolNix', r'C:\Program Files\7-Zip',  r'C:\Program Files (x86)\7-Zip', repo]

dontMux = False
stopAfterMuxing = False

debug = False
verbose = True
plsWriteLogs = True
logFile = None
logFileName = 'muxing_log.txt'
logWriteCount = 0
logInAppFolder = True

defaultTimer = None
cpuCount = 1
terminalSupportUnicode = False

# basic inputs
episode = 1
version = 1
groupTag = 'Hue'
showName = 'Pupa'
baseFolder = r'F:\newlycomer\2013-fuyu\dunno\Pupa\$2ep$'
baseFolder = r'/media/yumi/DATA/newlycomer/2013-fuyu/dunno/Pupa/$2ep$/'
subtitle = r"Pupa ? $2ep$.ass"
video = r"*premux*.mkv"
fonts = r"fonts" # the folder containing fonts inside base folder
chapters = r"Pupa - $2ep$.chapter?.txt"
title = r"Pupa - $2ep$"
output = r'[$tag$] $show$ - $2ep$ [$crc$].mkv'
output_v2 = r'[$tag$] $show$ - $2ep$v$ver$ [$crc$].mkv'
output_tmp = 'muxed.mkv'
previousVersion = r'[$tag$] $show$ - $2ep$v$lver$ [$crc$].mkv'
previousVersionFound = False

# track languages and names
video_Name = "H.264 720p"
video_Lang = "jpn"
audio_Name = "AAC LC 2.0"
audio_Lang = "jpn"
subtitle_Name = "Powered by Engrish(tm)"
subtitle_Lang = "eng"

patchv2_FolderName = 'patch_ep_$2ep$_v$lver$_to_v$ver$'
patchMux_FolderName = 'patch_ep_$2ep$_mux'
patchUndoMux_FolderName = 'patch_ep_$2ep$_undo_mux'
patchv2_Created = False
patchMux_Created = False
patchUndoMux_Created = False

subtitleArchive = '[Hue] Pupa - $2ep$ [sub].7z'
patchRawArchive = patchMux_FolderName + '.7z'
patchv2Archive = patchv2_FolderName + '.7z'
patchAllArchive = 'patch_ep_$2ep$_all.7z'

plsAddCrc = True
plsCreatePatch_Mux = True
plsCreatePatch_UndoMux = False
plsCreatePatch_v2 = True
plsPackStuff = True

fontList = []
fontList_Name = []
muxParams = []

# replace $2ep$, $1ver$ with real value
def fillInValue(text):
	import re

	specialChars = r'.^$*+?{}, \[]|():=#!<'
	reg_Ep = re.compile(r'\$(\d)ep\$')
	reg_Ver = re.compile(r'\$ver\$')
	reg_Lver = re.compile(r'\$lver\$')
	reg_Tag = re.compile(r'\$tag\$')
	reg_Show = re.compile(r'\$show\$')
	reg_Crc = re.compile(r'\$crc\$')
	regArray = [reg_Ep, reg_Show, reg_Ver, reg_Lver, reg_Tag, reg_Crc]

	def regRepl(matchOjb):
		# episode number
		if (matchOjb.re == reg_Ep):
			formatStr = '%0' + matchOjb.groups(1)[0] +'d'
			# just return variable episode if it's not a number
			try:
				return formatStr % episode
			except:
				return episode
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
	global baseFolder, subtitle, video, fonts, chapters, title, output, output_v2, previousVersion, patchv2_FolderName, patchMux_FolderName, patchUndoMux_FolderName, subtitleArchive, patchRawArchive, patchv2Archive, patchAllArchive
	baseFolder = fillInValue(baseFolder)  
	subtitle = fillInValue(subtitle)
	video = fillInValue(video)
	fonts = fillInValue(fonts)
	chapters = fillInValue(chapters)
	title = fillInValue(title)
	patchv2_FolderName = fillInValue(patchv2_FolderName)
	patchMux_FolderName = fillInValue(patchMux_FolderName)
	patchUndoMux_FolderName = fillInValue(patchUndoMux_FolderName)
	subtitleArchive = fillInValue(subtitleArchive)
	patchRawArchive = fillInValue(patchRawArchive)
	patchv2Archive = fillInValue(patchv2Archive)
	patchAllArchive = fillInValue(patchAllArchive)
	output = fillInValue(output)
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
				if fpath.endswith('.exe') or fpath.endswith('.bat') or fpath.endswith('.py') or fpath.endswith('.cmd'):
					return True
		return False

	def search_exec(binName, firstTry = None):
		if hasattr(firstTry, 'startswith'):
			abspath = os.path.abspath(firstTry)
			if is_exe(abspath):
				return abspath
		# for win32 compatibility
		if sys.platform == 'win32' and not (binName.endswith('.exe') or binName.endswith('.bat') or binName.endswith('.py') or binName.endswith('.cmd')):
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

def printAndLog(text):
	print(text)
	if plsWriteLogs:
		writeToLog2(text)

def writeToLog2(text):
	writeToLog(text + '\n')

# Open the file in append mode and write text to it
# File handle is kept open because re-opening the file 
# every single time something needs writing is a bad idea
# Flush write buffer every a while pls
def writeToLog(text):
	import codecs, sys, os
	global logFile, logWriteCount

	if not plsWriteLogs:
		return

	try:
		if logFile == None:
			logFile = codecs.open(logFileName, 'a', 'utf-8')
		logFile.write(text)
		logWriteCount += 1
		if logWriteCount > 9:
			logFile.flush()
			logWriteCount = 0
	except Exception as e:
		if sys.version_info[0] < 3:
			error = unicode(e)
		else:
			error = str(e)
		print("Error! Can't write to log file: %s" % error)

def getInputList():
	import sys, os
	global fontList, video, subtitle, chapters, previousVersion, previousVersionFound, output

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
		# Finally, locks the end of pattern
		# Note: Convert the pattern to unicode string first
		# This file is in utf-8, so you can just assume it
		def convertPatternToRegex(pattern):
			specialChars = '.^$*+?{}, \\[]|():=#!<'
			regex = ''

			if hasattr(pattern, 'decode'):
				pattern = pattern.decode('utf-8') 

			# parse pattern
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

	# TODO: make it use pattern specified in output_v2
	def searchForVer(baseFolder, wantedVer):
		for (dirpath, dirnames, filenames) in os.walk(baseFolder):
			if wantedVer > 1:
				pattern = previousVersion.replace('$crc$', '*')
			else:
				pattern = output.replace('$crc$', '*')
			filenames2 = patternMatching(filenames, pattern)
			if len(filenames2) > 0:
				return filenames2[0]
			break
		return ''

	printAndLog('Gathering inputs...')
	fillInInputs()
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

	if os.path.isfile(os.path.join(baseFolder, subtitle)):
		printAndLog('Found subtitle file: %s.' % subtitle)
	else:
		result, pattern = searchForInputs(baseFolder, subtitle, 2)
		if result == None:
			printAndLog('Subtitle file not found.')
			error = True
		else:
			if not pattern: 
				printAndLog('Subtitle file "%s" not found, but found "%s".' % (subtitle, result))
				searched = True
			else:
				printAndLog('Found subtitle file: %s.' % result)
			subtitle = result

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

	# fonts
	# don't bother to verify them
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

	# previous version
	if plsCreatePatch_v2 and version > 1:
		v1Filename = searchForVer(baseFolder, version - 1)
		output = output_v2
		if len(v1Filename) > 0:
			previousVersion = v1Filename
			previousVersionFound = True

	if previousVersionFound:
		printAndLog('Found previous version: %s.' % previousVersion)

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

	# subtitle
	tmp = ["--language", "0:%s" % subtitle_Lang, "--track-name", "0:%s" % subtitle_Name, "--default-track", "0:yes", "--forced-track", "0:no", "--compression", "0:zlib", "-s", "0"]
	tmp += ["-D", "-A", "-T", "--no-global-tags", "--no-chapters"] # don't remove subtitle or attachments
	muxParams = muxParams + tmp
	muxParams.append(os.path.join(baseFolder, subtitle))

	# track order
	muxParams.append("--track-order")
	muxParams.append("0:0,0:1,1:0") # track 0 (video) from file 0 (premux) > track 1 (audio) > track 0 from file 1 (subtitle)

	# fonts
	for i in range(len(fontList)):
		tmp = ["--attachment-mime-type", "application/x-truetype-font", "--attachment-name"]
		muxParams = muxParams + tmp
		muxParams.append(fontList_Name[i])
		muxParams.append("--attach-file")
		muxParams.append(fontList[i])

	# title
	muxParams.append("--title")
	muxParams.append(title)

	# chapters
	if chapterFileExists:
		muxParams.append("--chapters")
		muxParams.append(os.path.join(baseFolder, chapters))

	tmp = ''
	for p in muxParams:
		tmp += '"%s" ' % p
	writeToLog2(tmp)

# executes given task and return console output, return code and error message if any
def executeTask(params, taskName = ''):
	import subprocess, sys
	if taskName != '':
		printAndLog('Executing task "%s"...' % taskName)

	execOutput = ''
	returnCode = 0
	error = False
	try:
		execOutput = subprocess.check_output(params)
	except subprocess.CalledProcessError as e:
		execOutput = e.output
		returnCode = e.returncode
		error = True
	if sys.stdout.encoding != None: # It's None when debugging in Sublime Text
		execOutput = execOutput.decode(sys.stdout.encoding)

	return execOutput, returnCode, error

def addCrc32():
	import shutil, os
	global finalFile

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
					if sys.version_info[0] < 3 and crc32 < 0:
						crc32 += 2 ** 32
					return '%08X' % crc32, False
				crc32 = zlib.crc32(buffer, crc32)

		except Exception as e:
			if sys.version_info[0] < 3:
				error = unicode(e)
			else:
				error = str(e)
			return 0, error

	oldPath = os.path.join(baseFolder, output_tmp)
	hashS, error = getCrc32(oldPath)
	
	if version == 1:
		newName = os.path.join(baseFolder, output)
	else:
		newName = os.path.join(baseFolder, output_v2)
	newName = newName.replace('$crc$', hashS)

	try:
		shutil.move(oldPath, newName)
		finalFile = newName
	except:
		doNothing = 1

# Dear maintainer (probably myself), if you're working on this function, please spend some time on the EOL problem.
# Windows uses \r\n, Unix/Linux uses \n, and Mac OS uses \r for EOL. 
# If applying scripts doesn't use the correct EOL, they might NOT work at all.
# The base scripts bundled with AutoMuxer should use the correct EOL (I did it manually). 
# For some reasons beyond my current knowledge about Python, output scripts used the correct EOL, too.
# Weren't they supposed to use system EOL, which was Unix \n as I was running LinuxMint 16 XFCE edition x86_64?
# I tested this on Python 2.7.5 and 3.3.2; they gave identical results. Magic?!
# Updated: tested on Python 3.3.3 and Windows 7 x64. Also "magic".
# If you're also working on Yet Another xdelta-based Patch Creator, pls take care of this problem as well.
# As the time I was writing this, YAXBPC used Unix EOL for Mac OS script, and Linux script was out-of-date.
#
# One more thing to bother you: patches for files with non-ASCII name. 
# For pure ASCII filenames, patches work fine, and cross-platform. # For non-ASCII filenames, well, they don't. 
# In YAXBPC, I made simpler version of applying script for non-ASCII filenames.
# As you can (or can't) see, I use paramenter "-A" to set the application specific header in output vcdiff file.
# It should contain source and target filenames (and no path). If you run "xdelta3 -d changes.vcdiff" 
# (no source/target specified), xdelta3 will use the filenames stored in changes.vcdiff.
# Looks good? It does *look* good, but isn't actually good. xdelta3 doesn't store and load filenames 
# using the same encoding cross-platform. In Windows, it uses UTF-16 (wide char); in Unix/Linux, it uses UTF-8;
# I have no idea about Mac OS, but it might be another one. This is a mess, really.
# Patches created on Unix won't work on Windows, and blablah. However, I came with a few "solution": 
# - For Windows script, encode it in UTF-8 without BOM, and put "chcp 65001" at the beginning. 
# This will tell the command prompt to switch to UTF-8 encoding, and so, it reads UTF-8 file fine.
# You can just use the normal script for this. The downside is that code page 65001 is buggy; I have no idea
# if it works on multiply version of Windows.
# - For Linux/Mac OS, make a Python script to apply. It's Python, so everything can be done nicely. 
# Most distro should have Python installed, so it's fine. # On the other hand, most Windows installations 
# don't have Python installed. So bad. I haven't tested if UTF-8 shell scripts works yet.
# Maybe you can just throw 9001 scripts in and tell users to try until it works ┐(´～`；)┌
# Rewrite comments here while you're working pls
def createPatch():
	import os, codecs, shutil

	# Open pre-made applying scripts; replace '%basefile%' and '%patchedfile%';
	# and then save it to output folder
	# Copy xdelta3 binaries, too
	def generateApplyScripts(outputFolder, baseFile, patchedFile):

		applyScripts = ['apply_patch_linux.sh', 'apply_patch_mac.command', 'apply_patch_windows.bat']

		for s in applyScripts:
			base = os.path.join(repo, s)
			targ = os.path.join(outputFolder, s)
			if os.path.isfile(base):
				f = codecs.open(base, "r", "utf-8")
				f2 = codecs.open(targ, 'w', 'utf-8')
				content = f.read()
				f.close()
				content = content.replace(r'%basefile%', baseFile)
				content = content.replace(r'%patchedfile%', patchedFile)
				f2.write(content)
				f2.close()

		binaries = ['xdelta3', 'xdelta3.exe', 'xdelta3.x86_64']

		for b in binaries:
			source = os.path.join(repo, b)
			targ = os.path.join(outputFolder, b)
			shutil.copy2(source, targ)

	# See the wall of text above
	def createPatchSub(outputFolder, baseFile, patchedFile):
		try:
			shutil.rmtree(outputFolder, True)
			os.makedirs(outputFolder)
		except:
			doNothing = 1

		dummy, baseFileName = os.path.split(baseFile)
		dummy, patchedFileName = os.path.split(patchedFile)

		xparams = [xdelta3Path, '-A=%s//%s/' % (patchedFileName, baseFileName), '-D', '-R', '-f', '-e', '-s']
		xparams.append(baseFile)
		xparams.append(patchedFile)
		xparams.append(os.path.join(outputFolder, 'changes.vcdiff'))

		log, returnCode, error = executeTask(xparams)
		generateApplyScripts(outputFolder, baseFileName, patchedFileName)
		# return True if error occurs, and False if it works
		if not error:
			return False
		else:
			printAndLog(log)
			return True

	global patchv2_Created, patchMux_Created, patchUndoMux_Created

	baseFile = os.path.join(baseFolder, video)
	v1File = os.path.join(baseFolder, previousVersion)

	if len(finalFile) > 1 and len(patchMux_FolderName) > 0 and plsCreatePatch_Mux:
		outdir = os.path.join(baseFolder, patchMux_FolderName)
		error = createPatchSub(outdir, baseFile, finalFile)
		if not error:
			patchMux_Created = True

	if len(finalFile) > 1 and len(patchUndoMux_FolderName) > 0 and plsCreatePatch_UndoMux:
		outdir = os.path.join(baseFolder, patchUndoMux_FolderName)
		error = createPatchSub(outdir, finalFile, baseFile)
		if not error:
			patchUndoMux_Created = True

	if len(finalFile) > 1 and len(patchv2_FolderName) > 0 and plsCreatePatch_v2 and previousVersionFound:
		outdir = os.path.join(baseFolder, patchv2_FolderName)
		error = createPatchSub(outdir, v1File, finalFile)
		if not error:
			patchv2_Created = True

def packFiles():
	import os

	if not plsPackStuff: return

	def packFilesSub(baseFolder, filenames, archive):
		# 7z [options] command input(s)
		zparams = [sevenzipPath, '-aoa', '-mx7', 'a']
		zoutput = os.path.join(baseFolder, archive)
		zparams.append(zoutput)
		for fname in filenames:
			zparams.append(os.path.join(baseFolder, fname))
			# don't need to check if fname is valid. 7z will just ignore invalid inputs
		try:
			os.remove(zoutput) # attempt delete output file to prevent 7z from adding files to it
		except:
			doNothing = 1
		executeTask(zparams)

	if len(subtitleArchive) > 0:
		packFilesSub(baseFolder, [subtitle, fonts], subtitleArchive)
	if len(patchRawArchive) > 0 and patchMux_Created:
		packFilesSub(baseFolder, [patchMux_FolderName], patchRawArchive)
	if len(patchv2Archive) > 0 and version > 1 and patchv2_Created:
		packFilesSub(baseFolder, [patchv2_FolderName], patchv2Archive)
	if len(patchAllArchive) > 0 and (patchv2_Created or patchMux_Created or patchUndoMux_Created):
		fileList = []
		if patchv2_Created: fileList.append(patchv2_FolderName) # in case this patch is not enabled but folder already exists
		if patchMux_Created: fileList.append(patchMux_FolderName)
		if patchUndoMux_Created: fileList.append(patchUndoMux_FolderName)
		packFilesSub(baseFolder, fileList, patchAllArchive)

# ED2K is a pain because of its fixed-size chunk
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

				if sys.version_info[0] < 3 and crc32 < 0:
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
		if sys.version_info[0] < 3:
			error = unicode(e)
		else:
			error = str(e)
		return '00000000', '', '', '', '', '', '', error

def printFileInfo():
	import os

	fileSize = os.path.getsize(finalFile)
	dummy, name = os.path.split(finalFile)
	crc32, md4, md5, sha1, sha256, sha512, ed2k, error = hasher(finalFile)

	if error == False:
		printAndLog('Filename: %s' % name)
		printAndLog('Size: %0.1f MB (%d bytes)' % (fileSize / (1000 * 1000), fileSize))
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

def isPureAscii(text):
	for c in text:
		code = ord(c)
		if code > 127:
			return False
	return True

def initStuff():
	import sys
	global defaultTimer, terminalSupportUnicode, cpuCount, logFileName

	if not logInAppFolder:
		logFileName = os.path.join(baseFolder, logFileName)

	writeToLog2('\nInitializing new session...\n')
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

	sVersion = 'Python version: %d.%d.%d\n' % (sys.version_info[0], sys.version_info[1], sys.version_info[2])
	if debug:
		printAndLog(sVersion)
	else:
		writeToLog2(sVersion)

def cleanUp():
	if logFile != None:
		logFile.close()

initStuff()
getInputList()
generateMuxCmd()

if dontMux:
	sys.exit()

# Muxing
startTime = defaultTimer()

try:
	notice = 'Muxing episode %d version %d...' % (episode, version)
except:
	notice = 'Muxing %s version %d' % (episode, version)
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
if plsAddCrc:
	printAndLog('Adding CRC-32...')
	startTime = defaultTimer()	
	addCrc32()	
	endTime = defaultTimer()
	crcTime = endTime - startTime
else:
	finalFile = output
	crcTime = 0

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

cleanUp()