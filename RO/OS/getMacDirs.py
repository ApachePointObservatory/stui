#!/usr/local/bin/python
"""Utilities for finding standard Mac directories.

History:
2004-02-04 ROwen
2004-02-12 ROwen	Modified to use fsref.as_pathname() instead of Carbon.File.pathname(fsref).
2005-07-11 ROwen	Modified getAppSuppDirs to return None for nonexistent directories.
					Removed doCreate argument from getAppSuppDirs, getDocsDir and getPrefsDir.
					Added getDocsDir.
2005-09-27 ROwen	Changed getPrefsDir to getPrefsDirs.
					Added getAppDirs.
					Refactored to use getMacUserDir and getMacUserSharedDirs.
"""
import Carbon.Folder, Carbon.Folders
import MacOS

def getStandardDir(domain, dirType, doCreate=False):
	"""Return a path to the specified standard directory or None if not found.
	
	The path is in unix notation for MacOS X native python
	and Mac colon notation for Carbon python,
	i.e. the form expected by the os.path module.
	
	Inputs:
	- domain: one of the domain constants found in Carbon.Folders,
		such as kUserDomain, kLocalDomain or kSystemDomain.
	- dirType: one of the type constants found in Carbon.Folders,
		such as kPreferencesFolderType or kTrashFolderType.
	- doCreate: try to create the directory if it does not exist?
	"""
	try:
		fsref = Carbon.Folder.FSFindFolder(domain, dirType, doCreate)
		return fsref.as_pathname()
	except MacOS.Error:
		return None

def getMacUserSharedDirs(dirType):
	"""Return the path to the user and shared folder of a particular type.
	The path will be None if the directory does not exist.
	
	Inputs:
	- dirType	one of the Carbon.Folders constants
	"""	
	retDirs = []
	for domain in Carbon.Folders.kUserDomain, Carbon.Folders.kLocalDomain:
		path = getStandardDir(
			domain = domain,
			dirType = dirType,
			doCreate = False,
		)
		retDirs.append(path)
	return retDirs
	kApplicationsFolderType

def getMacUserDir(dirType):
	"""Return the path to the user and shared folder of a particular type,
	or None if the directory does not exist.

	Inputs:
	- dirType	one of the Carbon.Folders constants
	"""	
	return getStandardDir(
		domain = Carbon.Folders.kUserDomain,
		dirType = dirType,
		doCreate = False,
	)

def getAppDirs():
	"""Return two paths: user's private and shared application directory.
	
	If a directory does not exist, its path is set to None.
	"""
	return getMacUserSharedDirs(Carbon.Folders.kApplicationsFolderType)
	
def getAppSuppDirs():
	"""Return two paths: the user's private and shared application support directory.
	
	If a directory does not exist, its path is set to None.
	"""
	return getMacUserSharedDirs(Carbon.Folders.kApplicationSupportFolderType)

def getDocsDir():
	"""Return the path to the user's documents directory.
	
	Return None if the directory does not exist.
	"""
	return getMacUserDir(Carbon.Folders.kDocumentsFolderType)

def getPrefsDir():
	"""Return the path to the user's preferences directory.

	Return None if the directory does not exist.
	"""
	return getMacUserDir(Carbon.Folders.kPreferencesFolderType)

def getPrefsDirs():
	"""Return two paths: the user's local and shared preferences directory.
	
	If a directory does not exist, its path is set to None.
	"""
	return getMacUserSharedDirs(Carbon.Folders.kPreferencesFolderType)
	

if __name__ == "__main__":
	print "Testing"
	print 'getAppSuppDirs = %r' % getAppSuppDirs()
	print 'getDocsDir()   = %r' % getDocsDir()
	print 'getPrefsDir()  = %r' % getPrefsDir()
