"""The Python portion of the script that builds TUI

Usage:
% python setup.py py2app

To do:
- figure out if distDir is under control, and if so,
  specify it (makes final copy more reasonable)
- delete tcl docs at end or else comment out or remove the code to delete them
- how much of Plist is useful and how much is replaced by py2app?
  I'd like to specify shortversstr and getinfostr, but let py2app do the rest

History:
2004-02-20 ROwen	Specify libs in buildapp instead of as cmd-line args.
					Stop forcing in the "os" module since that's no longer needed.
					Use USE_ZIPIMPORR=False instead of unpacking Modules.zip.
2004-03-03 ROwen	Modified to use the new runtui.py as the main program.
2004-08-23 ROwen	Modified to save the source for built-in scripts.
2004-09-09 ROwen	Bug fix: was not including the tcl snack package.
2004-10-06 ROwen	Modified to include version info in the proper way.
					Hence also modified to stop including it in the file name.
2004-11-19 ROwen	Modified to use current RO and TUI instead of one on the
					PYTHONPATH, to avoid importing svn stuff.
2005-03-03 ROwen	Modified to import the new RO/Wdg/Resources.
2005-08-02 ROwen	Modified for the new TUI layout that allows the python code
					to be zipped and separated from resources.
2005-09-22 ROwen	Added TUI/Scripts to the list of resources.
2006-01-20 ROwen	Renamed and modified to use py2app -- IN PROGRESS!!!
"""
from distutils.core import setup
import py2app
import os
import shutil
import sys
from plistlib import Plist

tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [tuiRoot] + sys.path
import RO.OS
import TUI.Version

tuiDir = os.path.dirname(os.path.abspath(TUI.__file__))

## Do NOT put python code into a zip archive
## because it breaks auto-loading of code by the TUI package.
## This may be an unsupported hook, but if it goes away
## it is likely to be replaced by a command-line argument.
#bundlebuilder.USE_ZIPIMPORT = False

mainProg = os.path.join(tuiRoot, "runtui.py")

# Generate the full app name here
# since it's needed for some file copying later.
versDate = TUI.Version.VersionStr
appVers = versDate.split()[0]
appName = "TUI"
appPath = "dist/%s.app" % (appName,)
iconFile = "%s.icns" % appName

plist = Plist(
	CFBundleName				= appName,
#	CFBundleIconFile			= iconFile, # doesn't work; specify iconfile py2app option instead
	CFBundleShortVersionString	= appVers,
	CFBundleGetInfoString		= ' '.join([appName, versDate]),
	CFBundleExecutable			= appName,
)

data_files = []
resourceFiles = ("TUI/Help", "TUI/Scripts", "TUI/Sounds", "RO/Bitmaps")
lenTUIRoot = len(tuiRoot)
for resBase in resourceFiles:
	resPath = os.path.join(tuiRoot, resBase)
	for (dirPath, dirNames, fileNames) in os.walk(resPath):
		if ".svn" in dirPath:
			continue
		if not dirPath.startswith(tuiRoot):
			raise RuntimeError("Cannot deal with %r files; %s does not start with %r" % \
				(resBase, dirPath, tuiRoot))
		resSubPath = os.path.join("Python", dirPath[lenTUIRoot+1:])
		filePaths = [os.path.join(dirPath, fileName) for fileName in fileNames]
		data_files.append(
			(resSubPath, filePaths)
		)
	
# Add tk snack to bogus location, then move it later
# because these files get copied before the Tcl framework is built,
# which screws up building the framework
snackDir = "/Library/Tcl/snack2.2"
data_files.append(
	("snack2.2", RO.OS.findFiles(snackDir)),
)

#print "files:"
#for finfo in data_files:
#	print finfo
#temp = data_files[-1]
#print "snack in", temp[0]
#for fname in temp[1]:
#	print fname
#sys.exit(0)

setup(
	app = [mainProg],
	options = dict(
		py2app = dict (
			plist = plist,
			iconfile = iconFile,
		)
	),
	data_files = data_files,
)

# move snack to its final location
sourceDir = appPath + "/Contents/Resources/snack2.2"
destDir = appPath + "/Contents/Frameworks/Tcl.Framework/Resources/snack2.2"
print "rename %r to %r" % (sourceDir, destDir)
os.rename(sourceDir, destDir)

## Delete extraneous files
#print "Deleting extraneous files:"
#
## Delete Tcl/Tk documentation
## Note: needs revision for ActiveState Tcl
#for pkgName in ["Tcl", "Tk"]:
#	pkgPath = os.path.join(frameworkDir, "%s.framework" % (pkgName))
#	for lprojPath in RO.OS.findFiles(pkgPath, "English.lproj", returnDirs=True):
#		docPath = os.path.join(lprojPath, "Documentation")
#		if os.path.exists(docPath):
#			print "*", docPath
#			shutil.rmtree(docPath)
