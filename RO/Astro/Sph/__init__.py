"""
Astronomical math in spherical coordinates.
Most coordinate conversions are in the Cnv package,
which works in cartesian coordinates. Hence to
apply a conversion in spherical coordinates
you must convert to cartesian and back, e.g.:
toPos = scFromCC(Cnv.geoFromICRS(ccFromSC(fromPos)))

Conventions used in Sph:
- Spherical coordinates are listed
  with the equatorial angle first, hence:
  (RA, Dec), (Long, Lat), (Az, Alt).
- Angles are in degrees.
- The sign convention for altitude is
  0 to the south, 90 to the east (which is right handed).

This Software is made available free of charge for use by:
a) private individuals for non-profit research; and
b) non-profit educational, academic and research institutions.
Commercial use is prohibited without making separate arrangements
with Pat Wallace and me. Contact me for more information.

This software is supplied "as is" and without technical support.
However, I do appreciate notification of bugs.

Russell Owen
University of Washington
Astronomy Dept.
PO Box 351580
Seattle, WA 98195
owen@astro.washington.edu
"""
from Airmass import *
from AngSep import *
from AngSideAng import *
from AzAltFromHADec import *
from CCFromSC import *
from CCFromSCPV import *
from CCFromSCPVOff import *
from CoordConv import *
from DCFromSC import *
from HADecFromAzAlt import *
from SCFromCC import *
from SCFromCCPV import *
from SCFromCCPVOff import *
from SCFromDC import *