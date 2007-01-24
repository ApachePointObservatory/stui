#!/usr/bin/env python
import math
import RO.PhysConst
import RO.MathUtil

def gmstFromUT1(ut1):
    """Convert from universal time (MJD)
    to Greenwich mean sidereal time, in degrees

    Based on Pat Wallace's GMST, whose comments follow:
    
    The IAU 1982 expression (see page S15 of 1984 Astronomical
    Almanac) is used, but rearranged to reduce rounding errors.
    This expression is always described as giving the GMST at
    0 hours UT.  In fact, it gives the difference between the
    GMST and the UT, which happens to equal the GMST (modulo
    24 hours) at 0 hours UT each day.  In this routine, the
    entire UT is used directly as the argument for the
    standard formula, and the fractional part of the UT is
    added separately;  note that the factor 1.0027379... does
    not appear.
    
    See also the routine GMSTA, which delivers better numerical
    precision by accepting the UT date and time as separate arguments.
    
    P.T.Wallace   Starlink   14 September 1995
    
    History:
    2002-20-12 ROwen    Removed an extra + sign that was doing nothing.
                        Thanks to pychecker.
    """
    # convert date to Julian centuries since J2000
    jc= (ut1 - RO.PhysConst.MJDJ2000) / 36525.0

    return RO.MathUtil.wrapPos (
        (math.fmod(ut1, 1.0) * 360.0) # fraction of day of UT1, in degrees
         + (24110.54841
            + (8640184.812866
               + (0.093104-(6.2e-6*jc))*jc)*jc)*0.0041666666666666666)

if __name__ == "__main__":
    # test data is from GMST and is UT days, gmst deg
    import sys
    print "testing gmstFromUT1"
    testData = (
        (33282.0000000000, 100.075688557397),
        (34490.9775000000, 203.601164908095),
        (35699.9550000000, 307.126642108924),
        (36908.9324999999, 50.6521201625018),
        (38117.9099999999, 154.177599063566),
        (39326.8874999999, 257.703078814740),
        (40535.8649999999, 1.22855941601971),
        (41744.8424999999, 104.754040867395),
        (42953.8199999998, 208.279523168868),
        (44162.7974999998, 311.805006320424),
        (45371.7749999998, 55.3304903220624),
        (46580.7524999998, 158.855975176404),
        (47789.7299999998, 262.381460878190),
        (48998.7074999997, 5.90694743003934),
        (50207.6849999997, 109.432434831948),
        (51416.6624999997, 212.957923083911),
        (52625.6399999997, 316.483412185921),
        (53834.6174999997, 60.0089021379735),
        (55043.5949999996, 163.534392942689),
        (56252.5724999996, 267.059884594810),
        (57461.5499999996, 10.5853770969548),
        (58670.5274999996, 114.110870449122),
        (59879.5049999996, 217.636364651301),
        (61088.4824999995, 321.161859703488),
        (62297.4599999995, 64.6873556083032),
        (63506.4374999995, 168.212852360494),
        (64715.4149999995, 271.738349962673),
        (65924.3924999995, 15.2638484148369),
        (67133.3699999994, 118.789347716987),
        (68342.3474999994, 222.314847869105),
        (69551.3249999994, 325.840348871200),
    )
    for testInput, expectedOutput in testData:
        actualOutput = gmstFromUT1(testInput)
        if RO.MathUtil.compareFloats(actualOutput, expectedOutput, rtol=1e-8):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
