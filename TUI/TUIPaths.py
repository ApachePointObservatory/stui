#!/usr/local/bin/python
"""Get paths to main TUI modules and additions.

Additions are kept in two optional folders named TUIAdditions,
one in the standard application support location for shared files,
the other in the standard application support location for user files.

See RO.OS.getAppSuppDirs for details on where these are.
For unix, there is no standard application support location for shared files
so TUI's root directory is used, instead.

2004-07-09 ROwen
2005-07-11 ROwen	Modified for changed RO.OS.getAppSuppDirs.
"""
import os
import sys
import RO.OS
import TUI  # for TUI.__file__

def getTUIPaths():
	"""Return the list of TUI-related paths:
	- tuiPath	the path to the parent directory of the TUI package
	- addPathList	a list of 0 or more paths to existing TUIAdditions
				directories, in order: local, shared.
	"""
	tuiPath = os.path.dirname(TUI.__file__)

	# start with the application support directories
	# include TUI's root if unix (since it has no standard shared location)
	appSuppDirs = RO.OS.getAppSuppDirs()
	addPathList = [dir for dir in appSuppDirs if dir != None]
	if RO.OS.PlatformName == "unix":
		tuiRoot = os.path.dirname(tuiPath)
		addPathList.append(tuiRoot)

	# look in subdir "TUIAdditions" of each of these dirs
	addPathList = [os.path.join(path, "TUIAdditions") for path in addPathList]
	
	# remove nonexistent dirs
	addPathList = [path for path in addPathList if os.path.isdir(path)]
	
	# remove duplicates
	addPathList = RO.OS.removeDupPaths(addPathList)

	# return TUI's directory (the place to look for TUI's main code)
	# and a list of 0 or more places to look for additions
	return (tuiPath, addPathList)

if __name__ == "__main__":
	print "path list=", getTUIPaths()
