"""The Python portion of the script that builds TUI

Usage:
% python setup.py [--quiet] py2app

History:
2004-02-20 ROwen    Specify libs in buildapp instead of as cmd-line args.
                    Stop forcing in the "os" module since that's no longer needed.
                    Use USE_ZIPIMPORR=False instead of unpacking Modules.zip.
2004-03-03 ROwen    Modified to use the new runtui.py as the main program.
2004-08-23 ROwen    Modified to save the source for built-in scripts.
2004-09-09 ROwen    Bug fix: was not including the tcl snack package.
2004-10-06 ROwen    Modified to include version info in the proper way.
                    Hence also modified to stop including it in the file name.
2004-11-19 ROwen    Modified to use current RO and TUI instead of one on the
                    PYTHONPATH, to avoid importing svn stuff.
2005-03-03 ROwen    Modified to import the new RO/Wdg/Resources.
2005-08-02 ROwen    Modified for the new TUI layout that allows the python code
                    to be zipped and separated from resources.
2005-09-22 ROwen    Added TUI/Scripts to the list of resources.
2006-01-21 ROwen    Renamed from buildtui.py to setup.py.
                    Modified to use py2app.
2006-02-24 ROwen    Modified to include matplotlib.
                    Added addDataFiles.
2006-03-08 ROwen    Modified to use new runtuiWithLog.py instead of runtui.py.
2006-05-25 ROwen    Added module FileDialog so the NICFPS:Focus script loads.
2006-06-01 ROwen    Corrected location of matplotlib data files.
2006-09-08 ROwen    Modified for py2app version 0.3.4 (which requires setuptools
                    and handles matplotlib automatically).
                    Added UniversalBinaryOK constant.
2006-12-01 ROwen    Changed UniversalBinaryOK to True, due to universal Aqua Tcl/Tk 8.4.14.
2006-12-28 ROwen    Changed UniversalBinaryOK back to False; Aqua Tcl/Tk 8.4.14 is buggy.
2007-01-16 ROwen    Added email.Utils to required modules (needed for Python 2.5).
2007-01-30 ROwen    Modified unused resource-adding code to support new RO layout.
2007-06-07 ROwen    Changed UniversalBinaryOK to True, due to universal Aqua Tcl/Tk 8.4.15.
2007-09-10 ROwen    Changed UniversalBinaryOK back to False due to the bugs in Aqua Tcl/Tk 8.4.15
                    (color picker broken and window geometry wrong on MacOS X 10.3.9)
2007-10-01 ROwen    Changed UniversalBinaryOK back to True, due to universal Aqua Tcl/Tk 8.4.16.
                    The color picker is fixed, but window geometry is still bad under MacOS X 10.3.9.
2007-11-08 ROwen    Changed UniversalBinaryOK back to False due to the bugs in Aqua Tcl/Tk 8.4.16
                    (nasty memory leak)
2007-12-20 ROwen    Bug fix: always built a universal binary on Intel Macs (regardless of UniversalBinaryOK).
2008-01-14 ROwen    Changed UniversalBinaryOK back to True. Aqua Tcl/Tk 8.4.14 does have the problem
                    of losing the mouse pointer, but with the improved guider control-click
                    and 8.4.15-8.4.17 have a nasty memory leak and may be the last 8.4.x produced.
2008-01-29 ROwen    Modified to put tcl snack in a new location that is now supported by runtuiWithLog.py
                    and no longer requires that the Tcl/Tk Framework be installed.
                    Other tweaks to better support not including the Tcl/Tk Framework.
"""
import os
import platform
from plistlib import Plist
import shutil
import subprocess
import sys
from setuptools import setup

# If True a universal binary is built; if False a PPC-only version is built
# Only set true if all extensions are universal binaries and Aqua Tcl/Tk is sufficiently reliable
UniversalBinaryOK = True

# add tuiRoot to sys.path before importing RO or TUI
tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
roRoot = os.path.join(tuiRoot, "ROPackage")
sys.path = [roRoot, tuiRoot] + sys.path
import TUI.Version

appName = "TUI"
mainProg = os.path.join(tuiRoot, "runtuiWithLog.py")
iconFile = "%s.icns" % appName
appPath = os.path.join("dist", "%s.app" % (appName,))
contentsDir = os.path.join(appPath, "Contents")
fullVersStr = TUI.Version.VersionStr
shortVersStr = fullVersStr.split(None, 1)[0]

inclModules = (
    "email.Utils", # needed for Python 2.5
    "FileDialog",
)
# packages to include recursively
inclPackages = (
    "TUI",
    "RO",
    "matplotlib",
)

plist = Plist(
    CFBundleName                = appName,
    CFBundleShortVersionString  = shortVersStr,
    CFBundleGetInfoString       = "%s %s" % (appName, fullVersStr),
    CFBundleExecutable          = appName,
    LSPrefersPPC                = not UniversalBinaryOK,
)

setup(
    app = [mainProg],
    setup_requires = ["py2app"],
    options = dict(
        py2app = dict (
            plist = plist,
            iconfile = iconFile,
            includes = inclModules,
            packages = inclPackages,
        )
    ),
)

# Copy tcl/tk snack extension
print "*** Copying tcl snack library ***"
snackSrcDir = "/Library/Tcl/snack2.2"
if not os.path.isdir(snackSrcDir):
    print "Warning: could not find snack dir: %r" % (snackSrcDir,)
else:
    snackDestDir = os.path.join(contentsDir, "Resources", "tcllib", "snack2.2")
    shutil.copytree(snackSrcDir, snackDestDir)

# Delete Tcl/Tk documentation
tclFrameworkDir = os.path.join(contentsDir, "Frameworks", "Tcl.framework")
tclDocDir = os.path.join(tclFrameworkDir, "Resources", "English.lproj", "ActiveTcl-8.4")
if os.path.isdir(tclFrameworkDir):
    "*** Tcl/Tk Framework IS part of the application package ***"
    if os.path.isdir(tclDocDir):
        # Delete extraneous files
        print "*** Removing Tcl/Tk help from the application package ***"
        shutil.rmtree(tclDocDir)
else:
    print "*** Tcl/Tk Framework is NOT part of the application package ***"

print "*** Creating disk image ***"
appName = "TUI_%s_Mac" % shortVersStr
destFile = os.path.join("dist", appName)
args=("hdiutil", "create", "-srcdir", appPath, destFile)
retCode = subprocess.call(args=args)

if UniversalBinaryOK:
    print "*** Built %s as a universal binary ***" % (appName,)
else:
    print "*** Built %s as a PPC binary ***" % (appName,)
