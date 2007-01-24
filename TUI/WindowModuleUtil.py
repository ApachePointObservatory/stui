#!/usr/bin/env python
"""Utilities to find and load TUI windows modules.

2005-08-08 ROwen
2006-10-25 ROwen    Minor clarifications of logFunc in a doc string.
"""
import os
import sys
import traceback
import RO.Constants
import RO.OS

def findWindowsModules(
    path,
    isPackage = False,
    loadFirst = None,
):
    """Iterator: recursively find TUI "window modules" in a given path
    and return the associated module name.
    
    Window modules are files whose name ends in 'Window.py'.
    
    Does NOT verify that the module is actually part of a valid package.
    To load these modules YOU must make sure that:
    - There are no missing __init__.py files in the directory hierarchy.
    - The the path is on the python path.
    
    Inputs:
    - path      root of path to search
    - isPackage the path is a package; the final directory
                should be included as part of the name of any module loaded.
    - loadFirst name of subdir to load first;
    """
    os.chdir(path)
    fileList = RO.OS.findFiles(os.curdir, "*Window.py")
    if loadFirst and fileList:
        # rearrange so modules in specified subdir come first
        # use decorate/sort/undecorate pattern
        decList = [(not fname.startswith(loadFirst), fname) for fname in fileList]
        decList.sort()
        fileList = zip(*decList)[1]

    for fileName in fileList:
        # generate the module name:
        # <rootmodulename>.subdir1.subdir2...lastsubdir.<modulename>
        fileNameNoExt = os.path.splitext(fileName)[0]
        pathList = RO.OS.splitPath(fileNameNoExt)
        # avoid hidden files
        if pathList[-1].startswith("."):
            continue
        if isPackage:
            pkgName = os.path.basename(path)
            pathList.insert(0, pkgName)
        moduleName = ".".join(pathList)
        yield moduleName

def loadWindows(
    path,
    tlSet,
    isPackage = False,
    loadFirst = None,
    logFunc = None,
):
    """Automatically load all windows in any subdirectory of the path.
    The path is assumed to be on the python path (sys.path).
    Windows have a name that ends in 'Window.py'.
    
    Inputs:
    - path      root of path to search
    - tlSet     toplevel set (see RO.Wdg.Toplevel)
    - isPackage the path is a package; the final directory
                should be included as part of the name of any module loaded.
    - loadFirst name of subdir to load first;
    - logFunc   function for logging messages or None of no logging wanted;
                logFunc must take two arguments:
                - the text to log
                - severity (by name): one of the RO.Constant.sev constants,
                    defaulting to RO.Constants.sevNormal.
    
    Raises RuntimeError if loadFirst is specified and no modules are found.
    """
    if logFunc:
        logFunc("Searching for additions in %r" % (path,))
    for moduleName in findWindowsModules(
        path = path,
        isPackage = isPackage,
        loadFirst = loadFirst,
    ):
        # import the module
        try:
            module = __import__(moduleName, globals(), locals(), "addWindow")
            module.addWindow(tlSet)
            if logFunc:
                logFunc("Added %r" % (moduleName,))
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            errMsg = "%s.addWindow failed: %s" % (moduleName, e)
            if logFunc:
                logFunc(errMsg, severity=RO.Constants.sevError)
            sys.stderr.write(errMsg + "\n")
            traceback.print_exc(file=sys.stderr)
