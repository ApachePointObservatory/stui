#!/usr/local/bin/python
def epj2d (epj):
	"""
	Converts Julian epoch to Modified Julian Date.
	
	Inputs:
	- epj	Julian epoch
	
	Returns:
	- mjd	Modified Julian Date (JD - 2400000.5).
	
	Reference:
	Lieske,J.H., 1979. Astron.Astrophys.,73,282.
	
	History:
	P.T.Wallace	Starlink	February 1984
	2002-07-11 ROwen  Converted EPJ2D to Python and renamed.
	"""
	return 51544.5 + (epj-2000.0)*365.25


if __name__ == "__main__":
	import RO.MathUtil
	print "testing epj2d"
	# testData is a list of duples consisting of:
	# - input data
	# - the expected output
	testData = (
		(1850, -3243.000000),
		(1900, 15019.50000),
		(1950, 33282.00000),
		(2000, 51544.50000),
		(2050, 69807.00000),
	)
	for testInput, expectedOutput in testData:
		actualOutput = epj2d(testInput)
		if 0 != RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-15):
			print "failed on input:", testInput
			print "expected output:", expectedOutput
			print "actual output  :", actualOutput
