#!/usr/bin/env python
"""
History:
2002-07-22 ROwen    Converted to Python from the TCC's cnv_AppGeo2AppTopo.
2007-04-24 ROwen    Changed Numeric to numpy in a doc string.
"""
import RO.MathUtil
from AzAltFromHADec import *

# needs test code

def topoFromGeoSimple(appGeoP, last, lat):
    """Converts apparent topocentric position to apparent geocentric.
    "Simple" because it only corrects for local sidereal time,
    ignoring diurnal parallax, diurnal aberration and pole wander.
    
    Inputs:
    - appGeoP(3)    apparent geocentric cartesian position (RA/Dec)
    - last          local apparent sidereal time (deg)
    - lat           latitude (deg)
    
    Returns:
    - appTopoP(3)   apparent topocentric cartesian position (az, alt), a numpy.array
    
    Note: unlike topoFromGeo, the position units need not be au;
    the output position will be the same units as the input position.
    
    Sign convention:
    increasing azAlt[x] is south-ish
    increasing azAlt[y] is east
    """
    sinLAST = RO.MathUtil.sind (last)
    cosLAST = RO.MathUtil.cosd (last)

    # rotate position and offset to (-HA)/Dec (still cartesian, of course)
    posA = (
          cosLAST * appGeoP(1) + sinLAST * appGeoP(2),
        - sinLAST * appGeoP(1) + cosLAST * appGeoP(2).
          appGeoP(3),
    )
    
    return azAltFromHADec (posA, lat)
