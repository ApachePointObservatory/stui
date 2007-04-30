#!/usr/bin/env python
"""
History:
2002-07-22 ROwen    Converted from the TCC's cnv_FK5Prec 6-1
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
import numpy
from RO.Astro import llv

def fk5Prec (fromP, fromV, fromDate, toDate):
    """
    Inputs:
    - fromDate  TDB date of initial coordinates (Julian epoch)
                note: tdt will always do and utc is usually adequate
    - fromP(3)  initial mean FK5 cartesian position (au)
    - fromV(3)  initial mean FK5 cartesian velocity (au per Jul. year)
    - toDate    TDB date to which to precess (Julian epoch)
    
    Returns:
    - toP(3)    final mean FK5 cartesian position (au), a numpy.array
    - toV(3)    final mean FK5 cartesian velocity (au per Julian year), a numpy.array
    
    Error Conditions:
    none
    
    References:
    "The Astronomical Almanac" for 1987, page B39
    P.T. Wallace's prec routine
    """
    fromP = numpy.asarray(fromP, dtype=float)
    fromV = numpy.asarray(fromV, dtype=float)

    # compute new precession constants
    rotMat = llv.prec (fromDate, toDate)

    # correct for velocity (proper motion and radial velocity)
    tempP = fromP + fromV * (toDate - fromDate)

    # precess position and velocity
    return (
        numpy.dot(rotMat, tempP),
        numpy.dot(rotMat, fromV),
    )



if __name__ == "__main__":
    import RO.SeqUtil
    print "testing fk5Prec"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((10000, 20000, 30000), (-40, -50, -60), 1950, 2050), 
        (
            (5429.63503475633, 15127.7990408549, 24055.5349050662), 
            (-38.2871632516581, -50.8753601165976, -60.3803847548804), 
        )),
        (((10000, 20000, 30000), (-40, -50, -60), 1950, 2010), 
        (
            (7217.20547812636, 17099.3910941875, 26443.1989232491), 
            (-38.9751386185012, -50.5297510570680, -60.2302484452733), 
        )),
        (((10000, 20000, 30000), (-40, -50, -60), 1990, 2010), 
        (
            (9058.94571467942, 19040.8302229114, 28817.7425722550), 
            (-39.6593024745821, -50.1781322594907, -60.0774064867872), 
        )),
        (((10000, 20000, 30000), (0, -50, -60), 1990, 2010), 
        (
            (9858.93620317733, 19044.4080842078, 28819.2973138458), 
            (0.340221950313561, -49.9992391946709, -59.9996694072443), 
        )),
        (((10000, 20000, 30000), (0, -50, 0), 1990, 2010), 
        (
            (9856.60409079185, 19044.4028690133, 30019.2950476873), 
            (0.223616331039277, -49.9994999543923, 2.172848283428381E-004), 
        )),
        (((10000, 20000, 30000), (0, 0, 0), 1990, 2010), 
        (
            (9852.13176417106, 20044.3928681012, 30019.2907019907), 
            (0.000000000000000, 0.000000000000000, 0.000000000000000), 
        )),
        (((10000, 20000, 0), (0, 0, 0), 1990, 2010), 
        (
            (9910.43457380820, 20044.5232479619, 19.3473559543917), 
            (0.000000000000000, 0.000000000000000, 0.000000000000000), 
        )),
        (((10000, 0, 30000), (0, 0, 0), 1990, 2010), 
        (
            (9941.57829658677, 44.5928863442324, 30019.3776159221), 
            (0.000000000000000, 0.000000000000000, 0.000000000000000), 
        )),
        (((0, 0, 30000), (0, 0, 0), 1990, 2010), 
        (
            (-58.3028096371421, -0.130379860719548, 29999.9433460363), 
            (0.000000000000000, 0.000000000000000, 0.000000000000000), 
        )),
    )
    for testInput, expectedOutput in testData:
        actualOutput = fk5Prec(*testInput)
        expectedFlat = RO.SeqUtil.flatten(expectedOutput)
        actualFlat = RO.SeqUtil.flatten(actualOutput)
        if RO.SeqUtil.matchSequences(actualFlat, expectedFlat, rtol=1.0e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
