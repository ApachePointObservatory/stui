#!/usr/bin/env python
"""GuideImage represents a guide image

History:
2006-08-03 ROwen    Separated ImObj out of GuideWdg.py into this file
                    and renamed to GuideImage.
2006-09-12 ROwen    Modified GuideImage.getFITSObj to parse the header
                    and set various useful attributes.
2007-01-16 ROwen    Added commented-out code to print a traceback if file read fails.
2007-01-30 ROwen    Was not caching FITS header info (despite code to do this).
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
2009-04-01 ROwen    Changed isDone() to isDone and didFail() to didFail.
2009-07-18 ROwen    Added preliminar support for the plate view; some details need refinement.
2009-09-11 ROwen    Removed defRadMult, defThresh and defGuideMode.
2009-09-14 ROwen    Disabled code to assemble a plate view;
                    only re-enable it when there is a bit of metadata
                    that tells me if the image format includes plate view metadata.
                    Handle errors if assembling a plate view fails.
2009-09-15 ROwen    Tweak traceback printing and disabling of plate view.
2009-10-29 ROwen    Added parsing of SDSSFMT header keyword.
                    Fixed bug using hubModel.httpRoot.
2009-10-30 ROwen    Moved test of whether fits images have plate data to AssembleImage.
                    Modified for TUI.HubModel->TUI.Models.HubModel.
"""
import os
import pyfits
import sys
import traceback
import RO.StringUtil
import TUI.Models.HubModel
import AssembleImage

_DebugMem = False # print a message when a file is deleted from disk?

SDSSFmtType = "gproc"
SDSSFmtMajorVersion = 1

class BasicImage(object):
    """Information about an image.
    
    Inputs:
    - localBaseDir  root image directory on local machine
    - imageName path to image relative, specifically:
                if isLocal False, then a URL relative to the download host
                if isLocal True, then a local path relative to localBaseDir
    - imageName unix path to image, relative to host root directory
    - guideModel    guide model for this actor
    - fetchCallFunc function to call when image info changes state
    - isLocal   set True if image is local or already downloaded
    """
    Ready = "Ready to download"
    Downloading = "Downloading"
    Downloaded = "Downloaded"
    FileReadFailed = "Cannot read file"
    DownloadFailed = "Download failed"
    Expired = "Expired; file deleted"
    ErrorStates = (FileReadFailed, DownloadFailed, Expired)
    DoneStates = (Downloaded,) + ErrorStates

    def __init__(self,
        localBaseDir,
        imageName,
        downloadWdg = None,
        fetchCallFunc = None,
        isLocal = False,
    ):
        #print "%s localBaseDir=%r, imageName=%s" % (self.__class__.__name__, localBaseDir, imageName)
        self.localBaseDir = localBaseDir
        self.imageName = imageName
        self.downloadWdg = downloadWdg
        self.hubModel = TUI.Models.HubModel.Model()
        self.errMsg = None
        self.fetchCallFunc = fetchCallFunc
        self.isLocal = isLocal
        if not self.isLocal:
            self.state = self.Ready
        else:
            self.state = self.Downloaded
        self.isInSequence = not isLocal
        
        # set local path
        # this split suffices to separate the components because image names are simple
        if isLocal:
            self._localPath = os.path.join(self.localBaseDir, imageName)
        else:
            pathComponents = self.imageName.split("/")
            self._localPath = os.path.join(self.localBaseDir, *pathComponents)
        #print "GuideImage localPath=%r" % (self._localPath,)
    
    @property
    def didFail(self):
        """Return False if download failed or image expired"""
        return self.state in self.ErrorStates
    
    def expire(self):
        """Delete the file from disk and set state to expired.
        """
        if self.isLocal:
            if _DebugMem:
                print "Would delete %r, but is local" % (self.imageName,)
            return
        if self.state == self.Downloaded:
            # don't use _setState because no callback wanted
            # and _setState ignored new states once done
            self.state = self.Expired
            if os.path.exists(self._localPath):
                if _DebugMem:
                    print "Deleting %r" % (self._localPath,)
                os.remove(self._localPath)
            elif _DebugMem:
                print "Would delete %r, but not found on disk" % (self.imageName,)
        elif _DebugMem:
            print "Would delete %r, but state = %r is not 'downloaded'" % (self.imageName, self.state,)

    def fetchFile(self):
        """Start downloading the file."""
        #print "%s fetchFile; isLocal=%s" % (self, self.isLocal)
        if self.isLocal:
            self._setState(self.Downloaded)
            return

        fromURL = self.hubModel.getFullURL(self.imageName)
        if fromURL == None:
            self._setState(
                self.DownloadFailed,
                "Cannot download images; hub httpRoot keyword not available",
            )
            return
        
        self._setState(self.Downloading)
        self.downloadWdg.getFile(
            fromURL = fromURL,
            toPath = self._localPath,
            isBinary = True,
            overwrite = True,
            createDir = True,
            doneFunc = self._fetchDoneFunc,
            dispStr = self.imageName,
        )
    
    def getFITSObj(self):
        """If the file is available, return a pyfits object, else return None.
        """
        if self.state == self.Downloaded:
            try:
                fitsIm = pyfits.open(self.localPath)
                if fitsIm:
                    return fitsIm
                
                self.state = self.FileReadFailed
                self.errMsg = "No image data found"
                return None
            except Exception, e:
                self.state = self.FileReadFailed
                self.errMsg = RO.StringUtil.strFromException(e)
#               sys.stderr.write("Could not read file %r:\n" % (self.localPath,))
#               traceback.print_exc(file=sys.stderr)
        return None
    
    @property
    def localPath(self):
        """Return the full local path to the image."""
        return self._localPath
    
    def getStateStr(self):
        """Return a string describing the current state."""
        if self.errMsg:
            return "%s: %s" % (self.state, self.errMsg)
        return self.state

    @property
    def isDone(self):
        """Return True if download finished (successfully or otherwise)"""
        return self.state in self.DoneStates

    def _fetchDoneFunc(self, httpGet):
        """Called when image download ends.
        """
        if httpGet.getState() == httpGet.Done:
            self._setState(self.Downloaded)
        else:
            self._setState(self.DownloadFailed, httpGet.getErrMsg())
            #print "%s download failed: %s" % (self, self.errMsg)
            return
    
    def _setState(self, state, errMsg=None):
        if self.isDone:
            return
    
        self.state = state
        if self.didFail:
            self.errMsg = errMsg
        
        if self.fetchCallFunc:
            self.fetchCallFunc(self)
        if self.isDone:
            self.fetchCallFunc = None
    
    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.imageName)


class GuideImage(BasicImage):
    """Add support for guide images, e.g. information about stars
    """
    def __init__(self,
        localBaseDir,
        imageName,
        downloadWdg = None,
        fetchCallFunc = None,
        isLocal = False,
    ):
        self.starDataDict = {} # dict of star type char: star keyword data
        self.defSelDataColor = None
        self.selDataColor = None
        self.guiderPredPos = None
        self.currGuideMode = None
        self.parsedFITSHeader = False
        self.binFac = None
        self.expTime = None

        self.plateViewAssembler = AssembleImage.AssembleImage(relSize=0.8)
        self.plateImageArr = None
        self.plateMaskArr = None
        self.plateInfoList = None

        BasicImage.__init__(self,
            localBaseDir = localBaseDir,
            imageName = imageName,
            downloadWdg = downloadWdg,
            fetchCallFunc = fetchCallFunc,
            isLocal = isLocal,
        )

    def getFITSObj(self):
        """Return the pyfits image object, or None if unavailable.
        
        Parse the FITS header, if not already done,
        and set the following attributes:
        - binFac: bin factor (a scalar; x = y)
        - expTime: exposure time (floating seconds)
        """
        fitsObj = BasicImage.getFITSObj(self)
        if fitsObj and not self.parsedFITSHeader:
            imHdr = fitsObj[0].header
            self.expTime = imHdr.get("EXPTIME")
            self.binFac = imHdr.get("BINX")
            self.parsedFITSHeader = True

            try:
                self.plateImageArr, self.plateMaskArr, self.plateInfoList = self.plateViewAssembler(fitsObj)
            except AssembleImage.NoPlateInfo:
                pass
            except AssembleImage.AIException, e:
                sys.stderr.write("Could not assemble plate view of %r: %s\n" % \
                    (self.localPath, RO.StringUtil.strFromException(e)))
            except Exception:
                sys.stderr.write("Could not assemble plate view of %r:\n" % (self.localPath,))
                traceback.print_exc(file=sys.stderr)

        return fitsObj
    
    @property
    def hasPlateView(self):
        return self.plateImageArr != None
