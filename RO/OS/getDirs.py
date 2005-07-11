#!/usr/local/bin/python
"""Get useful directories for Mac (X or Classic), unix
or modern versions of Windows. Defines:

PlatformName: one of 'mac', 'win' or 'unix'
(note that Mac includes both MacOS X and Carbon).

getAppSuppDirs():
	Return two paths: the user's private and shared application support directory.
	
	If a directory does not exist, its path is set to None.
	
	A typical return on English system is:
	- MacOS X: [~/Library/Application Support, (with ~ expanded)
		/Library/Application Support]
	- Mac Classic: ?
	- unix: [getPrefsDir(), None]
	- Windows: [C:\Documents and Settings\<username>\Application Data,
		C:\Documents and Settings\All Users\Application Data]

getDocsDir():
	Return the path to the user's documents directory.

	Return None if the directory does not exist.
	
	A typical return on English system is:
	- MacOS X: ~/Documents (with ~ expanded)
	- Mac Classic: ?
	- unix: The user's home directory
	- Windows: C:\Documents and Settings\<username>\My Documents

getPrefsDir():
	Return the path to the user's preferences directory.

	Return None if the directory does not exist.
	
	A typical return on English system is:
	- MacOS X: ~/Library/Preferences (with ~ expanded)
	- Mac Classic: System Folder:Preferences
	- unix: The user's home directory
	- Windows: C:\Documents and Settings\<username>\Application Data

plus additional routines as described below.

History:
2004-02-03 ROwen
2004-12-21 Improved main doc string. No code changes.
2005-07-11 ROwen	Modified getAppSuppDirs to return None for nonexistent directories.
					Added getDocsDir.
"""
import os

PlatformName = None

def getHomeDir():
	"""Return the user's home directory, if known, else None.
	"""
	return os.environ.get('HOME')

try:
	# try Mac
	from getMacDirs import getAppSuppDirs, getDocsDir, getPrefsDir
	PlatformName = 'mac'
except ImportError:
	# try Windows
	try:
		from getWinDirs import getAppSuppDirs, getDocsDir, getPrefsDir
		PlatformName = 'win'
	except ImportError:
		# assume Unix
		PlatformName = 'unix'
		def getPrefsDir():
			return os.environ['HOME']
		def getAppSuppDirs():
			return [getPrefsDir(), None]
		def getDocsDir():
			return getPrefsDir()

def getPrefsPrefix():
	"""Return the usual prefix for the preferences file:
	'.' for unix, '' otherwise.
	"""
	global PlatformName
	if PlatformName == 'unix':
		return '.'
	return ''


if __name__ == '__main__':
	print 'PlatformName     = %r' % PlatformName
	print 'getHomeDir()     = %r' % getHomeDir()
	print 'getPrefsPrefix() = %r' % getPrefsPrefix()
	print
	print 'getAppSuppDirs = %r' % getAppSuppDirs()
	print 'getDocsDir()   = %r' % getDocsDir()
	print 'getPrefsDir()  = %r' % getPrefsDir()

