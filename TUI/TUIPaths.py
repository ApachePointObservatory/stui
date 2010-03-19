#!/usr/bin/env python
"""Get paths to various TUI-related directories.

2004-07-09 ROwen
2005-07-11 ROwen    Modified for changed RO.OS.getAppSuppDirs.
2005-09-22 ROwen    Changed getAddPaths to getTUIPaths.
                    Added getResourceDir.
2007-01-19 ROwen    Made getAddPaths compatible with pyinstaller.
2009-11-03 ROwen    Changed TUIAdditions to <ApplicationName>Additions
2010-03-18 ROwen    Moved unix shared TUIAdditions directory up one level (to the parent of the parent of
                    the directory named TUI), so that it is independent of the TUI source tree and is shared
                    by all versions of TUI.
                    Added ifExists argument to getAddPaths.
                    Added getGeomFile and getPrefsFile.
"""
import os
import sys
import RO.OS
import TUI  # for TUI.__file__
import TUI.Version

AppAdditions = "%sAdditions" % (TUI.Version.ApplicationName,)

def getAddPaths(ifExists=True):
    """Return a list of 0 or more paths to existing additions directories, in order: local, shared.
    
    Inputs:
    - ifExists: only return directories that exist

    Additions are kept in two optional folders named <applicationName>Additions,
    one in the standard application support location for shared files,
    the other in the standard application support location for user files.

    See RO.OS.getAppSuppDirs for details on where these are.
    For unix, there is no standard application support location for shared files
    so TUI's root directory is used, instead. This is the directory containing
    the TUI package, e.g. tuiRoot contains TUI, RO and possibly <applicationName>Additions.
    """
    # start with the application support directories
    # include TUI's root if unix (since it has no standard shared location)
    appSuppDirs = RO.OS.getAppSuppDirs()
    addPathList = [dir for dir in appSuppDirs if dir != None]
    if RO.OS.PlatformName == "unix":
        tuiRoot = os.path.dirname(os.path.dirname(RO.OS.getResourceDir(TUI)))
        addPathList.append(tuiRoot)

    # look in subdir "<applicationName>Additions" of each of these dirs
    addPathList = [os.path.join(path, AppAdditions) for path in addPathList]
    
    # remove nonexistent dirs
    if ifExists:
        addPathList = [path for path in addPathList if os.path.isdir(path)]
    
    # remove duplicates
    addPathList = RO.OS.removeDupPaths(addPathList)

    return addPathList

def getGeomFile():
    geomDir = RO.OS.getPrefsDirs(inclNone=True)[0]
    if geomDir == None:
        raise RuntimeError("Cannot determine prefs dir")
    geomName = "%s%sGeom" % (RO.OS.getPrefsPrefix(), TUI.Version.ApplicationName)
    return os.path.join(geomDir, geomName)

def getPrefsFile():
    prefsDir = RO.OS.getPrefsDirs(inclNone=True)[0]
    if prefsDir == None:
        raise RuntimeError("Cannot determine prefs dir")
    prefsName = "%s%sPrefs" % (RO.OS.getPrefsPrefix(), TUI.Version.ApplicationName)
    return os.path.join(prefsDir, prefsName)

def getResourceDir(*args):
    """Return the resource directory for a specified resource.
    Input:
    - one or more path elements (strings)
    
    For example:
    getResourceDir("Sounds") returns the directory of TUI sounds
    """
    return RO.OS.getResourceDir(TUI, *args)


if __name__ == "__main__":
    print "TUI Prefs =", getPrefsFile()
    print "TUI Geom = ", getGeomFile()
    print "TUI Additions =", getAddPaths()
    print "TUI Sounds =", getResourceDir("Sounds")
