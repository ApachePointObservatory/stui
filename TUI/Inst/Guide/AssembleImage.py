#!/usr/bin/env python
"""Assemble a set of postage stamps images of guide fiber bundles into one image

The postage stamp images are displayed at full scale and in roughly
their correct position on the focal plane while using space efficiently.

This code implements an algorithm suggested by Jim Gunn, with a few refinements of my own.

TO DO:
- check orientation of decimated images. X and Y axes may have to be swapped or some such.
- clean up background subtraction:
  - Remove it if guider starts doing it
  - Modify it if un-set pixels in rotated postage stamps get a mask bit

History:
2009-07-14 ROwen    Initial work.
2009-10-29 ROwen    Modified for guider v1_0_10 preliminary.
"""
import itertools
import time
import numpy

PlateDiameterMM = 0.06053 * 3600 * 3 # 60.53 arcsec/mm, 3 degree FOV

def asArr(seq, shape=(2,), dtype=float):
    retArr = numpy.array(seq, dtype=dtype)
    if retArr.shape != tuple(shape):
        raise ValueError("Input data shape = %s != desired shape %s" % (retArr.shape, shape))
    return retArr

class StampInfo(object):
    """Information about a postage stamp
    
    For now allow much of the info to be None, but once the names are nailed down
    for the FITS file then require all of these that my code uses
    (and perhaps ditch the rest).
    """
    def __init__(self,
        shape,
        gpExists = True,
        gpEnabled = True,
        gpPlatePosMM = (numpy.nan, numpy.nan),
        gpCtr = (numpy.nan, numpy.nan),
        gpRadius = numpy.nan,
        gpFocusOffset = numpy.nan,
        starCtr = (numpy.nan, numpy.nan),
        starRotation = numpy.nan,
        starXYErrMM = (numpy.nan, numpy.nan),
        starRADecErrMM = (numpy.nan, numpy.nan),
        fwhmArcSec = numpy.nan,
        posErr = numpy.nan,
    ):
        """Create a StampInfo
        
        Note: more info is wanted, including:
        - what are the zero points of the various Ctr positions
        - are the Ctr positions rotated?
        
        Inputs (all in binned pixels unless noted):
        - shape: x,y shape of postage stamp
        - gpExists: guide probe exists
        - gpEnabled: guide probe enabled (forced False if gpExists is False)
        - gpPlatePosMM: x,y position of guide probe on plate (mm)
        - gpCtr: desired x,y center of probe
        - gpRadius: radius of guide probe active area; binned pixels
        - gpFocusOffset: focus offset of guide probe (um, direction unknown)
        - starCtr: measured star x,y center
        - starRotation: rotation of star on sky (deg)
        - starXYErrMM: position error of guide star on image (mm)
        - starRADecErrMM: position error of guide star on image in RA, Dec on sky (mm)
        - fwhmArcSec: FWHM of star (arcsec -- not consistent with other units, but what we get)
        - posErr: ???a scalar of some kind; centroid uncertainty? (???)
        """
        self.shape = asArr(shape, dtype=int)
        self.gpExists = bool(gpExists)
        self.gpEnabled = bool(gpEnabled) and self.gpExists # force false if probe does not exist
        self.gpPlatePosMM = asArr(gpPlatePosMM)
        self.gpRadius = float(gpRadius)
        self.starCtr = asArr(starCtr)
        self.starRotation = float(starRotation)
        self.starXYErrMM = asArr(starXYErrMM)
        self.starRADecErrMM = asArr(starRADecErrMM)
        self.fwhmArcSec = float(fwhmArcSec)
        self.posErr = float(posErr)
        self.decImStartPos = None
        self.decImCtrPos = None
    
    def setDecimatedImagePos(self, ctrPos):
        """Set position of center stamp on decimated image.
        
        Inputs:
        - ctrPos: desired position of center of postage stamp on decimated image (float x,y)
        """
        ctrPos = numpy.array(ctrPos, dtype=float)
        self.decImStartPos = numpy.round(ctrPos - (self.shape / 2.0)).astype(int)
        self.decImEndPos = self.decImStartPos + self.shape
        self.decImCtrPos = (self.decImStartPos + self.decImEndPos) / 2.0

    def getDecimatedImageRegion(self):
        """Return region of this stamp on the decimated image.
        The indices are swapped because that's now numpy does it.
        """
        return tuple(slice(self.decImStartPos[i], self.decImEndPos[i]) for i in (1, 0))

def decimateStrip(imArr):
    """Break an image consisting of a row of square postage stamps into individual postage stamp images.
    
    Inputs:
    - imArr: an image array of shape [imageSize * numIm, imageSize], where numIm is an integer
    
    Returns:
    - stampImageList: a list of numIm image arrays, each imageSize x imageSize
    
    Note: the axes of imArr are (y, x) relative to ds9 display of the image.
    
    Raise ValueError if imArr shape is not [imageSize * numIm, imageSize], where numIm is an integer
    """
    stampShape = imArr.shape
    stampSize = imArr.shape[1]
    numIm = stampShape[0] / stampSize
    if stampSize * numIm != stampShape[0]:
        raise ValueError("image shape %s is not a column of an even number of squares" % (stampShape,))
    stampImageList = [imArr[(ind * stampSize):((ind + 1) * stampSize), :] for ind in range(numIm)]
    return stampImageList


class AssembleImage(object):
    # tuning constants
    InitialCorrCoeff = 1.5
    MinQuality = 5.0    # system is solved when quality metric reaches this value
    MaxIters = 100
    Separation = 2  # separation between postage stamps, in binned pixels
    def __init__(self, relSize=1.0):
        """Create a new AssembleImage
        
        Inputs:
        - relSize: size of assembled image (along x or y) / size of original image
        """
        self.relSize = float(relSize)

    def __call__(self, guideImage):
        """Assemble an image array by arranging postage stamps from a guider FITS image
        
        Inputs:
        - guideImage: a guider image (pyfits image):
        
        Returns:
        - retImageArr: assembled image array (numpy array)
        - retMaskArr: assembled mask array (numpy array); bit 0=sat, 1=bad, 2=masked
        - stampInfoList: a list of StampInfo objects, one entry per postage stamp
        
        Note: the contents of the images and masks are not interpreted by this routine;
        the data is simply rearranged into a new output image and mask.
        
        Image format: SDSSFmt = gproc 1 x
        <http://sdss3.apo.nmsu.edu/opssoft/guider/ProcessedGuiderImages.html>
        """
        inImageSize = numpy.array(guideImage[0].data.shape, dtype=int)
        imageSize = numpy.array(inImageSize * self.relSize, dtype=int)
        dataTable = guideImage[6].data

        # subtract estimated background; I hope the guider will do this in the future
        nonBkgndMask = (guideImage[1].data != 0)
        for dataEntry in dataTable:
            gpCtr = int(dataEntry["xCenter"] + 0.5), int(dataEntry["yCenter"] + 0.5)
            gpRadius = int(dataEntry["radius"] + 0.5)
            nonBkgndMask[gpCtr[0]-gpRadius: gpCtr[0]+gpRadius, gpCtr[1]-gpRadius: gpCtr[1]+gpRadius] = 1
        bkgndImage = numpy.ma.array(guideImage[0].data, mask=nonBkgndMask)
        bkgndPixels = bkgndImage.compressed()
        meanBkgnd = bkgndPixels.mean()
#        print "mean background=", meanBkgnd
        
        smallStampImage = guideImage[2].data
        smallStampImage = numpy.where(smallStampImage > 0, smallStampImage - meanBkgnd, 0)
        largeStampImage = guideImage[4].data
        largeStampImage = numpy.where(largeStampImage > 0, largeStampImage - meanBkgnd, 0)
        
        smallStampImageList = decimateStrip(smallStampImage)
        smallStampMaskList = decimateStrip(guideImage[3].data)
        smallStampSize = smallStampImageList[0].shape
        numSmallStamps = len(smallStampImageList)

        largeStampImageList = decimateStrip(largeStampImage)
        largeStampMaskList = decimateStrip(guideImage[5].data)
        largeStampSize = largeStampImageList[0].shape
        numLargeStamps = len(largeStampImageList)
        stampImageList = smallStampImageList + largeStampImageList
        stampMaskList  = smallStampMaskList  + largeStampMaskList
        numStamps = len(stampImageList)
        
        shapeArr = numpy.array([stampImage.shape for stampImage in stampImageList])
        radArr = (numpy.sqrt(shapeArr[:, 0]**2 + shapeArr[:, 1]**2) + self.Separation) / 2.0
        
        bgPixPerMM = (imageSize - smallStampSize) / PlateDiameterMM
        minPosMM = -imageSize / (2.0 * bgPixPerMM)

        stampInfoList = []
        for ind, dataEntry in enumerate(dataTable):
            if dataEntry["fiber_type"].lower() == "tritium":
                continue
            stampInfoList.append(StampInfo(
                shape = shapeArr[ind],
                gpExists = dataEntry["exists"],
                gpEnabled = dataEntry["enabled"],
                gpPlatePosMM = (dataEntry["xFocal"], dataEntry["yFocal"]),
                gpCtr = (dataEntry["xCenter"], dataEntry["yCenter"]),
                gpRadius = dataEntry["radius"],
                gpFocusOffset = dataEntry["focusOffset"],
                starRotation = dataEntry["rotStar2Sky"],
                starCtr = (dataEntry["xstar"], dataEntry["ystar"]),
                starXYErrMM = (dataEntry["dx"], dataEntry["dy"]),
                starRADecErrMM = (dataEntry["dRA"], dataEntry["dDec"]),
                fwhmArcSec = (dataEntry["fwhm"]),
                posErr = dataEntry["poserr"],
            ))
        if len(stampInfoList) != len(stampImageList):
            raise ValueError("number of non-tritium data entries = %s != %s = number of postage stamps" % \
                (len(stampInfoList), len(stampImageList)))
        desPosArrMM = numpy.array([stampInfo.gpPlatePosMM for stampInfo in stampInfoList])
        desPosArr = (desPosArrMM - minPosMM) * bgPixPerMM

        actPosArr, quality, nIter = self.removeOverlap(desPosArr, radArr, imageSize)

        retImageArr = numpy.zeros(imageSize, dtype=float)
        retMaskArr  = numpy.zeros(imageSize, dtype=numpy.uint8)
        junk = False
        for stampInfo, actPos, stampImage, stampMask in \
            itertools.izip(stampInfoList, actPosArr, stampImageList, stampMaskList):
            stampInfo.setDecimatedImagePos(actPos)
            mainRegion = stampInfo.getDecimatedImageRegion()
#            print "put annotation centered on %s at %s" % (stampInfo.decImCtrPos, mainRegion)
            retImageArr[mainRegion] = stampImage
            retMaskArr [mainRegion] = stampMask
        return (retImageArr, retMaskArr, stampInfoList)

    def removeOverlap(self, desPosArr, radArr, imageSize):
        """Remove overlap from an array of bundle positions.
        
        Inputs:
        - desPosArr: an array of the desired position of the center of each postage stamp
        - radArr: an array of the radius of each postage stamp
        - imageSize: size of image
        
        Returns:
        - actPosArr: an array of positions of the center of each postage stamp
        - quality: quality of solution; smaller is better
        - nIter: number of iterations
        """
        actPosArr = desPosArr.copy()
        maxCorr = radArr.min()
        quality = numpy.inf 
        corrArr = numpy.zeros(actPosArr.shape, dtype=float)
        corrCoeff = self.InitialCorrCoeff
        nIter = 0
        nUndos = 0
#        print "corrCoeff=%s" % (corrCoeff,)
        while quality >= self.MinQuality:
            corrArr[:,:] = 0.0
            edgeQuality = self.computeEdgeCorr(corrArr, actPosArr, radArr, corrCoeff, imageSize)
            conflictQuality = self.computeConflictCorr(corrArr, actPosArr, radArr, corrCoeff)
            quality = edgeQuality + conflictQuality
#            print "quality=%s; edgeQuality=%s; conflictQuality=%s" % (quality, edgeQuality, conflictQuality)

            # limit correction to max corr
            corrRadius = numpy.sqrt(corrArr[:, 0]**2 + corrArr[:, 1]**2)
            for ind in range(2):
                corrArr[:,ind] = numpy.where(corrRadius > maxCorr, (corrArr[:,ind] / corrRadius) * maxCorr, corrArr[:,ind])
            actPosArr += corrArr
            quality = edgeQuality + conflictQuality

            nIter += 1
            if nIter > self.MaxIters:
                break

        return (actPosArr, quality, nIter)

    def computeEdgeCorr(self, corrArr, posArr, radArr, corrFrac, imageSize):
        """Compute corrections to keep fiber bundles on the display
        
        In/Out:
        - corrArr: updated
        
        In:
        - posArr: position of each fiber bundle
        - radArr: radius of each bundle
        - corrFrac: fraction of computed correction to apply
        - imageSize: size of image
        
        Returns:
        - quality: quality of solution due to edge overlap
        """
        quality = 0
        llBound = radArr
        urBound = imageSize - radArr[:, numpy.newaxis]
#         print "llBound=%s; urBound=%s; rad=%s" % (llBound, urBound, rad)
        for ind, pos in enumerate(posArr):
            corr = numpy.where(pos < llBound[ind], llBound[ind] - pos, 0)
#             print "pos=%s, llBound=%s, where=%s" % \
#                 (pos, llBound, numpy.where(pos < llBound, llBound - pos, 0))
            corr += numpy.where(pos > urBound[ind], urBound[ind] - pos, 0)
#            print "ind=%s, corr=%s" % (ind, corr)
            quality += (corr[0]**2 + corr[1]**2)
            corrArr[ind] += corr * corrFrac
#        print "quality=%s, corrArr=%s" % (quality, corrArr)
        return quality

    def computeConflictCorr(self, corrArr, posArr, radArr, corrFrac):
        """Compute corrections to avoid overlap with other bundles

        In:
        - posArr: position of each fiber bundle
        - radArr: radius of each bundle
        - corrFrac: fraction of computed correction to apply
        
        Returns:
        - quality: quality of solution due to overlap with other bundles
        """
        quality = 0
        corr = numpy.zeros(2, dtype=float)
        for ind, pos in enumerate(posArr):
            rad = radArr[ind]
            minSepArr = radArr + rad
            corr = numpy.zeros(2, dtype=float)
            diffVec = pos - posArr
            radSepArr = numpy.sqrt(diffVec[:,0]**2 + diffVec[:,1]**2)
            radSepArr[ind] = minSepArr[ind] # don't try to avoid self
            # note: correct half of error; let other object correct the rest
            corrRadArr = numpy.where(radSepArr < minSepArr, 0.5 * (minSepArr - radSepArr), 0.0)
            corrArr2 = (diffVec / radSepArr[:,numpy.newaxis]) * corrRadArr[:,numpy.newaxis]
            corr = numpy.sum(corrArr2, 0)
            quality += (corr[0]**2 + corr[1]**2)
            corrArr[ind] += corr * corrFrac
        return quality

if __name__ == "__main__":
    import pyfits
    imAssembler = AssembleImage()
    im = pyfits.open("proc-dummy_star.fits")
    results = imAssembler(im)
    print results
