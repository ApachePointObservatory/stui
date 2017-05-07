#!/usr/bin/env python
"""A script to release a new version of TUI from a git working copy

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

roPath = os.environ.get("RO_DIR")
if not roPath:
    print "RO not setup"
    sys.exit(1)
else:
    print "RO found at", roPath

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

print "Status of git repository:"
subprocess.call(["git", "status"])

getOK = raw_input("Is the git repository up to date? (y/[n]) ")
if not getOK.lower().startswith("y"):
    sys.exit(0)

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

print "Copying %s repository to %r" % (PkgName, exportPath)

# to write directly to a .zip file (but it won't include the RO package):
# git archive --prefix=<exportFileName>/ -o <zipFilePath> HEAD
#status = subprocess.call(["git", "archive", "--prefix=%s/" % (exportFileName,), "-o", zipFilePath, "HEAD"])
# to write to a directory, tar and untar in one command:
# git archive --format=tar --prefix=<exportFileName>/ HEAD | (cd <exportRoot> && tar xf -)
cmdStr = "git archive --format=tar --prefix=%s/ HEAD | (cd %s && tar xf -)" % \
    (exportFileName, exportRoot)
status = subprocess.call(cmdStr, shell=True)
if status != 0:
    print "git archive failed!"
    sys.exit(1)

print "Copying RO repository"

roTempName = "ROTemp"
roTempDir = os.path.join(exportRoot, roTempName)
cmdStr = "git archive --format=tar --prefix=%s/ HEAD python/RO | (cd %s && tar xf -)" % \
    (roTempName, exportRoot,)
status = subprocess.call(cmdStr, shell=True, cwd=roPath)
if status != 0:
    print "git archive failed!"
    sys.exit(1)

# copy RO source into the output repo and delete the empty extra crap
shutil.move(os.path.join(roTempDir, "python", "RO"), exportPath)
shutil.rmtree(os.path.join(roTempDir))

print "Zipping %r" % (exportPath,)
status = subprocess.call(["zip", "-r", "-q", zipFileName, exportFileName], cwd=exportRoot)
if status != 0:
    print "Zip failed!"
else:
    print "Source zipped"

if sys.platform == "darwin":
    # open the directory in Finder, as a convenience for the user
    status = subprocess.call(["open", exportRoot])

    print "Building Mac version"
    macBuildDir = os.path.join(exportPath, "BuildForMac")
    print("Mac Build Dir", macBuildDir)
    status = subprocess.call(['python setup.py -q py2app'],
                             cwd=macBuildDir, shell=True)
    if status != 0:
        print "Mac build failed!"
    else:
        print "Mac build finished!"
        status = subprocess.call(["open", os.path.join(macBuildDir, "dist")])

print "TUI releases: <http://sdss3.apo.nmsu.edu/opssoft/stui-downloads/>"
print "TUI betas:    <http://sdss3.apo.nmsu.edu/opssoft/stui-downloads/files/>"
