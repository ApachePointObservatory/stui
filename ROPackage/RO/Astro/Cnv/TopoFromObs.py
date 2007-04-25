#!/usr/bin/env python
"""
History:
2002-07-22 ROwen    Converted to Python from the TCC's cnv_UnRefract 2-2.
2002-12-23 ROwen    Fixed "obsP too small" message; thanks to pychecker.
2005-04-26 ROwen    Fixed minor indentation oddity.
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
from math import sqrt
import numpy
import RO.SysConst
import RO.PhysConst
import RO.MathUtil

# Constants
#  For zdu > _MaxZDU the correction is computed at _MaxZDU.
#  This is unphysical, but allows working with arbitrary positions.
#  The model used (at this writing) is not much good beyond 83 degrees
#  and going beyond ~87 requires more iterations to give reversibility
_MaxZDU = 85.0

def topoFromObs (obsP, refCo):
    """
    Removes correction for refraction,
    i.e. converts observed coordinates to apparent topocentric.
    
    Inputs:
    - obsP(3)       observed cartesian position (au) (az/alt)
    - refCo(2)      refraction coefficients A and B (degrees)
    
    Returns a tuple containing:
    - appTopoP(3)   apparent topocentric cartesian position (au) (az/alt), a numpy.array;
                    the magnitude will be slightly different than obsP
    - tooLow        log true => position too near horizon; a max correction applied
    
    Error Conditions:
    If the unrefracted zenith distance > _MaxZDU the tooLow flag is set true
    and the correction applied is that computed at _MaxZDU.
    
    Raises a ValueError if if the magnitude of the input position vector is so small
    that the computation may overflow.
    
    Details:
    Uses the model:
      zdu = zdr + A tan zdr + B (tan zdr)^3
    where:
    * zdu = unrefracted zenith distance
    * zdr = refracted zenith distance
    * A, B = refraction coefficients
    """
    tooLow = 0

    #  convert inputs to easy-to-read variables
    # u means "unrefraced"
    # r means "refracted"
    # zd means zenith distance
    rx, ry, rz = obsP
    refA, refB = refCo

    #  useful quantities
    rxysq = (rx * rx) + (ry * ry)
    rxymag = sqrt (rxysq)
    rmag = rxysq + (rz * rz)

    #  test input vector
    if rxysq * RO.SysConst.FAccuracy <= RO.SysConst.FSmallNum:
        if rmag * RO.SysConst.FAccuracy <= RO.SysConst.FSmallNum:
            #  |R| is too small to use -- probably a bug in the calling software
            raise ValueError, \
                'obsP %r too small' % obsP 
        #  at zenith; set output = input
        appTopoP = numpy.array(obsP, copy=True, dtype=numpy.float)
    else:

        #  refracted zenith distance
        zdr = RO.MathUtil.atan2d (rxymag, rz)
    
        #  Compute the refraction correction. Compute it at the refracted zenith distance,
        #  unless that zd is too large, in which case compute the correction at the
        #  maximum UNrefracted zd (this provides reversibility with cnv_Refract).
        if zdr > _MaxZDU:
            #  zdr < zdu, so we're certainly past the limit
            #  don't even bother to try computing the standard correction
            tooLow = 1
        else:
            tanzd = RO.MathUtil.tand (zdr)
            zdu = zdr + (refA * tanzd) + (refB * tanzd**3)
            if zdu > _MaxZDU:
                tooLow = 1
    
        if tooLow:
            #  compute correction at zdu = _MaxZDU and use that instead
            #  (iteration is required because we want the correction
            #   at a known zdu, not at a known zdr)
            zdr_u = 0.0
            zduIter = _MaxZDU
            for iterNum in range(2):
                zdrIter = zduIter + zdr_u
                coszd = RO.MathUtil.cosd (zdrIter)
                tanzd = RO.MathUtil.tand (zdrIter)
                zdr_u -= ((zdr_u + refA * tanzd + refB * tanzd**3) /  \
                    (1.0 + (RO.PhysConst.RadPerDeg * (refA + 3.0 * refB * tanzd**2) / coszd**2)))
                zdu = zdr - zdr_u
    
        #  compute unrefracted position as a cartesian vector
        uz = rxymag * RO.MathUtil.tand (90.0 - zdu)
        appTopoP = numpy.array((rx, ry, uz))
        
    return (appTopoP, tooLow)


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing topoFromObs"
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
        (((1, 2, 3), (0.01, -1e-5)),
            ((1, 2, 2.99918610747604), 0)),
        (((1, 2, 0), (0.01, -1e-5)),
            ((1, 2, -3.824935598845491E-003), 1)),
        (((1, 2, 0), (0, -1e-5)),
            ((1, 2, 5.881115183713512E-004), 1)),
        (((1, 2, 0), (1e-5, -1e-5)),
            ((1, 2, 5.835961356548571E-004), 1)),
        (((1, 2, 0.1), (0.01, -1e-5)),
            ((1, 2, 9.616770769538227E-002), 1)),
        (((1, 2, 0.5), (0.01, -1e-5)),
            ((1, 2, 0.498204362979310), 0)),
        (((1, 2, 100), (0.01, -1e-5)),
            ((1, 2, 99.9825410367273), 0)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = topoFromObs(*testInput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
