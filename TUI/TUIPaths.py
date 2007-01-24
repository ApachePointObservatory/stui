#!/usr/bin/env python
"""Get paths to various TUI-related directories.

2004-07-09 ROwen
2005-07-11 ROwen    Modified for changed RO.OS.getAppSuppDirs.
2005-09-22 ROwen    Changed getAddPaths to getTUIPaths.
                    Added getResourceDir.
2007-01-19 ROwen    Made getAddPaths compatible with pyinstaller.
"""
import os
import sys
import RO.OS
import TUI  # for TUI.__file__

def getAddPaths():
    """Return a list of 0 or more paths to existing TUIAdditions
    directories, in order: local, shared.

    Additions are kept in two optional folders named TUIAdditions,
    one in the standard application support location for shared files,
    the other in the standard application support location for user files.

    See RO.OS.getAppSuppDirs for details on where these are.
    For unix, there is no standard application support location for shared files
    so TUI's root directory is used, instead. This is the directory containing
    the TUI package, e.g. tuiRoot contains TUI, RO and possibly TUIAdditions.
    """
    # start with the application support directories
    # include TUI's root if unix (since it has no standard shared location)
    appSuppDirs = RO.OS.getAppSuppDirs()
    addPathList = [dir for dir in appSuppDirs if dir != None]
    if RO.OS.PlatformName == "unix":
        tuiRoot = os.path.dirname(RO.OS.getResourceDir(TUI))
        addPathList.append(tuiRoot)

    # look in subdir "TUIAdditions" of each of these dirs
    addPathList = [os.path.join(path, "TUIAdditions") for path in addPathList]
    
    # remove nonexistent dirs
    addPathList = [path for path in addPathList if os.path.isdir(path)]
    
    # remove duplicates
    addPathList = RO.OS.removeDupPaths(addPathList)

    return addPathList

def getResourceDir(*args):
    """Return the resource directory for a specified resource.
    Input:
    - one or more path elements (strings)
    
    For example:
    getResourceDir("Sounds") returns the directory of TUI sounds
    """
    return RO.OS.getResourceDir(TUI, *args)


if __name__ == "__main__":
    print "TUI Additions =", getAddPaths()
    print "TUI Sounds =", getResourceDir("Sounds")
