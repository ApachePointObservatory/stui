#!/usr/local/bin/python
import math
import Numeric
import RO.PhysConst
from euler import *

def prebn (bep0, bep1):
	"""
	Generate the matrix of precession between two epochs,
	using the old, pre-IAU1976, Bessel-Newcomb model,
	using Kinoshita's formulation.
	
	Inputs:
	- bep0		beginning Besselian epoch
	- bep1		ending Besselian epoch
	
	Returns:
	- pMat		the precession matrix, a 3x3 Numeric.array
	
	The matrix is in the sense	p(bep1)  =  pMat * p(bep0)
	
	Reference:
	Kinoshita, H. (1975) 'Formulas for precession', SAO Special
	Report No. 364, Smithsonian Institution Astrophysical
	Observatory, Cambridge, Massachusetts.
	
	History:
	P.T.Wallace	Starlink	30 December 1992
	2002-07-11 ROwen  Converted to Python from PREBN
	2004-05-18 ROwen  Removed import of Numeric from test code.
	"""
	# Interval between basic epoch b1850.0 and beginning epoch,
	# in tropical centuries
	bigt = (bep0-1850.0)/100.0

	# Interval over which precession required, in tropical centuries
	t = (bep1-bep0)/100.0

	# Euler angles
	tas2r = t*RO.PhysConst.RadPerArcSec
	w = 2303.5548+(1.39720+0.000059*bigt)*bigt

	zeta = (w+(0.30242-0.000269*bigt+0.017996*t)*t)*tas2r
	z = (w+(1.09478+0.000387*bigt+0.018324*t)*t)*tas2r
	theta = (2005.1125+(-0.85294-0.000365*bigt)*bigt+  \
		(-0.42647-0.000365*bigt-0.041802*t)*t)*tas2r

	# Rotation matrix
	return euler([(2, -zeta), (1, theta), (2, -z)])


if __name__ == "__main__":
	print "testing prebn"
	# testData is a list of duples consisting of:
	# - a tuple of input data for prebn
	# - the expected output matrix (a Numeric.array)
	testData = (
		((1950, 2050), (
			(  0.999702925227436     , -2.235400672121219E-002, -9.713890838176736E-003),
			(  2.235400653972023E-002,  0.999750112076083     , -1.086070028410654E-004),
			(  9.713891255833509E-003, -1.085696408823337E-004,  0.999952813151352     ),
		)),
		((1970, 2070), (
			(  0.999702872690676     , -2.235671596278743E-002, -9.713062615332701E-003),
			(  2.235671578129640E-002,  0.999750051494445     , -1.086109082376431E-004),
			(  9.713063033073562E-003, -1.085735432862135E-004,  0.999952821196231     ),
		)),
		((2030, 1990), (
			(  0.999952461856730     ,  8.942888422119049E-003,  3.885714005854547E-003),
			( -8.942888426765425E-003,  0.999960011422823     , -1.737397063945970E-005),
			( -3.885713995161012E-003, -1.737636209952268E-005,  0.999992450433907     ),
		)),
		((2030, 2100), (
			(  0.999854346003950     , -1.565475935755611E-002, -6.798182585786489E-003),
			(  1.565475931397953E-002,  0.999877455330509     , -5.322224165938840E-005),
			(  6.798182686134024E-003, -5.320942252576248E-005,  0.999976890673441     ),
		)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = prebn(*testInput)
		if not Numeric.allclose(actualOutput, expectedOutput, rtol=1e-15, atol=1e-15):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput


