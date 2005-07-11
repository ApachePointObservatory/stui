#!/usr/local/bin/python
"""Utilities for finding standard Mac directories.

History:
2004-02-04 ROwen
2004-02-12 ROwen	Modified to use fsref.as_pathname() instead of Carbon.File.pathname(fsref).
2005-07-11 ROwen	Modified getAppSuppDirs to return None for nonexistent directories.
					Removed doCreate argument from getAppSuppDirs, getDocsDir and getPrefsDir.
					Added getDocsDir.
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

def getAppSuppDirs():
	"""Return two paths: the user's private and shared application support directory.
	
	If a directory does not exist, its path is set to None.
	"""
	retDirs = []
	for domain in Carbon.Folders.kUserDomain, Carbon.Folders.kLocalDomain:
		path = getStandardDir(
			domain = domain,
			dirType = Carbon.Folders.kApplicationSupportFolderType,
			doCreate = False,
		)
		retDirs.append(path)
	return retDirs

def getDocsDir():
	"""Return the path to the user's documents directory.
	
	Return None if the directory does not exist.
	"""
	return getStandardDir(
		domain = Carbon.Folders.kUserDomain,
		dirType = Carbon.Folders.kDocumentsFolderType,
		doCreate = False,
	)

def getPrefsDir():
	"""Return the path to the user's preferences directory.

	Return None if the directory does not exist.
	"""
	return getStandardDir(
		domain = Carbon.Folders.kUserDomain,
		dirType = Carbon.Folders.kPreferencesFolderType,
		doCreate = False,
	)
	

if __name__ == "__main__":
	print "Testing"
	print 'getAppSuppDirs = %r' % getAppSuppDirs()
	print 'getDocsDir()   = %r' % getDocsDir()
	print 'getPrefsDir()  = %r' % getPrefsDir()
