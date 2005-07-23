#!/usr/local/bin/python
"""Telescope User Interface.
This is the main routine that calls everything else.

2003-02-27 ROwen	First version with history.
					Modified to use the new Hub authorization
2003-03-20 ROwen	Added DIS
2003-03-25 ROwen	Moved TCC widgets into TCC subdirectory;
	modified to load TUI windows from TUIWindow.py
	and to auto-load windows from TCC, Inst and Misc directories
2003-04-04 ROwen	Fixed auto-load code to be platform-independent.
2003-04-22 ROwen	Modified to not auto-load window modules
					whose file name begins with ".".
2003-06-09 ROwen	Modified to use TUIModel.
2003-06-18 ROwen	Modified to print a full traceback for unexpected errors;
					modified to exclude SystemExit and KeyboardInterrupt
					when testing for general exceptions.
2003-12-17 ROwen	Modified to auto load windows from all of the
					TCC package (instead of specific sub-packages)
					and also from TUISharedAdditions and TUIUserAdditions.
2004-01-23 ROwen	Modified to not rely on modules being loaded from the
					same dir as this file. This simplifies generating a
					Mac standalone app.
					Modified to load *all* windows in TUI,
					rather than searching specific directories.
					Improved error handling of loadWindows:
					- if TUI cannot be loaded, fail
					- reject module names with "." in them
					(both changes help debug problems with making
					standalone apps).
2004-02-05 ROwen	Changed the algorithm for finding user additions.
2004-02-06 ROwen	Adapted to RO.OS.walkDirs->RO.OS.findFiles.
2004-02-17 ROwen	Changed to call buildMenus instead of buildAutoMenus
					in the "None.Status" toplevel. .
2004-03-03 ROwen	Modified to print the version number during startup.
2004-03-09 ROwen	Bug fix: unix code was broken.
2004-05-17 ROwen	Modified to be runnable by an external script (e.g. runtui.py).
					Modified to print version to log rather than stdout.
2004-07-09 ROwen	Modified to use TUI.TUIPaths
2004-10-06 ROwen	Modified to use TUI.MenuBar.
2005-06-16 ROwen	Modified to use improved KeyDispatcher.logMsg.
2005-07-22 ROwen	Modified to hide tk's console window if present.
"""
import os
import sys
import traceback
import Tkinter
import RO.Constants
import RO.OS
import RO.Wdg
import TUI.BackgroundTasks
import TUI.TUIPaths
import TUI.TUIModel
import TUI.Version
import TUI.MenuBar

def loadWindows(
	path,
	tlSet,
	isPackage = False,
	loadFirst = None,
	allowPYC = False,
	dispatcher = None,
):
	"""Automatically load all windows in any subdirectory of the path.
	The path is assumed to be on the python path (sys.path).
	Windows have a name that ends in 'Window.py'.
	
	Inputs:
	- path		root of path to search
	- tlSet		toplevel set (see RO.Wdg.Toplevel)
	- isPackage the path is a package; the final directory
				should be included as part of the name of any module loaded.
	- loadFirst	name of subdir to load first;
	- allowPYC	if no .py files are found, should it look for .pyc files?
	- dispatcher	message dispatcher to which to report progress;
					if omitted then progress is not reported
	
	Raises RuntimeError if loadFirst is specified and no modules are found.
	"""
	if dispatcher:
		dispatcher.logMsg("Searching for additions in %r" % (path,))
	os.chdir(path)
	fileList = RO.OS.findFiles(os.curdir, "*Window.py")
	if not fileList and allowPYC:
		# no .py files loaded; try .pyc files instead
		fileList = RO.OS.findFiles(os.curdir, "*Window.pyc")
	if loadFirst:
		# rearrange so modules in specified subdir come first
		# use decorate/sort/undecorate pattern
		if not fileList:
			raise RuntimeError("No windows modules found in %r" % (path,))
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

		# import the module
		try:
			module = __import__(moduleName, globals(), locals(), "addWindow")
			module.addWindow(tlSet)
			if dispatcher:
				dispatcher.logMsg("Added %r" % (moduleName,))
		except (SystemExit, KeyboardInterrupt):
			raise
		except Exception, e:
			errMsg = "%s.addWindow failed: %s" % (moduleName, e)
			if dispatcher:
				dispatcher.logMsg(errMsg, severity=RO.Constants.sevError)
			sys.stderr.write(errMsg + "\n")
			traceback.print_exc(file=sys.stderr)

def runTUI():
	"""Run TUI.
	"""
	# must do this before setting up preferences
	root = Tkinter.Tk()
	root.withdraw()
	# if console exists, hide it
	try:
		root.tk.call("console", "hide")
	except Tkinter.TclError:
		pass
	
	# create and obtain the TUI model
	tuiModel = TUI.TUIModel.getModel()
	
	# set up background tasks
	backgroundHandler = TUI.BackgroundTasks.BackgroundKwds(dispatcher=tuiModel.dispatcher)

	# get locations to look for windows
	tuiPath, addPathList = TUI.TUIPaths.getTUIPaths()
	
	# add additional paths to sys.path
	sys.path += addPathList
	
	# load standard windows modules
	loadWindows(
		path = tuiPath,
		tlSet = tuiModel.tlSet,
		isPackage=True,
		loadFirst="TUIMenu",
		allowPYC=True,
		dispatcher = None, # no log window yet, so don't report progress
	)
	
	# load additional windows modules
	for winPath in addPathList:
		loadWindows(
			path = winPath,
			tlSet = tuiModel.tlSet,
			dispatcher = tuiModel.dispatcher,
		)
	
	tuiModel.dispatcher.logMsg("TUI Version %s: ready to connect" % (TUI.Version.VersionStr,))
	
	# add the main menu
	TUI.MenuBar.MenuBar()
	
	root.mainloop()

if __name__ == "__main__":
	runTUI()
