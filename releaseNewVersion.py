#!/usr/bin/env python
"""A script to release a new version of TUI from a subversion working copy

If run on a unix box it exports the current version of TUI and then zips that.
If run on MacOS X it also tries to build the Mac binary.
Not intended for use on Windows.

To use:
    ./releaseNewVersion.py
"""
from __future__ import with_statement
import os
import re
import shutil
import sys
import subprocess

PkgName = "STUI"
import TUI.Version
versionName = TUI.Version.VersionName
fullVersStr = "%s %s" % (versionName, TUI.Version.VersionDate)
queryStr = "Version in Version.py = %s; is this OK? (y/[n]) " % (fullVersStr,)
getOK = raw_input(queryStr)
if not getOK.lower().startswith("y"):
    sys.exit(0)

versRegEx = re.compile(r"<h3>(\d.*\s\d\d\d\d-\d\d-\d\d)</h3>")
with file(os.path.join("TUI", "Help", "VersionHistory.html")) as vhist:
    for line in vhist:
        versMatch = versRegEx.match(line)
        if versMatch:
            histVersStr = versMatch.groups()[0]
            if histVersStr == fullVersStr:
                print "Version in VersionHistory.html matches"
                break
            else:
                print "Error: version in VersionHistory.html = %s != %s" % (histVersStr, fullVersStr)
                sys.exit(0)

print "Status of subversion repository:"
subprocess.call(["svn", "status"])

getOK = raw_input("Is the subversion repository up to date? (y/[n]) ")
if not getOK.lower().startswith("y"):
    sys.exit(0)

print "Subversion repository OK"

exportRoot = os.environ["HOME"]
exportFileName = "%s_%s_Source" % (PkgName, versionName)
exportPath = os.path.abspath(os.path.join(exportRoot, exportFileName))
zipFileName = "%s.zip" % (exportFileName,)
zipFilePath = os.path.abspath(os.path.join(exportRoot, zipFileName))
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
    sys.exit(1)

print "Zipping %r" % (exportPath,)
status = subprocess.call(["zip", "-r", "-q", zipFileName, exportFileName], cwd=exportRoot)
if status != 0:
    print "Zip failed!"
else:
    print "Unix package zipped"
    status = subprocess.call(["open", exportRoot])
    
if sys.platform == "darwin":
    print "Building Mac version"
    ExtraMacPathFile = "BuildForMac/stui.pth"
    if os.path.isfile(ExtraMacPathFile):
        destExtraMacPathLink = os.path.join(exportPath, ExtraMacPathFile)
        print "Linking to %s from %s" % (ExtraMacPathFile, destExtraMacPathLink)
        os.link(ExtraMacPathFile, destExtraMacPathLink)
    else:
        print "Did not find extra path file", ExtraMacPathFile

    macBuildDir = os.path.join(exportPath, "BuildForMac")
    status = subprocess.call(["python", "setup.py", "-q", "py2app"], cwd=macBuildDir)
    if status != 0:
        print "Mac build failed!"
    else:
        print "Mac build finished!"
        status = subprocess.call(["open", os.path.join(macBuildDir, "dist")])

print "TUI releases: <http://sdss3.apo.nmsu.edu/opssoft/stui-downloads/>"
print "TUI betas:    <http://sdss3.apo.nmsu.edu/opssoft/stui-downloads/files/>"
