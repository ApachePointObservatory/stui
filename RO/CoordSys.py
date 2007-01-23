#!/usr/local/bin/python
"""Basic information and utilities for dealing with coordinate systems.

To do:
- Some easy way to see if a name matches or is in a set in a non-case-sensitive manner.
- Make use of the Unknown coordinate system; input can be set to that
  until it is specified.
- Add a None coordinate system; the trick is that None is reserved.
- Move from names to _CoordSysConst objects and change ICRS, etc.
  to be those constants. This is a huge change--TCCModel will have
  to pass around an object instead of a Tkinter variable,
  the coord system converter will need to be overhauled...it may not be
  worth the effort.

History:
2002-07-31 ROwen    Extracted from CoordSysWdg.
2002-08-08 ROwen    First draft with _CoordSysConst and CoordSysObj
2003-05-09 ROwen    Replaced ConstDict with getSysConst function;
                    moved most functions to coord sys constants.
2003-05-28 ROwen    Added dateIsSidTime; changed dateInYears to dateIsYears.
2003-10-24 ROwen    Made J2000 the default date for ICRS (instead of no date).
2005-08-12 ROwen    Removed unused import of string module.
"""
import sys
import RO.Astro.Tm
import RO.StringUtil

ICRS = "ICRS"
FK5 = "FK5"
FK4 = "FK4"
Galactic = "Galactic"
Geocentric = "Geocentric"
Topocentric = "Topocentric"
Observed = "Observed"
Physical = "Physical"
Mount = "Mount"
NoCSys = "None"
Unknown = ""

class _CoordSysConst(object):
    def __init__(self, name, datePrefix, posLabels):
        """Specifies constant information about a coordinate system
        and provides a number of convenient methods.
        
        Inputs:
        - name          name of coordinate system (these names are used by the TCC)
        - datePrefix    "J" for Julian epoch, "B" for Besselian epoch, "" for UT1 MJD
        - posLabels(2)  label strings for the equatorial and polar angles
        
        Notes:
        - compares equal to strings of the same name, case insensitive.
        - the unknown coordinate system is treated like ICRS
        """
        self._name = name
        self._nameLower = name.lower()
        # default date: None means current date
        self._defDate = {ICRS:2000.0, FK5:2000.0, FK4:1950.0}.get(name, None)
        
        self._isMean = name in (ICRS, FK5, FK4, Galactic, Unknown)
        self._eqInHours = name in (ICRS, FK5, FK4, Galactic, Geocentric, Unknown)
        self._hasEquinox = name in (FK5, FK4)
        
        if self._eqInHours:
            self._eqDegPerDisp = 15.0
            self._eqUnitsStr = "h:m:s"
        else:
            self._eqDegPerDisp = 1.0
            self._eqUnitsStr = RO.StringUtil.DMSStr

        self._posLabels = tuple(posLabels)
        self._datePrefix = datePrefix
        self._dateIsYears = self._datePrefix in ("B", "J")
        self._dateIsSidTime = name in (Topocentric, Observed)
    
    def dateIsYears(self):
        """Is the date given in years?
        If false, the date is sidereal time or there is no date.
        """
        return self._dateIsYears
    
    def dateIsSidTime(self):
        """Is the date given in hours (sidereal time)?
        If false, the date is in years or there is no date.
        """
        return self._dateIsSidTime
    
    def datePrefix(self):
        return self._datePrefix
    
    def currDefaultDate(self):
        """Returns the current default date, resolving None to the
        current date. Query dateIsYears() for the units.
        """
        if self._defDate:
            return self._defDate
        if self._dateIsYears:
            return RO.Astro.Tm.epJFromMJD(RO.Astro.Tm.utcFromPySec())
        else:
            return RO.Astro.Tm.utcFromPySec()
        
    def defaultDate(self):
        """Returns the default date, or None if none.
        """
        return self._defDate
    
    def eqInHours(self):
        """Is the equatorial angle traditionally given in hours instead of degrees?
        """
        return self._eqInHours

    def eqUnitsStr(self):
        """The units string for the equatorial angle: "h:m:s" or <degsym>:":'
        where <degsym> is the unicode symbol for degrees.
        """
        return self._eqUnitsStr

    def eqDegFromDisp(self, eqDisp):
        """Returns the equatorial angle in degrees
        given the equatorial angle in display units (hours or degrees).
        
        Inputs:
        - eqDisp    equatorial angle in display units (a number in hours or degrees)
        """
        return eqDisp * self._eqDegPerDisp
    
    def hasEquinox(self):
        """Coordinate system requires a date of equinox.
        """
        return self._hasEquinox
    
    def name(self):
        """Name of coordinate system.
        """
        return self._name
    
    def posLabels(self):
        """Position labels, e.g. ("RA", "Dec").
        """
        return self._posLabels

    def isMean(self):
        """Is this a mean coordinate system?
        """
        return self._isMean
    
    def posDegFromDispStr(self, pos1Str, pos2Str):
        """Return the position in degrees given the displayed sexagesimal value
        in traditional units (deg:':" or h:m:s for pos1, deg:':" for pos2)
        """
        return (
            RO.StringUtil.degFromDMSStr(pos1Str) * self._eqDegPerDisp,
            RO.StringUtil.degFromDMSStr(pos2Str),
        )
    
    def __eq__(self, other):
        try:
            return other._nameLower == self._nameLower
        except AttributeError:
            try:
                return other.lower() == self._nameLower
            except AttributeError:
                return False
    
    def __repr__(self):
        return "<RO.CoordSys._CoordSysConst object %s>" % (self._name)
    
    def __str__(self):
        return self._name

# _SysConstList is a private list used to generate _SysConstDict
_SysConstList = [
    #               coord sys    date     pos labels
    #                           prefix 
    _CoordSysConst(       ICRS,   "J",     ("RA", "Dec")),
    _CoordSysConst(        FK5,   "J",     ("RA", "Dec")),
    _CoordSysConst(        FK4,   "B",     ("RA", "Dec")),
    _CoordSysConst(   Galactic,   "J",   ("Long", "Lat")),
    _CoordSysConst( Geocentric,   "J",     ("RA", "Dec")),
    _CoordSysConst(Topocentric,    "",     ("Az", "Alt")),
    _CoordSysConst(   Observed,    "",     ("Az", "Alt")),
    _CoordSysConst(   Physical,    "",     ("Az", "Alt")),
    _CoordSysConst(      Mount,    "",     ("Az", "Alt")),
    _CoordSysConst(     NoCSys,    "",          ("", "")),
    _CoordSysConst(    Unknown,    "",          ("", "")),
]

# _SysConstDict is a private dictionary for use by getSysConst
# (a dictionary is faster and more convenient than a list)
_SysConstDict = {}
for sysConst in _SysConstList:
    _SysConstDict[sysConst._name.lower()] = sysConst

# various useful lists of coordinate system names
MeanRADec = (ICRS, FK5, FK4)
RADec = (ICRS, FK5, FK4, Geocentric)
LongLat = (Galactic,)
AzAlt = (Topocentric, Observed, Physical, Mount)
All = [sysConst._name for sysConst in _SysConstList]

def getSysConst(coordSys, defSys=""):
    """Returns a coordinate system constant given its name (not case sensitive).
    Raises ValueError if the name is not valid.

    Potentially useful defaults include Unknown and ICRS.
    """
    coordSys = coordSys or defSys
    
    # check for None first since it does not support lower()
    if coordSys == None:
        raise ValueError, "None is not a valid coord sys name"
        
    try:
        return _SysConstDict[coordSys.lower()]
    except KeyError:
        raise ValueError, "unknown coordinate system %r" % (coordSys,)

def isValid(coordSys):
    """Returns True if the coordinate system name is valid (not case sensitive),
    False otherwise.
    """
    return _SysConstDict.has_key(coordSys.lower())
