#!/usr/local/bin/python
import math
import Numeric
import RO.PhysConst
from RO.Astro import llv

class ObserverData (object):
	"""Observatory-specific (or observer-specific) data.
	
	This data is primarily intended for conversion between apparent geocentric
	and apparent topocentric coordinates.
	
	The fields are:
	- longitude		observatory longitude east, deg
	- latitude		observatory latitude north, deg
	- elevation		observatory elevation (km)
	- p				observatory cartesian position (au)
	- dirAbVecMag	magnitude of diurnal aberration correction
	"""
	def __init__(self, longitude, latitude, elevation):
		"""Create a new ObserverData object for a specific date.
		Inputs:
		- longitude		observatory observatory longitude east, deg
		- latitude		observatory observatory latitude north, deg
		- elevation		observatory observatory elevationation (km)
		"""
		self.longitude, self.latitude, self.elevation = longitude, latitude, elevation
		
		sidRate = 2.0 * math.pi * RO.PhysConst.SidPerSol / RO.PhysConst.SecPerDay

		polarDist, zDist = llv.geoc (self.latitude * RO.PhysConst.RadPerDeg, self.elevation * 1000.0)
		#  |diurnal aberration vector|
		#  = speed of rot. of observatory / speed of light
		self.diurAbVecMag = polarDist * sidRate / RO.PhysConst.VLight
		# position of observer
		self.p = Numeric.array((polarDist, 0.0, zDist))		

if __name__ == "__main__":
	print "To test ObserverData, run the tests for topoFromGeo"
