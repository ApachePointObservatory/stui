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
"""
import os
import numarray as num
import pyfits
import PyGuide

import TUI.TUIModel
import GuideModel

# data for NA2 guider
actor = "gcam"
bias = 0 # 1780 is alleged, but our test images have a much lower signal!!!
readNoise = 21.391
ccdGain = 1.643 # e-/pixel

# other constants you may wish to set
mask = None
g_expTime = 15.0
g_thresh = 3.0

# leave alone
tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

def centroid(fileName, on, rad=None, cmdID = 0, isNew=False):
	im = pyfits.open(fileName)
	
	try:
		cd = PyGuide.centroid(
			data = im[0].data,
			mask = mask,
			xyGuess = on,
			rad = rad,
			bias = bias,
			readNoise = readNoise,
			ccdGain = ccdGain,
		)
	except StandardError, e:
		dispatch("f text=\"centroid failed: %s\"" % str(e))
		return
	
	try:
		ss = PyGuide.starShape(
				data = im[0].data,
				mask = mask,
				xyCtr = cd.xyCtr,
			)
	except StandardError, e:
		print "GuideTest: starShape failed with error:", e
		ss = PyGuide.StarShapeData()


	dispatch(
		"i files=c, %d, %r, %r, %r" % (isNew, "", fileName, ""),
		cmdID = cmdID,
	)
	
	if (rad != None):
		dispatch(
			"i centroidPyGuideConfig=%.2f" % (rad,),
			cmdID = cmdID,
		)
		
	dispatch(
		"i star=c, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, NaN, NaN, %.2f, %d, %.2f, %.2f" % \
			(1,
			cd.xyCtr[0], cd.xyCtr[1], cd.xyErr[0], cd.xyErr[1], cd.rad, cd.asymm,
			ss.fwhm, ss.chiSq, cd.counts, ss.bkgnd, ss.ampl),
		cmdID = cmdID,
	)

def dispatch(replyStr, cmdID=0):
	"""Dispatch the reply string.
	The string should start from the message type character
	(thus program ID, actor and command ID are added).
	"""
	dispatcher = tuiModel.dispatcher
	cmdr = tuiModel.getCmdr()
	
	msgStr = "%s %d %s %s" % (cmdr, cmdID, actor, replyStr)
#	print "dispatching %r" % msgStr

	tuiModel.root.after(20, tuiModel.dispatcher.doRead, None, msgStr)

def findStars(fileName, count=None, thresh=None, cmdID = 0, isNew=False):
	"""Search for stars
	"""
	global g_thresh
	if not thresh:
		thresh = g_thresh

	im = pyfits.open(fileName)

	isSat, cdList = PyGuide.findStars(
		data = im[0].data,
		mask = mask,
		bias = bias,
		readNoise = readNoise,
		ccdGain = ccdGain,
		dataCut = thresh,
	)[0:2]

	if count:
		cdList = cdList[0:count]
	
	setParams(thresh=thresh)

	dispatch(
		"i files=f, %d, %r, %r, %r" % (isNew, "", fileName, ""),
		cmdID = cmdID,
	)

# clean this up so the default value is printed if set to None
# (but nothing is printed if both values are None)
#	if (count != None) or (thresh != None):
#		dispatch(
#			"i findStarsPyGuideConfig=%d, %.2f" % (count, thresh),
#			cmdID = cmdID,
#		)

	ind = 1
	for cd in cdList:
		try:
			ss = PyGuide.starShape(
				data = im[0].data,
				mask = mask,
				xyCtr = cd.xyCtr,
			)
		except StandardError, e:
			print "GuideTest: starShape failed with error:", e
			ss = PyGuide.StarShapeData()
		
		dispatch(
			"i star=f, %d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, NaN, NaN, %.2f, %d, %.2f, %.2f" % \
				(ind,
				cd.xyCtr[0], cd.xyCtr[1], cd.xyErr[0], cd.xyErr[1], cd.rad, cd.asymm,
				ss.fwhm, ss.chiSq, cd.counts, ss.bkgnd, ss.ampl),
			cmdID = cmdID,
		)
		ind += 1
	dispatch(":", cmdID = cmdID)

def setParams(expTime=None, thresh=None, count=None, cmdID = 0):
#	print "setParams(expTime=%r, thresh=%r)" % (expTime, thresh)
	global g_expTime, g_thresh
	
	strList = []

	if expTime != None:
		g_expTime = float(expTime)
		strList.append("time=%.1f" % g_expTime)
	if thresh != None:
		g_thresh = float(thresh)
		strList.append("thresh=%.1f" % g_thresh)
	if strList:
		dispatch(
			": %s" % "; ".join(strList),
			cmdID = cmdID,
		)

def showFile(fileName, cmdID=0):
	dispatch(
		": imgFile=%s" % (fileName,),
		cmdID = cmdID,
	)
	findStars(fileName)

def start():
	currDir = os.path.dirname(__file__)
	fileName = 'gimg0128.fits'
	fileName = os.path.join(currDir, fileName)

	setParams(expTime = 15.0, thresh = 3.0)
	findStars(fileName, isNew=True)
