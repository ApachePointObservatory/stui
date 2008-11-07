#!/usr/bin/env python
"""Code to handle imager windowing (subimage) and binning.

Note: uses the expansionist or inclusive philosophy.
The new window is grown to the maximum possible extent
whenever binning or unbinning. For example:
- An unbinned window of [1-3, 1-3, 1-3, 1-3] will bin 3x3 to [1, 1, 1, 1]
- A 3x3 binned window of [1, 1, 1, 1] will unbin to [1, 1, 3, 3]

2008-11-06 ROwen
"""
import math
import RO.CnvUtil

class ImageWindow(object):
    """Class to handle imager windowing and binning.
    
    Optimized for use with instruments that directly report
    x,y bin factor and unbinned window whenever those values change.
    However, you can use this with other instruments by calling
    the appropriate functions when needed.

    Inputs:
    - imSize        image size (x, y unbinned pixels)
    - isOneBased    if True, the address of the LL pixel is (1,1)
                    else it is (0,0). DIS uses (1,1).
    - isInclusive   if True, the max x, max y portion of the image window
                    is included in the data, else it is omitted.
                    DIS uses True, but some instruments may prefer False
                    since it is matches C++ and Python style indexing.
    
    *Key variables are defined in RO.KeyVariable.
    """
    def __init__(self,
        imSize,
        isOneBased = True,
        isInclusive = True,
    ):
        if len(imSize) != 2:
            raise ValueError("imSize must be two integers; imSize = %r" % (imSize,))
        self.imSize = tuple([int(mc) for mc in imSize])
        self.isInclusive = bool(isInclusive)
        
        if self.isInclusive:
            urPosAdj = 0
            ubUROff = 0
            binUROff = -1
        else:
            urPosAdj = 1
            ubUROff = 1
            binUROff = 0
        
        def posToWin(xyPos, urOff):
            return tuple(xyPos) + tuple([val + urOff for val in xyPos])

        if isOneBased:
            imLL = (1, 1)
        else:
            imLL = (0, 0)
        imUR = [(imLL[ind] + imSize[ind] - 1) for ind in range(2)]
        self.minWin = posToWin(imLL, urPosAdj)
        self.maxUBWin = posToWin(imUR, urPosAdj)

        self.binWinOffset = posToWin(imLL, ubUROff)
        self.ubWinOffset = posToWin(imLL, binUROff)
            
    def binWindow(self, ubWin, binFac):
        """Converts unbinned window to binned.
        
        The output is constrained to be in range for the given bin factor,
        though this is only an issue if ubWin is out of range.

        Inputs:
        - ubWin: unbinned window coords (LL x, LL y, UR x, UR y)
        
        Returns binned window coords (LL x, LL y, UR x, UR y)
        
        If any element of ubWin or binFac is None, all returned elements are None.
        """
        if len(ubWin) != 4:
            raise ValueError("ubWin=%r; must have 4 elements" % (ubWin,))
        if len(binFac) != 2:
            raise ValueError("binFac=%r; must have 2 elements" % (binFac,))
            
        if None in ubWin or None in binFac:
            return (None,)*4
        
        # apply limits
        ubWin = [min(max(ubWin[ind], self.minWin[ind]), self.maxUBWin[ind])
            for ind in range(4)]
        
        binXYXY = binFac * 2

        # apply binning
        binWin = [int(math.floor(self.binWinOffset[ind] + ((ubWin[ind] - self.binWinOffset[ind]) / float(binXYXY[ind]))))
            for ind in range(4)]
#       print "binWindow(ubWin=%r, binFac=%r) = %r" % (ubWin, binFac, binWin)
        return binWin
    
    def unbinWindow(self, binWin, binFac):
        """Converts binned window to unbinned.
        
        The output is constrained to be in range for the given bin factor.

        Inputs:
        - binWin: binned window coords (LL x, LL y, UR x, UR y)
        
        Returns unbinned window coords: (LL x, LL y, UR x, UR y)
        
        If any element of ubWin or binFac is None, all returned elements are None.
        """
        if len(binWin) != 4:
            raise ValueError("binWin=%r; must have 4 elements" % (binWin,))
        if len(binFac) != 2:
            raise ValueError("binFac=%r; must have 2 elements" % (binFac,))
            
        if None in binWin or None in binFac:
            return (None,)*4
        
        binXYXY = [int(binFac[ii]) for ii in (0, 1, 0, 1)]
        binWin = [int(val) for val in binWin]

        # unbin window, ignoring limits
        ubWin = [((binWin[ind] - self.ubWinOffset[ind]) * binXYXY[ind]) + self.ubWinOffset[ind]
            for ind in range(len(binWin))]
        
        # apply limits
        ubWin = [min(max(ubWin[ind], self.minWin[ind]), self.maxUBWin[ind])
            for ind in range(4)]
#       print "unbinWindow(binWin=%r, binFac=%r) = %r" % (binWin, binFac, ubWin)
        return ubWin
    
    def getMinWindow(self):
        """Return the minimum window coords (which is independent of bin factor).
        
        Returns (LL x, LL y, UR x, UR y)
        """
        return self.minWin[:]

    def getMaxBinWindow(self, binFac=(1,1)):
        """Return the maximum binned window coords, given a bin factor.
        Note: the minimum window coords are the same binned or unbinned: self.minWin

        Returns (LL x, LL y, UR x, UR y)
        """
        if len(binWin) != 4:
            raise ValueError("binWin=%r; must have 4 elements" % (binWin,))
        binXYXY = [int(binFac[ii]) for ii in (0, 1, 0, 1)]
        return [int(math.floor(self.binWinOffset[ind] + ((self.maxUBWin[ind] - self.binWinOffset[ind]) / float(binXYXY[ind]))))
            for ind in range(4)]


if __name__ == "__main__":
    ci = ImageWindow(imSize=(2045, 1024))
    for bfx in range(1, 4):
        binFac = (bfx, bfx)
        for begInd in range(1, bfx + 1):
            for endInd in range(begInd, bfx + 1):
                unbWin = [begInd, begInd, endInd, endInd]
                binWin = tuple(ci.binWindow(unbWin, binFac))
                if binWin != (1, 1, 1, 1):
                    raise RuntimeError("Test failed; unbWin=%s != (1, 1, 1, 1), binWin=%s; binFac=%s" % \
                        (unbWin, binWin, binFac))
                newUnbWin = tuple(ci.unbinWindow(binWin, binFac))
                if newUnbWin != (1, 1, bfx, bfx):
                    raise RuntimeError("Test failed; newUnbWin=%s != (1, 1, %s, %s), binWin=%s; binFac=%s" % \
                        (newUnbWin, bfx, bfx, binWin, binFac))
            
