#!/usr/bin/env python
import Numeric
import RO.MathUtil
from RO.Astro import llv

# Magic Numbers
# if the number of iterations exceeds "_MaxIter" before converging,
# then the routine fails.
_MaxIter = 20
# If all three components of (P this itNum - P last itNum) / |P|
# are less than "_Accuracy", then the iteration has converged.
_Accuracy = 1.0e-10

def icrsFromGeo (appGeoP, agData):
    """
    Converts apparent geocentric coordinates to ICRS.
    
    Inputs:
    - appGeoP(3)    apparent geocentric cartesian position (au)
    - agData        an AppGeoData object containing star-independent
                    apparent geocentric data
    
    Returns
    - icrsP         ICRS cartesian position (au), a Numeric.array
    
    Warnings:
    - Uses the approximation ICRS = FK5 J2000.0
    - Not fully accurate for solar system objects.
    - Requires iteration, so it will be slower than GeoFromICRS
    
    Error Conditions:
    Raises RuntimeError if iteration fails to converge.
    
    Details:
    The following approximations have been used:
    - The annual aberration correction is only appropriate for stellar objects;
      it introduces unacceptable errors for solar system objects.
    - No correction is applied for the bending of light by sun's gravity.
      This introduces errors on the order of 0.02"
      at a distance of 20 degrees from the sun (Wallace, 1986)
    
    icrsFromGeo performs the inverse transform of geoFromICRS.
    Unfortunately, some of the equations (e.g. annual aberration)
    are not invertable, so they have been solved by iteration.
    To make the code easier to follow, the symbols used here are identical
    to those used in GeoFromICRS.
    
    The convergence criterion is set by the magic numbers _MaxIter and _Accuracy.
    
    References:
    GeoFromICRS
    aberat, an APPLE (J2000) subroutine; U.S. Naval Observatory
    P.T. Wallace's MAPQK routine
    P.T. Wallace, "Proposals for Keck Tel. Point. Algorithms," 1986 (unpub.)
    "The Astronomical Almanac" for 1978, U.S. Naval Observatory
    
    History:
    2002-07-22 ROwen  Converted to Python from cnv_AppGeo2J 4-2.
    2002-12-23 ROwen    Fixed "failed to converge" message; thanks to pychecker.
    """
    # compute constants needed to check iteration
    approxMagP = RO.MathUtil.vecMag(appGeoP)
    allowedErr = _Accuracy * approxMagP

    # correct position for nutation and precession
    p3 = Numeric.matrixmultiply(Numeric.transpose(agData.pnMat), appGeoP)

    # iterively correct for annual aberration
    itNum = 1
    maxErr = approxMagP
    p2 = p3.copy()
    while (maxErr > allowedErr) and (itNum <= _MaxIter):
        itNum += 1
        p2Dir, p2Mag = llv.vn (p2)
        dot2 = Numeric.dot(p2Dir, agData.bVelC)
        vfac = p2Mag * (1.0 + dot2 / (1.0 + agData.bGamma))
        oldP2 = p2.copy()
        p2 = (((1.0 + dot2) * p3) - (vfac * agData.bVelC)) / agData.bGamma
        maxErr = max (abs (p2 - oldP2))
    # if no convergence, complain and exit
    if (itNum > _MaxIter):
        raise RuntimeError, 'aberration correction failed to converge;' + \
            'after %s iterations; fractional error = %s, max allowed = %s' \
            % (_MaxIter, maxErr, allowedErr)

    # here is where the (iterative) correction for sun's gravity belongs

    # correct for Earth's offset from the barycenter
    return p2 + agData.bPos


if __name__ == "__main__":
    import RO.SeqUtil
    from AppGeoData import AppGeoData
    print "testing icrsFromGeo"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((10000, 20000, 30000), AppGeoData(1950)), 
            (9632.55084436298, 20111.7895401981, 30046.3855040227)
        ), 
        (((10000, 20000, 0), AppGeoData(1950)), 
            (9776.84807379959, 20110.7726234825, 47.8531284647973)
        ), 
        (((10000, 0, 0), AppGeoData(1950)), 
            (9999.07116248488, 112.986538740346, 49.1091751895581)
        ), 
        (((0, 0, 30000), AppGeoData(1950)), 
            (-143.177682840613, 1.80039994129501, 30000.0445088086)
        ), 
        (((10000, 20000, 30000), AppGeoData(2000)), 
            (10001.0754863063, 20000.4650112102, 30000.2437263796)
        ), 
        (((10000, 20000, 30000), AppGeoData(2050)), 
            (10373.9666646492, 19885.2991035402, 29950.1310196054)
        ), 
    )
    for testInput, expectedOutput in testData:
        actualOutput = icrsFromGeo(*testInput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-9):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput


