#!/usr/bin/env python
import math
import RO.PhysConst
from SCFromCC import *

# Constants
_ASPerCy_Per_RadPerYear = 100.0 * RO.PhysConst.ArcSecPerDeg / RO.PhysConst.RadPerDeg
_KMPerSec_Per_AUPerYear = RO.PhysConst.KmPerAU / (RO.PhysConst.DayPerYear * RO.PhysConst.SecPerDay)

def scFromCCPV (p, v):
    """
    Converts cartesian position and velocity to spherical coordinates
    (if you just want to convert position, use sph_CC2SC).
    
    Inputs:
    p(3)    cartesian position (au)
    v(3)    cartesian velocity (au per year)
    
    Returns a tuple containing:
    pos(2)  spherical position (degrees)
            ranges: pos[0]: [0, 360), pos[1]: [-90,90]
    pm(2)   proper motion (arcsec per century)
            dpos/dt, not velocity on the sky (i.e. large near the poles)
    parallax    parallax (arcsec)
    radVel  radial velocity (km/s, positive receding)
    atPole  true if at a pole; see "Error Cond." for implications
    
    Error Conditions:
    Raises valueError if |p| is too small
    
    If p is very near a pole, atPole is set true and pos[1], pm[0] and pm[1]
    are set to zero; pos[0], parallax and radVel are computed correctly
    (pos[0] is +/-90.0, as appropriate).
    
    If inputs are too large, overflows are possible--roughly if
    p^2 or v^2 overflows.
    
    History
    2002-07-08 ROwen  Converted from TCC's sph_SCPV2CC 1-1.
    """
    x, y, z = p
    vX, vY, vZ = v
    
    pos, magP, atPole = scFromCC (p)
    
    #  warning: test atPole after computing radial velocity and parallax
    #  since they can be correctly computed even at the pole
    
    #  compute parallax; note that arcsec = 1 / parsec;
    #  the division is safe because magP must have some reasonable
    #  minimum value, else scFromCC would have raised an exception
    parallax = RO.PhysConst.AUPerParsec / magP

    #  compute radial velocity in (au/year) and convert to (km/s)
    radVel = float ((x * vX) + (y * vY) + (z * vZ)) / magP
    radVel *= _KMPerSec_Per_AUPerYear
    
    #  now that parallax and radial velocity have been computed
    #  handle the "at pole" case
    if atPole:
        #  pos, parallax and radVel are already set
        pm = [0.0, 0.0]
    else:
        #  useful quantities
        magPxySq  = float((x * x) + (y * y))
        magPxy = math.sqrt (magPxySq)
        magPSq = magPxySq + z * z
    
        #  compute proper motion in rad per year,
        #  then convert to arcsec per century;
        #  the divisions are save because:
        #  - magPxySq must have some reasonable minimum value,
        #  else sph_CC2SC would have set atPole true,
        #  and that case has already been handled above
        #  - magPSq must have some reasonable minimum value,
        #  else sph_CC2SC would have set isOK false
        pm = [
            ((x * vY) - (y * vX)) / magPxySq,
            ((vZ * magPxy) - ((z / magPxy) * ((x * vX) + (y * vY)))) / magPSq,
        ]
        pm[0] = pm[0] * _ASPerCy_Per_RadPerYear
        pm[1] = pm[1] * _ASPerCy_Per_RadPerYear

    return (pos, pm, parallax, radVel, atPole)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing scFromCCPV"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((10000, 20000, 30000), (40, 50, 60)),
            ((63.4349488229220, 53.3007747995101), (-12375.8883748258, -7906.66505373138),
             5.51265882804246, 405.422085569533, 0)),
        (((10000, 20000, 30000), (0.4, 0.5, 0.6)),
            ((63.4349488229220, 53.3007747995101), (-123.758883748258, -79.0666505373138),
             5.51265882804246, 4.05422085569533, 0)),
        (((100000, 200000, 300000), (0.4, 0.5, 0.6)),
            ((63.4349488229220, 53.3007747995101), (-12.3758883748258, -7.90666505373139),
             0.551265882804246, 4.05422085569533, 0)),
        (((1, 0, 30000), (4, 5, 6)),
            ((0.000000000000000, 89.9980901406836), (103132403.123548, -2750.05990370150),
             6.87549353775016, 28.4434546950337, 0)),
        (((1, 0, 300000), (4, 5, 6)),
            ((0.000000000000000, 89.9998090140683), (103132403.123548, -275.018366561031),
             0.687549354153168, 28.4428858542247, 0)),
        # note: the Alpha FORTRAN version handles the next three cases without setting atPole
        (((1.0e-7, 0, 300000), (0.4, 0.5, 0.6)),
            ((0.000000000000000, 89.9999999999809), (0.0, 0.0),
             0.687549354156988, 2.84428226481164, 1)),
        (((1.0e-13, 0, 300000), (0.4, 0.5, 0.6)),
            ((0.000000000000000, 90.0000000000000), (0.0, 0.0),
             0.687549354156988, 2.84428226481101, 1)),
        (((1e-100, 0, 300000), (0.4, 0.5, 0.6)),
            ((0.000000000000000, 90.0000000000000), (0.0, 0.0),
             0.687549354156988, 2.84428226481101, 1)),
        (((1e-200, 0, 300000), (0.4, 0.5, 0.6)),
            ((0.000000000000000, 90.0000000000000), (0.0, 0.0),
             0.687549354156988, 2.84428226481101, 1)),
        (((100000, 0, 300000), (0.4, 0.5, 0.6)),
            ((0.000000000000000, 71.5650511770780), (103.132403123548, -12.3758883748258),
             0.652266588874152, 3.29795043058250, 0)),
        (((100000, 0, -300000), (0.4, 0.5, 0.6)),
            ((0.000000000000000, -71.5650511770780), (103.132403123548, 37.1276651244773),
             0.652266588874152, -2.09869572855250, 0)),
        (((100000, 0, -300000), (-0.4, -0.5, -0.6)),
            ((0.000000000000000, -71.5650511770780), (-103.132403123548, -37.1276651244773),
             0.652266588874152, 2.09869572855250, 0)),
        (((100000, 200000, 000000), (-0.4, -0.5, -0.6)),
            ((63.4349488229220, 0.000000000000000), (12.3758883748258, -55.3466553761197),
             0.922444256268662, -2.96800396261342, 0)),
        (((100000, 200000, 100000), (-0.4, -0.5, -0.6)),
            ((63.4349488229220, 24.0948425521107), (12.3758883748258, -24.5985135004976),
             0.842072545332370, -3.87057790735260, 0)),


        (((17863.0562116661, 10313.2403123548, 35726.1124233321),
            (27.0531474670740, 15.7346120263798, 55.0062949341481)),
            ((30, 60), (100, 200), 5, 300, 0)),
        (((17863.0562116661, 10313.2403123548, 35726.1124233321),
            (-27.7531474670740, -15.9078171071366, -54.6062949341481)),
            ((30, 60), (100, 200), 5, -300, 0)),
        (((17863.0562116661, 10313.2403123548, 35726.1124233321),
            (27.7531474670740, 15.9078171071366, 54.6062949341481)),
            ((30, 60), (-100, -200), 5, 300, 0)),
        (((41252.9612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (63.2848582670328, -0.200000000000000, -0.400000000000000)),
            ((0, 0), (-100, -200), 5, 300, 0)),
        (((41252.9612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (63.2848582670328, 0.200000000000000, 0.400000000000000)),
            ((0, 0), (100, 200), 5, 300, 0)),
        (((41252.9612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (6.32848582670328, 0.200000000000000, 0.400000000000000)),
            ((0, 0), (100, 200), 5, 30, 0)),
        (((41252.9612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (0.632848582670328, 0.200000000000000, 0.400000000000000)),
            ((0, 0), (100, 200), 5, 3, 0)),
        (((41252.9612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (-0.632848582670328, 0.200000000000000, 0.400000000000000)),
            ((0, 0), (100, 200), 5, -3, 0)),
        (((0.000000000000000E+000, 41252.9612494193, 0.000000000000000E+000),
            (-0.200000000000000, -0.632848582670328, 0.400000000000000)),
            ((90, 0), (100, 200), 5, -3, 0)),
        (((17863.0562116661, 10313.2403123548, 35726.1124233321),
            (-0.624031474670740, -0.244814686046026, -0.348062949341481)),
            ((30, 60), (100, 200), 5, -3, 0)),
        (((17863.0562116661, 10313.2403123548, 35726.1124233321),
            (7.596852532925974E-002, -7.160960528913816E-002, -0.748062949341481)),
            ((30, 60), (-100, -200), 5, -3, 0)),
        (((178630.562116661, 103132.403123548, 357261.124233321),
            (3.22596852532926, 0.707813258116857, -2.54806294934148)),
            ((30, 60), (-100, -200), 0.5, -3, 0)),
        (((412529.612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (-0.632848582670328, -2.00000000000000, -4.00000000000000)),
            ((0, 0), (-100, -200), 0.5, -3, 0)),
        (((412529.612494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (-6.32848582670328, -2.00000000000000, -4.00000000000000)),
            ((0, 0), (-100, -200), 0.5, -30, 0)),
        (((4125296.12494193, 0.000000000000000E+000, 0.000000000000000E+000),
            (-6.32848582670328, -2.00000000000000, -4.00000000000000)),
            ((0, 0), (-10, -20), 0.05, -30, 0)),
        (((1389499.10845179, 245006.182490408, 3876510.32716463),
            (1.68886219054623, -0.396800739776020, -7.31491200540396)),
            ((10, 70), (-10, -20), 0.05, -30, 0)),
        (((1389499.10845179, 245006.182490408, -3876510.32716463),
            (-5.71447043664036, -1.70220802910830, 4.57875085879861)),
            ((10, -70), (-10, -20), 0.05, -30, 0)),
        (((1389499.10845179, 245006.182490408, -3876510.32716463),
            (-5.71447043664036, -1.70220802910830, 4.57875085879861)),
            ((10, -70), (-10, -20), 0.05, -30, 0)),
# fails if rtol > 1e-10, but not a physically meaningful case
        (((138949910845.179, 24500618249.0408, -387651032716.463),
            (-358290.528023025, -132635.558089514, -136802.110498835)),
            ((10, -70), (-10, -20), 0.0000005, -30, 0)),
        (((412529612494.193, 0.000000000000000E+000, 0.000000000000000E+000),
            (-6.32848582670328, -20.0000000000000, -40.0000000000000)),
            ((0, 0), (-0.001, -0.002), 0.0000005, -30, 0)),
        (((412529612494.193, 0.000000000000000E+000, 0.000000000000000E+000),
            (-63.2848582670328, -20.0000000000000, -40.0000000000000)),
            ((0, 0), (-0.001, -0.002), 0.0000005, -300, 0)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = scFromCCPV(*testInput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-10, atol=1.0e-10):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
