#!/usr/local/bin/python
import Numeric
import RO.MathUtil

def haDecFromAzAlt (azAlt, lat):
	"""Converts alt/az position to HA/Dec position.

	Inputs:
	- azAlt(3)	cartesian Az/Alt (any units)
	- lat		observer's latitude north (deg)
	
	Returns:
	- haDec(3)	cartesian hour angle, declination (same units as azAlt), a Numeric.array
	
	Error Conditions:
	(none)
	
	Sign convention:
	increasing azAlt[0] is south-ish
	increasing azAlt[1] is east
	
	History:
	2002-07-22 ROwen	Converted from the TCC's cnv_AzAlt2HADec 1-1.
	2002-12-23 ROwen	Cosmetic change to make pychecker happy.
	"""
	sinLat = RO.MathUtil.sind (lat)
	cosLat = RO.MathUtil.cosd (lat)

	# convert cartesian azAlt to cartesian HA/Dec
	return Numeric.array((
		  sinLat * azAlt[0] + cosLat * azAlt[2],
		  azAlt[1],
		- cosLat * azAlt[0] + sinLat * azAlt[2],
	))


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing haDecFromAzAlt"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((1, 0, 0), 30),
		     (0.500000000000000, 0.000000000000000, -0.866025403784439)),
		(((0, 1, 0), 30),
		     (0.000000000000000, 1.00000000000000, 0.000000000000000)),
		(((0, 0, 1), 30),
		     (0.866025403784439, 0.000000000000000, 0.500000000000000)),
		(((1, 2, 3), 30),
		     (3.09807621135332, 2.00000000000000, 0.633974596215561)),
		(((3, 2, 1), -30),
		     (-0.633974596215561, 2.00000000000000, -3.09807621135332)),
		(((-3, -2, -1), -30),
		     (0.633974596215561, -2.00000000000000, 3.09807621135332)),
		(((-3, -2, -1), -45),
		     (1.41421356237310, -2.00000000000000, 2.82842712474619)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = haDecFromAzAlt(*testInput)
		if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-15):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
