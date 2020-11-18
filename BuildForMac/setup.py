"""The Python portion of the script that builds TUI

Usage:
% python setup.py [--quiet] py2app

Note: if the resulting application failed at startup with a complaint in the log file
about zope.interface not being available, either of the following will fix the problem:
- Update to a newer version of py2app
- Add an empty __init__.py file to the zope directory in site-packages

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
2009-11-09 ROwen    Removed installation of snack (now that TUI uses pygame to play sounds).
                    Modified to use TUI.Version.ApplicationName.
2010-07-21 ROwen    Removed email.Utils and FileDialog from inclModules;
                    the former is forbidden in Python 2.6 and the latter is not needed.
2010-09-29 ROwen    Modified to handle interlocks' requirement on plc.
                    Modified to ignore stui.pth; use eups instead.
2011-08-11 ROwen    Removed  obsolete LSPrefersPPC from property list.
                    Removed obsolete constant UniversalBinaryOK.
2012-11-02 ROwen    Removed import of obsolete interlocks package (that code is now in the plc package).
2014-02-17 ROwen    Added LSArchitecturePriority to PList to force 32-bit mode (for 10.9 compatibility).
                    Added LSMinimumSystemVersion to PList.
2014-10-22 ROwen    Back to 64-bit mode, now that we have a modern version of Tcl/Tk to try.
2015-11-10 ROwen    Added "FileDialog" back to inclModules; the current py2app requires it.
2018-02-06 JGallego Modified to replace libcrypto and libpng if building in 10.13.
                    Modified minimum version to macOS 10.11.

"""

import distutils
import glob
import os
import platform

from plistlib import Plist
import shutil
import subprocess
from setuptools import setup


macOS_version = distutils.version.StrictVersion(platform.mac_ver()[0])

tuiRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import TUI.Version
import plc # so I can find tcl code

appName = TUI.Version.ApplicationName
mainProg = os.path.join(tuiRoot, "runtuiWithLog.py")
iconFile = "%s.icns" % appName
appPath = os.path.join("dist", "%s.app" % (appName,))
contentsDir = os.path.join(appPath, "Contents")
fullVersStr = TUI.Version.VersionStr
shortVersStr = fullVersStr.split(None, 1)[0]

inclModules = (
    "FileDialog",
)
# packages to include recursively
inclPackages = (
    "TUI",
    "RO",
    "matplotlib", # py2app already does this, but it doesn't hurt to insist
    "actorkeys",
    "opscore",
    "plc",
    "pygame",
    "Tkinter"
)

plist = Plist(
    CFBundleName                = appName,
    CFBundleShortVersionString  = shortVersStr,
    CFBundleGetInfoString       = "%s %s" % (appName, fullVersStr),
    CFBundleExecutable          = appName,
    LSMinimumSystemVersion      = "10.12.0",
#    LSArchitecturePriority      = ("i386",) # force 32-bit mode;
        # this is needed for Tcl/TK 8.5.11 to run on MacOS X 10.9;
        # I'm stuck with 8.5.11 due to a crashing bug in Tcl/Tk 8.5.12 - 8.5.15.1
        # 8.5.16 has a nasty regression in http that prevents downloading images
        # 8.5.17 is a possibility; I'm trying a release candidate as I write this
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

# Copy interlocks tcl code
print "*** Copying PLC tcl code ***"
etcDestDir = os.path.join(contentsDir, "Resources", "lib", "etc")
plcRootDir = os.path.dirname(os.path.dirname(os.path.dirname(plc.__file__)))
etcSrcDir = os.path.join(plcRootDir, "etc")
if not os.path.isdir(etcSrcDir):
    raise RuntimeError("Could not find plc etc dir: %r" % (etcSrcDir,))
shutil.copytree(etcSrcDir, etcDestDir)

# Delete Tcl/Tk documentation
tclFrameworkDir = os.path.join(contentsDir, "Frameworks", "Tcl.framework")
tclDocDir = os.path.join(tclFrameworkDir, "Resources", "English.lproj", "ActiveTcl-8.5")
if os.path.isdir(tclFrameworkDir):
    print "*** Tcl/Tk Framework is part of the application package ***"
    if os.path.isdir(tclDocDir):
        # Delete extraneous files
        print "*** Removing Tcl/Tk help from the application package ***"
        shutil.rmtree(tclDocDir)
else:
    # if os.environ.get('CI'):
    #     subprocess.call(args=['cp', '-r', '/Library/Frameworks/Tcl.framework',
    #                           os.path.join(contentsDir, 'Frameworks/')])
    #     subprocess.call(args=['cp', '-r', '/Library/Frameworks/Tk.framework',
    #                           os.path.join(contentsDir, 'Frameworks/')])
    # else:
    print "*** WARNING: Tcl/Tk Framework is NOT part of the application package ***"

if macOS_version >= distutils.version.StrictVersion('10.13'):
    for asset in glob.glob('assets/*.dylib'):
        print('*** Adding {} asset ***'.format(os.path.basename(asset)))
        shutil.copy(asset, os.path.join(contentsDir, 'Frameworks'))

print "*** Creating disk image ***"
appName = "%s_%s_Mac" % (appName, shortVersStr)
destFile = os.path.join("dist", appName)
args = ('hdiutil', 'create', '-layout', 'SPUD', '-fs', 'HFS+J', '-srcdir', appPath, destFile)
retCode = subprocess.call(args=args)

print "*** Done building %s ***" % (appName,)
