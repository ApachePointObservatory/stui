#!/usr/local/bin/python
from AngSideAng import *
from SCFromCCPV import *
from SCFromCC import *

def scFromCCPVOff (p, v, offP):
	"""
	Converts cartesian position, velocity and offset to spherical coordinates
	(see also SCFromCC and SCFromCCPV).
	
	Inputs:
	- p(3)		position (au)
	- v(3)		velocity (au per year)
	- offP(3)	offset position (au)
	
	Returns:
	- pos(2)	spherical position (degrees)
				ranges: axis 1: [0, 360), axis 2: [-90,90]
	- pm(2)		proper motion (arcsec per century)
	- parlax	parallax (arcsec)
	- radVel	radial velocity (km/s)
	- offDir	offset direction (degrees):
				dir. of increasing pos[0] = 0
				dir. of increasing pos[1] = 90
	- offMag	magnitude of offset (degrees on the sky)
	- atPole	true if at a pole; see "Error Cond." for implications
	
	Error Conditions:
	- Raises ValueError if |p| is too small to safely compute.
		
	- If p is very near a pole, atPole is set true,
	  pos[1], pm[0], pm[1] and offDir are set to zero;
	  pos[0], parlax, radVel and offMag are still computed correctly
	  (pos[0] is +/-90.0, as appropriate).
	
	- If inputs are too large, overflows are possible--roughly if p^2 or v^2 overflows.
	
	History
	2002-08-22 ROwen  Converted to Python from the TCC's sph_CCPVOff2SC 6-1.
	"""
	#  convert p and v from cartesian to spherical
	pos, pm, parlax, radVel, atPole = scFromCCPV (p, v)
	
	#  convert offP from cartesian to spherical
	offPos, magOffP, offAtPole = scFromCC (offP)
	
	#  compute offset direction and magnitude
	ang_A, side_bb, ang_C, offAtPole2 = angSideAng (
		90.0 - pos[1], offPos[0] - pos[0], 90.0 - offPos[1],
	)
	offMag = side_bb
	if atPole:
		offDir = 0.0
	else:
		offDir = 90.0 - ang_C

	return (pos, pm, parlax, radVel, offDir, offMag, atPole)



if __name__ == "__main__":
	import RO.SeqUtil
	print "testing scFromCCPVOff"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((10000, 20000, 30000), (40, 50, 60), (11000, 19000, 28000)), 
		    ((63.4349488229220, 53.3007747995101), (-12375.8883748258, -7906.66505373138), 
		       5.51265882804246, 405.422085569533, 
		      -148.051940568670, 2.54694063720967, 0)), 
		(((-10000, 20000, 30000), (40, 50, 60), (-11000, 19000, 28000)), 
		    ((116.565051177078, 53.3007747995101), (-53628.8496242450, 7906.66505373139), 
		       5.51265882804246, 304.066564177150, 
		      -31.9480594313300, 2.54694063720964, 0)), 
		(((-10000, -20000, 30000), (40, 50, 60), (-11000, -19000, 28000)), 
		    ((243.434948822922, 53.3007747995101), (12375.8883748258, 47439.9903223883), 
		       5.51265882804246, 50.6777606961916, 
		      -148.051940568670, 2.54694063720967, 0)), 
		(((-10000, -20000, -30000), (40, 50, 60), (-11000, -19000, -28000)), 
		    ((243.434948822922, -53.3007747995101), (12375.8883748258, -7906.66505373138), 
		       5.51265882804246, -405.422085569533, 
		      -211.948059431330, 2.54694063720964, 0)), 
		(((10000, 20000, 30000), (40, 50, 60), (10001, 19999, 29999)), 
		    ((63.4349488229220, 53.3007747995101), (-12375.8883748258, -7906.66505373138), 
		       5.51265882804246, 405.422085569533, 
		      -169.897388208472, 2.086861750740354E-003, 0)), 
		(((0, 0, 30000), (40, 50, 60), (10001, 19999, 29999)), 
		    ((0.000000000000000, 90.0000000000000), (0.000000000000000, 0.000000000000000), 
		       6.87549354156988, 284.428226481101, 
		      0.000000000000000, 36.6995913096756, 1)), 
	)
	for testInput, expectedOutput in testData:
		actualOutput = scFromCCPVOff(*testInput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-10, atol=1.0e-10):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
