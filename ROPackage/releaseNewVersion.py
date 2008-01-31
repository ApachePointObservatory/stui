#!/usr/bin/env python
"""A script to release a new version of RO Python Package and upload it to PyPI

To use:
    ./releaseNewVersion.py
"""
from __future__ import with_statement
import os
import re
import shutil
import sys
import subprocess

PkgRoot = "python"
PkgName = "RO"
PkgDir = os.path.join(PkgRoot, PkgName)
sys.path.insert(0, PkgDir)
import Version
queryStr = "Version from RO.Version = %s; is this OK? (y/[n]) " % (Version.__version__,)
versOK = raw_input(queryStr)
if not versOK.lower() == "y":
    sys.exit(0)

versRegEx = re.compile(r"<h3>(\d.*?)\s+\d\d\d\d-\d\d-\d\d</h3>")
with file(os.path.join("docs", "VersionHistory.html")) as vhist:
    for line in vhist:
        versMatch = versRegEx.match(line)
        if versMatch:
            histVersStr = versMatch.groups()[0]
            if histVersStr == Version.__version__:
                print "Version in VersionHistory.html matches"
                break
            else:
                print "Error: version in VersionHistory.html = %s != %s" % (histVersStr, Version.__version__)
                sys.exit(0)

print "Status of subversion repository:"

subprocess.call(["svn", "status"])

versOK = raw_input("Is the subversion repository up to date? (y/[n]) ")
if not versOK.lower() == "y":
    sys.exit(0)

print "Subversion repository OK"

exportPath = os.path.abspath(os.path.join(os.environ["HOME"], "%s_%s_Source" % (PkgName, Version.__version__)))
if os.path.exists(exportPath):
    print "Export directory %r already exists" % (exportPath)
    versOK = raw_input("Should I delete the old %r? (yes/[n]) " % (exportPath,))
    if not versOK.lower() == "yes":
        sys.exit(0)
    print "Deleting %r" % (exportPath,)
    shutil.rmtree(exportPath)

print "Exporting subversion repository to %r" % (exportPath,)

status = subprocess.call(["svn", "export", ".", exportPath])
if status != 0:
    print "Svn export failed!"
    sys.exit(0)

print "Building, uploading and registering"
status = subprocess.call(["python", "setup.py", "sdist", "upload", "register"], cwd=exportPath)
if status != 0:
    print "Build and upload failed!"

versOK = raw_input("OK to delete %r? (y/[n]) " % (exportPath,))
if not versOK.lower() == "y":
    sys.exit(0)

print "Deleting %r" % (exportPath,)
shutil.rmtree(exportPath)