#!/usr/local/bin/python
import RO.PhysConst
import RO.MathUtil
from RO.Astro import llv
from LMSTFromUT1 import *

def lastFromUT1(ut1, longitude):
	"""Convert from universal time (MJD)
	to local apparent sidereal time (deg).

	Inputs:
	- ut1		UT1 MJD
	- longitude	longitude east (deg)

	Returns:
	- last		local apparent sideral time (deg)
	
	History:
	2002-08-05 ROwen  First version, loosely based on the TCC's tut_LAST.
	"""
	# convert UT1 to local mean sidereal time, in degrees
	lmst = lmstFromUT1(ut1, longitude)

	# find apparent - mean sidereal time, in degrees
	# note: this wants the TDB date, but UT1 is probably close enough
	appMinusMean = llv.eqeqx(ut1) / RO.PhysConst.RadPerDeg

	# find local apparent sideral time, in degrees, in range [0, 360)
	return RO.MathUtil.wrapPos (lmst + appMinusMean)
