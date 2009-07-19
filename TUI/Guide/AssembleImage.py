#!/usr/bin/env python
"""Assemble a set of postage stamps images of guide fiber bundles into one image

The postage stamp images are displayed at full scale and in roughly
their correct position on the focal plane while using space efficiently.

This code implements an algorithm suggested by Jim Gunn, with a few refinements of my own.

History:
2009-07-14 ROwen    Initial work. Probably riddled with bugs, and no test code.
                    WARNING: there may be additional places where the X and Y axes must be swapped
                    to get the desired FITS display.
"""
import numpy
import time

PlateDiameterMM = 0.06053 * 3600 * 3 # 60.53 arcsec/mm, 3 degree FOV

def asArr(seq, shape=(2,), dtype=float):
    retArr = numpy.array(seq, dtype=dtype)
    if retArr.shape != tuple(shape):
        raise ValueError("Input data shape = %s != desired shape %s" % (retArr.shape, shape))
    return retArr

class StampInfo(object):
    """Information about a postage stamp
    """
    def __init__(self, shape, ffCtr, desCtr, actCtr, rot, platePosMM, raDec, bitmask):
        """Create a StampInfo
        
        Note: more info is wanted, including:
        - what are the zero points of the various Ctr positions
        - are the Ctr positions rotated?
        
        Inputs:
        - shape: x,y shape of postage stamp (pixels)
        - ffCtr: x,y expected center of flat field (pixels)
        - desCtr: x,y expected star centroid (pixels)
        - actCtr: x,y measured star centroid (pixels)
        - rot: rotation of guide probe (details???)
        - platePosMM: x,y position of guide probe on plate (mm)
        - raDec: RA, Dec of guide star (deg)
        - bitmask: a bit mask describing the fiber:
            - 0: isBig
            - 1: isBroken
            - 2-3: type; one of:
                - 0: not in use
                - 1: guide star
                - 2: sky
                - ...any other types?
        """
        self.shape = asArr(shape, dtype=int)
        self.ffCtr = asArr(ffCtr)
        self.desCtr = asArr(desCtr)
        self.actCtr = asArr(actCtr)
        self.rot = float(rot)
        self.platePosMM = asArr(platePosMM)
        self.raDec = asArr(raDec)
        self.bitmask = int(bitmask)

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
    stampImageList = [imArr[(ind * stampSize):(((ind + 1) * stampSize) - 1), :] for ind in range(numIm)]
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
        
        guideImage format (from Craig Loomis, except HDU7 is a preliminary guess):
        - HDU0: full frame corrected image, with some FITS cards.
        - HDU1: full frame mask image; bit 0=sat, 1=bad, 2=masked
        - HDU2: rotated and centered postage stamps for small fibers
        - HDU3: rotated and centered postage stamps for small fiber masks
        - HDU4: rotated and centered postage stamps for large fibers
        - HDU5: rotated and centered postage stamps for large fiber masks
        - HDU6: binary table containing image-level quantities:
            - xseed, yseed  - expected position of fiber flats
            - rot           - known per-fiber rotation
            - xcen, ycen    - measured/calculated fiber center (what the postage stamps center on).
            - xoffset, yoffset - measured object center.
        - HDU7: binary table containing plate and sky-related quantities:
            - xposmm, yposmm: x and y position on plate, in mm
            - ra, dec: RA, Dec of guide star (if relevant; NaN if not)
            - bitmask: a bit mask describing the fiber:
                - 0: isBig
                - 1: isBroken
                - 2-3: type; one of:
                    - 0: not in use
                    - 1: guide star
                    - 2: sky
                    - ...any other types?
        """
        inImageSize = numpy.array(guideImage[0].data.shape, dtype=int)
        imageSize = numpy.array(inImageSize * self.relSize, dtype=int)
        
        smallStampImageList = decimateStrip(guideImage[2].data)
        smallStampMaskList = decimateStrip(guideImage[3].data)
        smallStampSize = smallStampImageList[0].shape
        numSmallStamps = len(smallStampImageList)

        largeStampImageList = decimateStrip(guideImage[4].data)
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

        imageTable = guideImage[6].data
        plateTable = guideImage[7].data
        print "len(imageTable)=", len(imageTable)
        print "len(plateTable)=", len(plateTable)
        print "len(shapeArr)=", len(shapeArr)
        print "num small images=", len(smallStampImageList)
        print "num large images=", len(largeStampImageList)
        if len(imageTable) != len(plateTable):
            raise ValueError("image table len = %s != %s = plate table length" % (len(imageTable), len(plateTable)))
        if len(imageTable) != len(stampImageList):
            raise ValueError("image table len = %s != %s = number of postage stamps" % (len(imageTable), len(stampImageList)))
        stampInfoList = []
        for ind in range(len(imageTable)):
            imageEntry = imageTable[ind]
            plateEntry = plateTable[ind]
            stampInfoList.append(StampInfo(
                shape = shapeArr[ind],
                ffCtr = (imageEntry["xseed"], imageEntry["yseed"]),
                desCtr = (imageEntry["xcen"], imageEntry["ycen"]),
                actCtr = (imageEntry["xoffset"], imageEntry["yoffset"]),
                rot = imageEntry["fiberRot"],
                platePosMM = (plateEntry["xplate"], plateEntry["yplate"]),
                raDec = (plateEntry["ra"], plateEntry["dec"]),
                bitmask = plateEntry["bitmask"],
            ))
        desPosArrMM = numpy.array([stampInfo.platePosMM for stampInfo in stampInfoList])
        desPosArr = (desPosArrMM - minPosMM) * bgPixPerMM

        actPosArr, quality, nIter = self.removeOverlap(desPosArr, radArr, imageSize)
        cornerPosArr = numpy.round(actPosArr - (shapeArr / 2.0)).astype(int)

        retImageArr = numpy.zeros(outSize, dtype=float)
        retImageArr[:,:] = numpy.nan
        retMaskArr  = numpy.zeros(outSize, dtype=numpy.uint8)
        for ind, stampImageArr in enumerate(stampImageList):
            startPos = cornerPosArr[ind]
            endPos = startPos + stampImageArr.shape
            retImageArr[startPos[1]:endPos[1], startPos[0]:endPos[0]] = stampImageArr
            retMaskArr [startPos[1]:endPos[1], startPos[0]:endPos[0]] = stampMaskArr
        return (retImageArr, retMaskArr, stampinfoList)

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
    im = pyfits.open("sample-withplate-gim.fits")
    results = imAssembler(im)
    print results
