#!/usr/local/bin/python
"""Code to display a grayscale image.

This attempts to emulate some of the more important features of ds9,
while minimizing controls and the space used by controls and status displays.

Required packages:
- numarray
- PIM

Mouse Gestures:
- control-drag left/right to adjust what is displayed as black
  (the center being 0)
- control-drag up/down to adjust what is displayed as white
  (the center is 256)
- double-control-click to restore normal black and white levels

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
- Try a drag-pan function to replace the scrollbars.

Maybe Do:
- Consider faster zoom in function and panning. Simplest is to copy ds9 and only display a portion
  of the image instead of all of it (the slowest part of zooming in is displaying a large image).
- Add more annotations: rectangle, line, ellipse, perhaps polygon.
- Implement histogram equalization.
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
2005-02-16 ROwen	Transitioning to improved zoom model, but with lots of work to do.
					At this point click-drag UR->LL will zoom in on the selected region.
					Still to do: make click not fail (make it zoom to fit?).
					Make click-drag UR->LL zoom out. Make other click-drags
					do something sensible -- e.g. be ignored or zoom or ???.
					Ditch old zoom controls and display current zoom factor.
					Ditch scroll bars? Implement a different pan?
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
	- doResize	resize object when zoom factor changes?
	**kargs		arguments for annType
	"""
	def __init__(self,
		gim,
		annType,
		imPos,
		rad,
		tags = None,
		doResize = True,
	**kargs):
		self.gim = gim
		self.annType = annType

		if doResize:
			rad = rad / float(gim.zoomFac)
		self.imPos = imPos
		self.unzRad = float(rad)

		self.idTag = "_ann_%s" % id(self)
		if not tags:
			tags = ()
		else:
			tags = RO.SeqUtil.asSequence(tags)
		self.tags = (self.idTag, _AnnTag) + tuple(tags)
		self.doResize = doResize
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
		if self.doResize:
			rad = self.unzRad * self.gim.zoomFac
		else:
			rad = self.unzRad
		rad = int(round(rad))
			
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
	
	Warning: under construction!
	"""
	def __init__(self,
		master,
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
		
		self.dispMinLevel = 0.0
		self.dispMaxLevel = 256.0
		
		# fields for drag-to-act
		self.dragStart = None
		self.dragRect = None
		
		# annotation dict;
		# key: a tuple of all tags used for the annotation
		# value: the annotation
		self.annDict = {}
		
		# tool bar
		toolFrame = Tkinter.Frame(self)
		RO.Wdg.StrLabel(toolFrame, text="Zoom:").pack(side="left")
		self.zoomMenuWdg = RO.Wdg.OptionMenu(
			master = toolFrame,
			items = ("1/16", "1/8", "1/4", "1/2", "1", "2", "4"),
			defValue = "1",
			callFunc = self.doZoomMenu,
		)
		self.zoomMenuWdg.pack(side="left")
		self.zoomOutWdg = RO.Wdg.Button(
			master = toolFrame,
			text = "-",
			callFunc = self.doZoomOut,
		)
		self.zoomOutWdg.pack(side="left")
		self.zoomInWdg = RO.Wdg.Button(
			master = toolFrame,
			text = "+",
			callFunc = self.doZoomIn,
		)
		self.zoomInWdg.pack(side="left")
		
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
		self.scrollFrame = Tkinter.Frame(self)
		
		self.hsb = Tkinter.Scrollbar(self.scrollFrame, orient="horizontal")
		self.hsb.grid(row=1, column=0, sticky="ew")
		self._hscrollbar = self.hsb
		
		self.vsb = Tkinter.Scrollbar(self.scrollFrame, orient="vertical")
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
		
		self.cnv.bind("<Control-B1-Motion>", self.doAdjLevels)
		self.cnv.bind("<Control-Button-1>", self.nullHandler)
		self.cnv.bind("<Control-Double-Button-1>", self.resetLevels)
		
		# try drag-to-zoom
		self.cnv.bind("<Button-1>", self.startDragToZoom)
		self.cnv.bind("<B1-Motion>", self.continueDragToZoom)
		self.cnv.bind("<ButtonRelease-1>", self.endDragToZoom)
	
	def startDragToZoom(self, evt):
		self.dragStart = self.cnvPosFromEvt(evt)
		self.dragRect = self.cnv.create_rectangle(
			self.dragStart[0], self.dragStart[1], self.dragStart[0], self.dragStart[1],
			outline = "green",
			tags = _DragRectTag,
		)
	
	def continueDragToZoom(self, evt):
		newPos = self.cnvPosFromEvt(evt)
		self.cnv.coords(self.dragRect, self.dragStart[0], self.dragStart[1], newPos[0], newPos[1])
	
	def endDragToZoom(self, evt):
		startPos = self.dragStart
		endPos = self.cnvPosFromEvt(evt)
		deltaPos = num.subtract(endPos, startPos)
		ctrCnvPos = num.add(startPos, deltaPos/2.0)

		self.cnv.delete(self.dragRect)
		self.dragStart = None
		self.dragRect = None
		
		# compute new zoom factor
		visShape = (
			self.hsb.winfo_width(),
			self.vsb.winfo_height(),
		)
		newZoomFac = _MaxZoomFac
		for ii in range(2):
			desZoomFac = visShape[ii] * self.zoomFac / deltaPos[ii]
			newZoomFac = min(desZoomFac, newZoomFac)
#			print "visShape=%s, desZoomFac=%s" % (visShape, desZoomFac)
		self.setZoomFac(newZoomFac, ctrCnvPos)
	
	def addAnnotation(self, annType, imPos, rad, tags=None, doResize=True, **kargs):
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
		- doResize	resize object when zoom factor changes?
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
			doResize = doResize,
		**kargs)
		self.annDict[annObj.tags] = annObj
		return annObj.idTag
	
	def applyRange(self, redisplay=True):
		"""Compute dispScale and dispOffset based on
		dispMin, dispMax, dispMaxLevel and dispMinLevel.
		"""

		self.dispScale = (self.dispMaxLevel - self.dispMinLevel) / 256.0
		self.dispOffset = self.dispMinLevel * float(self.dispScale)
#		print "applyRange(%r); dispMinLevel=%s, dispMaxLevel=%s, dispOffset=%r; dispScale=%r" % (redisplay, self.dispMinLevel, self.dispMaxLevel, self.dispOffset, self.dispScale)
		if redisplay:
			self.tkIm.paste(self.scaledIm.point(self._dispFromScaled))
	
	def doAdjLevels(self, evt):
		"""Adjust black and white levels based on position of cursor
		relative to the center of the canvas.
		"""
		ctr = [sh/2.0 for sh in self.cnvShape]
		dx = evt.x - ctr[0]
		dy = ctr[1] - evt.y
		self.dispMinLevel = 0 + dx
		self.dispMaxLevel = 256 + dy
		self.applyRange(redisplay=True)

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
	
	def doZoomMenu(self, *args):
		"""Handle new selection from zoom menu."""
		strVal = self.zoomMenuWdg.getString()
		valueList = strVal.split("/")
		if len(valueList) > 1:
			zoomFac = float(valueList[0]) / float(valueList[1])
		else:
			zoomFac = int(valueList[0])
		self.setZoomFac(zoomFac)
		
		# enable or disable zoom in/out widgets as appropriate
		if strVal == self.zoomMenuWdg._items[0]:
			self.zoomInWdg["state"] = "normal"
			self.zoomOutWdg["state"] = "disabled"
		elif strVal == self.zoomMenuWdg._items[-1]:
			self.zoomInWdg["state"] = "disabled"
			self.zoomOutWdg["state"] = "normal"
		else:
			self.zoomInWdg["state"] = "normal"
			self.zoomOutWdg["state"] = "normal"
	
	def doZoomIn(self, *args):
		"""Zoom in"""
		valList = self.zoomMenuWdg._items
		currInd = self.zoomMenuWdg.getIndex()
		if currInd == None:
			return
		if currInd + 1 >= len(valList):
			return

		newVal = valList[currInd + 1]
		self.zoomMenuWdg.set(newVal)

	def doZoomOut(self, *args):
		"""Zoom out"""
		valList = self.zoomMenuWdg._items
		currInd = self.zoomMenuWdg.getIndex()
		if currInd == None:
			return
		if currInd <= 0:
			return

		newVal = valList[currInd - 1]
		self.zoomMenuWdg.set(newVal)
	
	def doZoomToFit(self, *args):
		"""Zoom so that the entire image is visible."""
		visShape = (
			self.hsb.winfo_width(),
			self.vsb.winfo_height(),
		)
		minZoomFac = _MaxZoomFac
		for ii in range(2):
			desZoomFac = visShape[ii] / float(self.dataArr.shape[ii])
			minZoomFac = min(desZoomFac, minZoomFac)
#			print "visShape=%s, arrShape=%s, desZoomFac=%s, minZoomFac=%s" % (visShape, self.dataArr.shape, desZoomFac, minZoomFac)
		self.setZoomFac(minZoomFac)
	
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

	def resetLevels(self, evt=None):
		"""Reset black and white levels to their default values.
		"""
		self.dispMinLevel = 0
		self.dispMaxLevel = 256
		self.applyRange(redisplay=True)
	
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
	
	def setScaleFunc(self, func):
		"""Set a new scale function and redisplay.
		
		scaled value = func(data - dataMin)
		"""
		self.scaleFunc = func
#		print "scaleFunc = %r" % (self.scaleFunc)
		self.redisplay()
	
	def scrollToCtr(self, cnvPos):
		"""Adjust the scroll to center a given position
		(as best you can).
		"""
		visShape = (
			self.hsb.winfo_width(),
			self.vsb.winfo_height(),
		)
		funcSet = (
			self.cnv.xview_moveto,
			self.cnv.yview_moveto,
		)
		for ii in range(2):
			startCnvPos = cnvPos[ii] - (visShape[ii] / 2.0)
			startFrac = startCnvPos / float(self.cnvShape[ii])
#			print "ii=%s, cnvPos=%s, cnvShape=%s, visShape=%s, startCnvPos=%s, startFrac=%s" % (ii, cnvPos[ii], self.cnvShape[ii], visShape[ii], startCnvPos, startFrac)
			startFrac = min(1.0, max(0.0, startFrac))
			funcSet[ii](startFrac)	
	
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
		
		if not oldZoomFac:
#			print "no old zoom factor"
			return

		funcSet = (
			self.cnv.xview_moveto,
			self.cnv.yview_moveto,
		)
		if cnvPos == None:
			visShape = (
				self.hsb.winfo_width(),
				self.vsb.winfo_height(),
			)
			visCtr = num.divide(visShape, 2.0)
			cnvPos = self.cnvPosFromVisPos(visCtr)
		
		newCnvPos = num.multiply(cnvPos, zoomFac / float(oldZoomFac))
#		print "oldZoomFac=%s, newZoomFac=%s, cnvPos=%s, newCnvPos=%s" % (oldZoomFac, self.zoomFac, cnvPos, newCnvPos)
		
		self.redisplay()

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
		self.currPosWdg.set("%s, %s" % (imPos[0], imPos[1]))
		self.currValWdg.set(val)
	
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


