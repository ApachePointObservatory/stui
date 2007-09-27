#!/usr/bin/env python
from __future__ import with_statement
import re
import sys
import os
import RO.Alg

def compareChecks(newFile, oldFile, doDebug):
    """Compare pychecker logs, ignoring "cruft"
    """
    newDict = readAndStrip(newFile, doDebug)
    newSet = set(newDict.keys())
    oldDict = readAndStrip(oldFile, doDebug)
    oldSet = set(oldDict.keys())
    newExtras = list(newSet - oldSet)
    newExtras.sort()
    oldExtras = list(oldSet - newSet)
    oldExtras.sort()
    print "Errors in %r but not in %r:" % (newFile, oldFile)
    for errSummary in newExtras:
        errList = newDict[errSummary]
        for err in errList:
            print "  ", err
    
    print "Errors in %r but not in %r:" % (oldFile, newFile)
    for errSummary in oldExtras:
        errList = oldDict[errSummary]
        for err in errList:
            print "  ", err

roPackageStrip = re.compile("^(.*)/ROPackage/(.*)$")
errSummaryRE = re.compile("^(.*\:)\d+(\:.*)$")
def readAndStrip(fileName, doDebug=False):
    """Read a pychecker log, strip the cruft and return a set of lines.
    """
    if doDebug:
        print "readAndStrip reading %r" % (fileName)
    inF = None
    nLib = 0
    nBlank = 0
    nDig = 0
    nMatchFail = 0
    nGood = 0
    goodSet = set()
    goodDict = RO.Alg.ListDict()
    with file(fileName, 'rU') as inF:
        for line in inF:
            if line.startswith("/Library"):
                nLib += 1
                continue
            if line[0].isdigit(): # skip "n errors supressed"
                nDig += 1
                continue
            line = line.strip()
            if not line:
                nBlank += 1
                continue
            nGood += 1
            roPackageMatch = roPackageStrip.match(line)
            if roPackageMatch:
                line = "/".join(roPackageMatch.groups())
            lineMatch = errSummaryRE.match(line)
            if not lineMatch:
                continue
            nGood += 1
            lineSummary = "".join(lineMatch.groups())
            goodDict[lineSummary] = line
    if doDebug:
        print "readAndStrip found %s good summaries of %s good lines and stripped %s /Library, %s blank, %s matchfail and %s digit lines" % \
            (len(goodDict), nGood, nLib, nBlank, nMatchFail, nDig)
    return goodDict

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print "Usage: %s newFile, oldFile [doDebug]" % (sys.argv[0])
        sys.exit(1)

    doDebug = False
    newFile = sys.argv[1]
    oldFile = sys.argv[2]
    if len(sys.argv) > 3:
        doDebug = bool(int(sys.argv[3]))
    print "Comparing pychecker file %r to %r" % (newFile, oldFile)
    compareChecks(newFile, oldFile, doDebug)    