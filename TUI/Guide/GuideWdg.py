#!/usr/local/bin/python
"""Guiding support

To do:
- Fix threshWdg so you can use the contextual menu without executing
  the <FocusOut> method. Basically all entry widgets need a new kind of
  callback that only executes when the value changes (<return>, <enter>
  or <focusout> -- but not if a contextual menu used).
  This could be used for prefs, as well, and presumably in other situations.
  
- Add slit display
- Add snap points for dragging along slit -- a big job
- Add "show mask"
- Add display area for data about current star?
- Disable Center button if no object selected
- Use color prefs for markers
- Implement the various commands that right now talk to GuideTest or do nothing.

History:
2005-02-10 ROwen	alpha version; lots of work to do
2005-02-22 ROwen	Added drag to centroid. Modified for GryImageDispWdg 2005-02-22.
2005-02-23 ROwen	Added exposure time; first cut at setting exp time and thresh
					when a new image comes in.
"""
import Tkinter
import numarray as num
import pyfits
import RO.CanvasUtil
import RO.Constants
import RO.Wdg
import RO.Wdg.GrayImageDispWdg as GImDisp

import TUI.TUIModel
# import TUI.TCC.TCCModel
import GCamModel

_HelpPrefix = "<to be determined>"

_MaxDist = 15
_CentroidTag = "centroid"
_FindTag = "findStar"
_SelTag = "selStar"
_DragRectTag = "centroidDrag"
_MarkRad = 15
_HoleRad = 3

# set these via color prefs, eventually
_FindColor = "green"
_CentroidColor = "yellow"

class GuideWdg(Tkinter.Frame):
	def __init__(self,
		master,
		actor,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		self.actor = actor
		self.gcamModel = GCamModel.getModel(actor)
		self.tuiModel = TUI.TUIModel.getModel()

		self.dispFile = None
		self.isCurrent = False # is display image current?
		self.findStarsData = []	# star data from findstars
		self.centroidData = [] # star data from centroiding at a user-selected point
		self.selData = None # if a selection exists: stardata, else None
		self.getFindStarsDataID = None # cmdr, cmdID used to generate initial data
		
		row=0

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
		
		helpText = "threshold for finding stars"
		RO.Wdg.StrLabel(
			inputFrame,
			text = "Threshold",
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

		self.expButton = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Expose",
			helpText = "Take an exposure",
		)
		self.expButton.pack(side="left")

		self.ctrButton = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Center",
			helpText = "Put selected star on boresight",
		)
		if self.gcamModel.gcamInfo.slitViewer:
			self.ctrButton.pack(side="left")
		
		self.guideButton = RO.Wdg.Button(
			cmdButtonFrame,
			text = "Guide",
			helpText = "Start guiding on selected star",
		)
		self.guideButton.pack(side="left")

		cmdButtonFrame.grid(row=row, column=0, sticky="w")
		row += 1
		
		self.gcamModel.imgFile.addIndexedCallback(self.doImgFile)
		self.gcamModel.star.addCallback(self.updStar)
		
		# event bindings
		self.gim.cnv.bind("<Button-1>", self.dragStart, add=True)
		self.gim.cnv.bind("<B1-Motion>", self.dragContinue, add=True)
		self.gim.cnv.bind("<ButtonRelease-1>", self.dragEnd, add=True)
		
		self.threshWdg.bind("<FocusOut>", self.doFindStars)
		self.threshWdg.bind("<Return>", self.doFindStars)
		
		# keyword variable bindings
		self.gcamModel.expTime.addROWdg(self.expTimeWdg, setDefault=True)
		self.gcamModel.thresh.addROWdg(self.threshWdg, setDefault=True)

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

		meanPos = num.divide(num.add(startPos, endPos), 2.0)
		deltaPos = num.subtract(endPos, startPos)

		rad = max(deltaPos) / (self.gim.zoomFac * 2.0)
		imPos = self.gim.imPosFromCnvPos(meanPos)
		
		if abs(deltaPos[0]) > 1 and abs(deltaPos[1] > 1):
			# centroid
			# clear current selection and centroid data
			# (to make it more obvious if the new centroid fails)
			# I may want to skip this step once error reporting improves
			self.clearSelection()
			self.gim.removeAnnotation(_CentroidTag)
			self.centroidData = []

			# execute centroid command
			cmdStr = "centroid file=%r on=%s, %s radius=%s" % (self.dispFile, imPos[0], imPos[1], rad)
	#		cmdVar = KeyVariable.CmdVar(
	#			actor = self.actor,
	#			cmdStr = cmdCtr,
	#		)
	#		self.statusBar.doCmd(cmdVar)
	# use the following until the hub can do this
			print cmdStr
			GuideTest.centroid(self.dispFile, on=imPos, rad=rad)
			
		else:
			# select
			self.doSelect(evt)
	
	def clearSelection(self):
		"""Clear the current selection (if any)."""
		if self.selData:
			self.gim.removeAnnotation(_SelTag)
			self.selData = None
	
	def doFindStars(self, *args):
		thresh = self.threshWdg.getNum()
		
		# clear current star info
		self.findStarsData = []
		self.gim.removeAnnotation(_FindTag)
		self.clearSelection()
		
		# execute new command
		cmdStr = "findstars thresh=%s" % (thresh,)
		print cmdStr
		# this is a fake; replace with real cmd sent to hub
		GuideTest.findStars(
			fileName = fileName,
			thresh = thresh,
		)
	
	def doImgFile(self, fileName, isCurrent, **kargs):
		print "%s doImgFile; fileName=%r; isCurrent=%r" % (self.actor, fileName, isCurrent)
		if not isCurrent:
			return

		wasCurrent = self.isCurrent
		self.isCurrent = False
		self.ctrButton.setEnable(False)
		self.guideButton.setEnable(False)
		if not self.showNewWdg.getBool():
			if wasCurrent:
				self.statusBar.setMsg(
					"Not the current image; guiding controls disabled",
					RO.Constants.sevWarning,
				)
			return

		# get new image, display and set self.dispFile accordingly
#		self.statusBar.setMsg(
#			"Retrieving new image (NOT IMPLEMENTED)",
#			RO.Constants.sevNormal,
#		)
		im = pyfits.open(fileName)
		data = im[0].data

		self.gim.showArr(data)
		self.dispFile = fileName
		self.getFindStarsDataID = None

		self.isCurrent = True
		
		# re-enable the controls
		self.ctrButton.setEnable(True)
		self.guideButton.setEnable(True)
		
		# restore defaults for tweaks
		# (may have to be trickier if these keywords show up after the image file keyword)
		self.expTimeWdg.restoreDefault()
	
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

		# look for nearby centroid to choose
		selStarData = None
		minDistSq = _MaxDist
		for starData in self.centroidData + self.findStarsData:
			distSq = (starData[1] - imPos[0])**2 + (starData[2] - imPos[1])**2
			if distSq < minDistSq:
				minDistSq = distSq
				selStarData = starData

		if not selStarData:
			return
			
		self.selStar(selStarData, color=_FindColor)
	
	def selStar(self, starData, color):
		"""Select the specified star"""
		# remove current selection, if it exists
		self.clearSelection()

		# draw selection
		selID = self.gim.addAnnotation(
			GImDisp.ann_X,
			imPos = starData[1:3],
			isImSize = False,
			rad = _MarkRad,
			holeRad = _HoleRad,
			tags = _SelTag,
			fill = color,
		)
		self.selData = starData
	
	def updStar(self, starData, isCurrent, keyVar):
		"""New star data found.
		
		Overwrite existing findStars data if:
		- No existing data and file name matches
		- I generated the command
		else ignore.
		
		Replace existing centroid data if I generated the command,
		else ignore.
		"""
		if not isCurrent:
			return

		# if file name does not match, ignore
#		if file name in new data != self.dispFile:
#			return
		msgDict = keyVar.getMsgDict()

		isMe = msgDict["cmdr"] == self.tuiModel.getCmdr()

		ind = starData[0]
		if ind > 0:
			tag = _FindTag
			if isMe or self.getFindStarsDataID == (msgDict["cmdr"], msgDict["cmdID"]):
				if ind == 1:
					# starting a new list of findstars data
					# best star comes first, so select that one
					self.gim.removeAnnotation(_FindTag)
					self.findStarsData = [starData]
					self.selStar(starData, _FindColor)
					self.threshWdg.restoreDefault()
				else:
					if ind <= len(self.findStarsData):
						print "warning: unexpected index; plowing ahead as best I can"
					self.findStarsData.append(starData)

				color = _FindColor
			else:
				# not interested in this findstars data
				return
		elif isMe:
			print "centroid"
			# a centroid that I commanded
			self.clearSelection()
			self.gim.removeAnnotation(_CentroidTag)
			self.centroidData = [starData]
			tag = _CentroidTag
			color = _CentroidColor
			
			# select this star
			self.selStar(starData, color=_CentroidColor)
			
		else:
			# not interested in this centroid data
			return
		
		self.gim.addAnnotation(
			GImDisp.ann_Circle,
			imPos = starData[1:3],
			rad = starData[5],
			isImSize = True,
			tags = tag,
			outline = color,
		)
		
				
	def showFile(self, fileName):
		"""Display a local file.
		"""
		im = pyfits.open(fileName)
		data = im[0].data

		self.gim.showArr(data)
		self.dispFile = fileName
		self.getFindStarsDataID = None
		
		

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	import GuideTest
	
	fileName = 'gimg0128.fits'

	testFrame = GuideWdg(root, "gcam")
	testFrame.pack(expand="yes", fill="both")
	
	GuideTest.setParams(expTime = 15.0, thresh = 3.0)
	GuideTest.showFile(fileName)

	root.mainloop()


