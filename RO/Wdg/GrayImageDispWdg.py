#!/usr/local/bin/python
"""Code to display a grayscale image.

This attempts to emulate some of the more important features of ds9,
while minimizing controls and the space used by controls and status displays.

Required packages:
- numarray
- PIM

Mouse Gestures
	Zoom (Z mode or use button 3):
	- Drag UL->LR to zoom in on the enclosed region.
	  The maximum zoom is set by _MaxZoom.
	- Drag LR->UL to zoom out (a small box zooms out more).
	  The minimum zoom is that needed to show the entire image.
	- Zoom to see the entire image: double-click or drag a tiny amount LR->UL.
	
	Levels (L mode or use button 2)
	- Drag mouse to change the levels shown as black and white.
	  Black/white level is controlled by x/y distance from center.
	- Restore default values: double-click.

Coordinate Systems:
imPos	image position; 0,0 at lower left corner of image,
		0.5, 0.5 in center of lower left image pixel
		+x to the right, +y up
		This is the convention used by PyGuide.
		I'm not sure if it's the convention used by ds9 or iraf.
cnvPos	tk canvas x,y; 0,0 at upper left corner
		+x to the right, +y down
note that imPos is independent of zoom, whereas cnvPos varies with zoom.

To Do:
- Highlight saturated pixels, e.g. in red (see PyImage and mixing)

Maybe Do:
- Add more annotations: rectangle, line, ellipse, perhaps polygon.
- Implement histogram equalization.
- Improve scrolling/panning. But the zoom in/out may do the job.
  Any improvement probably requires ditching the scroll bars entirely
  and displaying only a portion of the image. This could potentially make
  image display really fast at high zoom factor, but if one is going to avoid
  making a full copy of the image at the desired zoom factor, it may involve
  a ton of work to handle annotations correctly (unless one can paint all annotations
  and just have most of them not be visible on the bit of the image that is shown).
- Allow color preference variables for annotation colors
  (and be sure to auto-update those colors).
- Add pseudocolor options.

History:
2004-12-14 ROwen	Compute range based on sorting input data to handle data range;
					thus range changes need not resort (or recompute a histogram),
					but instead now must re-apply the scaling function.
2005-01-28 ROwen	Bug fix: was sorting the input data.
2005-02-02 ROwen	Added pixPosFromDS9Pos.
					Bug fixes:
					- Annotation class was mis-calling func (supplying pos
					as a tuple instead of two arguments).
					- The list of annotations was not being set correctly;
					only the last annotation was saved for redraw.
2005-02-04 ROwen	Modified annotations to use imPos instead of cnvPos
					Added removeAnnotation.
2005-02-10 ROwen	Improved scrolling (by not using RO.Wdg.ScrolledWdg).
					Zoom now attempts to preserve the center.
					Added an experimental arcsinh scale function.
2005-02-11 ROwen	Removed Log (use ArcSinh instead) and Square
					(useless for astronomical data) scaling functions.
					Still need to work out how to set ArcSinh scale factor.
2005-02-15 ROwen	Modified the algorithm for display; scaledArr now goes from
					0-256 for input values dataDispMin-Max.
					Added command-drag to adjust brightness and (in essence) contrast.
					Added command-double-click to restore default brightness and contrast.
2005-02-17 ROwen	New zoom model. New toolbar for zoom, levels or normal mode,
					with shortcuts for those with multi-button mice.
2005-02-22 ROwen	Added isNormalMode method.
					Fixed zoom issue: zooming changed size of widget.
					Changed doResize to isImSize and thus changed units of radius when false.
"""
import Tkinter
import math
import numarray as num
import Image
import ImageTk
import RO.CanvasUtil
import RO.Wdg
import RO.SeqUtil

_AnnTag = "_gs_ann_"
_DragRectTag = "_gs_dragRect"
_MaxZoomFac = 4

_ModeNormal = "normal"
_ModeZoom = "zoom"
_ModeLevel = "level"

ann_Circle = RO.CanvasUtil.ctrCircle
ann_Plus = RO.CanvasUtil.ctrPlus
ann_X = RO.CanvasUtil.ctrX

class Annotation:
	"""Image annotation.

	Designed to allow easy redraw of the annotation when the image is zoomed.

	Inputs:
	- gim	GrayImageWdg widget
	- annType	One of the ann_ constants, or any function that draws an annotation
				and takes the following arguments by position:
				- cnv	see below
				- cnvPos	see below
				- rad	see below
				and by name:
				- tags	see below
				- any additional keyword supplied when creating this Annotation
	- cnv	canvas on which to draw the annotation
	- imPos	image position of center
	- rad	overall radius of annotation, in zoomed pixels.
			The visible portion of the annotation should be contained
			within this radius.
	- tags	0 or more tags for annotation; _AnnTag
			and a unique id tag will also be used as tags.
	- isImSize	is size (e.g. rad) in image pixels? else cnv pixels.
				If true, annotation is resized as zoom changes.
	**kargs		arguments for annType
	"""
	def __init__(self,
		gim,
		annType,
		imPos,
		rad,
		isImSize = True,
		tags = None,
	**kargs):
		self.gim = gim
		self.annType = annType

		self.imPos = imPos
		self.isImSize = isImSize
		self.holeRad = kargs.get("holeRad")
		if self.isImSize:
			# radius is in image units; put it in floating point now
			# and adjust for zoom factor when drawing it
			self.rad = float(rad)
			if self.holeRad != None:
				self.holeRad = float(self.holeRad)
		else:
			# radius is in canvas units
			# round it now and leave it alone later
			self.rad = int(round(rad))
			if self.holeRad != None:
				self.holeRad = int(round(self.holeRad))

		self.idTag = "_ann_%s" % id(self)
		if not tags:
			tags = ()
		else:
			tags = RO.SeqUtil.asSequence(tags)
		self.tags = (self.idTag, _AnnTag) + tuple(tags)
		self.kargs = kargs
		self.kargs["tags"] = self.tags
		self.draw()

	def draw(self):
		"""Draw the annotation.
		
		Warning: calling multiple times draws multiple copies.
		(Not an issue with GrayImageWdg because it tends to delete
		the canvas and start over when redrawing).
		"""
		cnvPos = self.gim.cnvPosFromImPos(self.imPos)
		if self.isImSize:
			# radius is in image units; adjust for zoom factor
			rad = int(round(self.rad * self.gim.zoomFac))
			if self.holeRad != None:
				kargs["holeRad"] = int(round(self.holeRad * self.gim.zoomFac))
		else:
			# radius is already in canvas units; leave it alone
			rad = self.rad

		return self.annType(
			self.gim.cnv,
			cnvPos[0],
			cnvPos[1],
			rad,
		**self.kargs)
	
	def delete(self):
		"""Delete the annotation from the canvas.
		"""
		self.gim.cnv.delete(self.idTag)
			
			
class GrayImageWdg(Tkinter.Frame):
	"""Display a grayscale image.
	
	Inputs:
	- master	parent widget
	- height	height of image portal (visible area)
	- width		applies of image portal (visible area)
	"""
	def __init__(self,
		master,
		height = 300,
		width = 300,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		# raw data array and attributes
		self.dataArr = None
		self.sortedDataArr = None
		self.dataDispMin = None
		self.dataDispMax = None
		
		# scaled data array and attributes
		self.scaledArr = None
		self.scaledIm = None
		self.scaleFuncOff = 0.0
		self.scaleFunc = None
		
		# displayed image attributes
		self.zoomFac = 1.0
		self.dispOffset = 0
		self.dispScale = 1.0
		self.imID = None
		self.visShape = (1.0, 1.0) # shape of area in which image can be displayed
		
		self.dispMinLevel = 0.0
		self.dispMaxLevel = 256.0
		
		# fields for drag-to-act
		self.dragStart = None
		self.dragRect = None
		
		# annotation dict;
		# key: a tuple of all tags used for the annotation
		# value: the annotation
		self.annDict = {}
		
		self.mode = _ModeNormal
		self.permMode = _ModeNormal
		
		# tool bar
		toolFrame = Tkinter.Frame(self)
		RO.Wdg.StrLabel(toolFrame, text="Zoom:").pack(side="left")
		self.currZoomWdg = RO.Wdg.FloatEntry(
			master = toolFrame,
			width = 4,
			defFormat = "%.2f",
			defValue = 1.0,
			defMenu = "default",
		)
		self.currZoomWdg.set(self.zoomFac)
		self.currZoomWdg.pack(side="left")
		self.currZoomWdg.bind("<Key-Return>", self.doZoomWdg)

		RO.Wdg.StrLabel(
			master = toolFrame,
			text = "Scale:",
		).pack(side = "left")
		self.scaleMenuWdg = RO.Wdg.OptionMenu(
			master = toolFrame,
			items = ("Linear", "ASinh 0.1", "ASinh 1", "ASinh 10"),
			defValue = "ASinh 0.1",
			width = 8,
			callFunc = self.doScaleMenu,
			helpText = "specify a scaling function",
		)
		self.scaleMenuWdg.pack(side = "left")
		self.rangeMenuWdg = RO.Wdg.OptionMenu(
			master = toolFrame,
			items = ("100%", "99.5%", "99%", "98%"),
			defValue = "99.5%",
			width = 5,
			callFunc = self.doRangeMenu,
			helpText = "range of scaled data relative to min/max",
		)
		self.rangeMenuWdg.pack(side="left")
		
		# try toolbar icons
		self.modeWdg = RO.Wdg.RadiobuttonSet(
			master = toolFrame,
			textList = (
				u"+",
				u"Z",
				u"L",
			),
			valueList = (
				_ModeNormal,
				_ModeZoom,
				_ModeLevel,
			),
			helpText = (
				"Default mode",
				"Drag to zoom",
				"Drag to adjust black and white levels",
			),
			indicatoron = False,
			width = 2,
			callFunc = self.setMode,
		)
		for b in self.modeWdg.getWdgSet():
			b.pack(side="left")
		toolFrame.pack(side="top", anchor="nw")
	
		# add current position and current value widgets
		posFrame = Tkinter.Frame(self)
		Tkinter.Label(posFrame, text="Position").pack(side="left")
		self.currPosWdg = RO.Wdg.StrLabel(posFrame)
		self.currPosWdg.pack(side="left")
		Tkinter.Label(posFrame, text="Value").pack(side="left")
		self.currValWdg = RO.Wdg.IntLabel(posFrame)
		self.currValWdg.pack(side="left")
		posFrame.pack(side="bottom", anchor="nw")
		
		# set up scrolling panel to display canvas
		self.scrollFrame = Tkinter.Frame(self, height=height, width=width)
		self.scrollFrame.grid_propagate(False)
		
		self.hsb = Tkinter.Scrollbar(
			self.scrollFrame,
			orient="horizontal",
			width = 10,
		)
		self.hsb.grid(row=1, column=0, sticky="ew")
		self._hscrollbar = self.hsb
		
		self.vsb = Tkinter.Scrollbar(
			self.scrollFrame,
			orient="vertical",
			width = 10,
		)
		self.vsb.grid(row=0, column=1, sticky="ns")

		self.cnv = Tkinter.Canvas(
			master = self.scrollFrame,
			cursor="crosshair",
			bd = 0,
			selectborderwidth = 0,
			highlightthickness = 0,
			xscrollcommand = self.hsb.set,
			yscrollcommand = self.vsb.set,
		)
		self.cnv.grid(row=0, column=0) #, sticky="nsew")
		self.hsb["command"] = self.cnv.xview
		self.vsb["command"] = self.cnv.yview

		self.scrollFrame.grid_rowconfigure(0, weight=1)
		self.scrollFrame.grid_columnconfigure(0, weight=1)
		
		self.scrollFrame.pack(side="top", expand=True, fill="both")
				
		bdWidth = 0
		for bdName in ("borderwidth", "selectborderwidth", "highlightthickness"):
			bdWidth += int(self.cnv[bdName])
		self.bdWidth = bdWidth
		self.cnvShape = (0,0)
		self.cnvWidth = 0
	
		# set up bindings
		self.cnv.bind("<Motion>", self._updCurrVal)
		self.hsb.bind("<Configure>", self._updVisShape)
		self.vsb.bind("<Configure>", self._updVisShape)
		
		# bindings for drag-to-zoom
		self.cnv.bind("<Button-2>", self.dragZoomStart)
		self.cnv.bind("<B2-Motion>", self.dragZoomContinue)
		self.cnv.bind("<ButtonRelease-2>", self.dragZoomEnd)
		self.cnv.bind("<Double-Button-2>", self.dragZoomReset)
		
		# bindings for adjusting black and white levels
		self.cnv.bind("<B3-Motion>", self.dragLevelContinue)
		self.cnv.bind("<Button-3>", self.dragLevelStart)
		self.cnv.bind("<ButtonRelease-3>", self.dragLevelEnd)
		self.cnv.bind("<Double-Button-3>", self.dragLevelReset)
		
		# bindings for mode-based control
		self.cnv.bind("<Button-1>", self.modeStart)
		self.cnv.bind("<B1-Motion>", self.modeContinue)
		self.cnv.bind("<ButtonRelease-1>", self.modeEnd)
		self.cnv.bind("<Double-Button-1>", self.modeReset)

		self.modeWdg.set(_ModeNormal)

	def setMode(self, wdg=None, isTemp=False):
		if isTemp:
			self.permMode = self.mode

		self.mode = self.modeWdg.getString()
		if self.mode == _ModeZoom:
			self.cnv["cursor"] = "icon"
		elif self.mode == _ModeLevel:
			self.cnv["cursor"] = "circle"
		elif self.mode == _ModeNormal:
			self.cnv["cursor"] = "crosshair"

	def modeStart(self, evt):
		"""Mouse down for current mode (whatever that might be).
		"""
		if self.mode == _ModeNormal:
			return
		elif self.mode == _ModeZoom:
			self.dragZoomStart(evt, isTemp = False)
		elif self.mode == _ModeLevel:
			self.dragLevelStart(evt, isTemp = False)
	
	def modeContinue(self, evt):
		if self.mode == _ModeNormal:
			return
		elif self.mode == _ModeZoom:
			self.dragZoomContinue(evt)
		elif self.mode == _ModeLevel:
			self.dragLevelContinue(evt)
	
	def modeEnd(self, evt):
		if self.mode == _ModeNormal:
			return
		elif self.mode == _ModeZoom:
			self.dragZoomEnd(evt, isTemp = False)
		elif self.mode == _ModeLevel:
			self.dragLevelEnd(evt, isTemp = False)
	
	def modeReset(self, evt):
		if self.mode == _ModeNormal:
			return
		elif self.mode == _ModeZoom:
			self.dragZoomReset(isTemp = False)
		elif self.mode == _ModeLevel:
			self.dragLevelReset(isTemp = False)			

	def addAnnotation(self, annType, imPos, rad, tags=None, isImSize=True, **kargs):
		"""Add an annotation.

		Inputs:
		- annType	One of the ann_ constants.
		- cnv	canvas on which to draw the annotation
		- imPos	image position of center
		- rad	overall radius of annotation, in zoomed pixels.
				The visible portion of the annotation should be contained
				within this radius.
		- tags	0 or more tags for annotation; _AnnTag
				and a unique id tag will also be used as tags.
		- isImSize	is radius in image pixels? else cnv pixels.
					If true, annotation is resized as zoom changes.
		**kargs: Additional arguments:
			- width: width of line
			- fill: color of line for ann_X and ann_Plus;
					color of middle of circle for ann_Circle
			- outline: color of line for ann_Circle
			- holeRad: radius of central hole (if any) for ann_X and ann_Plus
		
		Returns a unique id tag for use with removeAnnotaion.
		"""
		annObj = Annotation(
			gim = self,
			annType = annType,
			imPos = imPos,
			rad = rad,
			tags = tags,
			isImSize = isImSize,
		**kargs)
		self.annDict[annObj.tags] = annObj
		return annObj.idTag
	
	def applyRange(self, redisplay=True):
		"""Compute dispScale and dispOffset based on
		dispMin, dispMax, dispMaxLevel and dispMinLevel.
		"""
		minDisp = 0
		maxDisp = 245
		dispRange = maxDisp - minDisp

		self.dispScale = (self.dispMaxLevel - self.dispMinLevel) / dispRange
		self.dispOffset = self.dispMinLevel * float(self.dispScale) + minDisp
#		print "applyRange(%r); dispMinLevel=%s, dispMaxLevel=%s, dispOffset=%r; dispScale=%r" % (redisplay, self.dispMinLevel, self.dispMaxLevel, self.dispOffset, self.dispScale)
		if redisplay:
			self.tkIm.paste(self.scaledIm.point(self._dispFromScaled))

	def doRangeMenu(self, wdg=None, redisplay=True):
		"""Handle new selection from range menu."""
		strVal = self.rangeMenuWdg.getString()
		numVal = float(strVal[:-1]) / 100.0 # ignore % from end
		lowFrac = (1.0 - numVal) / 2.0
		highFrac = 1.0 - lowFrac
		dataLen = len(self.sortedData)
		lowInd = int(lowFrac * dataLen)
		highInd = int(highFrac * dataLen) - 1
		self.dataDispMin = self.sortedData[lowInd]
		self.dataDispMax = self.sortedData[highInd]
		
#		print "doRangeMenu; strVal=%r; numVal=%s; lowFrac=%s; highFrac=%s, dataLen=%s, lowInd=%s, highInd=%s, dataDispMin=%s, dataDispMax=%s" % (strVal, numVal, lowFrac, highFrac, dataLen, lowInd, highInd, self.dataDispMin, self.dataDispMax)
		self.redisplay()
		
	def doScaleMenu(self, *args):
		"""Handle new selection from scale menu."""
		strVal = self.scaleMenuWdg.getString()
		strList = strVal.split(None)
		funcName = "scale" + strList[0]
		args = [float(arg) for arg in strList[1:]]
		try:
			func = getattr(self, funcName)
		except AttributeError:
			raise RuntimeError("Bug! No function named %r" % (funcName,))
		func(*args)
	
	def doZoomWdg(self, wdg):
		"""Set zoom to the value typed in the current zoom widget.
		"""
		newZoomFac = self.currZoomWdg.getNum()
		self.setZoomFac(newZoomFac)
	
	def dragLevelContinue(self, evt):
		"""Adjust black and white levels based on position of cursor
		relative to the center of image portal.
		"""
		ctr = [sh/2.0 for sh in self.visShape]
		dx = evt.x - ctr[0]
		dy = ctr[1] - evt.y
		self.dispMinLevel = 0 + dx
		self.dispMaxLevel = 256 + dy
		self.applyRange(redisplay=True)
	
	def dragLevelEnd(self, evt, isTemp=True):
		if isTemp:
			self.modeWdg.set(self.permMode)

	def dragLevelReset(self, evt=None, isTemp=True):
		"""Reset black and white levels to their default values.
		"""
		self.dispMinLevel = 0
		self.dispMaxLevel = 256
		self.applyRange(redisplay=True)
		
		if isTemp:
			self.modeWdg.set(self.permMode)
		
	def dragLevelStart(self, evt, isTemp=True):
		if isTemp:
			self.modeWdg.set(_ModeLevel, isTemp=True)

	def dragZoomCancel(self, evt=None):
		self.cnv.delete(self.dragRect)
		self.dragStart = None
		self.dragRect = None
	
	def dragZoomContinue(self, evt):
		if self.dragStart == None:
			return

		newPos = self.cnvPosFromEvt(evt)
		self.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
	
	def dragZoomEnd(self, evt, isTemp=True):
		if self.dragStart == None:
			return

		startPos = self.dragStart
		endPos = self.cnvPosFromEvt(evt)
		
		self.dragZoomCancel()

		deltaPos = num.subtract(endPos, startPos)
		ctrCnvPos = num.add(startPos, deltaPos/2.0)
		
		if deltaPos[0] > 0 and deltaPos[1] > 0:
			# zoom in
			newZoomFac = _MaxZoomFac
			for ii in range(2):
				desZoomFac = self.visShape[ii] * self.zoomFac / float(max(1, abs(deltaPos[ii])))
				newZoomFac = min(desZoomFac, newZoomFac)
#				print "ii=%s, desZoomFac=%s; newZoomFac=%s" % (ii, desZoomFac, newZoomFac)
#			print "newZoomFac=%s" % (newZoomFac,)
			self.setZoomFac(newZoomFac, ctrCnvPos)
			
		elif deltaPos[0] < 0 and deltaPos[1] < 0:
			# zoom out
			newZoomFac = _MaxZoomFac
			for ii in range(2):
				desZoomFac = abs(deltaPos[ii]) * self.zoomFac / float(self.visShape[ii])
				newZoomFac = min(desZoomFac, newZoomFac)
#				print "ii=%s, desZoomFac=%s; newZoomFac=%s" % (ii, desZoomFac, newZoomFac)
#			print "newZoomFac=%s; minZoomFac=%s" % (newZoomFac, self.getFitZoomFac())
			newZoomFac = max(newZoomFac, self.getFitZoomFac())

			self.setZoomFac(newZoomFac, ctrCnvPos)
		
		if isTemp:
			self.modeWdg.set(self.permMode)
	
	def dragZoomReset(self, wdg=None, isTemp=True):
		"""Zoom so entire image is visible in image portal.
		"""
		newZoomFac = self.getFitZoomFac()
		self.setZoomFac(newZoomFac)
		
		if isTemp:
			self.modeWdg.set(self.permMode)

	def dragZoomStart(self, evt, isTemp=True):
		self.dragStart = self.cnvPosFromEvt(evt)
		self.dragRect = self.cnv.create_rectangle(
			self.dragStart[0], self.dragStart[1], self.dragStart[0], self.dragStart[1],
			outline = "green",
			tags = _DragRectTag,
		)
		
		if isTemp:
			self.modeWdg.set(_ModeZoom, isTemp=True)
	
	def getFitZoomFac(self):
		"""Return the largest zoom factor that makes the image fit.
		Include room for a 1-pixel border around the edge
		so it's obvious that the image is all visible.
		"""
		fitZoomFac = _MaxZoomFac
		for ii in range(2):
			desZoomFac = (self.visShape[ii]-2) / float(self.dataArr.shape[ii])
			fitZoomFac = min(desZoomFac, fitZoomFac)
#			print "arrShape=%s, desZoomFac=%s, fitZoomFac=%s" % (self.dataArr.shape, desZoomFac, fitZoomFac)
		return fitZoomFac
	
	def isNormalMode(self):
		return self.mode == _ModeNormal
	
	def redisplay(self):
		"""Starting from the data array, redisplay the data.
		"""
		dataShapeXY = self.dataArr.shape[::-1]
		
		# offset so minimum display value = scaling function minimum input
		# note: this form of equation reuses the input array for output
		num.subtract(self.dataArr, float(self.dataDispMin), self.scaledArr)
		
		offsetDispRange = [0.0, float(self.dataDispMax - self.dataDispMin)]
		
		# apply scaling function, if any
		if self.scaleFunc:
			self.scaledArr = self.scaleFunc(self.scaledArr)
			if self.scaledArr.type() == num.Float64:
#				print "damn numarray, anyway"
				self.scaledArr = self.scaledArr.astype(num.Float32)
			scaledMin, scaledMax = self.scaleFunc(offsetDispRange)
		else:
			scaledMin, scaledMax = offsetDispRange
		# linearly offset and stretch data so that
		# dataDispMin maps to 0 and dataDispMax maps to 256
		# (note: for most functions scaledMin is already 0
		# so the offset is superfluous)
		adjOffset = scaledMin		
		adjScale = 256.0 / (scaledMax - scaledMin)
#		print "apply adjOffset=%s; adjScale=%s" % (adjOffset, adjScale)
		self.scaledArr -= adjOffset
		self.scaledArr *= adjScale
		
		# create image with scaled data
		self.scaledIm = Image.frombuffer("F", dataShapeXY, self.scaledArr.tostring())

		# apply zoom
		if self.zoomFac != 1.0:
#			print "zoom factor =", self.zoomFac
			imShapeXY = [int(self.zoomFac * dim) for dim in dataShapeXY]
			self.scaledIm = self.scaledIm.resize(imShapeXY)
		else:
			imShapeXY = dataShapeXY
		
		# compute and apply current range
		self.applyRange(redisplay=False)
		currIm = self.scaledIm.point(self._dispFromScaled)
		
		# create PhotoImage objects for display on canvas
		# (must keep a reference, else it vanishes, plus the
		# local reference can be used for fast brightness/contrast changes)
		self.tkIm = ImageTk.PhotoImage(currIm)

		# delete currently displayedimage, if any
		if self.imID:
			self.cnv.delete(self.imID)
		
		# delete current annotations, if any
		self.cnv.delete(_AnnTag)
		
		# set canvas size; save the height for use elsewhere
		# because querying cnv can give the wrong answer if asked too soon!
		self.cnv.configure(
			width = imShapeXY[0],
			height = imShapeXY[1],
		)
		self.cnvShape = imShapeXY

		# update scroll region so scroll bars work
		self.cnv.configure(
			scrollregion = (0, 0, imShapeXY[0], imShapeXY[1]),
		)

		# display image
		self.imID = self.cnv.create_image(
			self.bdWidth, self.bdWidth,
			anchor="nw",
			image=self.tkIm,
		)
		
		# display annotations
		for ann in self.annDict.itervalues():
			ann.draw()

	def nullHandler(self, evt):
		"""Ignore an event."""
		return

	def removeAnnotation(self, tag):
		"""Remove all annotations (if any) with the specified tag.
		"""
		newDict = {}
		for tags, ann in self.annDict.iteritems():
			if tag in tags:
				ann.delete()
			else:
				newDict[tags] = ann
		self.annDict = newDict
	
	def scaleASinh(self, scaleFac=0.1):
		"""Apply an arcsinh scale
		
		Note: this needs tuning parameters, which are just kludged in for now.
		f(x) = arcsinh(scale [x - m])
		
		I don't yet set m. I might be able to add it, I'm just not sure
		it's useful given how I already stretch data
		"""
		def arcsinh(x):
			return num.arcsinh(num.multiply(x, scaleFac))
		self.setScaleFunc(arcsinh)
	
	def scaleLinear(self):
		"""Restore linear scaling and redisplay.
		"""
		self.setScaleFunc(None)

	def scaleSqrt(self):
		"""Apply a square root scale
		"""
		self.setScaleFunc(num.sqrt)
	
	def scrollToCtr(self, cnvPos):
		"""Adjust the scroll to center a given position
		(as best you can).
		"""
		funcSet = (
			self.cnv.xview_moveto,
			self.cnv.yview_moveto,
		)
		for ii in range(2):
			startCnvPos = cnvPos[ii] - (self.visShape[ii] / 2.0)
			startFrac = startCnvPos / float(self.cnvShape[ii])
#			print "ii=%s, cnvPos=%s, cnvShape=%s, startCnvPos=%s, startFrac=%s" % (ii, cnvPos[ii], self.cnvShape[ii], startCnvPos, startFrac)
			startFrac = min(1.0, max(0.0, startFrac))
			funcSet[ii](startFrac)	
	
	def setScaleFunc(self, func):
		"""Set a new scale function and redisplay.
		
		scaled value = func(data - dataMin)
		"""
		self.scaleFunc = func
#		print "scaleFunc = %r" % (self.scaleFunc)
		self.redisplay()
	
	def setZoomFac(self, zoomFac, cnvPos = None):
		"""Set the zoom factor.
		
		Inputs:
		- zoomFac	the desired new zoom factor (can be float);
					values > _MaxZoomFac are silently truncated
		- cnvPos	the desired center, in canvas x,y pixels;
					if omitted, the center of the visible image is used
		
		0.5 shows every other pixel, starting with the 2nd pixel
		1 shows the image at original size
		2 shows each pixel 2x as large as it should be
		etc.
		"""
		oldZoomFac = self.zoomFac
		self.zoomFac = float(zoomFac)
		if self.zoomFac != oldZoomFac:
			self.currZoomWdg.set(zoomFac)
			self.redisplay()
			
		if cnvPos == None:
			visCtr = num.divide(self.visShape, 2.0)
			cnvPos = self.cnvPosFromVisPos(visCtr)
		newCnvPos = num.multiply(cnvPos, zoomFac / float(oldZoomFac))
#		print "oldZoomFac=%s, newZoomFac=%s, cnvPos=%s, newCnvPos=%s" % (oldZoomFac, self.zoomFac, cnvPos, newCnvPos)
		self.scrollToCtr(newCnvPos)
		
	def showArr(self, arr):
		"""Specify an array to display.
		The data is initially scaled from minimum to maximum
		
		To do:
		- preserve existing zoom
		"""
		# delete current image, if any
		if self.imID:
			self.cnv.delete(self.imID)

		# display new image
		self.dataArr = num.array(arr)
		if arr.type() in (num.Complex32, num.Complex64):
			raise TypeError("cannot handle data of type %s" % arr.type())
		
		self.sortedData = num.ravel(self.dataArr.astype(num.Float32))
		self.sortedData.sort()

		# scaledArr gets computed in place by redisplay;
		# for now just allocate space of the appropriate type
		self.scaledArr = num.zeros(shape=self.dataArr.shape, type=num.Float32)
		
		self.doRangeMenu()

		self.redisplay()


	def _dispFromScaled(self, val):
		"""Convert a scaled value or image to a display value or image
		using the current zero and scale.
		Note: the form of the equation must strictly be val * scale + offset
		with no variation allowed, else this equation will not work with images.
		"""
#		print "_dispFromScaled(%r); scale=%r; offset=%r" % (val, self.dispScale, self.dispOffset)
		return val * self.dispScale + self.dispOffset
	
	def _updCurrVal(self, evt):
		"""Show the value that the mouse pointer is over.
		"""
		cnvPos =  self.cnvPosFromEvt(evt)
		imPos = self.imPosFromCnvPos(cnvPos)
		try:
			arrIJ = self.arrIJFromImPos(imPos)
		except IndexError:
			return
		
#		print "evtxy=%s; cnvPos=%s; ds9pos=%s; arrIJ=%s" %  ((evt.x, evt.y), cnvPos, imPos, arrIJ)
				
		val = self.dataArr[arrIJ[0], arrIJ[1]]
		self.currPosWdg.set("%.1f, %.1f" % (imPos[0], imPos[1]))
		self.currValWdg.set(val)
	
	def _updVisShape(self, evt=None):
		"""Update shape of region that is used to display the image.
		"""
		self.visShape = (
			self.hsb.winfo_width(),
			self.vsb.winfo_height(),
		)
#		print "self.visShape=%s" % (self.visShape,)
	
	def cnvPosFromImPos(self, imPos):
		"""Convert image pixel position to canvas position
		
		The image pixel position convention is:
		- 0,0 is the lower left corner of the lower left image pixel
		- 0.5, 0.5 is the center of the lower left image pixel
		
		The returned position is floating point and should be rounded
		before being applied to draw anything.
		"""
		# cnvLLPos is the canvas position relative to the
		# lower left corner of the image (with borders removed)
		# and with +y increasing upwards
		cnvLLPos = [(imElt * float(self.zoomFac)) - 0.5 for imElt in imPos]
		
		cnvPos = [
			cnvLLPos[0] + self.bdWidth,
			self.cnvShape[1] - self.bdWidth - cnvLLPos[1] - 1,
		]
		return cnvPos
	
	def arrIJFromImPos(self, imPos):
		"""Convert an image position to an the corresponding array index.
		Raise RangeError if out of range.
		"""
		arrIJ = [int(math.floor(imPos[ii])) for ii in (1, 0)]
		if not (0 <= arrIJ[0] < self.dataArr.shape[0] \
			and 0 <= arrIJ[1] < self.dataArr.shape[1]):
			raise IndexError("%s out of range" % arrIJ)
		return arrIJ
	
	def imPosFromCnvPos(self, cnvPos):
		"""Convert canvas position to image pixel position.
		
		See cnvPosFromImPos for details.
		"""
		cnvLLPos = (
			cnvPos[0] - self.bdWidth,
			self.cnvShape[1] - self.bdWidth - cnvPos[1] - 1,
		)
		
		imPos = [(cnvLL + 0.5) / float(self.zoomFac) for cnvLL in cnvLLPos]
		
		return imPos
	
	def cnvPosFromEvt(self, evt):
		"""Computed canvas x,y from an event.

		Note: event position is relative to the upper-left *visible*
		portion of the canvas. It matches the canvas position
		if and only if the upper-left corner of the canvas is visible.
		"""
		return self.cnvPosFromVisPos((evt.x, evt.y))

	def cnvPosFromVisPos(self, visPos):
		"""Computed canvas x,y from visible position,
		e.g. that position returned by an event.

		Note: visible is relative to the upper-left *visible*
		portion of the canvas. It matches the canvas position
		if and only if the upper-left corner of the canvas is visible.
		"""
		
		return (
			self.cnv.canvasx(visPos[0]),
			self.cnv.canvasy(visPos[1]),
		)
	

if __name__ == "__main__":
	import pyfits
	import RO.DS9
	root = RO.Wdg.PythonTk()
	root.geometry("400x400")

	fileName = 'gimg0128.fits'

	testFrame = GrayImageWdg(root)
	testFrame.pack(expand="yes", fill="both")

	if not fileName:
		arrSize = 255
		
		arr = num.arange(arrSize**2, shape=(arrSize,arrSize))
		# put marks at center
		ctr = (arrSize - 1) / 2
		arr[ctr] = 0
		arr[:,ctr] = 0
	else:
		im = pyfits.open(fileName)
		arr = im[0].data

	testFrame.showArr(arr)
	
#	ds9 = RO.DS9.DS9Win()
#	ds9.showArray(arr)
	
	root.mainloop()


