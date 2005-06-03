#!/usr/local/bin/python
import math
import RO.MathUtil
import RO.SysConst
from DCFromSC import *
from SCFromDC import *
from RO.Astro import Cnv

def haDecFromAzAlt (azAlt, lat):
	"""Converts alt/az position to ha/dec position.

	Inputs:
	 - azAlt	(az, alt) (deg)
	 - lat		latitude (degrees);
				>0 is north of the equator, <0 is south
	
	Returns a tuple containing:
	- haDec		(HA, Dec) (deg), a tuple;
				HA is in the range (-180, 180]
	- atPole	true => object near the pole (see Error Conditions)
	
	Error Conditions:
	- If converted position is too near the north or south pole,
	atPole is set true and HA is some arbitrary value.
	
	Details:
	  Sign conventions:
	  - azimuth is 0 south and 90 east
	  - ha/dec is the usual left-handed coordinate system
	
	History:
	3/01 ROwen  Converted to Python from TCC's sph_AzAlt2HADec 1-2.
	2/02 ROwen  Minor tweaks to header.
	2002-07-02 ROwen	Renamed from azAltToHADec.
	2003-05-06 ROwen	Changed HA range from [0, 360) to (-180, 180]
	"""
	# convert spherical az/alt (deg) to direction cosines
	azAltDC = dcFromSC (azAlt)

	# convert az/alt direction cosines to -ha/dec direction cosines
	negHADecDC = Cnv.haDecFromAzAlt (azAltDC, lat)

	# convert -ha/dec direction cosines to spherical -ha/dec (deg)
	((negHA, dec), atPole) = scFromDC (negHADecDC)

	return ((RO.MathUtil.wrapCtr(-negHA), dec), atPole)


if __name__ == "__main__":
	from AngSep import angSep
	MaxErrArcSec = 1e-6 # max error on sky, in arc seconds
	print "testing haDecFromAzAlt"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((45, 0), 32), ((-62.0800217871046, -36.8455908815806), 0)),
		(((45, 45), 32), ((-30.0403054044160, -2.82666166924072), 0)),
		(((45, 89.9999999999), 32), ((-8.338199255877087E-011, 31.9999999999), 0)),
		(((45, 89.999999999999), 32), ((-8.294357651155915E-013, 31.999999999999), 0)),
		(((45, 89.99999999999999), 32), ((-1.184908235879425E-014, 32.0), 0)),
		(((45, 90), 32), ((0.0, 32.0), 0)),
		(((0, 70), 32), ((0.0, 12.0), 0)),
		(((-45, 70), 32), ((-345.348740244005, 17.0295713726456), 0)),
		(((180, 31.9999), 32), ((-180, 89.9999), False)),
		(((180, 31.9999999999), 32), ((-180.0, 89.9999999999), True)),
		(((180, 32), 32), ((0.0, 90.0), 1)),
		(((179.9999, 32), 32), ((-89.999973504, 89.999915195), False)),
		(((179.999999, 32), 32), ((-90.0, 89.9999999999), True)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = haDecFromAzAlt(*testInput)
		errOnSkyArcSec = angSep(actualOutput[0], expectedOutput[0]) * 3600.0
		if actualOutput[1] != expectedOutput[1] or errOnSkyArcSec > MaxErrArcSec:
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
			print "error on sky = %s\"" % errOnSkyArcSec
