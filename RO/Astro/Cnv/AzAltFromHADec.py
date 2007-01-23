#!/usr/local/bin/python
import Numeric
import RO.MathUtil

def azAltFromHADec (haDec, lat):
    """Converts cartesian HA/Dec position to alt/az.
    
    Inputs:
    - haDec(3)  cartesian hour angle, declination (any units)
    - lat       observers latitude north (deg)
    
    Returns:
    - azAlt(3)  cartesian hour angle, declination (same units as haDec), a Numeric.array
    
    Sign convention:
    increasing azAlt[0] is south-ish
    increasing azAlt[1] is east
    
    History:
    2002-07-22 ROwen  Converted to Python from the TCC's cnv_HADec2AzAlt 1-1.
    """
    sinLat = RO.MathUtil.sind (lat)
    cosLat = RO.MathUtil.cosd (lat)

    # convert cartesian -HA/Dec to cartesain Az/Alt
    return Numeric.array((
        sinLat * haDec[0] - cosLat * haDec[2],
        haDec[1],
        cosLat * haDec[0] + sinLat * haDec[2],
    ))


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing azAltFromHADec"
    # test data is formatted as follows:
    # a list of entries, each consisting of:
    # - the input argument
    # - the expected result
    testData = (
        (((1, 0, 0), 25), 
            (0.422618261740699, 0.000000000000000, 0.906307787036650)), 
        (((0, 1, 0), 25), 
            (0.000000000000000, 1.00000000000000, 0.000000000000000)), 
        (((0, 0, 1), 25), 
            (-0.906307787036650, 0.000000000000000, 0.422618261740699)), 
        (((1, 2, 3), 25), 
            (-2.29630509936925, 2.00000000000000, 2.17416257225875)), 
        (((-3, -2, -1), -25), 
            (2.17416257225875, -2.00000000000000, -2.29630509936925)), 
    )
    for testInput, expectedOutput in testData:
        actualOutput = azAltFromHADec(*testInput)
        if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol=1.0e-15):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput
