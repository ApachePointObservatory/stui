"""Astronomical math, including various coordinate conversions.

The heart of these routines is software written by Pat Wallace.
I have converted his code and algorithms from FORTRAN to Python
and added my own code.

Public:
- Cnv   Coordinate conversions in cartesian coordinates.
- Sph   Subroutines in spherical coordinates,
        including conversions to/from cartesian.
- Tm    Time functions.

Private:
- llv   Low-level conversion functions
        (using a different units convention)

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
rowen@u.washington.edu
"""
