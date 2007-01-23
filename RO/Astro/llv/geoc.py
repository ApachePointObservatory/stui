#!/usr/local/bin/python
from math import sin, cos, sqrt

# Constants
# Earth equatorial radius (metres)
_A0 = 6378140.0

# Reference spheroid flattening factor and useful function
_F = 1.0/298.257
_B = (1.0-_F)**2

# Astronomical unit in metres
_MPerAU = 1.49597870e11

def geoc (lat, ht):
    """
    Convert geodetic position to geocentric
    
    Inputs:
    - lat   latitude (geodetic, radians)
    - ht    height above reference spheroid (geodetic, metres)
    
    Returns a tuple containing:
    - distance from Earth axis (au)
    - distance from plane of Earth equator (au)
    
    Notes:
    1)  Geocentric latitude can be obtained by evaluating atan2(Z,R).
    2)  IAU 1976 constants are used.
    
    Reference:
    Green,R.M., Spherical Astronomy, cup 1985, p98.
    
    History:    
    lat.T.Wallace   Starlink    4th October 1989
    2002-07-11 ROwen  Converted to Python.
    """
    sinLat=sin(lat)
    cosLat=cos(lat)
    c=1.0/sqrt(cosLat*cosLat+_B*sinLat*sinLat)
    S=_B*c
    return (
        (_A0*c+ht)*cosLat/_MPerAU,
        (_A0*S+ht)*sinLat/_MPerAU,
    )


if __name__ == "__main__":
    import RO.SeqUtil
    print "testing geoc"
    # testData is a list of duples consisting of:
    # - input data
    # - the expected output
    testData = (
        ((  0,  1000), (  4.264191729467806E-005,  0.000000000000000E+000)),
        (( 30,  1000), (  6.599172672421954E-006, -4.198695990961744E-005)),
        (( 60,  1000), ( -4.062534944231760E-005, -1.291472755629494E-005)),
        (( 90,  1000), ( -1.915802991112609E-005,  3.796826227832314E-005)),
        ((-45, 20000), (  2.252193403527315E-005, -3.623701722733858E-005)),
    )
    for testInput, expectedOutput in testData:
        actualOutput = geoc(*testInput)
        if RO.SeqUtil.matchSequences(actualOutput, expectedOutput, rtol = 1.e-10):
            print "failed on input:", testInput
            print "expected output:\n", expectedOutput
            print "actual output:\n", actualOutput

