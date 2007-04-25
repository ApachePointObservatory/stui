#!/usr/bin/env python
"""
History:
6/01 ROwen  Initial release.
2002-07-24 ROwen    Simplified by using Numeric.
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
import math
import numpy
import RO.MathUtil
from DCFromSC import *

def angSep (posA, posB):
    """Computes the angular separation between two points on a sphere.

    Inputs:
    - posA(2)   one spherical coordinate (deg)
                longitude (increasing x to y), latitude,
                e.g. (RA, Dec), (-HA, Dec) or (Az, Alt)
    - posB(2)   the other spherical coordinate (deg)
    
    Returns:
    - angSep    the angular separation between the two points (deg)
    
    Error Conditions:
    (none)
        
    Details:
    Convert to Cartesian vectors and go from there.
    The simplest method is to take the arc cosine of the dot product,
    but this works poorly for small angles. To avoid this problem,
    construct a triangle from the origin to one of the vectors
    to the halfway point between the vectors, then use atan2
    to compute the angle at the origin (half the desired angle)
    
    Based on Pat Wallace's SEP routine.
    """
    # convert from sherical to Cartesian coordinates
    vecA = dcFromSC(posA)
    vecB = dcFromSC(posB)
    
    # compute the magnitude squared of half the difference vector
    diffMagSqQuarter = numpy.sum((vecA - vecB)**2) * 0.25
    
    # compute the angle
    return 2.0 * RO.MathUtil.atan2d (
        math.sqrt(diffMagSqQuarter),
        math.sqrt(max(0.0, 1.0-diffMagSqQuarter))
    )

if __name__ == "__main__":
    import RO.PhysConst
    print "testing angSep"
    # testData is a list of duples consisting of:
    # - input data
    # - the expected output
    # the data comes from running DSEP
    # so the inputs and output are in radians
    testData = (
        (((0, 0), (0, 0)), 0.000000000000000),
        (((0, 0), (1, 1)), 1.27455578230629),
        (((0, 0), (1, 0)), 1.00000000000000),
        (((0, 0), (0, 1)), 1.00000000000000),
        (((-1, 0), (0, 0)), 1.00000000000000),
        (((-1, 1), (1, -1)), 2.54911156461259),
        (((0.000001, 0.000001), (0, 0)), 1.414213562372977E-006),
    )
    for testInput, expectedOutput in testData:
        testInput = [(x[0] / RO.PhysConst.RadPerDeg, x[1] / RO.PhysConst.RadPerDeg) for x in testInput]
        expectedOutput = expectedOutput / RO.PhysConst.RadPerDeg
        # print "(%r, %r)" % (testInput, expectedOutput)
        actualOutput = angSep(*testInput)
        if 0 != RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput

