#!/usr/local/bin/python
import Numeric
import RO.MathUtil
import RO.SysConst

def vn (vec):
	"""
	Normalises a vector.
	
	Inputs:
	- vec	vector
	
	Returns a tuple containing:
	- the unit vector as a Numeric.array
	- the magnitude of the vector
	
	If the magnitude of vec is too small to compute,
	the unit vector is all zeros and the magnitude is zero.
	
	History:	
	P.T.Wallace	Starlink	November 1984
	2002-07-11 ROwen  Rewrote in Python.
	"""
	vecMag = RO.MathUtil.vecMag(vec)
	
	if vecMag < RO.SysConst.FSmallNum:
		# this odd construct is a silly way of
		# returning the correct number of zeros
		return (Numeric.array(vec) * 0.0, 0.0)
	
	return (Numeric.array(vec) / vecMag, vecMag)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing vn"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		((1, 2, 3), ((0.267261241912424, 0.534522483824849, 0.801783725737273), 3.74165738677394)),
		((0, 3, 4), ((0.000000000000000, 0.600000000000000, 0.800000000000000), 5.00000000000000)),
		((0, 0, 0), ((0.000000000000000, 0.000000000000000, 0.000000000000000), 0.000000000000000)),
		((-1, -2, -3), ((-0.267261241912424, -0.534522483824849, -0.801783725737273), 3.74165738677394)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = vn(testInput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1e-15):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
