"""Build TUI for Windows

  python buildtui.py py2exe

History:
2005-10-07 ROwen
2006-02-23 ROwen	Modified to not explicitly include numarray (auto-detect now works).
					Modified to include matplotlib (currently it is only used by a script,
					and thus cannot be auto-detected).
"""
from distutils.core import setup
import os
import py2exe
import sys

tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def printlist(descr, alist):
	print descr
	for item in alist:
		print "*", repr(item)

sys.path = [tuiRoot] + sys.path
import RO.OS
import TUI
tuiDir = os.path.dirname(os.path.abspath(TUI.__file__))

mainProg = os.path.join(tuiRoot, "runtui.py")

inclModules = [
]
inclPackages = [
	"matplotlib",
]

# add TUI and RO resources
# Use "files" instead of "resources" because they need to be in
# Contents/Resources/TUI-or-RO instead of Contents/Resources
files = []
resourceFiles = ("TUI\Help", "TUI\Scripts", "TUI\Sounds", "RO\Bitmaps")
lenTUIRoot = len(tuiRoot)
for resBase in resourceFiles:
	resPath = os.path.join(tuiRoot, resBase)
	for (dirPath, dirNames, fileNames) in os.walk(resPath):
		if not dirPath.startswith(tuiRoot):
			raise RuntimeError("Cannot deal with %r files; %s does not start with %r" %\
				(resBase, dirPath, tuiRoot))
		resSubPath = dirPath[lenTUIRoot+1:]
		filePaths = [os.path.join(dirPath, fileName) for fileName in fileNames]
		files.append(
			(resSubPath, filePaths)
		)
#print "files:"
#for finfo in files:
#	print finfo
	
# add tk snack
snackDir = "C:\\Program Files\\Python24\\tcl\\snack2.2"
files.append(
	("tcl\snack2.2", RO.OS.findFiles(snackDir)),
)

setup(
	options = dict(
		py2exe = dict (
			includes = inclModules,
			packages = inclPackages,
		)
	),
	console=[ # windows= for no console, console= for console
		dict(
			script = mainProg,
			icon_resources = [(1, "TUI.ico")],
		),
	],
	data_files = files,
)
