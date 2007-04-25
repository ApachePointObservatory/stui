#!/usr/bin/env python
"""
History
2002-07-23 ROwen  Converted from TCC's sph_SC2CC 1-1.
2007-04-24 ROwen    Converted from Numeric to numpy.
"""
import numpy
import RO.MathUtil

def ccFromSC (pos, magP):
    """
    Converts a spherical position to cartesian coordinates.
    
    Inputs:
    - pos(2)    sherical position (deg)
                longitude (increasing x to y) and latitude,
                e.g. (RA, Dec), (-HA, Dec) or (Az, Alt)
    - magP      desired magnitude of the cartesian position vector
    
    Returns:
    - p(3)      cartesian position (same units as magP), a numpy.array
    """
    return numpy.array((
        RO.MathUtil.cosd (pos[1]) * RO.MathUtil.cosd (pos[0]),
        RO.MathUtil.cosd (pos[1]) * RO.MathUtil.sind (pos[0]),
        RO.MathUtil.sind (pos[1]),
    )) * magP

if __name__ == "__main__":
    import RO.SeqUtil
    print "testing ccFromSC"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((10, 0), 1.0), (0.984807753012208, 0.173648177666930, 0.000000000000000)),
        (((10, 10), 10.0), (9.69846310392954, 1.71010071662834, 1.73648177666930)),
        (((-10, -10), 10.0), (9.69846310392954, -1.71010071662834, -1.73648177666930)),
        (((45, 45), 100.0), (50.0000000000000, 50.0000000000000, 70.7106781186548)),
        (((75, 30), 1000.0), (224.143868042013, 836.516303737808, 500.000000000000)),
        (((45, 90), 1.0), (0.0, 0.0, 1.0)),
        (((120, -80), 1.0), (-8.682408883346518e-002, 0.150383733180435, -0.984807753012208)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = ccFromSC(*testInput)
        if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-14):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
