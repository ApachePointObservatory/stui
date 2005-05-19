#!/usr/local/bin/python
"""Guide test code that crudely substitutes for the hub

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
2005-05-19 ROwen	Modified for PyGuide 1.3.
"""
import os
import numarray as num
import pyfits
import PyGuide

import TUI.TUIModel
import GuideModel

# data for NA2 guider
actor = "ecam"
bias = 0 # 1780 is alleged, but our test images have a much lower signal!!!
readNoise = 21.391
ccdGain = 1.643 # e-/pixel

# other constants you may wish to set
mask = None
g_expTime = 15.0
g_thresh = 3.0

# leave alone
_CmdID = 0

def centroid(fileName, on, rad=None, isNew=False, thresh=None):
	#print "centroid(filenName=%r; on=%s; rad=%d; isNew=%s)" % (fileName, on, rad, isNew)
	global g_thresh
	if not thresh:
		thresh = g_thresh

	im = pyfits.open(fileName)
	incrCmdID()
	
	ccdInfo = PyGuide.CCDInfo(
		bias = bias,
		readNoise = readNoise,
		ccdGain = ccdGain,
	)
	ctrData = PyGuide.centroid(
		data = im[0].data,
		mask = mask,
		xyGuess = on,
		rad = rad,
		ccdInfo = ccdInfo,
		thresh = thresh,
	)
	if not ctrData.isOK:
		dispatch("f text=\"centroid failed: %s\"" % ctrData.msgStr)
		return
	
	shapeData = PyGuide.starShape(
			data = im[0].data,
			mask = mask,
			xyCtr = ctrData.xyCtr,
			rad = ctrData.rad,
		)
	if not shapeData.isOK:
		print "GuideTest: starShape failed with error:", shapeData.msgStr

	dispatch(
		"i files=c, %d, %r, %r, %r" % (isNew, "", fileName, ""),
	)
	
	if (rad != None):
		dispatch(
			"i centroidPyGuideConfig=%.2f" % (rad,),
		)
		
	dispatch(
		"i star=c, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, NaN, %.2f, %d, %.2f, %.2f" % \
			(1,
			ctrData.xyCtr[0], ctrData.xyCtr[1], ctrData.xyErr[0], ctrData.xyErr[1],
			ctrData.rad, ctrData.asymm,
			shapeData.fwhm, shapeData.fwhm, shapeData.chiSq, ctrData.counts,
			shapeData.bkgnd, shapeData.ampl),
	)

def dispatch(replyStr):
	"""Dispatch the reply string.
	The string should start from the message type character
	(thus program ID, actor and command ID are added).
	"""
	global tuiModel, _CmdID
	cmdr = tuiModel.getCmdr()
	
	msgStr = "%s %d %s %s" % (cmdr, _CmdID, actor, replyStr)
#	print "dispatching %r" % msgStr

	tuiModel.root.after(20, tuiModel.dispatcher.doRead, None, msgStr)

def findStars(fileName, count=None, thresh=None, isNew=False):
	"""Search for stars
	"""
	global g_thresh
	if not thresh:
		thresh = g_thresh

	im = pyfits.open(fileName)
	incrCmdID()
	
	ccdInfo = PyGuide.CCDInfo(
		bias = bias,
		readNoise = readNoise,
		ccdGain = ccdGain,
	)
	ctrDataList, imStats = PyGuide.findStars(
		data = im[0].data,
		mask = mask,
		ccdInfo = ccdInfo,
		thresh = thresh,
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

def setParams(expTime=None, thresh=None, count=None):
#	print "setParams(expTime=%r, thresh=%r)" % (expTime, thresh)
	global g_expTime, g_thresh
	
	strList = []

	if expTime != None:
		g_expTime = float(expTime)
		strList.append("time=%.1f" % g_expTime)
	if thresh != None:
		g_thresh = float(thresh)
		strList.append("fsActThresh=%.1f" % g_thresh)
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

def init():
	global tuiModel

	tuiModel = TUI.TUIModel.getModel(True)

def run():
	global tuiModel
	init()

	dispatch(": guiding=off")

	currDir = os.path.dirname(__file__)
	fileName = 'gimg0128.fits'
	fileName = os.path.join(currDir, fileName)

	setParams(expTime = 15.0, thresh = 3.0)
	
	fileNames = ('gimg0128.fits', 'gimg0129.fits', 'gimg0130.fits', 'gimg0131.fits', 'gimg0132.fits', 'gimg0133.fits', 'gimg0134.fits', )
	def fileNameIter():
		while True:
			for fileName in fileNames:
				yield fileName

	fni = fileNameIter()
	fni = iter(fileNames[0:2])
	
	def anime():
		try:
			fileName = fni.next()
		except StopIteration:
			return
		print "load %r" % (fileName,)
		filePath = os.path.join(currDir, fileName)
		findStars(filePath, isNew=True)
		tuiModel.root.after(1000, anime)
#	anime()
	tuiModel.root.after(1000, anime) # give window time to be displayed

	#findStars(fileName, isNew=True)
