#!/usr/local/bin/python
from nutc import nutc
from euler import euler

def nut (tdb):
	"""
	Form the matrix of nutation for a given TDB - IAU 1980 theory
	(double precision)
	
	References:
	Final report of the IAU Working Group on Nutation,
	chairman P.K.Seidelmann, 1980.
	Kaplan,G.H., 1981, USNO circular no. 163, pA3-6.
	
	Inputs:
	- TDB	TDB date (loosely et) as Modified Julian Date

	Returns the nutation matrix as a 3x3 Numeric.array
	
	The matrix is in the sense	V(true)  =  rmatn * V(mean)
	
	History:	
	P.T.Wallace	Starlink	1 January 1993
	2002-07-11 ROwen  Converted to Python.
	"""
	# Nutation components and mean obliquity
	dpsi, deps, eps0 = nutc(tdb)

	# Rotation matrix
	return euler((
		(0, eps0), (2, -dpsi), (0, -(eps0+deps))
	))


if __name__ == "__main__":
	import Numeric
	print "testing nut"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument for nut
	# - the expected resulting matrix
	testData = (
		(1850, Numeric.array((
			(0.999999997740556     , -6.166733319512448E-005, -2.675868442177890E-005),
			(6.166806861174569E-005,  0.999999997720858     ,  2.748333298885353E-005),
			(2.675698953693931E-005, -2.748498308319247E-005,  0.999999999264320     ),
		))),
		(1900, Numeric.array((
			(0.999999997261050     , -6.789636996613104E-005, -2.946156251173922E-005),
			(6.789714782419645E-005,  0.999999997346449     ,  2.640227464817402E-005),
			(2.945976981495399E-005, -2.640427493189046E-005,  0.999999999217468     ),
		))),
		(1950, Numeric.array((
			(0.999999997705095     , -6.214938713894101E-005, -2.696781135198901E-005),
			(6.215005719845853E-005,  0.999999997760011     ,  2.484651402678839E-005),
			(2.696626709596209E-005, -2.484819002079863E-005,  0.999999999327694     ),
		))),
		(2000, Numeric.array((
			(0.999999998322670     , -5.313294781937530E-005, -2.305538574830272E-005),
			(5.313364356569443E-005,  0.999999998133064     ,  3.017760795070989E-005),
			(2.305378227999123E-005, -3.017883291672740E-005,  0.999999999278881     ),
		))),
		(2050, Numeric.array((
			(0.999999998097855     , -5.658176058949696E-005, -2.455186961347029E-005),
			(5.658258269842343E-005,  0.999999997838577     ,  3.348517274825991E-005),
			(2.454997491037558E-005, -3.348656189278154E-005,  0.999999999137974     ),
		))),
	)
	for testInput, expectedOutput in testData:
		actualOutput = nut(testInput)
		if not Numeric.allclose(actualOutput, expectedOutput, rtol=1e-15, atol=1e-15):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput

