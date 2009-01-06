#!/usr/bin/env python
"""Code to handle imager windowing (subimage) and binning.

Note: uses the expansionist or inclusive philosophy.
The new window is grown to the maximum possible extent
whenever binning or unbinning. For example, assuming 1-based and inclusive:
- An unbinned window of [1/2/3, 1/2/3, 4/5/6, 4/5/6] will bin 3x3 to [1, 1, 2, 2]
- A 3x3 binned window of [1, 1, 2, 2] will unbin to [1, 1, 6, 6]

2008-11-06 ROwen
2008-12-15 ROwen    Bug fix: binWindow was mis-computing limits.
"""
import math
import RO.CnvUtil

class ImageWindow(object):
    """Class to handle imager windowing and binning.
    
    Users typically prefer to specify windows (subregions) in binned coordinates,
    but then what happens if the user changes the bin factor? This class offers
    functions that help handle such changes.

    Inputs:
    - imSize        image size (x, y unbinned pixels)
    - isOneBased    if True, the address of the lower left pixel is (1,1), else it is (0, 0)
    - isInclusive   if True, the upper right portion of the image window is included in the data,
                    else it is omitted.
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
        if None in ubWin or None in binFac:
            return (None,)*4
        ubWin = self._getWin(ubWin, "ubWin")
        binXYXY = self._getBinXYXY(binFac)
        
        # bin window, ignoring limits
        binWin = [int(math.floor(self.binWinOffset[ind] + ((ubWin[ind] - self.binWinOffset[ind]) / float(binXYXY[ind]))))
            for ind in range(4)]

        # apply limits
        binWin = [min(max(binWin[ind], self.minWin[ind]), self.maxUBWin[ind] // binXYXY[ind]) for ind in range(4)]

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
        if None in binWin or None in binFac:
            return (None,)*4
        binWin = self._getWin(binWin, "binWin")
        binXYXY = self._getBinXYXY(binFac)

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
        binXYXY = self._getBinXYXY(binFac)
        return [int(math.floor(self.binWinOffset[ind] + ((self.maxUBWin[ind] - self.binWinOffset[ind]) / float(binXYXY[ind]))))
            for ind in range(4)]

    def _getBinXYXY(self, binFac):
        """Check bin factor and return as 4 ints: x, y, x, y"""
        if len(binFac) != 2:
            raise ValueError("binFac=%r; must have 2 elements" % (binFac,))
        try:
            binXY = [int(bf) for bf in binFac]
        except Exception:
            raise ValueError("binFac=%r; must have 2 integers" % (binFac,))
        if min(binXY) < 1:
            raise ValueError("binFac=%r; must be >= 1" % (binFac,))
        return binXY * 2

    def _getWin(self, win, winName="window"):
        """Check window argument and return as 4 ints"""
        if len(win) != 4:
            raise ValueError("%s=%r; must have 4 elements" % (winName, win))
        try:
            return [int(w) for w in win]
        except Exception:
            raise ValueError("%s=%r; must have 4 integers" % (winName, win))


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
            
