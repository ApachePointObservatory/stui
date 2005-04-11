#!/usr/local/bin/python
"""Guiding support

To do:
- Handle history
- Download mask files (a bit tricky because multiple images 
  use the same mask, so don't download unless needed)
- Allow user to ask to see mask or data or data*(mask==0)

- Fix threshWdg so you can use the contextual menu without executing
  the <FocusOut> method. Basically all entry widgets need a new kind of
  callback that only executes when the value changes (<return>, <enter>
  or <focusout> -- but not if a contextual menu used).
  This could be used for prefs, as well, and presumably in other situations.
  
- Display name of current image
- Add display area for data about current star.
- Add preference to limit # of images saved to disk
- Add slit display
- Add snap points for dragging along slit -- a big job
- Add "show mask"
- Add history controls; incorporate Show New into those, I think.
- Retain zoom if the next image is the same size as the current image.
- Use color prefs for markers

History:
2005-02-10 ROwen	alpha version; lots of work to do
2005-02-22 ROwen	Added drag to centroid. Modified for GryImageDispWdg 2005-02-22.
2005-02-23 ROwen	Added exposure time; first cut at setting exp time and thresh
					when a new image comes in.
2005-03-28 ROwen	Modified for improved files and star keywords.
2005-03-31 ROwen	Implemented hub commands. Added display of current image name.
2005-04-11 ROwen	Modified for GCamModel->GuideModel
"""
import os
import Tkinter
import numarray as num
import pyfits
import RO.CanvasUtil
import RO.Constants
import RO.Alg
import RO.Comm.FTPGet as FTPGet
import RO.KeyVariable
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp
import TUI.TUIModel
# import TUI.TCC.TCCModel
import GuideModel

_HelpPrefix = "<to be determined>"

_MaxDist = 15
_CentroidTag = "centroid"
_FindTag = "findStar"
# _GuideTag = "guide"
_SelTag = "showSelection"
_DragRectTag = "centroidDrag"
_MarkRad = 15
_HoleRad = 3

_HistLen = 20

# set these via color prefs, eventually
_FindColor = "green"
_CentroidColor = "cyan"
# _GuideColor = "red"

_TypeTagColorDict = {
	"c": (_CentroidTag, _CentroidColor),
	"f": (_FindTag, _FindColor),
#	"g": (_GuideTag, _GuideColor),
}

_LocalMode = True # true to NOT send commands to the hub

class ImObj:
	def __init__(self,
		baseDir,
		imageName,
		maskName,
		cmdChar,
		cmdr,
		cmdID,
	):
		self.baseDir = baseDir

		# path to image and mask files, relative to baseDir or imageRoot
		self.imageName = imageName
		self.maskName = maskName
		
		self.currCmdChar = cmdChar
		self.currCmdrCmdID = (cmdr, cmdID)
		self.sawStarTypes = []
		self.starDataDict = {}
		self.selDataColor = None
		
		# start by setting these to the current global defaults
		# then update if the hub sends additional data
		# (none of that is coded as I write this)
		self.defRadius = None
		self.defThresh = None
		
class GuideWdg(Tkinter.Frame):
	def __init__(self,
		master,
		actor,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		self.actor = actor
		self.gcamModel = GuideModel.getModel(actor)
		self.tuiModel = TUI.TUIModel.getModel()
		
		# may want to switch to an array of imdata
		# so we can have multiple images pending
		# but keeping track of what to display would be very awkward
		# so I hope we don't have to bother
		self.nToSave = _HistLen # eventually allow user to set?
		self.imObjDict = RO.Alg.OrderedDict()
		self.dispImObj = None # object data for most recently taken image, or None
		
		row=0
		
		histFrame = Tkinter.Frame(self)
		
		self.imNameWdg = RO.Wdg.StrLabel(histFrame, anchor="w")
		self.imNameWdg.pack(side="left", expand=True, fill="x")
		
		histFrame.grid(row=row, column=0, sticky="ew")
		row += 1

		self.gim = GImDisp.GrayImageWdg(self)
		self.gim.grid(row=row, column=0, sticky="news")
		self.grid_rowconfigure(row, weight=1)
		self.grid_columnconfigure(0, weight=1)
		row += 1
		
		inputFrame = Tkinter.Frame(self)

		helpText = "exposure time"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Exp Time",
			helpText = helpText,
		).pack(side="left")
		
		self.expTimeWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = self.gcamModel.gcamInfo.minExpTime,
			maxValue = self.gcamModel.gcamInfo.maxExpTime,
			defValue = 15.0, # set from hub, once we can!!!
			defFormat = "%.1f",
			defMenu = "Current",
			minMenu = "Minimum",
			autoIsCurrent = True,
			helpText = helpText,
		)
		self.expTimeWdg.pack(side="left")

		RO.Wdg.StrLabel(
			inputFrame,
			text = "sec",
			width = 4,
			anchor = "w",
		).pack(side="left")

		helpText = "binning factor"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Bin",
			helpText = helpText,
		).pack(side="left")
		
		self.binFacWdg = RO.Wdg.IntEntry(
			inputFrame,
			minValue = 1,
			maxValue = 99,
			defValue = 1, # set from hub, once we can!!!
			defMenu = "Current",
			autoIsCurrent = True,
			helpText = helpText,
		)
		self.binFacWdg.pack(side="left")
		
		helpText = "threshold for finding stars"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Thresh",
			helpText = helpText,
		).pack(side="left")
		
		self.threshWdg = RO.Wdg.FloatEntry(
			inputFrame,
			minValue = 0,
			defValue = 3.0, # set from hub, once we can!!!
			defFormat = "%.1f",
			defMenu = "Current",
			autoIsCurrent = True,
			width = 5,
			helpText = helpText,
		)
		self.threshWdg.pack(side="left")

		RO.Wdg.StrLabel(
			inputFrame,
			text = u"\N{GREEK SMALL LETTER SIGMA}",
		).pack(side="left")

		inputFrame.grid(row=row, column=0, sticky="w")
		row += 1
				
		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			dispatcher = self.tuiModel.dispatcher,
			prefs = self.tuiModel.prefs,
			playCmdSounds = True,
			helpURL = _HelpPrefix + "StatusBar",
		)
		self.statusBar.grid(row=row, column=0, sticky="ew")
		row += 1
		
		cmdButtonFrame = Tkinter.Frame(self)
		
		self.showNewWdg = RO.Wdg.Checkbutton(
			cmdButtonFrame,
			text = "Show New",
			defValue = True,
			helpText = "Automatically display new images?",
		)
		self.showNewWdg.pack(side="left")

		self.exposeBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Expose",
			callFunc = self.doExpose,
			helpText = "Take an exposure",
		)
		self.exposeBtn.pack(side="left")

		self.centerBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Center",
			callFunc = self.doCenter,
			helpText = "Put selected star on boresight",
		)
		if self.gcamModel.gcamInfo.slitViewer:
			self.centerBtn.pack(side="left")
		
		self.guideBtn = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide",
			callFunc = self.doGuide,
			helpText = "Start guiding on selected star",
		)
		self.guideBtn.pack(side="left")

		cmdButtonFrame.grid(row=row, column=0, sticky="w")
		row += 1
		
		# disable centroid and guide buttons (no star selected)
		self.centerBtn.setEnable(True)
		self.guideBtn.setEnable(True)
		
		# event bindings
		self.gim.cnv.bind("<Button-1>", self.dragStart, add=True)
		self.gim.cnv.bind("<B1-Motion>", self.dragContinue, add=True)
		self.gim.cnv.bind("<ButtonRelease-1>", self.dragEnd, add=True)
		
		self.threshWdg.bind("<FocusOut>", self.doFindStars)
		self.threshWdg.bind("<Return>", self.doFindStars)
		
		# keyword variable bindings
		self.gcamModel.expTime.addROWdg(self.expTimeWdg, setDefault=True)
		self.gcamModel.fsDefThresh.addROWdg(self.threshWdg, setDefault=True)
		self.gcamModel.files.addCallback(self.updFiles)
		self.gcamModel.star.addCallback(self.updStar)
	
	def clearSelection(self):
		"""Clear the current selection (if any).
		Clears the data in the current imObj as well as the display.
		"""
		self.gim.removeAnnotation(_SelTag)

		if not self.dispImObj:
			return

		self.dispImObj.selDataColor = None		
	
	def doExistingImage(self, imageName, cmdChar, cmdr, cmdID):
		"""Data is about to arrive for an existing image.
		Decide whether we are interested in it,
		and if so, get ready to receive it.
		"""
#		print "doExistingImage(imageName=%r, cmdChar=%r, cmdr=%r, cmdID=%r" % (imageName, cmdChar, cmdr, cmdID)
		# see if this data is of interest
		imObj = self.imObjDict.get(imageName)
		if not imObj:
			# I have no knowledge of this image, so ignore the data
			return
		isMe = (cmdr == self.tuiModel.getCmdr())
		if not isMe:
			# I didn't trigger this command, so ignore the data
			return
		
		# data is of interest; update cmdr and cmdID
		# and clear sawStarTypes
		imObj.currCmdChar = cmdChar
		imObj.currCmdrCmdID = (cmdr, cmdID)
		imObj.sawStarTypes = []
	
	def doCenter(self, wdg=None):
		"""Center up on the selected star.
		"""
		if not self.dispImObj:
			raise RuntimeError("No guide image")
		if not self.dispImObj.selDataColor:
			raise RuntimeError("No star selected")
		
		starData, color = self.dispImObj.selDataColor
		pos = starData[2:4]
		rad = starData[6]
		cmdStr = "guide on file=%r centerOn=%.2f,%.2f noGuide cradius=%.1f" % \
			(self.dispImObj.imageName, pos[0], pos[1], rad)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr

	def doExpose(self, wdg=None):
		"""Take an exposure.
		"""
		expTime = self.expTimeWdg.getNum()
		binFac = self.binFacWdg.getNum()
		thresh = self.threshWdg.getNum()
		cmdStr = "findstars time=%.2f bin=%d thresh=%d" % (expTime, binFac, thresh)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
		
	def doFindStars(self, *args):
		thresh = self.threshWdg.getNum()
		
		# execute new command
		cmdStr = "findstars file=%r thresh=%s" % (self.dispImObj.imageName, thresh)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
			GuideTest.findStars(self.dispImObj.imageName, thresh = thresh)
	
	def doGuide(self, wdg=None):
		"""Guide on the selected star.
		"""
		if not self.dispImObj:
			raise RuntimeError("No guide image")
		if not self.dispImObj.selDataColor:
			raise RuntimeError("No star selected")
		
		starData, color = self.dispImObj.selDataColor
		pos = starData[2:4]
		rad = starData[6]
		cmdStr = "guide on file=%r gstar=%.2f,%.2f cradius=%.1f" % \
			(self.dispImObj.imageName, pos[0], pos[1], rad)
		if not _LocalMode:
			cmdVar = RO.KeyVariable.CmdVar(
				actor = self.actor,
				cmdStr = cmdStr,
			)
			self.statusBar.doCmd(cmdVar)
		else:
			print cmdStr
	
	def doSelect(self, evt):
		"""Select a star based on a mouse click
		- If near a found star, select it
		- Otherwise centroid at that point and select the result (if successful)
		"""
		if not self.gim.isNormalMode():
			return
		cnvPos = self.gim.cnvPosFromEvt(evt)
		imPos = self.gim.imPosFromCnvPos(cnvPos)

		# remove current selection, if it exists
		self.clearSelection()

		# get current image object
		if not self.dispImObj:
			return

		# look for nearby centroid to choose
		selStarData = None
		minDistSq = _MaxDist
		for typeChar, starDataList in self.dispImObj.starDataDict.iteritems():
#			print "doSelect checking typeChar=%r, nstars=%r" % (typeChar, len(starDataList))
			tag, color = _TypeTagColorDict[typeChar]
			for starData in starDataList:
				distSq = (starData[2] - imPos[0])**2 + (starData[3] - imPos[1])**2
				if distSq < minDistSq:
					minDistSq = distSq
					selStarData = starData
					selColor = color

		if not selStarData:
			self.centerBtn.setEnable(False)
			self.guideBtn.setEnable(False)
			return

		self.centerBtn.setEnable(True)
		self.guideBtn.setEnable(True)
			
		self.dispImObj.selDataColor = (selStarData, selColor)
		self.showSelection()

	def dragStart(self, evt):
		"""Mouse down for current drag (whatever that might be).
		"""
		if not self.gim.isNormalMode():
			return
		self.dragStart = self.gim.cnvPosFromEvt(evt)
		self.dragRect = self.gim.cnv.create_rectangle(
			self.dragStart[0], self.dragStart[1], self.dragStart[0], self.dragStart[1],
			outline = _CentroidColor,
			tags = _DragRectTag,
		)
	
	def dragContinue(self, evt):
		if not self.gim.isNormalMode():
			return
		newPos = self.gim.cnvPosFromEvt(evt)
		self.gim.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
	
	def dragEnd(self, evt):
		if not self.gim.isNormalMode():
			return

		endPos = self.gim.cnvPosFromEvt(evt)
		startPos = self.dragStart or endPos

		self.gim.cnv.delete(_DragRectTag)
		self.dragStart = None
		self.dragRect = None
		
		if not self.dispImObj:
			return

		meanPos = num.divide(num.add(startPos, endPos), 2.0)
		deltaPos = num.subtract(endPos, startPos)

		rad = max(deltaPos) / (self.gim.zoomFac * 2.0)
		imPos = self.gim.imPosFromCnvPos(meanPos)
		
		if abs(deltaPos[0]) > 1 and abs(deltaPos[1] > 1):
			# centroid

			# execute centroid command
			cmdStr = "centroid file=%r on=%s,%s radius=%s" % (self.dispImObj.imageName, imPos[0], imPos[1], rad)
			if not _LocalMode:
				cmdVar = RO.KeyVariable.CmdVar(
					actor = self.actor,
					cmdStr = cmdStr,
				)
				self.statusBar.doCmd(cmdVar)
			else:
				print cmdStr
				GuideTest.centroid(self.dispImObj.imageName, on=imPos, rad=rad)
			
		else:
			# select
			self.doSelect(evt)
		
	def fetchImage(self, imObj, getMask=False):
		"""Fetch an image from APO.
		"""
#		print "fetchImage(imObj=%r, getMask=%r)" % (imObj, getMask)
		if getMask:
			relPath = imObj.maskName
		else:
			relPath = imObj.imageName
		
		if not _LocalMode:
			# pre-pend directory information
			(host, rootDir), isCurr = self.gcamModel.imageRoot.get()
			if None in (host, rootDir):
				raise RuntimeError("base dir unknown")

			# do NOT use os.path to join remote host path components;
			# simply concatenate instead
			fromPath = rootDir + relPath

			# DO use os.path to concatenate local path components
			toPath = os.path.join(imObj.baseDir, relPath)
			
			self.gcamModel.ftpLogWdg.getFile(
				host = host,
				fromPath = fromPath,
				toPath = toPath,
				isBinary = True,
				overwrite = False,
				createDir = True,
				callFunc = self.fetchCallback,
				dispStr = relPath,
				username = "images",
				password = "7nights."
			)

		else:
			self.after(100, self.showImage, imObj, getMask)
		
	def fetchCallback(self, ftpGet):
		"""Called while an image is being downloaded.
		When the download finishes, handle it.
		"""
		if not ftpGet.isDone():
			return
		relPath = ftpGet.dispStr
		imObj = self.imObjDict.get(relPath)
		if not imObj:
			return
		ftpState = ftpGet.getState()
		if ftpState == FTPGet.Done:
			if self.showNewWdg.getBool():
				self.showImage(imObj)
		elif ftpState == FTPGet.Failed:
			raise RuntimeError("Get %r failed" % relPath)
	
	def showImage(self, imObj, showMask=False):
		"""Display an image.
		"""
#		print "showImage(imObj=%r, showMask=%r)" % (imObj, showMask)
		if showMask:
			fileName = imObj.maskName
		else:
			fileName = imObj.imageName

		fullPath = os.path.join(imObj.baseDir, fileName)
		fitsIm = pyfits.open(fullPath)
		imArr = fitsIm[0].data

		# remove existing annotations
		for (tag, color) in _TypeTagColorDict.itervalues():
			self.gim.removeAnnotation(tag)
		self.gim.removeAnnotation(_SelTag)
		
		# display new data
		self.gim.showArr(imArr)
		self.dispImObj = imObj
		self.imNameWdg["text"] = fileName
		
		# add existing annotations, if any
		# (for now just display them,
		# but eventually have a control that can show/hide them,
		# and -- as the first step -- set the visibility of the tags appropriately)
		for cmdChar, starDataList in imObj.starDataDict.iteritems():
			for starData in starDataList:
				tag, color = _TypeTagColorDict[cmdChar]
				self.gim.addAnnotation(
					GImDisp.ann_Circle,
					imPos = starData[2:4],
					rad = starData[6],
					isImSize = True,
					tags = tag,
					outline = color,
				)
		
		self.showSelection()
	
	def showSelection(self):
		"""Display the current selection.
		"""
		# clear current selection
		self.gim.removeAnnotation(_SelTag)

		if not self.dispImObj or not self.dispImObj.selDataColor:
			return

		starData, color = self.dispImObj.selDataColor

		# draw selection
		selID = self.gim.addAnnotation(
			GImDisp.ann_X,
			imPos = starData[2:4],
			isImSize = False,
			rad = _MarkRad,
			holeRad = _HoleRad,
			tags = _SelTag,
			fill = color,
		)
	
	def updFiles(self, fileData, isCurrent, keyVar):
#		print "%s updFiles; fileData=%r; isCurrent=%r" % (self.actor, fileData, isCurrent)
		if not isCurrent:
			return
		
		cmdChar, isNew, baseDir, imageName, maskName = fileData[0:5]
		msgDict = keyVar.getMsgDict()
		cmdr = msgDict["cmdr"]
		cmdID = msgDict["cmdID"]
		imageName = baseDir + imageName
		maskName = baseDir + maskName

		if not isNew:
			# handle data for existing image
			self.doExistingImage(imageName, cmdChar, cmdr, cmdID)
			return
		
		# at this point we know we have a new image
		
		# create new object data
		baseDir = self.gcamModel.ftpSaveToPref.getValue()
		msgDict = keyVar.getMsgDict()
		cmdr = msgDict["cmdr"]
		cmdID = msgDict["cmdID"]
		imObj = ImObj(
			baseDir = baseDir,
			imageName = imageName,
			maskName = maskName,
			cmdChar = cmdChar,
			cmdr = cmdr,
			cmdID = cmdID,
		)
		self.imObjDict[imObj.imageName] = imObj
		self.dispImObj = imObj
		
		# purge excess images
		if len(self.imObjDict) > self.nToSave:
			keys = self.imObjDict.keys()
			for imName in keys[0:-self.nToSave]:
				del(self.imObjDict[imName])
			
		# if there is a graphical representation of this image buffer,
		# now is the time to update it!
		
		# start retreiving the image data
		self.fetchImage(imObj)

	def updStar(self, starData, isCurrent, keyVar):
		"""New star data found.
		
		Overwrite existing findStars data if:
		- No existing data and cmdr, cmdID match
		- I generated the command
		else ignore.
		
		Replace existing centroid data if I generated the command,
		else ignore.
		"""
#		print "updStar(starDataType=%r, isCurrent=%r)" % (starData[0], isCurrent)
		if not isCurrent:
			return

		# get image object (ignore if no match)
		msgDict = keyVar.getMsgDict()
		cmdrCmdID = (msgDict["cmdr"], msgDict["cmdID"])
		for imObj in self.imObjDict.itervalues():
			if cmdrCmdID == imObj.currCmdrCmdID:
				break
		else:
			return
		
		isVisible = (self.dispImObj.imageName == imObj.imageName)
		typeChar = starData[0]
		try:
			tag, color = _TypeTagColorDict[typeChar]
		except KeyError:
			raise RuntimeError("Unknown type character %r for star data" % (typeChar,))

		updSel = False
		if typeChar in imObj.sawStarTypes:
			# add star data
			imObj.starDataDict[typeChar].append(starData)
		else:	
			# first star data of this type seen for this command;
			# update selection if necessary and restart this type of data
			if not imObj.sawStarTypes:
				# first star data of ANY type seen for this command; reset selection
				imObj.selDataColor = (starData, color)
				updSel = True

			# reset this type of data
			imObj.starDataDict[typeChar] = [starData]
			imObj.sawStarTypes.append(typeChar)

			if isVisible:
				self.gim.removeAnnotation(tag)
				self.gim.removeAnnotation(_SelTag)

		if not isVisible:
			# this image is not being displayed, so we're done
			return
		
		# update the display
		self.gim.addAnnotation(
			GImDisp.ann_Circle,
			imPos = starData[2:4],
			rad = starData[6],
			isImSize = True,
			tags = tag,
			outline = color,
		)
		
		# if this star was selected, display selection
		if updSel:
			self.showSelection()
			

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	import GuideTest

	testFrame = GuideWdg(root, "gcam")
	testFrame.pack(expand="yes", fill="both")

	GuideTest.start()	

	root.mainloop()


