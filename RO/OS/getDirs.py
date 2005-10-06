#!/usr/local/bin/python
"""Get useful directories for Mac (X or Classic), unix
or modern versions of Windows. Defines:

PlatformName: one of 'mac', 'win' or 'unix'
(note that Mac includes both MacOS X and Carbon).

getAppDirs(inclNone = False):
	Return up to two paths: the user's private and shared application support directory.
	
	If a directory does not exist, its path is set to None.
	
	A typical return on English system with inclNone True is:
	- MacOS X: [~/Library/Application Support, (with ~ expanded)
		/Library/Application Support]
	- Mac Classic: ?
	- unix: [None, None] (use PATH to find applications!)
	- Windows: 	[None, C:\Program Files]


getAppSuppDirs(inclNone = False):
	Return up to two paths: the user's private and shared application support directory.
	
	If a directory does not exist, its path is set to None.
	
	A typical return on English system is:
	- MacOS X: [~/Library/Application Support, (with ~ expanded)
		/Library/Application Support]
	- Mac Classic: ?
	- unix: [The user's home directory, None]
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

getPrefsDirs(inclNone = False):
	Return up to two paths: the user's private and shared preferences directory.

	Return None if the directory does not exist.
	
	A typical return on English system is:
	- MacOS X: [~/Library/Preferences, /Library/Preferences] (with ~ expanded)
	- Mac Classic: [System Folder:Preferences, ?None?]
	- unix: [The user's home directory, None]
	- Windows: [C:\Documents and Settings\<username>\Application Data,
		C:\Documents and Settings\All Users\Application Data]

plus additional routines as described below.

History:
2004-02-03 ROwen
2004-12-21 Improved main doc string. No code changes.
2005-07-11 ROwen	Modified getAppSuppDirs to return None for nonexistent directories.
					Added getDocsDir.
2005-09-28 ROwen	Changed getPrefsDir to getPrefsDirs.
					Added getAppDirs.
2005-10-05 ROwen	Added inclNone argument to getXXXDirs functions.
					Documented getAppDirs.
					Improved test code.
2005-10-06 ROwen	Make sure unix getHomeDirs can never return [None]
					(which could happen on Windows with missing required modules).
"""
import os

PlatformName = None

def getHomeDir():
	"""Return the user's home directory, if known, else None.
	"""
	return os.environ.get('HOME')

try:
	# try Mac
	from getMacDirs import getAppDirs, getAppSuppDirs, getDocsDir, getPrefsDirs
	PlatformName = 'mac'
except ImportError:
	# try Windows
	try:
		from getWinDirs import getAppDirs, getAppSuppDirs, getDocsDir, getPrefsDirs
		PlatformName = 'win'
	except ImportError:
		# assume Unix
		PlatformName = 'unix'
		def getAppDirs(inclNone = False):
			# use PATH to find apps on unix
			if inclNone:
				return [None, None]
			else:
				return []
				
		def getAppSuppDirs(inclNone = False):
			return getPrefsDirs(inclNone = inclNone)

		def getDocsDir():
			return getHomeDir()

		def getPrefsDirs(inclNone = False):
			if inclNone:
				return [getHomeDir(), None]
			else:
				homeDir = getHomeDir()
				if homeDir != None:
					return [homeDir]
			return []

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
	for inclNone in (False, True):
		print 'getAppDirs(%s)     = %r' % (inclNone, getAppDirs(inclNone))
		print 'getAppSuppDirs(%s) = %r' % (inclNone, getAppSuppDirs(inclNone))
		print 'getPrefsDirs(%s)   = %r' % (inclNone, getPrefsDirs(inclNone))
	print 'getDocsDir()         = %r' % getDocsDir()

