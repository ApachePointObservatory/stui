#!/usr/local/bin/python
import math
import RO.MathUtil
import RO.SysConst

def scFromCC (p):
	"""
	Converts cartesian position to spherical coordinates.
	
	Inputs:
	- p(3)		cartesian position (arbitrary units)
	
	Returns a tuple containing:
	- pos(2):	spherical position (deg) as equatorial, polar angle,
				e.g. (RA, Dec), (-HA, Dec) or (Az, Alt);
	  			ranges are: pos[0]: [0, 360), pos[1]: [-90,90]
	- magP:		magnitude of p (same units as p)
	- atPole:	True if very near the pole, in which case pos[1] = 0,
				and pos[0] = +/- 90 as appropriate.
	
	Error Conditions:
	- If |p| is too small, raises ValueError.
	- If |p| is too large, overflows are possible--roughly if p^2 overflows.
	
	History
	2002-07-23 ROwen	Converted from TCC's sph_SC2CC 1-1.
	2003-05-06 ROwen	Modified to use FAccuracy instead of FSmallNum;
						this is more realistic and fixes HADecFromAzAlt.
	"""
	x, y, z = p

	magPxySq = float((x * x) + (y * y))
	magPSq   = magPxySq + (z * z)
	magP   = math.sqrt (magPSq)

	# make sure |p| is large enough
	# one gains margin by testing |p|^2 instead of |p|
	if magPSq < RO.SysConst.FAccuracy:
		raise ValueError, '|p| too small; p=%r' % (p,)

	# check to see if too near the pole
	# one gains margin by testing |pxy|^2 instead of |pxy|
	if magPxySq < RO.SysConst.FAccuracy:
		# too near pole
		atPole = True
		pos1 = 0.0
		if (z > 0.0):
			pos2 =  90.0
		else:
			pos2 = -90.0
	else:
		atPole = False
		
		# compute position (in degrees)
		pos1 = RO.MathUtil.atan2d (y, x)
		pos2 = RO.MathUtil.atan2d (z, math.sqrt(magPxySq))
	
		# put pos1 into the range [0,360); presently it's in range (-180,180]
		if (pos1 < 0.0):
			pos1 += 360.0

	return ((pos1, pos2), magP, atPole)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing scFromCC"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		((0.984807753012208, 0.173648177666930, 0.000000000000000), ((10, 0), 1.0, False)),
		((9.69846310392954, 1.71010071662834, 1.73648177666930), ((10, 10), 10.0, False)),
		((96.9846310392954, -17.1010071662834, -17.3648177666930), ((350, -10), 100.0, False)),
		((500.000000000000, 500.000000000000, 707.106781186548), ((45, 45), 1000.0, False)),
		((0.224143868042013, 0.836516303737808, 0.500000000000000), ((75, 30), 1.0, False)),
		((0.000000000000000, 0.000000000000000, 1.00000000000000), ((0, 90), 1.0, True)),
		((-8.682408883346518e-002, 0.150383733180435, -0.984807753012208), ((120, -80), 1.0, False)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = scFromCC(testInput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
