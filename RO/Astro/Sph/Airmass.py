#!/usr/local/bin/python
import RO.MathUtil

# constants
_MinAlt = 3.0

def airmass (alt):
	"""Computes the airmass at a given altitude.
	
	Inputs:
	- alt	the observed altitude, as affected by refraction (deg)
	
	Returns an estimate of the air mass, in units of that at the zenith.

	Warnings:	
	- Alt < _MinAlt is treated as _MinAlt to avoid arithmetic overflow.

	Adapted from AIRMAS by Pat Wallace, whose notes follow:
	
	Uses Hardie's (1962) polynomial fit to Bemporad's data for
	the relative air mass, X, in units of thickness at the zenith
	as tabulated by Schoenberg (1929). This is adequate for all
	normal needs as it is accurate to better than 0.1% up to X =
	6.8 and better than 1% up to X = 10. Bemporad's tabulated
	values are unlikely to be trustworthy to such accuracy
	because of variations in density, pressure and other
	conditions in the atmosphere from those assumed in his work.
	
	References:
	- Hardie, R.H., 1962, in "Astronomical Techniques"
	  ed. W.A. Hiltner, University of Chicago Press, p180.
	- Schoenberg, E., 1929, Hdb. d. Ap.,
	  Berlin, Julius Springer, 2, 268.
	
	History:
	Original code by P.W.Hill, St Andrews
	Adapted by P.T.Wallace, Starlink, 5 December 1990
	2002-08-02 ROwen  Converted to Python
	"""
	# secM1 is secant(zd) - 1 where zd = 90-alt
	secM1 = (1.0 / (RO.MathUtil.sind(max(_MinAlt, alt)))) - 1.0

	return 1.0 + secM1 * (0.9981833 - secM1 * (0.002875 + (0.0008083 * secM1)))


if __name__ == "__main__":
	print "testing airmass"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(90, 1.00000000000000),
		(80, 1.01539789919896),
		(70, 1.06404912554392),
		(60, 1.15434769607778),
		(50, 1.30456126868380),
		(40, 1.55368763671996),
		(30, 1.99450000000000),
		(20, 2.90391385011086),
		(10, 5.59791051025326),
		( 3, 13.3329567893470),
		( 0, 13.3329567893470),
	)
	for testInput, expectedOutput in testData:
		actualOutput = airmass(testInput)
		if RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1.0e-14):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
