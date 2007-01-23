#!/usr/local/bin/python
import RO.MathUtil
from GMSTFromUT1 import *

def lmstFromUT1(ut1, longitude):
    """Convert from universal time (MJD) to local apparent sidereal time (deg).
    
    Inputs:
    - ut1       UT1 MJD
    - longitude longitude east (deg)

    Returns:
    - lmst      local mean sideral time (deg)

    History:
    2002-08-05 R Owen.
    """
    # convert UT1 to Greenwich mean sidereal time (GMST), in degrees
    gmst = gmstFromUT1(ut1)

    # find local mean sideral time, in degrees, in range [0, 360)
    return RO.MathUtil.wrapPos (gmst + longitude)   # degrees
