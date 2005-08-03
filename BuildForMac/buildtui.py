"""The Python portion of the script that builds TUI

To use, at the Terminal type:
  ./buildtui.sh
or:
  python buildtui.py

Note: the reason this is not self-contained (is run by buildtui.sh
instead of simply ./buildtui.py) is an obscure bug that causes
the self-contained version to build a non-working application on my system
(this seems to be related to my having unix-X11 build of python
in /usr/local/bin/python). Rather than risking non-functional builds,
I keep the shell script around.

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
"""
import bundlebuilder
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
fullAppName = "%s.app" % appName
iconFile = "%s.icns" % appName

# Include all python code in the RO and TUI packages.
inclPkgs = [
	"numarray",
	#"pyfits",
	#"RO",
	#"TUI",
]
# No extra modules are needed (for awhile I had to explicitly import os,
# but that problem seems to have corrected itself).
inclMods = [
]

# Include the Tcl and Tk frameworks.
libs = [
	"/Library/Frameworks/Tcl.framework",
	"/Library/Frameworks/Tk.framework",
]

plist = Plist(
	CFBundleName				= appName,
#	CFBundleIconFile			= iconFile,
	CFBundleShortVersionString	= appVers,
	CFBundleGetInfoString		= ' '.join([appName, versDate]),
	CFBundleExecutable			= appName,
)

resources = []

# add TUI and RO resources using files instead of resources
# because they need to be in Contents/Resources/TUI-or-RO
# instead of Contents/Resources
resRoot = "Contents/Resources"
files = []
resourceFiles = ("TUI/Help", "TUI/Sounds", "RO/Bitmaps")
for resFile in resourceFiles:
	files.append(
		(os.path.join(tuiRoot, resFile), os.path.join(resRoot, resFile))
	)

# add tk snack
files.append(
	("/Library/Tcl/snack2.2", "Contents/Frameworks/Tcl.Framework/Resources/snack2.2"),
)

# if no args supplied, build the application
if len(sys.argv) == 1:
	sys.argv.append('build')

bundlebuilder.buildapp(
	name = appName,				# application name 
	builddir  =  ".",			# dir for application
	mainprogram = mainProg,		# your app's main()
	iconfile = iconFile,		# file containing your app's icons
	argv_emulation = False,		# drag&dropped filenames show up in sys.argv?
	semi_standalone = True,		# make this app self contained.
	includeModules = inclMods,	# additional Modules to force in
	includePackages = inclPkgs,	# additional Packages to force in
	libs = libs,				# extra libraries to force in
	resources = resources,		# extra files or folders to copy to Resources
	files = files,				# extra files or folders to copy to a specified destination
	plist = plist,
)

# Delete extraneous files
print "Deleting extraneous files:"

# Delete Tcl/Tk debug versions.
frameworkDir = os.path.join(fullAppName, "Contents", "Frameworks")
for path in RO.OS.findFiles(frameworkDir, ["Tcl_debug", "Tk_debug"]):
	print "*", path
	os.remove(path)

# Delete Tcl/Tk documentation
for pkgName in ["Tcl", "Tk"]:
	pkgPath = os.path.join(frameworkDir, "%s.framework" % (pkgName))
	for lprojPath in RO.OS.findFiles(pkgPath, "English.lproj", returnDirs=True):
		docPath = os.path.join(lprojPath, "Documentation")
		if os.path.exists(docPath):
			print "*", docPath
			shutil.rmtree(docPath)
