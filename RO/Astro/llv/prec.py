#!/usr/local/bin/python
import RO.PhysConst
from euler import *

def prec (begEpoch, endEpoch):
    """
    Return the matrix of precession between two epochs
    (IAU 1976, FK5)
    
    Inputs:
    - begEpoch  beginning Julian epoch (e.g. 2000 for J2000)
    - endEpoch  ending Julian epoch
    
    Returns:
    - pMat      the precession matrix as a 3x3 Numeric.array,
                where pos(endEpoch) = rotMat * pos(begEpoch)
    
    Based on Pat Wallace's PREC. His notes follow:
    - The epochs are TDB (loosely ET) Julian epochs.
    - Though the matrix method itself is rigorous, the precession
    angles are expressed through canonical polynomials which are
    valid only for a limited time span.  There are also known
    errors in the IAU precession rate.  The absolute accuracy
    of the present formulation is better than 0.1 arcsec from
    1960AD to 2040AD, better than 1 arcsec from 1640AD to 2360AD,
    and remains below 3 arcsec for the whole of the period
    500BC to 3000AD.  The errors exceed 10 arcsec outside the
    range 1200BC to 3900AD, exceed 100 arcsec outside 4200BC to
    5600AD and exceed 1000 arcsec outside 6800BC to 8200AD.
    The routine PRECL implements a more elaborate model
    which is suitable for problems spanning several thousand years.
    
    References:
    Lieske,J.H., 1979. Astron.Astrophys.,73,282.
    equations (6) & (7), p283.
    Kaplan,G.H., 1981. USNO circular no. 163, pA2.
    
    History:
    P.T.Wallace   Starlink   10 July 1994
    2002-07-08 ROwen  Converted to Python.
    """
    # Interval between basic epoch J2000.0 and beginning epoch (JC)
    t0 = (begEpoch-2000.0)/100.0

    # Interval over which precession required (JC)
    dt = (endEpoch-begEpoch)/100.0

    # Euler angles
    tas2r = dt*RO.PhysConst.RadPerArcSec
    w = 2306.2181+(1.39656-0.000139*t0)*t0

    zeta = (w+((0.30188-0.000344*t0)+0.017998*dt)*dt)*tas2r
    z = (w+((1.09468+0.000066*t0)+0.018203*dt)*dt)*tas2r
    theta = ((2004.3109+(-0.85330-0.000217*t0)*t0)  \
        +((-0.42665-0.000217*t0)-0.041833*dt)*dt)*tas2r

    # Rotation matrix
    return euler([(2, -zeta), (1, theta), (2, -z)])


if __name__ == "__main__":
    import Numeric
    print "testing prec"
    # testData is a list of duples consisting of:
    # - a tuple of input data for prec
    # - the expected output matrix (a Numeric.array)
    testData = (
        ((1950, 2030), (
            (  0.999809792419498     , -1.788715986032035E-002, -7.773576667941649E-003),
            (  1.788715978599293E-002,  0.999840009541031     , -6.953977811948254E-005),
            (  7.773576838970592E-003, -6.952065684160097E-005,  0.999969782878466     ),
        )),
        ((1970, 2070), (
            (  0.999702727178637     , -2.236221379594438E-002, -9.715382943610174E-003),
            (  2.236221361450236E-002,  0.999749928529375     , -1.086635586956039E-004),
            (  9.715383361241160E-003, -1.086262127587724E-004,  0.999952798649261     ),
        )),
        ((2030, 1990), (
            (  0.999952438570540     ,  8.945088518154950E-003,  3.886642282660436E-003),
            ( -8.945088522800213E-003,  0.999959991744255     , -1.738239784471644E-005),
            ( -3.886642271969383E-003, -1.738478816182840E-005,  0.999992446826284     ),
        )),
        ((2030, 2100), (
            (  0.999854274721629     , -1.565860549319427E-002, -6.799808445329385E-003),
            (  1.565860544963551E-002,  0.999877395104029     , -5.324804399676666E-005),
            (  6.799808545636553E-003, -5.323523316777973E-005,  0.999976879617600     ),
        )),
    )
    for testInput, expectedOutput in testData:
        actualOutput = prec(*testInput)
        if not Numeric.allclose(actualOutput, expectedOutput, rtol=1e-15, atol=1e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
