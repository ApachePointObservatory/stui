#!/usr/local/bin/python
from CCFromSC import *

def dcFromSC (pos):
	"""Convert spherical coordinates to direction cosines, i.e. a unit vector.

	Inputs:
	- pos(2)	spherical coordinates (deg):
				longitude (increasing x to y), latitude,
				e.g. (RA, Dec), (-HA, Dec) or (Az, Alt)
	
	Returns:
	- dc(3)		direction cosines (rad), as a Numeric.array
	
	Error Conditions:
	  (none)
	
	History:
	2002-07-23 R Owen.
	"""
	return ccFromSC(pos, 1.0)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing dcFromSC"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		((10, 0), (0.984807753012208, 0.173648177666930, 0.000000000000000)),
		((10, 10), (0.969846310392954, 0.171010071662834, 0.173648177666930)),
		((-10, -10), (0.969846310392954, -0.171010071662834, -0.173648177666930)),
		((45, 45), (0.500000000000000, 0.500000000000000, 0.707106781186548)),
		((75, 30), (0.224143868042013, 0.836516303737808, 0.500000000000000)),
		((45, 90), (0.000000000000000, 0.000000000000000, 1.00000000000000)),
		((120, -80), (-8.682408883346518e-002, 0.150383733180435, -0.984807753012208)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = dcFromSC(testInput)
		if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-14):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
