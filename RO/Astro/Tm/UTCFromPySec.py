#!/usr/local/bin/python
import time
import RO.PhysConst

# Python time tuple for J2000: 2000-01-01 12:00:00 (a Saturday)
_TimeTupleJ2000 = (2000, 1, 1, 12, 0, 0, 5, 1, 0)

def utcFromPySec(pySec = None):
    """Returns the UTC (MJD) corresponding to the supplied python time, or now if none.
    """
    global _TimeTupleJ2000

    if pySec == None:
        pySec = time.time()
    
    # python time (in seconds) corresponding to 2000-01-01 00:00:00
    # this is probably constant, but there's some chance
    # that on some computer systems it varies with daylights savings time
    pySecJ2000 = time.mktime(_TimeTupleJ2000) - time.timezone
    
    return RO.PhysConst.MJDJ2000 + ((pySec - pySecJ2000) / RO.PhysConst.SecPerDay)

def pySecFromUTC(utcDays):
    """Returns the python time corresponding to the supplied UTC (MJD).
    """
    global _TimeTupleJ2000

    pySecJ2000 = time.mktime(_TimeTupleJ2000) - time.timezone

    return ((utcDays - RO.PhysConst.MJDJ2000) * RO.PhysConst.SecPerDay) + pySecJ2000
