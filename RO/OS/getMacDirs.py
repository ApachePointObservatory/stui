#!/usr/local/bin/python
"""Utilities for finding standard Mac directories.

History:
2004-02-04 ROwen
2004-02-12 ROwen	Modified to use fsref.as_pathname() instead of Carbon.File.pathname(fsref).
"""
import Carbon.Folder, Carbon.Folders
import MacOS

def findFolder(domain, dirType, doCreate=False):
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

def getPrefsDir(doCreate = False):
	"""Return a path to the user's preferences folder.
	
	Inputs:
	- doCreate	try to create the dir if it does not exist?

	Returns None if the directory does not exist
	(and could not be created if doCreate True).
	"""
	return findFolder(
		domain = Carbon.Folders.kUserDomain,
		dirType = Carbon.Folders.kPreferencesFolderType,
		doCreate = doCreate,
	)

def getAppSuppDirs(doCreate = False):
	"""Return a list of paths to the user's and local (shared) application support folder.
	
	Inputs:
	- doCreate	try to create each dir if it does not exist?
	
	If a folder does not exist (and could not be created if doCreate True),
	it is omitted; hence returns [] if nothing found.
	"""
	retDirs = []
	for domain in Carbon.Folders.kUserDomain, Carbon.Folders.kLocalDomain:
		path = findFolder(
			domain = domain,
			dirType = Carbon.Folders.kApplicationSupportFolderType,
			doCreate = doCreate,
		)
		if path != None:
			retDirs.append(path)
	return retDirs
	

if __name__ == "__main__":
	print "Testing"
	print "prefs=", getPrefsDir()
	print "app supp=", getAppSuppDirs()
