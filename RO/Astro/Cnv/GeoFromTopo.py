#!/usr/local/bin/python
import Numeric
import RO.MathUtil
from RO.Astro import llv
from HADecFromAzAlt import *

def geoFromTopo (appTopoP, last, obsData):
	"""
	Converts apparent topocentric coordinates to apparent geocentric coordinates.
	
	Inputs:
	- appTopoP(3)	apparent topocentric cartesian position (au) (az/alt)
	- last			local apparent sidereal time, as an angle (deg)
	- obsData		an ObserverData object
	
	Returns:
	- appGeoP(3)	apparent geocentric cartesian position (au) (RA/Dec), a Numeric.array
	
	Warnings:
	Computation of diurnal aberration is slightly approximate (see notes below),
	but not enough to make a difference on the sky.
	
	References:
	see topoFromGeo (note: the variables are identical)
	
	History:
	2002-07-22 ROwen	Converted to Python from the TCC's cnv_AppTopo2AppGeo 3-3.
	2002-12-23 ROwen	Cosmetic change to make pychecker happy.
	2004-05-18 ROwen	Stopped importing math; it wasn't used.
	"""
	#  compute useful quantities
	sinLAST = RO.MathUtil.sind (last)
	cosLAST = RO.MathUtil.cosd (last)

	#  rotate apparent topocentric position to HA/Dec;
	posC = haDecFromAzAlt (appTopoP, obsData.latitude)

	#  remove correction for diurnal aberration
	#  following Pat Wallace's sla_OAPQK, the same equation is used
	#  as applying the correction, but the sign of obsData.diurAbVecMag is reversed
	cDir, cMag = llv.vn(posC)
	diurAbScaleCorr = 1.0 + (obsData.diurAbVecMag * cDir[1])
	posB = Numeric.array ((
		 posC[0] * diurAbScaleCorr,
		(posC[1] - (obsData.diurAbVecMag * cMag)) * diurAbScaleCorr,
		 posC[2] * diurAbScaleCorr,
	))

	#  correct position for diurnal parallax (needed for planets, not stars)
	posA = posB + obsData.p

	#  rotate position from (-HA)/Dec to RA/Dec (but cartesian)
	return Numeric.array((
		cosLAST * posA[0] - sinLAST * posA[1],
		sinLAST * posA[0] + cosLAST * posA[1],
		posA[2],
	))


if __name__ == "__main__":
	import RO.SeqUtil
	from ObserverData import ObserverData
	print "testing geoFromTopo"
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
			(7521.37033559025, 35805.5922131246, 7835.08500923872)), 
		(((-2000, 1000, 4000), -27, obsData), 
			(2485.63380728737, -144.173843397214, 3847.18583114423)), 
		(((10000, 0, 0), 180, obsData), 
			(-5414.20065066055, 1.306204228130181E-002, -8407.52230547073)), 
		(((0, 0, 50000), 56, obsData), 
			(23507.1882738484, 34850.7230205824, 27071.0030967816)), 
		(((1, 1, 40000), 72, obsData), 
			(10391.5350741673, 31984.9234130943, 21655.9617304920)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = geoFromTopo(*testInput)
		if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-10):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
