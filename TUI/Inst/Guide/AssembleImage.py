#!/usr/bin/env python
"""Assemble a set of postage stamps images of guide fiber bundles into one image

The postage stamp images are displayed at full scale and in roughly
their correct position on the focal plane while using space efficiently.

This code implements an algorithm suggested by Jim Gunn, with a few refinements of my own.

History:
2009-07-14 ROwen    Initial work.
2009-10-29 ROwen    Modified for guider v1_0_10 preliminary.
2009-10-30 ROwen    Modified to test whether fits images have plate data; raise new exceptions if not.
2009-11-02 ROwen    Removed code to set 0-valued pixels of postage stamps images to background
                    (now that the guider does this).
2009-11-04 ROwen    Added margin argument to AssembleImage (to leave room for annotations).
                    Bug fix: mis-handled guide images with no postage stamps.
2009-11-05 ROwen    PostageStamp.setDecimatedImagePos now keeps the stamp in bounds of the larger image
                    and also verifies that the requested position is finite.
                    AssembleImage.__call__ now checks that removeOverlap has a finite quality;
                    this catches a failure when multiple guide probes have the same plate position.
                    Bug fix: was requiring the # of postage stamps = # of data entries but that is too picky.
2010-02-19 ROwen    Fix ticket #613: background levels are wrong. This was caused by ignoring masked pixels
                    when computing the background. The old guider did not set mask bits, but the new one does,
                    and so many pixels were masked that my crude backround computation gave too large a value.
                    Fixed by using the guider-supplied image background (IMGBACK) if available,
                    else use the median of the entire image (ignoring the mask).
2010-06-28 ROwen    Removed debug statement that forced computation of background (thanks to pychecker).
                    Removed a global variable and a few statements that had no effect (thanks to pychecker).
"""
import itertools
import math
import numpy
import sys

PlateDiameterMM = 0.06053 * 3600 * 3 # 60.53 arcsec/mm, 3 degree FOV

class AIException(Exception):
    """Base class for exceptions thrown by AssembleImage.
    """
    pass

class NoPlateInfo(AIException):
    """Exception thrown by AssembleImage if the image has no plate information.
    """
    pass
    
class PlateInfoWrongVersion(AIException):
    """Exception thrown by AssembleImage if the image has an unparseable version of plate info.
    """
    pass

class PlateInfoInvalid(AIException):
    """Plate information is invalid and cannot be parsed
    """
    pass
    
def asArr(seq, shape=(2,), dtype=float):
    retArr = numpy.array(seq, dtype=dtype)
    if retArr.shape != tuple(shape):
        raise ValueError("Input data shape = %s != desired shape %s" % (retArr.shape, shape))
    return retArr

class PlateInfo(object):
    """An object containing SDSS guide probe data including a plate image
    """
    def __init__(self, plateImageArr, plateMaskArr, stampList):
        self.plateImageArr = plateImageArr
        self.plateMaskArr = plateMaskArr
        self.stampList = stampList

class PostageStamp(object):
    """Information about a postage stamp
    
    For now allow much of the info to be None, but once the names are nailed down
    for the FITS file then require all of these that my code uses
    (and perhaps ditch the rest).
    """
    Separation = 2  # separation between postage stamps, in binned pixels
    def __init__(self,
        image,
        mask,
        gpNumber,
        gpExists = True,
        gpEnabled = True,
        gpPlatePosMM = (numpy.nan, numpy.nan),
        gpCtr = (numpy.nan, numpy.nan),
        gpRadius = numpy.nan,
        gpFocusOffset = numpy.nan,
        starCtr = (numpy.nan, numpy.nan),
        starRotation = numpy.nan,
        starXYErrArcsec = (numpy.nan, numpy.nan),
        starRADecErrArcSec = (numpy.nan, numpy.nan),
        fwhmArcSec = numpy.nan,
        posErr = numpy.nan,
    ):
        """Create a PostageStamp
        Inputs (all in binned pixels unless noted):
        - image: postage stamp image array
        - mask: postage stamp mask array
        - gpNumber: guide probe number
        - gpExists: guide probe exists
        - gpEnabled: guide probe enabled (forced False if gpExists is False)
        - gpPlatePosMM: x,y position of guide probe on plate (mm)
        - gpCtr: desired x,y center of probe
        - gpRadius: radius of guide probe active area; binned pixels
        - gpFocusOffset: focus offset of guide probe (um, direction unknown)
        - starCtr: measured star x,y center
        - starRotation: rotation of star on sky (deg)
        - starXYErrArcsec: position error of guide star on image (arcsec);
            warning: the value in the image table is in mm; be sure to convert it
        - starRADecErrArcSec: position error of guide star on image in RA, Dec on sky arcsec
            warning: the value in the image table is in mm; be sure to convert it
        - fwhmArcSec: FWHM of star (arcsec)
        - posErr: ???a scalar of some kind; centroid uncertainty? (???)
        """
        self.image = numpy.array(image)
        self.mask = numpy.array(mask)
        self.gpNumber = int(gpNumber)
        self.gpExists = bool(gpExists)
        self.gpEnabled = bool(gpEnabled) and self.gpExists # force false if probe does not exist
        self.gpPlatePosMM = asArr(gpPlatePosMM)
        self.gpCtr = asArr(gpCtr)
        self.gpRadius = float(gpRadius)
        self.gpFocusOffset = float(gpFocusOffset)
        self.starCtr = asArr(starCtr)
        self.starRotation = float(starRotation)
        self.starXYErrArcsec = asArr(starXYErrArcsec)
        self.starRADecErrArcSec = asArr(starRADecErrArcSec)
        self.fwhmArcSec = float(fwhmArcSec)
        self.posErr = float(posErr)
        self.decImStartPos = None
        self.decImCtrPos = None
    
    def setDecimatedImagePos(self, ctrPos, mainImageShape):
        """Set position of center stamp on decimated image.
        
        Inputs:
        - ctrPos: desired position of center of postage stamp on decimated image (float x,y)
        - mainImageShape: the position is adjusted as required to keep the probe entirely on the main image
        """
        ctrPos = numpy.array(ctrPos, dtype=float)
        if numpy.any(numpy.logical_not(numpy.isfinite(ctrPos))):
            raise RuntimeError("ctrPos %s is not finite" % (ctrPos,))
        imageShape = numpy.array(self.image.shape)
        adjustment = (0, 0)
        self.decImStartPos = numpy.round(ctrPos - (imageShape / 2.0)).astype(int)
        self.decImEndPos = self.decImStartPos + imageShape
        self.decImCtrPos = (self.decImStartPos + self.decImEndPos) / 2.0
        minStartPos = numpy.zeros([2], dtype=int)
        maxEndPos = mainImageShape
        leftMargin = self.decImStartPos - minStartPos
        rightMargin = maxEndPos - self.decImEndPos
        adjustment = numpy.where(leftMargin < 0, -leftMargin,
            numpy.where(rightMargin < 0, rightMargin, (0, 0)))
#        print "ctrPos=%s, adjustment=%s" % (ctrPos, adjustment)
        if numpy.any(adjustment != (0, 0)):
            if numpy.any(imageShape > mainImageShape):
                raise RuntimeError("mainImageShape %s < %s stamp image shape" % (mainImageShape, imageShape))
            self.decImStartPos += adjustment
            self.decImEndPos += adjustment
            self.decImCtrPos += adjustment
#             print "ctrPos=%s; self.image.shape=%s; mainImageShape=%s" % \
#                 (ctrPos, self.image.shape, mainImageShape)
#             print "self.decImCtrPos=%s; self.decImStartPos=%s; self.decImEndPos=%s" % \
#                 (self.decImCtrPos, self.decImStartPos, self.decImEndPos)

    def getDecimatedImageRegion(self):
        """Return region of this stamp on the decimated image.
        The indices are swapped because that's now numpy does it.
        """
        return tuple(slice(self.decImStartPos[i], self.decImEndPos[i]) for i in (1, 0))
    
    def getRadius(self):
        """Return radius of this region
        """
        return (math.sqrt(self.image.shape[0]**2 + self.image.shape[1]**2) + self.Separation) / 2.0


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
    if stampSize == 0:
        return []
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
    def __init__(self, relSize=1.0, margin=20):
        """Create a new AssembleImage
        
        Inputs:
        - relSize: size of assembled image (along x or y) / size of original image
        - margin: number of pixels of margin around each edge
        """
        self.relSize = float(relSize)
        self.margin = int(margin)

    def __call__(self, guideImage):
        """Assemble an image array by arranging postage stamps from a guider FITS image
        
        Inputs:
        - guideImage: a guider image (pyfits image):
        
        Returns a PlateInfo object
        
        Note: the contents of the images and masks are not interpreted by this routine;
        the data is simply rearranged into a new output image and mask.
        
        Written for image format: SDSSFmt = gproc 1 0, but will try to deal with higher versions.
        
        Raise class NoPlateInfo if the image has no plate information
        Raise PlateInfoWrongVersion if the image has an unparseable version of plate info
        """
        # check version info
        try:
            sdssFmtStr = guideImage[0].header["SDSSFMT"]
        except Exception:
            raise NoPlateInfo("Could not find SDSSFMT header entry")
        try:
            formatName, versMajStr, versMinStr = sdssFmtStr.split()
            formatMajorVers = int(versMajStr)
            formatMinorVers = int(versMinStr)
        except Exception:
            raise NoPlateInfo("Could not parse SDSSFMT = %s" % (sdssFmtStr,))
        if formatName.lower() != "gproc":
            raise NoPlateInfo("SDSSFMT %s != gproc" % (formatName.lower(),))
        # test SDSSFMT version here, if necessary
        
        try:
            plateScale = float(guideImage[0].header["PLATSCAL"]) # plate scale in mm/deg
            plateArcSecPerMM = 3600.0 / plateScale # plate scale in arcsec/mm
        except Exception:
            raise PlateInfoInvalid("Could not find or parse PLATSCAL header entry")
        
        inImageSize = numpy.array(guideImage[0].data.shape, dtype=int)
        imageSize = numpy.array(inImageSize * self.relSize, dtype=int)
        dataTable = guideImage[6].data

        try:
            background = guideImage[0].header["IMGBACK"]
        except Exception:
            sys.stderr.write("AssembleImage: IMGBACK header missing; estimating background locally\n")
            background = numpy.median(guideImage[0].data)

        smallStampImage = guideImage[2].data
        smallStampImage -= background
        largeStampImage = guideImage[4].data
        largeStampImage -= background
        
        smallStampImageList = decimateStrip(smallStampImage)
        smallStampMaskList = decimateStrip(guideImage[3].data)
        if len(smallStampImageList) != len(smallStampMaskList):
            raise PlateInfoInvalid("%s small image stamps != %s small image masks" % (len(smallStampImageList), len(smallStampMaskList)))
        numSmallStamps = len(smallStampImageList)

        largeStampImageList = decimateStrip(largeStampImage)
        largeStampMaskList = decimateStrip(guideImage[5].data)
        if len(largeStampImageList) != len(largeStampMaskList):
            raise PlateInfoInvalid("%s large image stamps != %s large image masks" % (len(largeStampImageList), len(largeStampMaskList)))
        numLargeStamps = len(largeStampImageList)
        numStamps = numSmallStamps + numLargeStamps
        
        if numStamps == 0:
            raise NoPlateInfo("No postage stamps")
        
        smallStampSize = smallStampImageList[0].shape
        bgPixPerMM = (imageSize - smallStampSize - (2 * self.margin)) / PlateDiameterMM
        minPosMM = -imageSize / (2.0 * bgPixPerMM)

        stampList = []
        for ind, dataEntry in enumerate(dataTable):
            stampSizeIndex = dataEntry["stampSize"]
            stampIndex = dataEntry["stampIdx"]
            if (stampSizeIndex < 0) or (stampIndex < 0):
                continue
            if stampSizeIndex == 1:
                if stampIndex > numSmallStamps:
                    raise PlateInfoInvalid("stampSize=%s and stampIdx=%s but there are only %s small stamps" % \
                        (stampSizeIndex, stampIndex, numSmallStamps))
                image = smallStampImageList[stampIndex]
                mask  = smallStampMaskList[stampIndex]
            elif stampSizeIndex == 2:
                if stampIndex > numLargeStamps:
                    raise PlateInfoInvalid("stampSize=%s and stampIdx=%s but there are only %s large stamps" % \
                        (stampSizeIndex, stampIndex, numLargeStamps))
                image = largeStampImageList[stampIndex]
                mask  = largeStampMaskList[stampIndex]
            else:
                continue
            if not dataEntry["exists"]:
                # do not show postage stamp images for nonexistent (e.g. broken) probes
                continue
            stampList.append(PostageStamp(
                image = image,
                mask = mask,
                gpNumber = ind + 1,
                gpExists = dataEntry["exists"],
                gpEnabled = dataEntry["enabled"],
                gpPlatePosMM = (dataEntry["xFocal"], dataEntry["yFocal"]),
                gpCtr = (dataEntry["xCenter"], dataEntry["yCenter"]),
                gpRadius = dataEntry["radius"],
                gpFocusOffset = dataEntry["focusOffset"],
                starRotation = dataEntry["rotStar2Sky"],
                starCtr = (dataEntry["xstar"], dataEntry["ystar"]),
                starXYErrArcsec = numpy.array((dataEntry["dx"], dataEntry["dy"])) * plateArcSecPerMM,
                starRADecErrArcSec = numpy.array((dataEntry["dRA"], dataEntry["dDec"])) * plateArcSecPerMM,
                fwhmArcSec = (dataEntry["fwhm"]),
                posErr = dataEntry["poserr"],
            ))
        radArr = numpy.array([stamp.getRadius() for stamp in stampList])
        desPosArrMM = numpy.array([stamp.gpPlatePosMM for stamp in stampList])
        desPosArr = (desPosArrMM - minPosMM) * bgPixPerMM

        actPosArr, quality, nIter = self.removeOverlap(desPosArr, radArr, imageSize)
        if not numpy.isfinite(quality):
            raise PlateInfoInvalid("removeOverlap failed: guide probe plate positions probably invalid")

        plateImageArr = numpy.zeros(imageSize, dtype=float)
        plateMaskArr  = numpy.zeros(imageSize, dtype=numpy.uint8)
        for stamp, actPos in itertools.izip(stampList, actPosArr):
            stamp.setDecimatedImagePos(actPos, plateImageArr.shape)
            mainRegion = stamp.getDecimatedImageRegion()
            plateImageArr[mainRegion] = stamp.image
            plateMaskArr [mainRegion] = stamp.mask
        return PlateInfo(plateImageArr, plateMaskArr, stampList)

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
