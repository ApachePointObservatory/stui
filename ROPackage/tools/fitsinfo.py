#!/usr/bin/env python
import sys
import numpy
import pyfits

if len(sys.argv) == 1:
    print """Print FITS header and image statistics for one or more images.
    
Usage: %s fitsFile1 [fitsFile2 [...]]"""
    sys.exit(1)
    

def printArrayStats(descr, arr):
    arr = numpy.array(arr)
    print "%s min=%s, max=%s, mean=%s, stdDev=%s" % \
        (descr, arr.min(), arr.max(), arr.mean(), arr.std())

prevName = None
prevArr = None
for fileName in sys.argv[1:]:
    fitsFile = pyfits.open(fileName)
    print "%s header:" % (fileName,)
    hdr = fitsFile[0].header
    for key, value in hdr.items():
        if key.upper() == "COMMENT":
            print "%s %s" % (key, value)
        elif isinstance(value, bool):
            if value:
                valueStr = "T"
            else:
                valueStr = "F"
            print "%-8s= %s" % (key, valueStr)
        else:
            print "%-8s= %r" % (key, value)
    imArr = fitsFile[0].data
    printArrayStats(fileName, imArr)
    if prevArr != None and prevArr.shape == imArr.shape:
        printArrayStats("%s-%s" % (fileName, prevName), imArr-prevArr)
    prevArr = imArr
    prevName = fileName
