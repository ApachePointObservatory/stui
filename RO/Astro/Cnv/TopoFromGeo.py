#!/usr/local/bin/python
import Numeric
import RO.MathUtil
from RO.Astro import llv
from AzAltFromHADec import *

def topoFromGeo (appGeoP, last, obsData):
	"""
	Converts apparent geocentric coordinates to apparent topocentric coordinates
	(not corrected for refraction).
	
	Inputs:
	- appGeoP(3)	current app. geocentric cartesian position (au) (RA/Dec)
	- last			local apparent sidereal time, as an angle (deg)
	- obsData		an ObserverData object
	
	Returns:
	- appTopo(3)	apparent topocentric cartesian position (au) (az/alt), a Numeric.array
	
	Details:
	The following approximation is used:
	- pole wander is ignored
	
	References:
	P.T. Wallace, "Proposals for Keck Tel. Pointing Algorithms", 1986 (unpub)
	
	History:
	2002-07-22 ROwen  Converted to Python from the TCC's cnv_AppGeo2AppTopo 7-3.
	2004-05-18 ROwen	Stopped importing math; it wasn't used.
	"""
	sinLAST = RO.MathUtil.sind (last)
	cosLAST = RO.MathUtil.cosd (last)

	#  rotate position and offset to (-ha)/Dec (still cartesian, of course)
	posA = Numeric.array((
		 cosLAST * appGeoP[0] + sinLAST * appGeoP[1],
		-sinLAST * appGeoP[0] + cosLAST * appGeoP[1],
		 appGeoP[2],
	))

	#  correct position for diurnal parallax
	posB = posA - obsData.p

	#  correct position for diurnal aberration
	#  follows Pat Wallace's AOPQK
	bDir, bMag = llv.vn(posB)
	diurAbScaleCorr = 1.0 - (obsData.diurAbVecMag * bDir[1])
	posC = Numeric.array ((
		 posB[0] * diurAbScaleCorr,
		(posB[1] + (obsData.diurAbVecMag * bMag)) * diurAbScaleCorr,
		 posB[2] * diurAbScaleCorr,
	))

	#  rotate position (posC) to alt/az;
	return azAltFromHADec (posC, obsData.latitude)


if __name__ == "__main__":
	import RO.SeqUtil
	from ObserverData import ObserverData
	print "testing topoFromGeo"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	# this test data was determined using cnv_AppGeo2AppTopo 7-3
	# jimmied to use mean longitude and latitude
	# (no adjustment for pole wander)
	# and using the position of the APO 3.5m telescope
	obsData = ObserverData(
		latitude  =   32.780361, 
		longitude = -105.820417,
		elevation =    2.788,
	)
	testData = (
        (((10000, 20000, 30000), 45, obsData),
                (-13737.3096861678, 7071.11494005153, 34077.6415438682)),
        (((-2000, 1000, 4000), -27, obsData),
                (-4573.62613211440, -16.9684895930802, 285.755228951995)),
        (((10000, 0, 0), 180, obsData),
                (-5414.20061489404, 1.306204232819004E-002, -8407.52237104441)),
        (((0, 0, 50000), 56, obsData),
                (-42037.6116422920, 6.531021137651641E-002, 27071.0030312079)),
        (((1, 1, 40000), 72, obsData),
                (-33629.4070854871, -0.589791352804704, 21657.8618265157)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = topoFromGeo(*testInput)
		if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-10):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
