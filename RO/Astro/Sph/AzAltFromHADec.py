#!/usr/local/bin/python
import math
import RO.MathUtil
import RO.SysConst
from DCFromSC import *
from SCFromDC import *
from RO.Astro import Cnv

def azAltFromHADec (haDec, lat):
	"""Converts HA/Dec position to az/alt.

	Inputs:
	 - haDec	(ha, dec) (degrees)
	 - lat	latitude (degrees)
	
	Returns a tuple containing:
	  (az, alt)	(degrees)
	  atPole	true => object near the pole (see Error Conditions)
	
	Error Conditions:
	- If converted position is too near the pole, atPole is true and ha is undefined.
	
	Sign convention: azimuth is 0 south and 90 east.
	
	History:
	2002-07-23 ROwen  Converted from TCC's sph_HADec2AzAlt 1-2.
	2003-05-06 ROwen	Modified test data to match new scFromCC.
	"""
	# convert spherical -ha/dec to direction cosines
	negHADec = (-haDec[0], haDec[1])
	haDecDC = dcFromSC (negHADec)

	# convert ha/dec direction cosines to az/alt direction cosines
	azAltDC = Cnv.azAltFromHADec (haDecDC, lat)

	# convert az/alt direction cosines to spherical az/alt (deg)
	return scFromDC (azAltDC)


if __name__ == "__main__":
	from AngSep import angSep
	MaxErrArcSec = 1e-6 # max error on sky, in arc seconds
	print "testing azAltFromHADec"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		 (((-62.0800217871046, -36.8455908815806), 32), ((45, 0), 0)),
		 (((-30.0403054044160, -2.82666166924072), 32), ((45, 45), 0)),
		 (((0, 31.9999), 32), ((0, 89.9999), 0)),
		 (((0, 31.999999), 32), ((0, 90), 1)),
		 (((0, 32), 32), ((0.0, 90.0), 1)),
		 (((0, 12), 32), ((0.0, 70.0), 0)),
		 (((-345.348740244005, 17.0295713726456), 32), ((315.0, 70.0), 0)),
		 (((-180, 89.9999999999), 32), ((180, 31.9999999999), 0)),
		 (((-180, 89.999999999999), 32), ((180, 31.999999999999), 0)),
		 (((0, 90), 32), ((180, 31.99999999999999), 0)),
		 (((0, 90), 32), ((180, 32), 0)),
		 (((-90, 89.9999999999), 32), ((179.9999999999, 32), 0)),
		 (((-90, 89.999999999999), 32), ((179.999999999999, 32), 0)),
		 (((0, 90), 32), ((179.99999999999999, 32), 0)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = azAltFromHADec(*testInput)
		errOnSkyArcSec = angSep(actualOutput[0], expectedOutput[0]) * 3600.0
		if actualOutput[1] != expectedOutput[1] or errOnSkyArcSec > MaxErrArcSec:
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
			print "error on sky = %s\"" % errOnSkyArcSec
