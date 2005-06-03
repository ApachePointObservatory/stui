#!/usr/local/bin/python
from SCFromCC import *

def scFromDC (p):
	"""Convert direction cosines or any cartesian vector to spherical coordinates.
	Similar to scFromCC but magnitude is not returned.

	Inputs:
	 - p(3)		direction cosines or any cartesian vector
	
	Returns a tuple containing:
	- pos(2)	spherical position (deg) as equatorial, polar angle,
				e.g. (RA, Dec), (-HA, Dec) or (Az, Alt);
				ranges are: pos[0]: [0, 360), pos[1]: [-90,90]
	- atPole	true if very near the pole, in which case pos[1] = 0,
				and pos[0] = +/- 90 as appropriate.
	
	Error Conditions:
	- If |p| is too small, raises ValueError.
	- If |p| is too large, overflows are possible--roughly if p^2 overflows.
	Of course neither of these can occur if p is a direction cosine (unit vector).
	
	History:
	2002-07-23 R Owen.
	"""
	pos, mag, atPole = scFromCC(p)
	return (pos, atPole)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing scFromDC"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		((0.984807753012208, 0.173648177666930, 0.000000000000000), ((10, 0), 0)),
		((0.969846310392954, 0.171010071662834, 0.173648177666930), ((10, 10), 0)),
		((0.969846310392954, -0.171010071662834, -0.173648177666930), ((350, -10), 0)),
		((0.500000000000000, 0.500000000000000, 0.707106781186548), ((45, 45), 0)),
		((0.224143868042013, 0.836516303737808, 0.500000000000000), ((75, 30), 0)),
		((0.000000000000000, 0.000000000000000, 1.00000000000000), ((0, 90), 1)),
		((-8.682408883346518e-002, 0.150383733180435, -0.984807753012208), ((120, -80), 0)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = scFromDC(testInput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
