#!/usr/bin/env python
"""Guide test code that crudely substitutes for the hub

To do:
- make the whole thing an object

History:
2005-01-31 ROwen
2005-02-08 ROwen    Updated for PyGuide 1.2.
2005-02-22 ROwen    Fixed centroid output (had not been updated to match new star format).
2005-03-25 ROwen    Updated for new keywords. Stopped using float("nan").
2005-03-28 ROwen    Updated again for improved files and star keywords.
2005-04-11 ROwen    Modified for GCamModel->GuideModel.
                    Adjusted for 2005-04-01 findStars.
2005-04-12 ROwen    Made safe to import even when not being used.
2005-04-18 ROwen    Improved test code to increment cmID and offered a separate
                    optional init function before run (renamed from start).
2005-05-20 ROwen    Modified for PyGuide 1.3.
                    Stopped outputting obsolete centroidPyGuideConfig keyword.
                    Added _Verbosity to set verbosity of PyGuide calls.
                    Modified to send thesh to PyGuide.centroid
                    Modified to output xxDefxx keywords at startup.
2005-05-25 ROwen    Added the requirement to specify actor.
2005-06-13 ROwen    Added runDownload for a more realistic way to get lots of images.
2005-06-16 ROwen    Modified to import (with warnings) if PyGuide missing.
2005-06-17 ROwen    Bug fix: init failed if no PyGuide.
2005-06-22 ROwen    Changed init argument doFTP to isLocal.
                    Modified to set GuideWdg._LocalMode and _HistLength.
2005-06-24 ROwen    Added nFiles argument to runLocalFiles.
2005-07-08 ROwen    Modified for http download: changed imageRoot to httpRoot.
2005-07-14 ROwen    Removed isLocal mode.
2006-04-13 ROwen    runDownload: added imPrefix and removed maskNum argument.
                    nextDownload: removed maskNum.
2006-05-24 ROwen    setParams: added mode, removed count.
2007-04-24 ROwen    Removed unused import of numarray.
2009-03-31 ROwen    Modified to use twisted timers.
2009-07-15 ROwen    Modified to work with sdss code.
"""
import gc
import os
import re
import resource
import TUI.TUIModel
import TUI.TUIMenu.LogWindow
import TUI.TUIMenu.DownloadsWindow
import GuideModel
import GuideWdg
import TUI.Base.TestDispatcher
import RO.SeqUtil

g_actor = None
g_ccdInfo = None

# other constants you may wish to set
g_expTime = 15.0
g_thresh = 3.0
g_radMult = 1.0
g_Mode = "field"

# leave alone
_CmdID = 0

# verbosity for PyGuide calls
_Verbosity = 1

def dumpGarbage():
    print "\nCOLLECTING GARBAGE:"
    gc.collect()
    print "GARBAGE OBJECTS REMAINING:"
    for x in gc.garbage:
        s = str(x)
        if len(s) > 80: s = s[:77] + "..."
        print type(x), "\n ", s

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("gmech")
tuiModel = testDispatcher.tuiModel

def dispatch(replies, **kwargs):
    """Dispatch the reply string.
    
    Inputs:
    - replies: a string or collection of strings to dispatch
    - **kwargs: keyword arguments for TUI.Base.TestDispatcher.TestDispatcher.dispatch,
        including actor and msgType
    """
    replyList = RO.SeqUtil.asCollection(replies)
    tuiModel.reactor.callLater(0.2, testDispatcher.dispatch, replies, **kwargs)

def setParams(expTime=None, thresh=None, radMult=None, mode=None):
#   print "setParams(expTime=%r, thresh=%r, radMult=%r, mode=%r)" % (expTime, thresh, radMult, mode)
    global g_expTime, g_thresh, g_radMult, g_mode
    
    strList = []

    if expTime != None:
        g_expTime = float(expTime)
        strList.append("time=%.1f" % g_expTime)
    if thresh != None:
        g_thresh = float(thresh)
        strList.append("fsActThresh=%.1f" % g_thresh)
    if radMult != None:
        g_radMult = float(radMult)
        strList.append("fsActRadMult=%.1f" % g_radMult)
    if mode != None:
        g_mode = mode
        strList.append("guideMode=%s" % g_mode)
    if strList:
        dispatch(": %s" % "; ".join(strList), msgCode=":")

def showFile(fileName):
    incrCmdID()
    dispatch("imgFile=%s" % (fileName,), msgCode=":")
    decrCmdID()
    findStars(fileName)

def decrCmdID():
    global _CmdID
    _CmdID -= 1
    
def incrCmdID():
    global _CmdID
    _CmdID += 1

def init(actor, bias=0, readNoise=21, ccdGain=1.6, histLen=5):
    global tuiModel, g_actor, g_ccdInfo
    
    GuideWdg._HistLength = histLen
    
    tuiModel = TUI.TUIModel.Model(True)
    g_actor = actor
    
    TUI.TUIMenu.DownloadsWindow._MaxLines = 5
    
    # create log window and ftp log window
    TUI.TUIMenu.LogWindow.addWindow(tuiModel.tlSet) 
    TUI.TUIMenu.DownloadsWindow.addWindow(tuiModel.tlSet, visible=True)
    
    # set image root
    dispatch('httpRoot="hub35m.apo.nmsu.edu", "/images/"', actor="hub")

def nextDownload(basePath, imPrefix, imNum, numImages=None, waitTime=2.0):
    """Download a series of guide images from APO.
    Assumes the images are sequential.
    
    Inputs:
    - basePath: path to images relative to export/images/
        with no leading "/" and one trailing "/"
        e.g. "keep/gcam/UT050422/"
    - imPrefix: portion of name before the number, e.g.
        "g" for "keep/gcam/UT050422/g0101.fits"
    - numImages: number of images to download
        None of no limit
        warning: if not None then at least one image is always downloaded
    - waitTime: interval (sec) before downloading next image
    """
    global tuiModel

    imName = "%s%04d.fits" % (imPrefix, imNum,)
    dispatch('files=g, 1, "%s", "%s", ""' % (basePath, imName))
    #if (numImages - 1) % 20 == 0:
        #print "Image %s; resource usage: %s" % (imNum, resource.getrusage(resource.RUSAGE_SELF))
    if numImages != None:
        numImages -= 1
        if numImages <= 0:
            #dumpGarbage()
            return
    tuiModel.reactor.callLater(waitTime, nextDownload, basePath, imPrefix, imNum+1, numImages, waitTime)
    
def runDownload(basePath, imPrefix, startNum, numImages=None, waitTime=2.0):
    """Download a series of guide images from APO.
    Assumes the images are sequential.
    
    WARNING: specify doFTP=True when you call init
    
    Inputs:
    - basePath: path to images relative to export/images/
        with no leading "/" and one trailing "/"
        e.g. "keep/gcam/UT050422/"
    - imPrefix: name portion of image name that appears before the number
        (e.g. "proc-d" for dcam images)
    - startNum: number of first image to download
    - numImages: number of images to download
        None if no limit
        warning: if not None then at least one image is always downloaded
    - waitTime: interval (sec) before downloading next image
    """
    #print "Image %s; resource usage: %s" % (startNum, resource.getrusage(resource.RUSAGE_SELF))

    nextDownload(
        basePath = basePath,
        imPrefix = imPrefix,
        imNum = startNum,
        numImages = numImages,
        waitTime = waitTime,
    )

