#!/usr/local/bin/python
"""Convert astronomical positions between various coordinate systems.

The CnvObj code is getting ugly enough (I had to add ICRS<->ICRS2000 cases
to handle the proper motion) that I'm wondering if it wouldn't be better
to just hand code the converter as I did in the TCC. I hate all those
if/then/else statements but it's probably more obvious what's going on
then this mess of magic stuff.

I could also hand code all apparent->ICRS2000 and back routines
and then ditch the entire catalog of methods. That might be cleanest.

History:
2002-08-07 ROwen	Beta release. Not yet well tested and I hope to clean up the code somewhat.
2002-08-23 ROwen	Renamed from Convert; added coordConv method and stopped exporting CnvObj
	(I'm giving up on CnvObj being useful for now, but may revive it later).
	Added velocity handling and default date handling. Still beta; still not well tested.
2002-12-23 ROwen	Bug fix: was not importing ICRSFromFK4 (thanks to pychecker);
	Reorganized the code that computates method dictionaries to make it clearer;
	Reduced the number of globals and made them self-hiding (initial underscore).
2003-05-28 ROwen	Modified to handle RO.CoordSys 2003-05-09 (defaultDate->currDefaultDate).
2005-01-21 ROwen	Bug fix: was miscomputing proper motion, due to using ICRS
					instead of ICRS2000 as the intermediate coordinate system.
"""
import Numeric
import RO.CoordSys
from RO.Astro import Tm
from AppGeoData import *
from FK4FromICRS import *
from FK5Prec import *
from GalFromICRS import *
from GeoFromICRS import *
from GeoFromTopo import *
from ICRSFromFK4 import *
from ICRSFromFixedFK4 import *
from ICRSFromGal import *
from ICRSFromGeo import *
from ObserverData import *
from ObsFromTopo import *
from TopoFromGeo import *
from TopoFromObs import *

_CSysList = (RO.CoordSys.ICRS, RO.CoordSys.FK5, RO.CoordSys.FK4, RO.CoordSys.Galactic,
	RO.CoordSys.Geocentric, RO.CoordSys.Topocentric, RO.CoordSys.Observed,
	"ICRS2000")

class _CnvObj (object):
	"""
	An object that can convert between coordinate systems. To use,
	create one of these objects and then call its "coordConv" method.
	
	This code is a slightly awkward mix of functional and object-oriented programming.
	Some data is stored as instance variables purely for ease of passing to functions,
	but at present the caching serves no other purpose. In the future I hope to figure out an
	interface whereby the user can save some data and repeatedly ask for conversions.
	For instance one could create an object and then repeatedly ask for its current
	observed position. Then CnvObj would start to feel more like a normal object.
	
	Also, the method dictionary really should be saved as a class variable, but these
	are relatively new to Python and clumsy, and I'm not yet sure I want to bother
	(especially as it makes the code incompatible with older versions of Python).
	"""
	ZeroV = (0.0, 0.0, 0.0)

	def __init__(self):
		# Compute self.methDictDict, a dictionary of _CnvObj method dictionaries
		# to convert between any two coordinate systems:
		# - key: the "from" coordinate system
		# - value: the method dictionary to use if starting from that coordinate system:
		#   - key: a "to" coordinate system
		#   - value: a tuple consisting of:
		#     - the _CnvObj method to convert to "to" from "from" coordinate system
		#     - the "from" coordinate system
		# Each method dictionary gives a chain of methods that stretches from a given
		# starting "from" coordinate system to all other coordinate systems
		
		def addMethods(methDict, fromSys):
			"""Recursively add all methods to a method dictionary
			starting from a given "from" coordinate system.
			
			For the first call, set methDict = {}
			
			Inputs:
			- methDict: the method dictionary
			- a "from" coordinate system
			"""
			# if first execution, set entry for "from" = "to":
			if methDict == {}:
				methDict[fromSys] = (None, None)
			
			# add an entry for each "to" coordinate system
			for toSys in _CSysList:
				if toSys == fromSys:
					continue
				if methDict.has_key(toSys):
					continue
				funcName = "%sFrom%s" % (toSys, fromSys)
				if hasattr(_CnvObj, funcName):
					methDict[toSys] = (getattr(_CnvObj, funcName), fromSys)
					# print "methDict[%s] = %r" % (toSys, methDict[toSys])
					addMethods(methDict, toSys)
		
		# pre-compute conversion dictionaries for every possible starting coordinate system
		# (which so far includes all in RO.CoordSys except Physical and Mount)
		methDictDict = {}
		for _whatGiven in _CSysList:
			# define method dictionary for coordsys _whatGiven given
			methDict = {}
			addMethods(methDict, _whatGiven)
			assert len(methDict) == len(_CSysList), "incomplete function list; check your conversion functions"
			methDictDict[_whatGiven] = methDict
			# print "methDictDict[%s] = %r" % (_whatGiven, methDictDict[_whatGiven])
	
		self.methDictDict = methDictDict

	def coordConv(self, fromP, fromV, fromSys, fromDate, toSys, toDate, obsData=None, refCo=None):
		"""Converts a position from one coordinate system to another.
		See notes for the coordConv function below.
		"""
		# handle default dates
		if fromDate == None:
			fromDate = RO.CoordSys.getSysConst(fromSys).currDefaultDate()
		if toDate == None:
			toDate = RO.CoordSys.getSysConst(toSys).currDefaultDate()
		
		self.fromDate = fromDate
		self.toDate = toDate
		self.obsData = obsData
		if refCo:
			self.refCo = refCo[:]
		else:
			refCo = None
		
		# convert to ICRS from fromSys
		icrsP, icrsV = self._getItem("ICRS2000", self.methDictDict[fromSys], fromP, fromV)
#		print "Cnv.coordConv: icrsP=%s, icrsV=%s" % (icrsP, icrsV)
		
		# convert to toSys from ICRS
		toP, toV = self._getItem(toSys, self.methDictDict["ICRS2000"], icrsP, icrsV)
#		print "Cnv.coordConv: toP=%s, toV=%s" % (toP, toV)
		return (toP, toV)

	def _getItem(self, csys, methDict, initP, initV):
		"""Internal routine that returns the position initP and velocity initV
		converted to the requested coordinate system.

		To perform a full conversion, first convert fromP, fromV, fromSys, fromDate to ICRS
		and then convert ICRS to toP, toV, toSys, toDate.
		
		Before calling, set self.fromDate, self.toDate, self.obsData and self.refCo.
				
		Inputs:
		- csys		desired coordinate system
		- methDict	_MethodDict[initSys], where initSys is the initial coordinate system
					(a dictionary of unbound coordinate conversion methods)
		- initP		position in initSys
		- initV		velocity in initSys
		"""
#		print "Cnv._CnvObj._getItem: csys=%s; fromP=%s; fromV=%s" % (csys, initP, initV)
		func, nextSys = methDict[csys]
#		print "Cnv._CnvObj._getItem: nextSys=%s; func=%s" % (nextSys, func)
		if func:
			toP, toV = func(self, *self._getItem(nextSys, methDict, initP, initV))
#			print "Cnv._CnvObj._getItem: toP=%s, toV=%s" % (toP, toV)
			return (toP, toV)
		else:
#			print "Cnv._CnvObj._getItem: null conversion; toP, V = fromP, V"
			return (initP, initV)

	# conversion functions
	def ICRSFromICRS2000(self, fromP, fromV):
		return (fromP + (Numeric.array(fromV) * (self.toDate - 2000.0)), fromV)
		
	def ICRS2000FromICRS(self, fromP, fromV):
		return (fromP + (Numeric.array(fromV) * (2000.0 - self.fromDate)), fromV)

	def FK5FromICRS2000(self, fromP, fromV):
		return fk5Prec(fromP, fromV, 2000.0, self.toDate)

	def ICRS2000FromFK5(self, fromP, fromV):
		return fk5Prec(fromP, fromV, self.fromDate, 2000.0)
	
	def FK4FromICRS2000(self, fromP, fromV):
		return fk4FromICRS (fromP, fromV, self.toDate)
	
	def ICRS2000FromFK4(self, fromP, fromV):
		if tuple(fromV) == (0.0, 0.0, 0.0):
			return (icrsFromFixedFK4 (fromP, self.fromDate), _CnvObj.ZeroV)
		else:
			return icrsFromFK4(fromP, fromV, self.fromDate)
	
	def GalacticFromICRS2000(self, fromP, fromV):
		return galFromICRS (fromP, fromV, self.toDate)
	
	def ICRS2000FromGalactic(self, fromP, fromV):
		return icrsFromGal(fromP, fromV, self.fromDate)
	
	def GeocentricFromICRS2000(self, fromP, fromV):
		agData = AppGeoData(Tm.epJFromMJD(self.toDate))
		return (geoFromICRS(fromP, fromV, agData), _CnvObj.ZeroV)
	
	def ICRS2000FromGeocentric(self, fromP, dumV):
		agData = AppGeoData(Tm.epJFromMJD(self.fromDate))
		return (icrsFromGeo(fromP, agData), _CnvObj.ZeroV)
	
	def TopocentricFromGeocentric(self, fromP, dumV):
		if self.obsData == None:
			raise ValueError, "must specify obsData to cnvert to Topocentric from Geocentric"
		return (
			topoFromGeo(fromP, Tm.lastFromUT1(self.toDate, self.obsData.longitude), self.obsData),
			_CnvObj.ZeroV,
		)
	
	def GeocentricFromTopocentric(self, fromP, dumV):
		if self.obsData == None:
			raise ValueError, "must specify obsData to convert to Geocentric from Topocentric"
		return (
			geoFromTopo(fromP, Tm.lastFromUT1(self.fromDate, self.obsData.longitude), self.obsData),
			_CnvObj.ZeroV,
		)
	
	def ObservedFromTopocentric(self, fromP, dumV):
		if self.refCo == None:
			raise ValueError, "must specify refCo to convert to Observed from Topocentric"
		return (obsFromTopo(fromP, self.refCo), _CnvObj.ZeroV)
	
	def TopocentricFromObserved(self, fromP, dumV):
		if self.refCo == None:
			raise ValueError, "must specify refCo to convert to Topocentric from Observed"
		return (topoFromObs(fromP, self.refCo), _CnvObj.ZeroV)

# create a singleton _CnvObj for the coordConv method to use
_TheCnvObj = _CnvObj()

# this is the only public function defined in this file
def coordConv(fromP, fromV, fromSys, fromDate, toSys, toDate, obsData=None, refCo=None):
		"""Converts a position from one coordinate system to another.
		
		Inputs:
		- fromP(3)	cartesian position (au)
		- fromV(3)	cartesian velocity (au/year); ignored if fromSys
					is Geocentric, Topocentric or Observed
		- fromSys	coordinate system from which to convert;
					any of the entries in the table below; use RO.CoordSys constants.
		- fromDate	date*
		- toSys		coordinate system to which to convert (see fromSys)
		- toDate	date*
		- obsData	an RO.Astro.Cnv.ObserverData object; required if fromSys or toSys
					is Topocentric or Observed; ignored otherwise.
		- refCo(2)	refraction coefficients; required if fromSys or toSys is Observed;
					ignored otherwise.
		
		Returns:
		- toP(3)	converted cartesian position (au)
		- toV(3)	converted cartesian velocity (au/year)

		*the units of date depend on the associated coordinate system:
		coord sys	def date	date
		ICRS		2000.0		Julian epoch of observation
		FK5			2000.0		Julian epoch of equinox and observation
		FK4			1950.0		Besselian epoch of equinox and observation
		Galactic	 now		Julian epoch of observation
		Geocentric	 now		UT1 (MJD)
		Topocentric	 now		UT1 (MJD)
		Observed	 now		UT1 (MJD)

		**Setting fromV all zero means the object is fixed. This slighly affects
		conversion to or from FK4, which has fictitious proper motion.
		
		Error Conditions:
		- If obsData or refCo are absent and are required, raises ValueError.
		
		Details:		
		The conversion is performed in two stages:
		- fromP/fromSys/fromDate -> ICRS
		- ICRS -> toP/toSys/toDate

		Each of these two stages is performed using the following graph:
		
		FK5 ------\
		FK4 ------ ICRS --- Geocentric -*- Topocentric -**- Observed
		Galactic--/
		
		* obsData required
		** refCo required
		"""
		return _TheCnvObj.coordConv(fromP, fromV, fromSys, fromDate, toSys, toDate, obsData, refCo)
