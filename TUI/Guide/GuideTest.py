#!/usr/local/bin/python
"""Guide test code that crudely substitutes for the hub

Format for star keyword; this is a guess as of 2005-01-31; fields may change:
1.  	index: an index identifying the star within the list of stars returned by the command.
2,3.  	x,yCenter: centroid (binned pixels)
4,5.  	x,yError: estimated standard deviation of x,yCenter (binned pixels)
6		radius: radius of centroid region
7.  	asymmetry: a measure of the asymmetry of the object;
		the value minimized by PyGuide.centroid.
		Warning: not normalized, so probably not much use.
8.  	FWHM
9,		ellipticity
10		ellMajAng: angle of ellipse major axis in x,y frame
11.  	chiSq: goodness of fit to model star (a double gaussian). From PyGuide.starShape.
12.  	counts: sum of all unmasked pixels within the centroid radius (ADUs). From PyGuide.centroid
13.  	background: background level of fit to model star (ADUs). From PyGuide.starShape
14.  	amplitude: amplitude of fit to model star (ADUs). From PyGuide.starShape

History:
2005-01-31 ROwen
2005-02-08 ROwen	Updated for PyGuide 1.2.
2005-02-22 ROwen	Fixed centroid output (had not been updated to match new star format).
"""
import numarray as num
import pyfits
import PyGuide

import TUI.TUIModel
import GCamModel

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
nan = float("nan")

def centroid(fileName, on, rad=None, cmdID = 0):
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
		"i star=%d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %d, %.2f, %.2f" % \
			(0,
			cd.xyCtr[0], cd.xyCtr[1], cd.xyErr[0], cd.xyErr[1], cd.rad, cd.asymm,
			ss.fwhm, nan, nan, ss.chiSq, cd.counts, ss.bkgnd, ss.ampl),
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

	tuiModel.dispatcher.doRead(None, msgStr)
	tuiModel.root.update_idletasks()

def findStars(fileName, count=None, thresh=None, cmdID = 0):
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
	)

	if count:
		cdList = cdList[0:count]
	
	setParams(thresh=thresh)

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
			"i star=%d, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %.2f, %d, %.2f, %.2f" % \
				(ind,
				cd.xyCtr[0], cd.xyCtr[1], cd.xyErr[0], cd.xyErr[1], cd.rad, cd.asymm,
				ss.fwhm, nan, nan, ss.chiSq, cd.counts, ss.bkgnd, ss.ampl),
			cmdID = cmdID,
		)
		ind += 1
	dispatch(":", cmdID = cmdID)

def setParams(expTime=None, thresh=None, cmdID = 0):
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
