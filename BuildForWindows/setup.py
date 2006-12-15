"""Build TUI for Windows

  python buildtui.py py2exe

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
2006-03-09 ROwen	Modified to call the executable TUI.exe.
					Got rid of the console window.
					Expected python and snack in slightly unusual locations,
					but now looks in C:\Python24 and C:\Python24\tcl\snacklib.
					Bug fix: required RO and TUI to be on the python path.
2006-12-14 ROwen	Added wxmsw26uh_vc.dll to dll_excludes to make it compatible
					with matplotlib 0.87.7 (which includes WxAgg support).
					Note: to actually use WxAgg support one would have to
					include that dll, not exclude it.
					Added TUI to the included packages because py2exe
					was not including TUI.Base.BaseFocusScript.
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
sys.path = [tuiRoot] + sys.path
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
snackDir = "C:\\Python24\\tcl\\snacklib"
addDataFiles(dataFiles, snackDir, "tcl\\snacklib")

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
				"wxmsw26uh_vc.dll",
			],
			excludes = [ # modules to exclude
				"_gtkagg",
				"_wxagg",
			],
			includes = [ # modules to include
			],
			packages = [
				"TUI",
				"matplotlib",
				"pytz", # required for matplotlib
#				"matplotlib.backends",
#				"matplotlib.numerix",
#				"dateutil", # used by matplotlib
#				"encodings",
#				"numarray",
			],
		)
	),
	windows=[ # windows= for no console, console= for console
		dict(
			script = mainProg,
			dest_base = "TUI",
			icon_resources = [(1, "TUI.ico")],
		),
	],
	data_files = dataFiles,
)
