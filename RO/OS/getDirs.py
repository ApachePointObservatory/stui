#!/usr/local/bin/python
"""Get useful directories for Mac (X or Classic), unix
or modern versions of Windows. Defines:

PlatformName: one of 'mac', 'win' or 'unix'
(note that Mac includes both MacOS X and Carbon).

getPrefsDir():
	Return the user's preferences directory, if found, else None.
	
	For MacOS X this is often:
		~/Library/Preferences (with ~ expanded)
	For Mac Classic this is often:
		System Folder:Preferences
	For unix this is the user's home directory.
	For Windows this is often:
		Windows\Application Support

getAppSuppDirs():
	Return one or more application support paths
	(starting with user and going to more widely shared),
	or [] if none found.
	
	For MacOS X this may be:
		[~/Library/Application Support, /Library/Application Support]
	For Mac Classic this is probably [] but I'm not sure.
	for unix and Windows this is [getPreferencesDir()]

plus additional routines as described below.

History:
2004-02-03 ROwen
"""
import os

PlatformName = None

def getHomeDir():
	"""Return the user's home directory, if known, else None.
	"""
	return os.environ.get('HOME')

try:
	# try Mac
	from getMacDirs import getPrefsDir, getAppSuppDirs
	PlatformName = 'mac'
except ImportError:
	# try Windows
	try:
		from getWinDirs import getPrefsDir, getAppSuppDirs
		PlatformName = 'win'
	except ImportError:
		# assume Unix
		PlatformName = 'unix'
		def getPrefsDir():
			return os.environ['HOME']
		def getAppSuppDirs():
			return [getPrefsDir()]

def getPrefsPrefix():
	"""Return the usual prefix for the preferences file:
	'.' for unix, '' otherwise.
	"""
	global PlatformName
	if PlatformName == 'unix':
		return '.'
	return ''


if __name__ == '__main__':
	print 'PlatformName:  %r' % PlatformName
	print 'Home Dir:      %r' % getHomeDir()
	print 'Prefs Dir:     %r' % getPrefsDir()
	print 'Prefs Prefix   %r' % getPrefsPrefix()
	print 'App Supp Dirs: %r' % getAppSuppDirs()
