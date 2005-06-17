#!/usr/local/bin/python
"""Guide test code that crudely substitutes for the hub

To do:
- make the whole thing and object

History:
2005-01-31 ROwen
2005-02-08 ROwen	Updated for PyGuide 1.2.
2005-02-22 ROwen	Fixed centroid output (had not been updated to match new star format).
2005-03-25 ROwen	Updated for new keywords. Stopped using float("nan").
2005-03-28 ROwen	Updated again for improved files and star keywords.
2005-04-11 ROwen	Modified for GCamModel->GuideModel.
					Adjusted for 2005-04-01 findStars.
2005-04-12 ROwen	Made safe to import even when not being used.
2005-04-18 ROwen	Improved test code to increment cmID and offered a separate
					optional init function before run (renamed from start).
2005-05-20 ROwen	Modified for PyGuide 1.3.
					Stopped outputting obsolete centroidPyGuideConfig keyword.
					Added _Verbosity to set verbosity of PyGuide calls.
					Modified to send thesh to PyGuide.centroid
					Modified to output xxDefxx keywords at startup.
2005-05-25 ROwen	Added the requirement to specify actor.
2005-06-13 ROwen	Added runDownload for a more realistic way to get lots of images.
2005-06-16 ROwen	Modified to import (with warnings) if PyGuide missing.
2005-06-17 ROwen	Bug fix: init failed if no PyGuide.
"""
import gc
import os
import re
import resource
import numarray as num
import pyfits
try:
	import PyGuide
except ImportError:
	print "Warning: PyGuide not installed; only non-local tests will work"
	PyGuide = None
import TUI.TUIModel
import TUI.TUIMenu.LogWindow
import TUI.TUIMenu.FTPLogWindow

import GuideModel

g_actor = None
g_ccdInfo = None

# other constants you may wish to set
mask = None
g_expTime = 15.0
g_thresh = 3.0
g_radMult = 1.0

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
	
def centroid(fileName, on, rad=None, thresh=None, isNew=False):
	#print "centroid(filenName=%r; on=%s; rad=%d; isNew=%s)" % (fileName, on, rad, isNew)
	global g_thresh
	if not thresh:
		thresh = g_thresh

	im = pyfits.open(fileName)
	incrCmdID()
	
	ctrData = PyGuide.centroid(
		data = im[0].data,
		mask = mask,
		xyGuess = on,
		rad = rad,
		ccdInfo = g_ccdInfo,
		thresh = thresh,
		verbosity = _Verbosity,
	)
	if not ctrData.isOK:
		dispatch("f text=\"centroid failed: %s\"" % ctrData.msgStr)
		return
	
	shapeData = PyGuide.starShape(
			data = im[0].data,
			mask = mask,
			xyCtr = ctrData.xyCtr,
			rad = ctrData.rad,
			verbosity = _Verbosity,
		)
	if not shapeData.isOK:
		print "GuideTest: starShape failed with error:", shapeData.msgStr

	dispatch(
		"i files=c, %d, %r, %r, %r" % (isNew, "", fileName, ""),
	)
		
	dispatch(
		"i star=c, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, NaN, %.2f, %d, %.2f, %.2f" % \
			(1,
			ctrData.xyCtr[0], ctrData.xyCtr[1], ctrData.xyErr[0], ctrData.xyErr[1],
			ctrData.rad, ctrData.asymm,
			shapeData.fwhm, shapeData.fwhm, shapeData.chiSq, ctrData.counts,
			shapeData.bkgnd, shapeData.ampl),
	)

def dispatch(replyStr, actor=None):
	"""Dispatch the reply string.
	The string should start from the message type character
	(thus program ID, actor and command ID are added).
	"""
	global tuiModel, _CmdID, g_actor
	cmdr = tuiModel.getCmdr()
	actor = actor or g_actor
	
	msgStr = "%s %d %s %s" % (cmdr, _CmdID, actor, replyStr)
#	print "dispatching %r" % msgStr

	tuiModel.root.after(20, tuiModel.dispatcher.doRead, None, msgStr)

def findStars(fileName, count=None, thresh=None, radMult=None, isNew=False):
	"""Search for stars
	"""
	global g_thresh
	if thresh == None:
		thresh = g_thresh
	if radMult == None:
		radMult = g_radMult

	im = pyfits.open(fileName)
	incrCmdID()
	
	ctrDataList, imStats = PyGuide.findStars(
		data = im[0].data,
		mask = mask,
		ccdInfo = g_ccdInfo,
		thresh = thresh,
		radMult = radMult,
		verbosity = _Verbosity,
	)

	if count:
		ctrDataList = ctrDataList[0:count]
	
	dispatch("i files=f, %d, %r, %r, %r" % (isNew, "", fileName, ""))

	setParams(thresh=thresh)

# clean this up so the default value is printed if set to None
# (but nothing is printed if both values are None)
#	if (count != None) or (thresh != None):
#		dispatch(
#			"i findStarsPyGuideConfig=%d, %.2f" % (count, thresh),
#		)

	ind = 1
	for ctrData in ctrDataList:
		shapeData = PyGuide.starShape(
			data = im[0].data,
			mask = mask,
			xyCtr = ctrData.xyCtr,
			rad = ctrData.rad,
			verbosity = _Verbosity,
		)
		if not shapeData.isOK:
			print "GuideTest: starShape failed with error:", shapeData.msgStr
		
		dispatch(
			"i star=f, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, NaN, %.2f, %d, %.2f, %.2f" % \
				(ind,
				ctrData.xyCtr[0], ctrData.xyCtr[1], ctrData.xyErr[0], ctrData.xyErr[1], ctrData.rad, ctrData.asymm,
				shapeData.fwhm, shapeData.fwhm, shapeData.chiSq, ctrData.counts, shapeData.bkgnd, shapeData.ampl),
		)
		ind += 1
	dispatch(":")

def setParams(expTime=None, thresh=None, count=None, radMult=None):
#	print "setParams(expTime=%r, thresh=%r, radMult=%r, count=%r)" % (expTime, thresh, radMult, count)
	global g_expTime, g_thresh, g_radMult, g_count
	
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
	if strList:
		dispatch(
			": %s" % "; ".join(strList),
		)

def showFile(fileName):
	incrCmdID()
	dispatch(
		": imgFile=%s" % (fileName,),
	)
	decrCmdID()
	findStars(fileName)

def decrCmdID():
	global _CmdID
	_CmdID -= 1
	
def incrCmdID():
	global _CmdID
	_CmdID += 1

def init(actor, bias=0, readNoise=21, ccdGain=1.6, doFTP=False):
	global tuiModel, g_actor, g_ccdInfo
	
	tuiModel = TUI.TUIModel.getModel(True)
	g_actor = actor
	if PyGuide:
		g_ccdInfo = PyGuide.CCDInfo(
			bias = bias,
			readNoise = readNoise,
			ccdGain = ccdGain,
		)
	
	if doFTP:
		TUI.TUIMenu.FTPLogWindow._MaxLines = 5
		
		# create log window and ftp log window
		TUI.TUIMenu.LogWindow.addWindow(tuiModel.tlSet)	
		TUI.TUIMenu.FTPLogWindow.addWindow(tuiModel.tlSet)
		
		# set image root
		dispatch('i imageRoot="tycho.apo.nmsu.edu", "/export/images/"')

def nextDownload(basePath, imPrefix, imNum, numImages=None, maskName=None, waitMs=2000):
	"""Download a series of guide images from APO.
	Assumes the images are sequential
	and that all images use the same mask.
	
	Inputs:
	- basePath: path to images relative to export/images/
		with no leading "/" and one trailing "/"
		e.g. "keep/gcam/UT050422/"
	- imPrefix: portion of name before the number, e.g.
		"g" for "keep/gcam/UT050422/g0101.fits"
	- numImages: number of images to download
		None of no limit
		warning: if not None then at least one image is always downloaded
	- maskName: mask file name; "" if no mask
	- waitMs: interval in ms before downloading next image
	"""
	global tuiModel

	imName = "%s%04d.fits" % (imPrefix, imNum,)
	dispatch('i files=g, 1, "%s", "%s", "%s"' % (basePath, imName, maskName))
	#if (numImages - 1) % 20 == 0:
		#print "Image %s; resource usage: %s" % (imNum, resource.getrusage(resource.RUSAGE_SELF))
	if numImages != None:
		numImages -= 1
		if numImages <= 0:
			#dumpGarbage()
			return
	tuiModel.root.after(waitMs, nextDownload, basePath, imPrefix, imNum+1, numImages, maskName, waitMs)
	
def runDownload(basePath, startNum, numImages=None, maskNum=None, waitMs=2000):
	"""Download a series of guide images from APO.
	Assumes the images are sequential
	and that all images use the same mask.
	
	WARNING: specify doFTP=True when you call init
	
	Inputs:
	- basePath: path to images relative to export/images/
		with no leading "/" and one trailing "/"
		e.g. "keep/gcam/UT050422/"
	- numImages: number of images to download
		None of no limit
		warning: if not None then at least one image is always downloaded
	- maskNum: mask file number to use for ALL images; None if no mask
	- waitMs: interval in ms before downloading next image
	"""
	#print "Image %s; resource usage: %s" % (startNum, resource.getrusage(resource.RUSAGE_SELF))

	m = re.search("/([a-z])cam/", basePath)
	if m == None:
		raise RuntimeError("cannot parse basePath=%r" % basePath)
	imPrefix = m.groups()[0]

	if maskNum != None:
		maskName = "mask%04d.fits" % (maskNum,)
	else:
		maskName = ""
	
	nextDownload(
		basePath = basePath,
		imPrefix = imPrefix,
		imNum = startNum,
		numImages = numImages,
		maskName = maskName,
		waitMs = waitMs,
	)

def runLocalDemo():
	"""Run full demo; loading files, etc."""
	global tuiModel, g_thresh, g_radMult

	dispatch(": guideState=off")

	currDir = os.path.dirname(__file__)

	# show defaults
	dispatch(": fsDefThresh=%s; fsDefRadMult=%s" % (g_thresh, g_radMult))
	
	dataList = (
		(True,  'g0121.fits'),
		(False, "i guideState=starting"),
		(True,  'g0122.fits'),
		(False, "w NoGuideStar"),
		(False, "i guideState=on"),
		(True,  'g0123.fits'),
		(False, "i StarQuality=0.5"),
		(False, "i guideState=stopping"),
		(False, "w NoGuideStar"), # should be ignored
		(False, "i StarQuality=0.5"), # should be ignored
		(False, "i guideState=off"),
	)
	dataIter = iter(dataList)
	
	def anime():
		try:
			isFile, dataStr = dataIter.next()
		except StopIteration:
			return
		if isFile:
			print "load %r" % (dataStr,)
			filePath = os.path.join(currDir, dataStr)
			findStars(filePath, isNew=True)
		else:
			dispatch(dataStr)
		tuiModel.root.after(1000, anime)

	tuiModel.root.after(1000, anime)

def runLocalFiles():
	"""Load local files"""
	global tuiModel, g_thresh, g_radMult

	dispatch(": guideState=off")

	currDir = os.path.dirname(__file__)

	# show defaults
	dispatch(": fsDefThresh=%s; fsDefRadMult=%s" % (g_thresh, g_radMult))
	
	fileNames = ('g0121.fits', 'g0122.fits', 'g0123.fits', 'g0124.fits', 'g0125.fits',)
	fni = iter(fileNames)
	
	def anime():
		try:
			fileName = fni.next()
		except StopIteration:
			return
		print "load %r" % (fileName,)
		filePath = os.path.join(currDir, fileName)
		findStars(filePath, isNew=True)
		tuiModel.root.after(1000, anime)

	tuiModel.root.after(1000, anime)
