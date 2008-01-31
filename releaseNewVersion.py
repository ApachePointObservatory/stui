#!/usr/bin/env python
"""A script to release a new version of TUI

If run on a unix box it exports the current version of TUI and then zips that.
If run on MacOS X it also tries to build the Mac binary.
Not intended for use on Windows.

To use:
    ./releaseNewVersion.py
"""
import os
import shutil
import sys
import subprocess

PkgName = "TUI"
import TUI.Version
versionName = TUI.Version.VersionName
print "%s version %s" % (PkgName, versionName)

getOK = raw_input("Is this version OK? (y/[n]) ")
if not getOK.lower().startswith("y")
    sys.exit(0)

print "Status of subversion repository:"

subprocess.call(["svn", "status"])

getOK = raw_input("Is the subversion repository up to date? (y/[n]) ")
if not getOK.lower().startswith("y")
    sys.exit(0)

print "Subversion repository OK"

exportPath = os.path.abspath(os.path.join(os.environ["HOME"], "%s_%s_Source" % (PkgName, versionName)))
zipFilePath = exportPath + ".zip"
if os.path.exists(exportPath):
    print "Export directory %r already exists" % (exportPath,)
    getOK = raw_input("Should I delete the old %r? (yes/[n]) " % (exportPath,))
    if not getOK.lower() == "yes":
        sys.exit(0)
    print "Deleting %r" % (exportPath,)
    shutil.rmtree(exportPath)
if os.path.exists(zipFilePath):
    getOK = raw_input("File %r already exists! Should I delete it? (yes/[n]) " % (zipFilePath,))
    if not getOK.lower() == "yes":
        sys.exit(0)
    print "Deleting %r" % (zipFilePath,)
    os.remove(zipFilePath)

print "Exporting subversion repository to %r" % (exportPath,)

status = subprocess.call(["svn", "export", ".", exportPath])
if status != 0:
    print "Svn export failed!"
    sys.exit(0)

print "Zipping %r" % (exportPath,)
status = subprocess.call(["zip", "-r", "-q", zipFilePath, exportPath])
if status != 0:
    print "Zip failed!"
    
if sys.platform == "darwin":
    print "Building Mac version"
    macBuildDir = os.path.join(exportPath, "BuildForMac")
    status = subprocess.call(["python", "setup.py", "-q", "py2app"], cwd=macBuildDir)
    if status != 0:
        print "Mac build failed!"
