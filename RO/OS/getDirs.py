#!/usr/local/bin/python
"""Get useful directories for Mac (X or Classic), unix
or modern versions of Windows. Defines:

PlatformName: one of 'mac', 'win' or 'unix'
(note that Mac includes both MacOS X and Carbon).

getPrefsDir():
	Return the user's preferences directory, if found, else None.
	
	Uses operating system calls, so should return the
	correct answer for any language or version of the OS.
	On English systems, presently returns:
	- MacOS X: ~/Library/Preferences (with ~ expanded)
	- Mac Classic: System Folder:Preferences
	- unix: The user's home directory
	- Windows: Windows\Application Support

getAppSuppDirs():
	Return one or more application support paths
	(starting with user and going to more widely shared),
	or [] if none found.
	
	Uses operating system calls, so should return the
	correct answer for any language or version of the OS.
	On English systems, presently returns:
	- MacOS X: [~/Library/Application Support,
		/Library/Application Support]
	- Mac Classic: probably [] but I'm not sure.
	- unix: [getPrefsDir()]
	- Windows: [getPrefsDir()]

plus additional routines as described below.

History:
2004-02-03 ROwen
2004-12-21 Improved main doc string. No code changes.
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
