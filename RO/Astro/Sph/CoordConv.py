#!/usr/local/bin/python
import Const
from RO.Astro import Cnv
import RO.MathUtil
from CCFromSCPV import *
from CCFromSCPVOff import *
from SCFromCCPVOff import *

def coordConv (
		fromPos, fromSys, fromDate, toSys, toDate,
		fromPM = (0.0, 0.0), fromParlax=0.0, fromRadVel=0.0,
		obsData = None, refCo = None, fromDir=0.0,
):
	"""
	Converts position, velocity, and unit position offset
	from one coordinate system to another.
	
	Inputs:
	- fromPos(2)	input position (deg)
	- fromSys		coord. system from which to convert (e.g. "ICRS");
					any of the entries in the table below; use RO.CoordSys constants.
	- fromDate		date of "from" coordinates*.
	- toSys			coordinate system to which to convert (see fromSys)
	- toDate		date of "to" coordinates*
	- fromPM(2)**	input proper motion (arcsec per century***); default is (0,0)
	- fromParlax**	input parallax (arcsec)
	- fromRadVel**	input radial velocity (km/sec, positive receding)
	- obsData		an RO.Astro.Cnv.ObserverData object; required if fromSys or toSys
					is Topocentric or Observed; ignored otherwise.
	- refCo(2)		refraction coefficients; required if fromSys or toSys is Observed;
					ignored otherwise.
	- fromDir		input reference direction (deg); input axis 1 = 0, axis 2 = 90
	
	Returns:
	- toPos(2)		converted position
	- toPM(2)		converted proper motion
	- toParlax		converted parallax
	- toRadVel		converted radial velocity
	- toDir			converted reference direction (deg); output axis 1 = 0, axis 2 = 90;
					the wrap is chosen so that |toDir - fromDir| < 360
	- ScaleChange	scale change along reference dir. (out mag/in mag)
	- atInf			true => object very far away (see Error Conditions)
	- atPole		true => toPos near the pole (see Error Conditions)

	*the units of date depend on the associated coordinate system:
	coord sys	def date	date
	ICRS		2000.0		Julian epoch of observation
	FK5			2000.0		Julian epoch of equinox and observation
	FK4			1950.0		Besselian epoch of equinox and observation
	Galactic	 now		Julian epoch of observation
	Geocentric	 now		UT1 (MJD)
	Topocentric	 now		UT1 (MJD)
	Observed	 now		UT1 (MJD)
	
	**Setting proper motion, parallax and radial velocity all zero implies
	the object is fixed. This slighly affects conversion to or from FK4,
	which has fictitious proper motion.
	These inputs are ignored for conversion from apparent coordinate systems.
	***Besselian for the FK4 system, Julian for all others
	
	Error Conditions:
	- If obsData or refCo are absend and are required, raises ValueError.
	- If the object is very far away: atInf is set true,
	  toParlax is set to 0.0 and toRadVel = fromRadVel.
	- If toPos is too near the pole: atPole is set 1
	  and toPos[0], toPM[0] and toDir are incorrect.
	
	Details:
	Sph.CoordConv is simply a front end to Cnv.CoordConv (which see)
	with the added support for measuring angle and scale factor.

	fromDir, toDir and ScaleChange:
	fromDir is used to create a small vector perpendicular to fromPos.
	A second position is created offset by this much, and both positions
	are converted. The resulting difference is then turned into a direction
	(toDir) and a length (ScaleChange = toOffMag/fromMag). This is used to track
	the effects of the conversion on orientation, for driving the rotator.
	
	In most cases, one may set fromDir = 0, ignore ScaleChange,
	and use toDir as the change in orientation.
	
	However, for drift scanning, you should set fromDir to the direction
	you are moving. This allows you to compensate velocity for refraction
	to keep the stars moving at the same rate across the CCD.
	Current scan velocity = scaleFactor * desired constant scan rate on sky.
	
	Note: actually implementing such a scan can be a headache as it mixes
	path length as seen at the telescope with a path whose direction
	is given in mean sky coordinates. On the TCCs I end up doing
	a bit of iteration and keeping track of	accumulated path length.
	If you have a small enough field of view you may be able to skip
	this step and put up with the resulting slight image blur.
	
	History:
	2002-08-23 ROwen  Untested beta. Converted to Python from the TCC's sph_CoordConv 6-4
	"""
	# convert RA, Dec, etc to cartesian coordinates
	fromP, fromV, fromOffP, atInf = ccFromSCPVOff (
		fromPos, fromPM, fromParlax, fromRadVel, fromDir, Const.OffMag)

	# convert coordinates
	toP, toV = Cnv.coordConv(fromP, fromV, fromSys, fromDate, toSys, toDate, obsData, refCo)
	toOffP, dumV = Cnv.coordConv(fromOffP, fromV, fromSys, fromDate, toSys, toDate, obsData, refCo)
	
	toPos, toPM, toParlax, toRadVel, toDir, toOffMag, atPole = scFromCCPVOff (toP, toV, toOffP)

	# put toDir into same wrap as fromDir
	toDir = fromDir + RO.MathUtil.wrapCtr (toDir - fromDir)

	# if at infinity, zero parallax and set to radial velocity = from radial velocity
	if atInf:
		toParlax = 0.0
		toRadVel = fromRadVel

	scaleChange = toOffMag / Const.OffMag

	return (toPos, toPM, toParlax, toRadVel, toDir, scaleChange, atInf, atPole)
