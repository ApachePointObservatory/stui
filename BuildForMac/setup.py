"""The Python portion of the script that builds TUI

Usage:
% python setup.py [--quiet] py2app

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
2006-01-21 ROwen	Renamed from buildtui.py to setup.py.
					Modified to use py2app.
"""
from distutils.core import setup
import py2app
import os
import shutil
import subprocess
import sys
from plistlib import Plist

# add tuiRoot to sys.path before importing RO and TUI
tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [tuiRoot] + sys.path
import RO.OS
import TUI.Version

appName = "TUI"
mainProg = os.path.join(tuiRoot, "runtui.py")
iconFile = "%s.icns" % appName
appPath = os.path.join("dist", "%s.app" % (appName,))
contentsDir = os.path.join(appPath, "Contents")
versDate = TUI.Version.VersionStr
appVers = versDate.split()[0]

plist = Plist(
	CFBundleName				= appName,
	CFBundleShortVersionString	= appVers,
	CFBundleGetInfoString		= "%s %s" % (appName, versDate),
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
	
# Add tk snack to simple bogus location, then move it later
# because data_files get copied before the Tcl framework is built,
# which screws up building the framework
snackDir = "/Library/Tcl/snack2.2"
data_files.append(
	("snack2.2", RO.OS.findFiles(snackDir)),
)

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
sourceDir = os.path.join(contentsDir, "Resources", "snack2.2")
destDir = os.path.join(contentsDir, "Frameworks", "Tcl.Framework", "Resources", "snack2.2")
# print "rename %r to %r" % (sourceDir, destDir)
os.rename(sourceDir, destDir)

# Delete extraneous files
print "*** deleting extraneous files ***"

# Delete Tcl/Tk documentation
docPath = os.path.join(contentsDir, "Frameworks", "Tcl.framework", "Resources", "English.lproj", "ActiveTcl-8.4")
if os.path.exists(docPath):
	print docPath
	shutil.rmtree(docPath)
else:
	print "Warning: could not find %r" % (docPath,)

print "*** creating disk image ***"
destFile = os.path.join("dist", "TUI_%s_Mac" % appVers)
args=("hdiutil", "create", "-srcdir", appPath, destFile)
retCode = subprocess.call(args=args)
