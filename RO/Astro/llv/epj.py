#!/usr/local/bin/python
def epj (mjd):
	"""
	Converts Modified Julian Date to Julian epoch.
	
	Inputs:
	- mjd	Modified Julian Date (JD - 2400000.5)
	
	Returns:
	- epj	Julian epoch.
	
	Reference:
	Lieske,J.H., 1979. Astron.Astrophys.,73,282.
	
	History:
	P.T.Wallace	Starlink	February 1984
	2002-07-11 ROwen  Converted EPJ to Python.
	"""
	return 2000.0 + (mjd-51544.5)/365.25


if __name__ == "__main__":
	import RO.MathUtil
	print "testing epj"
	# testData is a list of duples consisting of:
	# - input data
	# - the expected output
	testData = (
		(51000, 1998.50924024641),
		(15000, 1899.94661190965),
		(30000, 1941.01437371663),
		(    0, 1858.87885010267),
	)
	for testInput, expectedOutput in testData:
		actualOutput = epj(testInput)
		if 0 != RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-15):
			print "failed on input:", testInput
			print "expected output:", expectedOutput
			print "actual output  :", actualOutput
