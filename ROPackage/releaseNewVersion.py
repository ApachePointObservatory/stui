#!/usr/bin/env python
"""A script to release a new version of RO Python Package and upload it to PyPI

To use:
    ./releaseNewVersion.py
"""
import os
import shutil
import sys
import subprocess

PkgRoot = "python"
PkgName = "RO"
PkgDir = os.path.join(PkgRoot, PkgName)
sys.path.insert(0, PkgDir)
import Version
print "%s version %s" % (PkgName, Version.__version__)

versOK = raw_input("Is this version OK? (y/[n]) ")
if not versOK.lower() == "y":
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