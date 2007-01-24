#!/usr/bin/env python
import math
import RO.PhysConst
from nutc import *

_ArcSecPerRev = RO.PhysConst.ArcSecPerDeg * 360.0

def eqeqx (tdb):
    """The equation of the equinoxes (IAU 1994).
    
    Inputs:
    - tdb (MJD): TDB (loosely ET) as a Modified Julian Date
    
    Returns eqeqx, where:
    Greenwich apparent sidereal time = Greenwich mean sidereal time + eqeqx

    Based on Pat Wallace's EQEQX, which in turn is based on:
    IAU Resolution C7, Recommendation 3 (1994)
    Capitaine, N. & Gontier, A.-M., Astron. Astrophys., 275, 645-650 (1993)
    
    History:
    Patrick Wallace   Starlink   21 November 1994
    2002-07-11 ROwen  Converted to Python
    """
    # TDB - J2000 in centuries
    t=(tdb-51544.5)/36525.0

    # Longitude of the mean ascending node of the lunar orbit on the
    # ecliptic, measured from the mean equinox of date
    om=RO.PhysConst.RadPerArcSec*(450160.280+(-5.0*_ArcSecPerRev-482890.539  \
        +(7.455+0.008*t)*t)*t)

    # Nutation
    dpsi, deps, eps0 = nutc(tdb)

    # Equation of the equinoxes
    return dpsi*math.cos(eps0)+RO.PhysConst.RadPerArcSec*(0.00264*math.sin(om)+  \
        0.000063*math.sin(om+om))

if __name__ == "__main__":
    import RO.MathUtil
    print "testing eqeqx"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (1950, 6.213970160961727E-005),
        (1975, 5.656247048699819E-005),
        (2000, 5.312364773685637E-005),
        (2025, 5.337163045425660E-005),
        (2050, 5.657286389482546E-005),
        (2075, 5.971373668421823E-005),
    )
    for testInput, expectedOutput in testData:
        actualOutput = eqeqx(testInput)
        if RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
