#!/usr/local/bin/python
import RO.PhysConst
import RO.MathUtil
from CCFromSC import *

# Magic Numbers
# if parallax is less than _MinParallax,
# then _MinParallax is used and the "atInf" flag is set
_MinParallax = 1.0e-7  # arcsec

# Constants
_RadPerYear_per_ASPerCy = RO.PhysConst.RadPerDeg / (RO.PhysConst.ArcSecPerDeg * 100.0)
_AUPerYear_per_KMPerSec = RO.PhysConst.SecPerDay * RO.PhysConst.DayPerYear / RO.PhysConst.KmPerAU

def ccFromSCPV (
	pos,
	pm,
	parallax,
	radVel,
):
	"""
	Converts spherical position and velocity to cartesian coordinates.
	
	Inputs:
	- pos(2)	spherical position
	- pm(2)		proper motion ("/century)
	- parallax	parallax (arcsec)
	- radVel	radial velocity (km/s, positive receding)
	
	Returns a tuple consisting of:
	- p	cartesian position (au)
	- v	cartesian velocity (au/year)
	- atInf	true if object is very far away(see Details)
	
	Error Conditions:
	- Raises ValueError if pos[1] is not in the range -90 to 90 deg
	
	Warnings:
	- Negative parallax is silently treated as zero parallax (object at infinity).
	
	Details:
	- Proper motion is dPos/dt, not rate on the sky; in other words,
	  pm[0] gets large near the pole.
	
	- If the star is very far away (parallax < _MinParallax), atInf is set true,
	the distance is set to that limit and radial velocity is treated as zero.
	
	- We could handle any range of pos[1] by checking to see if it's
	in quadrants ii or iii, and if so, adding 180 degrees to offDir
	and possibly negating pm[0] and pm[1]. However, it's not certain that's
	what the user wanted, so for now avoid all that math and just complain.
	
	History
	2002-07-08 ROwen	Converted from TCC's sph_SCPV2CC 1-1.
	2002-12-23 ROwen	Cosmetic change to make pychecker happy.
	"""
	# handle case of parallax too small ("at infinity")
	if (parallax >= _MinParallax):
		atInf = 0
	else:
		atInf = 1
		parallax = _MinParallax
		radVel = 0.0

	# compute distance in au; note that distance (parsecs) = 1/parallax (")
	distAU = RO.PhysConst.AUPerParsec / parallax
	
	# compute p
	p = ccFromSC (pos, distAU)

	# compute useful quantities
	sinP0 = RO.MathUtil.sind(pos[0])
	cosP0 = RO.MathUtil.cosd(pos[0])
	sinP1 = RO.MathUtil.sind(pos[1])
	cosP1 = RO.MathUtil.cosd(pos[1])

	# change units of proper motion from "/cy to au/year
	# (multiply by distance and fix the units)
	# pm(au/year) = pm ("/cy) distAU(au) (rad/year) / ("/cy)
	pmAUPerYr = [x * distAU * _RadPerYear_per_ASPerCy for x in pm]

	# change units of radial velocity from km/sec to au/year
	radVelAUPerYr = radVel * _AUPerYear_per_KMPerSec 

	# compute velocity vector in au/year
	v = (
		- pmAUPerYr[0]*cosP1*sinP0 - pmAUPerYr[1]*sinP1*cosP0 + radVelAUPerYr*cosP1*cosP0,
		  pmAUPerYr[0]*cosP1*cosP0 - pmAUPerYr[1]*sinP1*sinP0 + radVelAUPerYr*cosP1*sinP0,
		                             pmAUPerYr[1]*cosP1       + radVelAUPerYr*sinP1,
	)
	
	return (p, v, atInf)


if __name__ == "__main__":
	import RO.SeqUtil
	print "testing ccFromSCPV"
	# test data is formatted as follows:
	# a list of entries, each consisting of:
	# - the input argument
	# - the expected result
	testData = (
		(((30, 60), (100, 200), 5, 300),
			((	 17863.0562116661	  ,   10313.2403123548	   ,   35726.1124233321 	),
			(	27.0531474670740	 ,	 15.7346120263798	  ,   55.0062949341481	   ), 0)),
		(((30, 60), (100, 200), 5, -300),
			((	 17863.0562116661	  ,   10313.2403123548	   ,   35726.1124233321 	),
			(  -27.7531474670740	 ,	-15.9078171071366	  ,  -54.6062949341481	   ), 0)),
		(((30, 60), (-100, -200), 5, 300),
			((	 17863.0562116661	  ,   10313.2403123548	   ,   35726.1124233321 	),
			(	27.7531474670740	 ,	 15.9078171071366	  ,   54.6062949341481	   ), 0)),
		(((0, 0), (-100, -200), 5, 300),
			((	 41252.9612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(	63.2848582670328	 , -0.200000000000000	  , -0.400000000000000	   ), 0)),
		(((0, 0), (100, 200), 5, 300),
			((	 41252.9612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(	63.2848582670328	 ,	0.200000000000000	  ,  0.400000000000000	   ), 0)),
		(((0, 0), (100, 200), 5, 30), 
			((	 41252.9612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(	6.32848582670328	 ,	0.200000000000000	  ,  0.400000000000000	   ), 0)),
		(((0, 0), (100, 200), 5, 3), 
			((	 41252.9612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  0.632848582670328	 ,	0.200000000000000	  ,  0.400000000000000	   ), 0)),
		(((0, 0), (100, 200), 5, -3),
			((	 41252.9612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			( -0.632848582670328	 ,	0.200000000000000	  ,  0.400000000000000	   ), 0)),
		(((90, 0), (100, 200), 5, -3),
			((	0.000000000000000E+000,   41252.9612494193	   ,  0.000000000000000E+000),
			( -0.200000000000000	 , -0.632848582670328	  ,  0.400000000000000	   ), 0)),
		(((30, 60), (100, 200), 5, -3),
			((	 17863.0562116661	  ,   10313.2403123548	   ,   35726.1124233321 	),
			( -0.624031474670740	 , -0.244814686046026	  , -0.348062949341481	   ), 0)),
		(((30, 60), (-100, -200), 5, -3),
			((	 17863.0562116661	  ,   10313.2403123548	   ,   35726.1124233321 	),
			(  7.596852532925974E-002, -7.160960528913816E-002, -0.748062949341481	   ), 0)),
		(((30, 60), (-100, -200), 0.5, -3),
			((	 178630.562116661	  ,   103132.403123548	   ,   357261.124233321 	),
			(	3.22596852532926	 ,	0.707813258116857	  ,  -2.54806294934148	   ), 0)),
		(((0, 0), (-100, -200), 0.5, -3),
			((	 412529.612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			( -0.632848582670328	 ,	-2.00000000000000	  ,  -4.00000000000000	   ), 0)),
		(((0, 0), (-100, -200), 0.5, -30),
			((	 412529.612494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  -6.32848582670328	 ,	-2.00000000000000	  ,  -4.00000000000000	   ), 0)),
		(((0, 0), (-10, -20), 0.05, -30),
			((	 4125296.12494193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  -6.32848582670328	 ,	-2.00000000000000	  ,  -4.00000000000000	   ), 0)),
		(((10, 70), (-10, -20), 0.05, -30),
			((	 1389499.10845179	  ,   245006.182490408	   ,   3876510.32716463 	),
			(	1.68886219054623	 , -0.396800739776020	  ,  -7.31491200540396	   ), 0)),
		(((10, -70), (-10, -20), 0.05, -30),
			((	 1389499.10845179	  ,   245006.182490408	   ,  -3876510.32716463 	),
			(  -5.71447043664036	 ,	-1.70220802910830	  ,   4.57875085879861	   ), 0)),
		(((10, 89.9999999999), (-10, -20), 0.05, -30),
			((	7.090742363007187E-006,  1.250289191850664E-006,   4125296.12494193 	),
			(	3.93923101203856	 ,	0.694592710662366	  ,  -6.32848582671026	   ), 0)),
		(((10, -70), (-10, -20), 0.05, -30),
			((	 1389499.10845179	  ,   245006.182490408	   ,  -3876510.32716463 	),
			(  -5.71447043664036	 ,	-1.70220802910830	  ,   4.57875085879861	   ), 0)),
		(((10, -70), (-10, -20), 0.0000005, -30),
			((	 138949910845.179	  ,   24500618249.0408	   ,  -387651032716.463 	),
			(  -358290.528023025	 ,	-132635.558089514	  ,  -136802.110498835	   ), 0)),
		(((0, 0), (-0.001, -0.002), 0.0000005, -30),
			((	 412529612494.193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  -6.32848582670328	 ,	-20.0000000000000	  ,  -40.0000000000000	   ), 0)),
		(((0, 0), (-0.001, -0.002), 0.0000005, -300),
			((	 412529612494.193	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  -63.2848582670328	 ,	-20.0000000000000	  ,  -40.0000000000000	   ), 0)),
		(((0, 0), (-0.001, -0.002), 0.000000005, -300),
			((	 2062648062470.96	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  0.000000000000000E+000,	-100.000000000000	  ,  -200.000000000000	   ), 1)),
		(((0, 0), (-0.001, -0.002), 0.000000005, -30000),
			((	 2062648062470.96	  ,  0.000000000000000E+000,  0.000000000000000E+000),
			(  0.000000000000000E+000,	-100.000000000000	  ,  -200.000000000000	   ), 1)),
		(((80, 30), (-0.001, -0.002), 0.000000005, -30000),
			((	 310188715871.775	  ,   1759167624974.16	   ,   1031324031235.48 	),
			(	102.651670961937	 ,	 83.4424019831773	  ,  -173.205080756888	   ), 1)),
	)
	for testInput, expectedOutput in testData:
		actualOutput = ccFromSCPV(*testInput)
		actualFlat = RO.SeqUtil.flatten(actualOutput)
		expectedFlat = RO.SeqUtil.flatten(expectedOutput)
		if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14, atol=1.0e-9):
			print "failed on input:", testInput
			print "expected output:\n", expectedOutput
			print "actual output:\n", actualOutput
