"""Class to represent the coordinates of a subframe of an image.

Includes some specializations (in fromFITS) that are unique to APO 3.5m guide images
though at some point the info may also be found in 3.5m science images.

History:
2006-09-13 ROwen
"""
import numarray as num

class SubFrame(object):
	def __init__(self, fullSize, subBeg, subSize):
		"""SubFrame represents the coordinates of a subframe of an image.
		
		Primarily works in unbinned pixels,
		but includes methods that work in binned pixels.
		
		Inputs:
		- fullSize: x, y size of full frame, in unbinned pixels
		- subBeg: x, y coordinate of start of subframe, in unbinned pixels;
			0,0 is lower-left pixel
		- subSize: x, y size of subframe in unbinned pixels
		"""
		self.fullSize = num.array(fullSize, shape=[2], type=num.Int)
		self.setSubBegSize(subBeg, subSize)
	
	def _binAsArr(self, binFac):
		"""Convert bin factor (one int or a pair of ints) to an integer array.
		"""
		if not hasattr(binFac, "__iter__"):
			binFac = (binFac, binFac)

		return num.array(binFac, shape=[2], type=num.Int)

	def __eq__(self, sf):
		"""Test equality with another SubFrame object
		"""
		if sf == None:
			return False

		return num.alltrue(self.fullSize == sf.fullSize) \
			and num.alltrue(self.subBeg == sf.subBeg) \
			and num.alltrue(self.subSize == sf.subSize)
	
	def copy(self):
		"""Return a copy of self"""
		return SubFrame(
			fullSize = self.fullSize,
			subBeg = self.subBeg,
			subSize = self.subSize,
		)

	def fromBinInfo(cls, fullSize, binFac, binSubBeg, binSubSize):
		"""Create a new SubFrame object from binned information.
		
		Inputs:
		- fullSize: x, y size of full frame, in unbinned pixels
		- binFac: x,y bin factor (if a single value, used for x and y)
		- binSubBeg: x, y coordinate of start of subframe, in binned pixels;
			0,0 is lower-left pixel
		- binSubSize: x, y size of subframe in binned pixels
		"""
		retObj = cls(
			fullSize = fullSize,
			subBeg = (0, 0),
			subSize = fullSize,
		)
		retObj.setBinSubBegSize(binFac, binSubBeg, binSubSize)
		return retObj
	fromBinInfo = classmethod(fromBinInfo)
	
	def fromFITS(cls, fitsHdr):
		"""Return a SubFrame object created from a fits header
		or dictionary containing the following keys
		(some of which are not part of the FITS standard):
		- FULLX,Y: unbinned size of full frame
		- BINX,Y: bin factor
		- BEGX,Y: binned size of subframe
		- NAXIS1,2: binned size of subframe
		
		Raises ValueError if any data is missing or invalid.
		"""
		try:
			fullSize = [int(fitsHdr.get(name)) for name in ("FULLX", "FULLY")]
			binFac = [int(fitsHdr.get(name)) for name in ("BINX", "BINY")]
			# This class uses 0,0 for the lower-left pixel
			# Normally FITS uses 1,1 (at least for WCS info)
			# but BEGX,Y uses 0,0; if that ever changes to the FITS standard
			# subtract 1 in the next line
			binSubBeg = [int(fitsHdr.get(name)) for name in ("BEGX", "BEGY")]
			binSubSize = [int(fitsHdr.get(name)) for name in ("NAXIS1", "NAXIS2")]
		except (KeyError, TypeError), e:
			raise ValueError(str(e))
		return cls.fromBinInfo(
			fullSize = fullSize,
			binFac = binFac,
			binSubBeg = binSubBeg,
			binSubSize = binSubSize,
		)
	fromFITS = classmethod(fromFITS)
	
	def getBinSubBegSize(self, binFac):
		"""Return binned subframe beg and size (as two separate arrays).
		
		Inputs:
		- binFac: x,y bin factor (if a single value, used for x and y)
		"""
		binFac = self._binAsArr(binFac)
		return (self.subBeg / binFac), (self.subSize / binFac)
	
	def getSubBegSize(self):
		"""Return unbinned subframe beg and size (as two separate arrays).
		
		Inputs:
		- binFac: x,y bin factor (if a single value, used for x and y)
		"""
		return (self.subBeg.copy(), self.subSize.copy())
	
	def isFullFrame(self):
		"""Return True if subframe is full frame.
		"""
		return num.alltrue(self.fullSize == self.subSize)
	
	def setBinSubBegSize(self, binFac, binSubBeg, binSubSize):
		"""Set subframe from binned beginning and size.
		"""
		binFac = self._binAsArr(binFac)
		self.subBeg = binFac * num.array(binSubBeg, shape=[2], type=num.Int)
		self.subSize = binFac * num.array(binSubSize, shape=[2], type=num.Int)

	def setFullFrame(self):
		"""Set subframe to full frame.
		"""
		self.subBeg = num.zeros(shape=[2], type=num.Int)
		self.subSize = self.fullSize.copy()
	
	def setSubBegSize(self, subBeg, subSize):
		"""Set subframe from unbinned beginning and size.
		"""
		self.subBeg = num.array(subBeg, shape=[2], type=num.Int)
		self.subSize = num.array(subSize, shape=[2], type=num.Int)
