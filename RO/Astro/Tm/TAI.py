#!/usr/local/bin/python
import RO.PhysConst
from UTCFromPySec import *

# global variable UTC-TAI (since leap seconds are unpredictable)
# set to some initial plausible value and update with setUTCMinusTAI
_UTCMinusTAIDays = -32 / RO.PhysConst.SecPerDay # a reasonable value correct as of 2001-10

def setUTCMinusTAI(newUTCMinusTAISec):
    """Sets UTC - TAI (in seconds)"""
    global _UTCMinusTAIDays
    _UTCMinusTAIDays = newUTCMinusTAISec / RO.PhysConst.SecPerDay

def taiFromUTC(utc):
    """Converts UTC (MJD) to TAI (MJD)"""
    global _UTCMinusTAIDays
    return utc - _UTCMinusTAIDays

def utcFromTAI(tai):
    """Converts TAI (MJD) to UTC (MJD)"""
    global _UTCMinusTAIDays
    return tai + _UTCMinusTAIDays

def taiFromPySec(pySec=None):
    return taiFromUTC(utcFromPySec(pySec))