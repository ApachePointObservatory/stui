"""Class to represent the coordinates of a subframe of an image.

Includes some specializations (in fromFITS) that are unique to APO 3.5m guide images
though at some point the info may also be found in 3.5m science images.

History:
2006-09-14 ROwen
2006-09-26 ROwen    Added isEqualBinned and isFullFrameBinned methods.
                    Broke binFacAsArr out as a separate function.
2006-11-06 ROwen    Modified for newly 1-based BEGX/Y in FITS headers.
2006-12-13 ROwen    Clarified some doc strings.
2007-04-24 ROwen    Modified to use numpy instead of numarray.
"""
import numpy
import RO.SeqUtil

def binFacAsArr(binFac):
    """Convert bin factor (one int or a pair of ints) to an integer array.
    """
    if not RO.SeqUtil.isSequence(binFac):
        binFac = (binFac, binFac)

    return numpy.array(binFac, dtype=numpy.int).reshape([2])

class SubFrame(object):
    def __init__(self, fullSize, subBeg, subSize):
        """SubFrame represents the coordinates of a subframe of an image.
        
        Primarily works in unbinned pixels,
        but includes methods that work in binned pixels.
        
        Inputs:
        - fullSize: x,y size of full frame, in unbinned pixels
        - subBeg: x,y coordinate of lower left corner of subframe, in unbinned pixels;
            0,0 is lower-left pixel
        - subSize: x,y size of subframe in unbinned pixels
        """
        self.fullSize = numpy.array(fullSize, dtype=numpy.int).reshape([2])
        self.setSubBegSize(subBeg, subSize)
    
    def __eq__(self, sf):
        """Test equality with another SubFrame object
        """
        if sf == None:
            return False

        return numpy.alltrue(self.fullSize == sf.fullSize) \
            and numpy.alltrue(self.subBeg == sf.subBeg) \
            and numpy.alltrue(self.subSize == sf.subSize)
    
    def __repr__(self):
        return "SubFrame(fullSize=%s, subBeg=%s, subSize=%s)" % \
            (tuple(self.fullSize), tuple(self.subBeg), tuple(self.subSize))
    
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
        - fullSize: x,y size of full frame, in unbinned pixels
        - binFac: x,y bin factor (if a single value, used for x and y)
        - binSubBeg: x, y coordinate of lower left corner of subframe, in binned pixels;
            0,0 is lower-left pixel
        - binSubSize: x, y size of subframe, in binned pixels
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
        - FULLX,Y: x,y size of full frame, in unbinned pixels
        - BINX,Y: x,y bin factor
        - BEGX,Y: x, y coordinate of lower left corner of subframe, in binned pixels;
            1,1 is lower-left pixel
        - NAXIS1,2: x,y size of subframe, in binned pixels
        
        Raises ValueError if any data is missing or invalid.
        """
        try:
            fullSize = [int(fitsHdr.get(name)) for name in ("FULLX", "FULLY")]
            binFac = [int(fitsHdr.get(name)) for name in ("BINX", "BINY")]
            # This class uses 0,0 for the lower-left pixel
            # but BEGX,Y use the FITS standard of 1,1, thus the "-1"...
            binSubBeg = [int(fitsHdr.get(name))-1 for name in ("BEGX", "BEGY")]
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
        binFac = binFacAsArr(binFac)
        return (self.subBeg / binFac), (self.subSize / binFac)
    
    def getSubBegSize(self):
        """Return unbinned subframe beg and size (as two separate arrays).
        
        Inputs:
        - binFac: x,y bin factor (if a single value, used for x and y)
        """
        return (self.subBeg.copy(), self.subSize.copy())
    
    def isEqualBinned(self, binFac, sf):
        """Return True if this subframe is equal to another
        when binned by the specified amount.
        (Binned subframes may be equal even if unbinned ones are not.)
        
        Inputs:
        - binFac: x,y bin factor (if a single value, used for x and y)
        - sf: the subframe being compared
        """
        if sf == None:
            return False

        binFac = binFacAsArr(binFac)
        myBinBeg, myBinSize = self.getBinSubBegSize(binFac)
        sfBinBeg, sfBinSize = sf.getBinSubBegSize(binFac)
        return numpy.alltrue(self.fullSize == sf.fullSize) \
            and numpy.alltrue(myBinBeg == sfBinBeg) \
            and numpy.alltrue(myBinSize == sfBinSize)
    
    def isFullFrame(self):
        """Return True if subframe is full frame.
        """
        return numpy.alltrue(self.fullSize == self.subSize)
    
    def isFullFrameBinned(self, binFac):
        """Return True if subframe is full frame
        at a particular bin factor.
        """
        binFac = binFacAsArr(binFac)
        binBeg, binSize = self.getBinSubBegSize(binFac)
        binFullSize = self.fullSize / binFac
        #print "isFullFrameBinned; binFac=%s; binBeg=%s, binSize=%s, binFullSize=%s" % (binFac, binBeg, binSize, binFullSize)
        return numpy.alltrue(binBeg == [0, 0]) \
            and numpy.alltrue(binSize == binFullSize)
    
    def setBinSubBegSize(self, binFac, binSubBeg, binSubSize):
        """Set subframe from binned beginning and size.
        """
        binFac = binFacAsArr(binFac)
        self.subBeg = binFac * numpy.array(binSubBeg, dtype=numpy.int).reshape([2])
        self.subSize = binFac * numpy.array(binSubSize, dtype=numpy.int).reshape([2])

    def setFullFrame(self):
        """Set subframe to full frame.
        """
        self.subBeg = numpy.zeros(2, dtype=numpy.int)
        self.subSize = self.fullSize.copy()
    
    def setSubBegSize(self, subBeg, subSize):
        """Set subframe from unbinned beginning and size.
        """
        self.subBeg = numpy.array(subBeg, dtype=numpy.int).reshape([2])
        self.subSize = numpy.array(subSize, dtype=numpy.int).reshape([2])
