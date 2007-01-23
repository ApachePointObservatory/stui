"""
Physical constants

References:
U.S. Naval Observatory, the APPLE subroutine library for J2000.0 data
U.S. Naval Observatory, "The Astronomical Almanac" for 1987
S. Selby, "Standard Mathematical Tables", 15th ed, 1967, Chemical Rubber Co.
C. Allen, "Astrophysical Quantities", 1973, Athlone Press (U. of London)
L. Taff, "Computational Spherical Astronomy", 1981, Wiley
R. Green, "Spherical Astronomy", 1985, Cambridge
S. Aoki, et. al. (1983) Astron. Astrophys. 128, 263-267

History:
2002-03-22 ROwen    Converted from tinc:phyysconst.for version 7 on the TCC.
2002-07-01 ROwen    Corrected JDMinusMJD, added MJDJ2000.
2004-07-19 ROwen    Added SecPerHour
"""
import math

# general constants
HrsPerDeg  = 24.0 / 360.0   # hours per degree
RadPerDeg  = math.pi / 180.0    # radians per degree
KmPerAU    = 1.49597870e8   # kilometers per astr. unit (Astr. Almanac)
AUPerParsec    = 206264.8062470964  # astronomical units per parsec (the APPLE subr. library)
ArcSecPerDeg = 60.0 * 60.0      # arcseconds per degree
RadPerArcSec = RadPerDeg / ArcSecPerDeg # radians per arcsec
SecPerDay  = 24.0 * 3600.0  # seconds per day
SecPerHour = 60.0 * 60.0    # seconds per hour
DayPerYear = 365.25     # days per TDT (or TAI...) year
VLight  = 1.0 / 499.004782  # the speed of light in vacuum (au/sec) (Astr. Almanac)
DegK_DegC = 273.150     # deg. Kelvin - deg. C (Allen)

# astronomical dates and times
JDMinusMJD = 2400000.5  # Julian Date - Modified Julian Date (days)
MJDJ2000 = 51544.5      # Modified Julian Date at epoch J2000.0 noon (days)
TDTMinusTAI = 32.184    # TDT-UTC (seconds) (Astr. Almanac)
BEquivJ2000 = 2000.001278   # Bessilian equiv. of J2000.0 (Taff)
JEquivB1950 = 1949.999790   # Julian equiv. of B1950 (Taff)
JYPerBY = 36524.2198781 / 36525.0   # Julian years per Besselian (tropical) Years (Taff)
SidPerSol = 1.00273790934   # Mean sidereal time units per mean solar time unit, in 1987
    # (Astr. Almanac) (defined as sid. days/UT days, equals sid. days/TAI days on ave.)
