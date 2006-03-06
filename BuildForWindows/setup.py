"""Build TUI for Windows

  python buildtui.py py2exe

BROKEN: including matplotlib prevents win32com.shell from loading
(and perhaps other important modules). I'm not sure why.
win32com.shell is unusual, but RO.OS.getWinDirs already
takes that into account successfully. At least that used to work;
something may have changed (e.g. in the latest py2exe).

Hints on including matplotlib came from the following
(search for libgdk_pixbuf-2.0-0.dll):
<http://sourceforge.net/mailarchive/forum.php?forum_id=40690&max_rows=25&style=nested&viewmonth=200510>

History:
2005-10-07 ROwen
2006-02-28 ROwen	Modified to include matplotlib (note: matplotlib requires
					a lot of work; you can't just rely on auto-detection).
					Added getDataFiles.
					Moved the win32com.shell workaround here from RO.OS.getWinDirs.
					TUI no longer opens a console window (now that it writes a log file).
"""
from distutils.core import setup
import os
import py2exe
import matplotlib
import sys

# The following code is necessary for py2exe to find win32com.shell.
# Solution from <http://starship.python.net/crew/theller/moin.cgi/WinShell>
import win32com
import py2exe.mf as modulefinder
for p in win32com.__path__[1:]:
	modulefinder.AddPackagePath("win32com", p)
for extra in ["win32com.shell"]:
	__import__(extra)
	m = sys.modules[extra]
	for p in m.__path__[1:]:
		modulefinder.AddPackagePath(extra, p)

tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# the following is required if importing RO or TUI
#sys.path = [tuiRoot] + sys.path
mainProg = os.path.join(tuiRoot, "runtui.py")

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
			numNames = len(dirNames)
			for ii in range(numNames-1, -1, -1):
				if dirNames[ii].startswith("."):
					del(dirNames[ii])
		if not dirPath.startswith(fromDir):
			raise RuntimeError("Cannot deal with %r files; %s does not start with %r" %\
				(resBase, dirPath, fromDir))
		toPath = os.path.join(toSubDir, dirPath[lenFromDir+1:])
		filePaths = [os.path.join(dirPath, fileName) for fileName in fileNames]
		dataFiles.append((toPath, filePaths))

# Add resource files for TUI and RO.
dataFiles = []
resBases = ("TUI\Help", "TUI\Scripts", "TUI\Sounds", "RO\Bitmaps")
lenTUIRoot = len(tuiRoot)
for resBase in resBases:
	resPath = os.path.join(tuiRoot, resBase)
	addDataFiles(dataFiles, resPath, resBase)
	
# Add tcl snack libraries.
snackDir = "C:\\Program Files\\Python24\\tcl\\snack2.2"
addDataFiles(dataFiles, snackDir, "tcl\\snack2.2")

# Add matplotlib's data files.
matplotlibDataPath = matplotlib.get_data_path()
addDataFiles(dataFiles, matplotlibDataPath, "matplotlibdata")

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
	options = dict(
		py2exe = dict (
			dll_excludes = [
				# the following are for matplotlib 0.87:
				"libgdk_pixbuf-2.0-0.dll", 
				"libgobject-2.0-0.dll",
				"libgdk-win32-2.0-0.dll",
			],
			excludes = [ # modules to exclude
				"_gtkagg",
				"_wxagg",
			],
			includes = [ # modules to include
			],
			packages = [
				"matplotlib",
				"pytz", # apparently required for matplotlib
#				"matplotlib.backends",
#				"matplotlib.numerix",
#				"encodings", "dateutil",
#				"numarray",
			],
		)
	),
	windows=[ # windows= for no console, console= for console
		dict(
			script = mainProg,
			icon_resources = [(1, "TUI.ico")],
		),
	],
	data_files = dataFiles,
)
