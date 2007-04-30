#!/usr/bin/env python
"""
History:
2002-07-22 ROwen  Converted from the TCC's cnv_Refract 2-2.
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
from math import sqrt
import numpy
import RO.SysConst
import RO.PhysConst
import RO.MathUtil

# Constants
_MaxZDU = 85.0

def obsFromTopo (appTopoP, refCo):
    """
    Corrects for refraction, i.e. converts apparent topocentric
    coordinates to observed coordinates.
    
    Inputs:
    - appTopoP(3)   apparent topocentric cartesian position (any units) (az/alt)
    - refCo(2)      refraction coefficients A and B (degrees)
    
    Returns a tuple consisting of:
    - obsP(3)       observed cartesian position (arb. units) (az/alt), a numpy.array;
                    the magnitude will be slightly different than appTopoP
    - tooLow        true => position too near horizon; a max correction applied
    
    Error Conditions:
    If the unrefracted zenith distance > _MaxZDU the tooLow flag is set true
    and the correction applied is that computed at _MaxZDU.
    
    Raises ValueError if the magnitude of the input position vector is so small
    that the computation may overflow.
    
    Details:
    Based on Pat Wallace's RefV, it uses two iterations to invert the simple
    A tan Z + B tan^3 model. Unlike RefV, it does not switch to a higher-accuracy
    equation at lower altitudes. Also, it goes to some trouble to be invertible.
    """
    tooLow = 0

    # convert inputs to easier-to-read variables
    # u means "unrefraced"
    # r means "refracted"
    # zd means zenith distance
    ux, uy, uz = appTopoP
    refA, refB = refCo

    #  useful quantities
    uxysq = (ux * ux) + (uy * uy)
    uxymag = sqrt (uxysq)
    umagsq = uxysq + (uz * uz)

    #  test input vector
    if uxysq * RO.SysConst.FAccuracy <= RO.SysConst.FSmallNum:
        if umagsq * RO.SysConst.FAccuracy <= RO.SysConst.FSmallNum:
            #  |R| is too small to use -- probably a bug in the calling software
            raise ValueError, \
                'appTopoP %r too small' % appTopoP 
        #  at zenith; set output = input
        obsP = numpy.asarray(appTopoP, copy=True, dtype=float)
    else:
        #  normal calculation...
        # unrefracted zenith distance
        zdu = RO.MathUtil.atan2d (uxymag, uz)
    
        #  Compute the refraction correction using an iterative approximation (see details).
        #  Compute it at the unrefracted zenith distance, unless that zd is too large,
        #  in which case compute the correction at the max unrefracted zenith distance.
        zdr_u = 0.0
        zduIter = zdu
        if (zduIter > _MaxZDU):
            tooLow = 1
            zduIter = _MaxZDU
        for iterNum in range(2):
            zdrIter = zduIter + zdr_u
            cosZD = RO.MathUtil.cosd (zdrIter)
            tanZD = RO.MathUtil.tand (zdrIter)
            zdr_u -= ((zdr_u + refA * tanZD + refB * tanZD**3) /  \
                (1.0 + (RO.PhysConst.RadPerDeg * (refA + 3.0 * refB * tanZD**2) / cosZD**2)))
    
        #  compute refracted position as a cartesian vector
        zdr = zdu + zdr_u
        rz = uxymag * RO.MathUtil.tand (90.0 - zdr)
        obsP = numpy.array((ux, uy, rz))
    return (obsP, tooLow)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing obsFromTopo"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    # this test data was determined using cnv_AppGeo2AppTopo 7-3
    # jimmied to use mean latitude instead of current latitude
    # and using the following telescope constants (which are for the APO 3.5m):
    # Latitude  =   32.780361   # latitude north, deg
    # Longitude = -105.820417   # longitude east, deg
    # Elevation =    2.788  # elevation, km
    testData = (
        (((1.00000000000000, 2.00000000000000, 3.00000000000000), 
                (1.000000000000000E-002, -1.000000000000000E-005)), 
                ((1.00000000000000, 2.00000000000000, 3.00081395588335), 0)), 
        (((1.00000000000000, 2.00000000000000, 0.100000000000000), 
                (1.000000000000000E-002, -1.000000000000000E-005)), 
                ((1.00000000000000, 2.00000000000000, 0.103832878680326), 1)), 
        (((1.00000000000000, 2.00000000000000, 1.000000000000000E-004), 
                (1.000000000000000E-002, -1.000000000000000E-005)), 
                ((1.00000000000000, 2.00000000000000, 3.924935899097769E-003), 1)), 
        (((1.00000000000000, 2.00000000000000, 0.500000000000000), 
                (1.000000000000000E-002, -1.000000000000000E-005)), 
                ((1.00000000000000, 2.00000000000000, 0.501790102482220), 0)), 
        (((1.00000000000000, 2.00000000000000, 0.500000000000000), 
                (1.000000000000000E-002, -1.000000000000000E-002)), 
                ((1.00000000000000, 2.00000000000000, 0.452932945642090), 0)), 
        (((1.00000000000000, 2.00000000000000, 0.500000000000000), 
                (5.000000000000000E-002, -1.000000000000000E-002)), 
                ((1.00000000000000, 2.00000000000000, 0.464185334828288), 0)), 
        (((1.00000000000000, 2.00000000000000, 1.00000000000000), 
                (0.100000000000000, -1.000000000000000E-002)), 
                ((1.00000000000000, 2.00000000000000, 1.00526762120880), 0)), 
    )
    for testInput, expectedOutput in testData:
        actualOutput = obsFromTopo(*testInput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
