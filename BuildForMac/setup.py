"""The Python portion of the script that builds TUI

Usage:
% python setup.py [--quiet] py2app

Warning: newer versions of matplotlib (sometime after 0.82)
have moved where they expect the data files to be.
Check matplotlib/__init__.py if you update matplotlib!

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
2006-02-24 ROwen	Modified to include matplotlib.
					Added addDataFiles.
2006-03-08 ROwen	Modified to use new runtuiWithLog.py instead of runtui.py.
2006-05-25 ROwen	Added module FileDialog so the NICFPS:Focus script loads.
2006-06-01 ROwen	Corrected location of matplotlib data files.
"""
from distutils.core import setup
import py2app
import os
import shutil
import subprocess
import sys
from plistlib import Plist
import matplotlib

import distutils
print "distutils.sysconfig.PREFIX=", distutils.sysconfig.PREFIX

# add tuiRoot to sys.path before importing RO or TUI
tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path = [tuiRoot] + sys.path
import TUI.Version

NDataFilesToPrint = 0 # number of data files to print, per directory

def addDataFiles(dataFiles, fromDir, toSubDir=None, inclHiddenDirs=False):
	"""Find data files and format data for the data_files argument of setup.
	
	In/Out:
	- dataFiles: a list to which is appended zero or more of these elements:
		[subDir, list of paths to resource files]
	
	Inputs:
	- fromDir: path to root directory of existing resource files
	- toSubDir: relative path to resources in package;
		if omitted then the final dir of fromDir is used
	- inclHiddenDirs: if True, the contents of directories whose names
		start with "." are included
	
	Returns a list of the following elements:
	"""
	lenFromDir = len(fromDir)
	if toSubDir == None:
		toSubDir = os.path.split(fromDir)[1]
	for (dirPath, dirNames, fileNames) in os.walk(fromDir):
		if not inclHiddenDirs:
			dirNamesCopy = dirNames[:]
			for ii in range(len(dirNamesCopy)-1, -1, -1):
				if dirNamesCopy[ii].startswith("."):
					del(dirNames[ii])
		if not dirPath.startswith(fromDir):
			raise RuntimeError("Cannot deal with %r files; %s does not start with %r" %\
				(resBase, dirPath, fromDir))
		toPath = os.path.join(toSubDir, dirPath[lenFromDir+1:])
		filePaths = [os.path.join(dirPath, fileName) for fileName in fileNames]
		dataFiles.append((toPath, filePaths))

appName = "TUI"
mainProg = os.path.join(tuiRoot, "runtuiWithLog.py")
iconFile = "%s.icns" % appName
appPath = os.path.join("dist", "%s.app" % (appName,))
contentsDir = os.path.join(appPath, "Contents")
versDate = TUI.Version.VersionStr
appVers = versDate.split()[0]

inclModules = [
	"FileDialog",
]
inclPackages = [
	"matplotlib",
]

plist = Plist(
	CFBundleName				= appName,
	CFBundleShortVersionString	= appVers,
	CFBundleGetInfoString		= "%s %s" % (appName, versDate),
	CFBundleExecutable			= appName,
)

dataFiles = []

# Add resource files for TUI and RO.
resBases = ("TUI/Help", "TUI/Scripts", "TUI/Sounds", "RO/Bitmaps")
lenTUIRoot = len(tuiRoot)
for resBase in resBases:
	resPath = os.path.join(tuiRoot, resBase)
	addDataFiles(dataFiles, resPath, "Python/" + resBase)

# Add tk snack to simple bogus location, then move it into
# the Tcl framework later. This is necessary because data_files
# get copied before the Tcl framework is built.
snackDir = "/Library/Tcl/snack2.2"
addDataFiles(dataFiles, snackDir)
snackTempDir = os.path.join(contentsDir, "Resources", "snack2.2")

# Add matplotlib's data files to a simple bogus location,
# as for tk snack
mplDataPath = matplotlib.get_data_path()
addDataFiles(dataFiles, mplDataPath, "matplotlib")
mplDataTempDir = os.path.join(contentsDir, "Resources", "matplotlib")

if NDataFilesToPrint > 0:
	print "\nData files:"
	for pathInfo in dataFiles:
		print pathInfo[0]
		nFiles = len(pathInfo[1])
		for resPath in pathInfo[1][0:NDataFilesToPrint]:
			print "  ", resPath
		if nFiles > NDataFilesToPrint:
			print "  ...and %d more" % (nFiles - NDataFilesToPrint)

setup(
	app = [mainProg],
	options = dict(
		py2app = dict (
			plist = plist,
			iconfile = iconFile,
			includes = inclModules,
			packages = inclPackages,
		)
	),
	data_files = dataFiles,
)

# move snack to its final location
snackDestDir = os.path.join(contentsDir, "Frameworks", "Tcl.Framework", "Resources", "snack2.2")
# print "rename %r to %r" % (snackTempDir, snackDestDir)
os.rename(snackTempDir, snackDestDir)

# move matplotlib to its final location
mplDataShareDir = os.path.join(contentsDir, "Frameworks", "Python.Framework", "Versions", \
	"%d.%d" % tuple(sys.version_info[0:2]), "share")
print "mkdir %r" % (mplDataShareDir,)
os.mkdir(mplDataShareDir)	
mplDataDestDir = os.path.join(mplDataShareDir, "matplotlib")
print "rename %r to %r" % (mplDataTempDir, mplDataDestDir)
os.rename(mplDataTempDir, mplDataDestDir)

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
