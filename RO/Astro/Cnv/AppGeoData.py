#!/usr/bin/env python
"""
History:
2004-05-18 ROwen    Stop importing RO.PhysConst; it wasn't used.
"""
from RO.Astro import llv
from RO.Astro import Tm

class AppGeoData (object):
    """Position-independent data for conversion
    between ICRS and apparent geocentric coordinates.
    
    The fields are:
    - dtPM: time interval for proper motion correction (Julian years)
    - bPos: barycentric position of Earth (au)
    - hDir: heliocentric direction of Earth (unit vector)
    - grav: solar gravity parameter: (grav rad Sun)*2/(Sun-Earth distance)
    - bVelC: barycentric velocity of the Earth in units of C
    - bGamma: sqrt(1-|bVelC|^2)
    - pnMat: precession and nutation 3x3 matrix
    """
    def __init__(self, tdbEpoch=None):
        """Create a new AppGeoData object for a specific date.
        Inputs:
        - tdbEpoch  TDB of apparent geocentric position (Julian year)
                    note: TDT will always do and UTC is usually adequate
                    default: current date
        """
        # compute star-independent apparent geocentric data
        if tdbEpoch == None:
            tdbDays = Tm.utcFromPySec()
        else:
            tdbDays = Tm.mjdFromEpJ (tdbEpoch)
        self.dtPM, self.bPos, self.hDir, self.grav, self.bVelC, self.bGamma, self.pnMat \
            = llv.mappa (2000.0, tdbDays)

# note: tested by GeoFromICRS (except for the default date handling)
