#!/usr/local/bin/python
import RO.MathUtil
from AngSideAng import *
from CCFromSC import *
from CCFromSCPV import *

def ccFromSCPVOff (pos, pm, parlax, radVel, offDir, offMag):
	"""
	Converts spherical to cartesian coordinates, including position, velocity
	and and a local offset along a great circle from the position vector.
	See also ccFromSCPV and ccFromSC.
	
	Inputs:
	- pos(2)	spherical position (degrees);
				pos[1] must be in the range [-90,90]
	- pm(2)		proper motion (arcsec per century)
	- parlax	parallax (arcsec)
	- radVel	radial velocity (km/s, positive receding)
	- offDir	offset direction (degrees):
				dir. of increasing pos[0] = 0, pos[1] = 90
	- offMag	offset magnitude (degrees on the sky)
	
	Returns:
	- p(3)		position vector (au)
	- v(3)		velocity (au per year)
	- offP(3)	offset position vector (au)
	- atInf		true if object is very far away (see Details)
	
	Error Conditions:
	- Raises ValueError if pos[1] is not in the range -90 to 90 deg
	
	Warnings:
	- Negative parallax is silently treated as zero parallax (object at infinity).
	
	Details:
	- See Sph.CCFromSCPV for more information.
	
	History
	2002-08-22 ROwen  Converted to Python from the TCC's sph_SCPVOff2CC 6-1.
	"""
	# convert spherical position and velocity to cartesian
	p, v, atInf = ccFromSCPV (pos, pm, parlax, radVel)
	
	# compute spherical coordinates of the offset position;
	# ignore the case of the offset position being at the pole,
	# as the standard calculations work fine for that case
	# (sets side_bb = 0 and ang_A = ang_C = 90)
	ang_A, side_bb, ang_C, offPosAtPole = angSideAng (90.0 - pos[1], 90.0 - offDir, offMag)
	offPos = (
		pos[0] + ang_C,
		90.0 - side_bb,
	)
	
	# convert the offset position to cartesian coordinates
	# (the offset is assumed to be long a great circle,
	# so the magnitude is exactly the same as the un-offset position)
	magP = RO.MathUtil.vecMag(p)
	offP = ccFromSC (offPos, magP)
	
	return (p, v, offP, atInf)



if __name__ == "__main__":
	import RO.SeqUtil
	print "testing ccFromSCPVOff"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((30, 60), (100, 200), 5, 300, 0, 0.01), 
		    ((17863.0562116661, 10313.2403123548, 35726.1124233321), 
		    (27.0531474670740, 15.7346120263798, 55.0062949341481), 
		    (17859.4559396144, 10319.4755381508, 35726.1118791923), 0)), 
		(((30, 60), (100, 200), 5, 300, 0, 1), 
		    ((17863.0562116661, 10313.2403123548, 35726.1124233321), 
		    (27.0531474670740, 15.7346120263798, 55.0062949341481), 
		    (17500.3538584502, 10935.1761903380, 35720.6711633667), 0)), 
		(((30, 60), (100, 200), 5, 300, 0, 0.001), 
		    ((17863.0562116661, 10313.2403123548, 35726.1124233321), 
		    (27.0531474670740, 15.7346120263798, 55.0062949341481), 
		    (17862.6962089454, 10313.8638490747, 35726.1124178907), 0)), 
		(((0, 0), (100, 200), 5, 300, 0, 0.001), 
		    ((41252.9612494193, 0.000000000000000, 0.000000000000000), 
		    (63.2848582670328, 0.200000000000000, 0.400000000000000), 
		    (41252.9612431361, 0.719999999966884, 0.000000000000000), 0)), 
		(((90, 0), (100, 200), 5, 300, 0, 0.001), 
		    ((0.000000000000000, 41252.9612494193, 0.000000000000000), 
		    (-0.200000000000000, 63.2848582670328, 0.400000000000000), 
		    (-0.719999999966884, 41252.9612431361, 0.000000000000000), 0)), 
		(((0, 90), (100, 200), 5, 300, 0, 0.001), 
		    ((0.000000000000000, 0.000000000000000, 41252.9612494193), 
		    (-0.400000000000000, 0.000000000000000, 63.2848582670328), 
		    (0.000000000000000, 0.719999999966884, 41252.9612431361), 0)), 
		(((10, 70), (100, 200), 5, 300, 0, 0.001), 
		    ((13894.9910845179, 2450.06182490408, 38765.1032716463), 
		    (20.9338198564662, 3.76065652105237, 59.6051223783431), 
		    (13894.8660557136, 2450.77088611304, 38765.1032657421), 0)), 
		(((10, 70), (100, 200), 5, 300, 45, 0.001), 
		    ((13894.9910845179, 2450.06182490408, 38765.1032716463), 
		    (20.9338198564662, 3.76065652105237, 59.6051223783431), 
		    (13894.4315299794, 2450.48013117274, 38765.2773939712), 0)), 
		(((10, 70), (100, 200), 5, 300, -45, 0.001), 
		    ((13894.9910845179, 2450.06182490408, 38765.1032716463), 
		    (20.9338198564662, 3.76065652105237, 59.6051223783431), 
		    (13895.3738203861, 2450.64628239510, 38764.9291375130), 0)), 
		(((10, 70), (100, 200), 50, 300, -45, 0.001), 
		    ((1389.49910845179, 245.006182490408, 3876.51032716463), 
		    (21.2776602361201, 3.75877151308230, 59.4819951267459), 
		    (1389.53738203861, 245.064628239510, 3876.49291375130), 0)), 
		(((10, 70), (100, 200), 0.5, 300, -45, 0.001), 
		    ((138949.910845179, 24500.6182490408, 387651.032716463), 
		    (17.4954160599272, 3.77950660075308, 60.8363948943155), 
		    (138953.738203861, 24506.4628239510, 387649.291375130), 0)), 
		(((10, 70), (100, 200), 0, 300, -45, 0.001), 
		    ((694749554225.895, 122503091245.204, 1938255163582.32), 
		    (-19102243.3141053, 104722.665003954, 6840402.86651338), 
		    (694768691019.303, 122532314119.755, 1938246456875.65), 1)), 
	)
	for testInput, expectedOutput in testData:
		actualOutput = ccFromSCPVOff(*testInput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14, atol=1.0e-9):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
