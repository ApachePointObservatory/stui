#!/usr/bin/env python
"""    
History:
2002-07-12 ROwen    Converted to Python from the TCC's cnv_J2AppGeo 7-3
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
import numpy
from RO.Astro import llv

def geoFromICRS (icrsP, icrsV, agData):
    """
    Converts ICRS coordinates to apparent geocentric coordinates.
    
    Inputs:
    - icrsP(3)      ICRS cartesian position (au)
    - icrsV(3)      ICRS cartesian velocity (au/year) (e.g. proper motion and radial velocity)
    - agData        an AppGeoData object containing star-independent apparent geocentric data
    
    Returns:
    - appGeoP(3)    apparent geocentric cartesian position (au), a numpy.array
    
    Warnings:
    - Uses the approximation ICRS = FK5 J2000.
    - Not fully accurate for solar system objects.
    
    Details:
    The following approximations have been used:
    - FK5 J2000 is the same as ICRS
    - The annual aberration correction is only appropriate for stellar objects;
      it introduces unacceptable errors for solar system objects.
    - No correction is applied for the bending of light by sun's gravity.
      This introduces errors on the order of 0.02"
      at a distance of 20 degrees from the sun (Wallace, 1986)
    
    References:
    ABERAT, from the APPLE (J2000) subroutine library, U.S. Naval Observatory
    P.T. Wallace's MAPQK routine
    P.T. Wallace, "Proposals for Keck Tel. Point. Algorithms", 1986 (unpub.)
    "The Astronomical Almanac" for 1978, U.S. Naval Observatory
    """
    # make sure inputs are floating-point numpy arrays    
    icrsP = numpy.asarray(icrsP, dtype = float)
    icrsV = numpy.asarray(icrsV, dtype = float)
    
    # correct for velocity and Earth's offset from the barycenter
    p2 = icrsP + icrsV * agData.dtPM - agData.bPos
    
    # here is where the correction for sun's gravity belongs
    
    # correct for annual aberration
    p2Dir, p2Mag = llv.vn(p2)
    dot2 = numpy.dot(p2Dir, agData.bVelC)
    # i.e. dot2 = p2 dot bVelC / |p2|
    # but handles |p2|=0 gracefully (by setting dot2 to 0)
    vfac = p2Mag * (1.0 + dot2 / (1.0 + agData.bGamma))
    p3 = ((p2 * agData.bGamma) + (vfac * agData.bVelC)) / (1.0 + dot2)
    
    # correct position for precession and nutation
    return numpy.dot(agData.pnMat, p3)


if __name__ == "__main__":
    import RO.SeqUtil
    from AppGeoData import AppGeoData
    print "testing geoFromICRS"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((100000, 200000, 300000), (40, 50, 60), AppGeoData(1950)),
            (   101616.047587440     ,   196371.892329210     ,   296531.557366214     ),
        ),
        (((100000, 200000, 300000), (40, 50, 60), AppGeoData(2000)),
            (   99987.5861610396     ,   200003.313339469     ,   300001.016519087     ),
        ),
        (((100000, 200000, 300000), (40, 50, 60), AppGeoData(2050)),
            (   98200.1249335042     ,   203635.085247207     ,   303493.296869389     ),
        ),
        (((100000, 200000, -300000), (40, 50, 60), AppGeoData(2050)),
            (   101131.941016949     ,   203633.956399684     ,  -296520.988361389     ),
        ),
        (((100000, -200000, -300000), (-40, 50, 60), AppGeoData(2050)),
            (   101630.658144059     ,  -196394.197602789     ,  -296513.725838492     ),
        ),
        (((-100000, -200000, -300000), (-40, 50, -60), AppGeoData(2050)),
            (  -98322.7238553338     ,  -198633.721174190     ,  -303475.014143563     ),
        ),
        (((-100000, -200000, 000000), (-40, 50, -60), AppGeoData(2050)),
            (  -99771.7063002051     ,  -198627.781267067     ,  -3489.74224469589     ),
        ),
        (((-100000, 00000, 000000), (-40, 50, -60), AppGeoData(2050)),
            (  -102005.618162834     ,   1349.56758685140     ,  -3499.36630249671     ),
        ),
        (((0, 0, 300000), (-40, 50, -60), AppGeoData(2050)),
            (  -3508.76894260083     ,   2470.81935668263     ,   296985.859145861     ),
        ),
    )
    for testInput, expectedOutput in testData:
        actualOutput = geoFromICRS(*testInput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-10):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
