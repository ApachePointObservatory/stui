#!/usr/local/bin/python
"""Code to display a grayscale image.

This is a work in progress as I attempt to emulate the
most important (to me) features of ds9.

Required packages:
- numarray
- PIM

Basic idea:
dataArr = input data converted to floating point
scaledArr = dataArr with a suitable offset, a suitable minimum cut,
	and multiplied by the desired scaling function.
	the offset is chosen such that the scaling function can safely be computed
	(and if possible, such that the resulting min value is 0)
scaledIm = image version of scaledArr with appropriate zoom factor
currIm = 8-bit display image = scaledIm with range applied
    to get display range of 0-256;
	the range can be quickly re-applied from scaledIm
	(using paste and the point function), which is why
	I keep a scaledIm around as well as currIm.

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
- Try asinh function (suggested by Robert Lupton)
- Consider faster zoom in function -- just display a piece of the array --
  but this would be messy.
- Can I apply my own LUT more efficiently than recomputing the scaling function
  for each pixel? I'd love to use an LUT to control data display, but its use
  in PyImage appears to be restricted to a useless subset of image types.
- Add more support for annotations, i.e. built in classes
  that add X, +, circle and square. Possibly also ellipses and lines.
- Highlight saturated pixels, e.g. in red
- Implement right-drag to change brightness and contrast?
- Implement histogram equalization.
- Highlight saturated pixels in red (see PyImage and mixing)
- Allow color preference variables for annotation colors
  (and auto-update colors).
- Add pan with mouse or perhaps emulate ds9 for panning and ditch the scrollbars.
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
		self.scaleFuncMinInput = 0.0
		self.scaleFunc = None
		self.scaledDispMin = None
		self.scaledDispMax = None
		
		# displayed image attributes
		self.zoomFac = 1.0
		self.dispOffset = 0
		self.dispScale = 1.0
		self.imID = None
		
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
			items = ("Linear", "Log", "Square", "Sqrt"),
			defValue = "Linear",
			width = 6,
			callFunc = self.doScaleMenu,
			helpText = "specify a scaling function",
		)
		self.scaleMenuWdg.pack(side = "left")
		self.rangeMenuWdg = RO.Wdg.OptionMenu(
			master = toolFrame,
			items = ("100%", "99.5%", "99%", "98%"),
			defValue = "99.5%",
			width = 4,
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
		self.cnvHeight = 0
	
		# set up bindings
		self.cnv.bind("<Motion>", self._updCurrVal)
	
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
		funcName = "scale" + strVal.replace(" ", "")
		try:
			func = getattr(self, funcName)
		except AttributeError:
			raise RuntimeError("Bug! No function named %r" % (funcName,))
		func()
	
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
	
	def redisplay(self):
		"""Starting from the data array, redisplay the data.
		"""
		dataShapeXY = self.dataArr.shape[::-1]
		
		# offset so minimum display value = scaling function minimum input
		# note: this form of equation reuses the input array for output
		offset = self.scaleFuncMinInput - self.dataDispMin
		num.add(self.dataArr, float(offset), self.scaledArr)
		num.maximum(self.scaledArr, float(self.scaleFuncMinInput), self.scaledArr)
		
		offsetDispRange = [self.dataDispMin + offset, self.dataDispMax + offset]
		
		# apply scaling function, if any
		if self.scaleFunc:
			self.scaledArr = self.scaleFunc(self.scaledArr)
			if self.scaledArr.type() == num.Float64:
#				print "damn numarray, anyway"
				self.scaledArr = self.scaledArr.astype(num.Float32)
			self.scaledDispMin, self.scaledDispMax = self.scaleFunc(offsetDispRange)
		else:
			self.scaledDispMin, self.scaledDispMax = offsetDispRange
#		print "self.scaledDispMin = %r; self.scaledDispMax = %r" % (self.scaledDispMin, self.scaledDispMax)
		
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
		self.setRange(self.scaledDispMin, self.scaledDispMax, redisplay=False)
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
		self.cnvHeight = imShapeXY[1]

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
	
	def scaleLinear(self):
		"""Restore linear scaling and redisplay.
		"""
		self.setScaleFunc(None)

	def scaleLog(self):
		"""Apply a natural log scale.
		"""
		self.setScaleFunc(num.log, minInput = 1.0)
	
	def scaleSquare(self):
		"""Apply a square scale
		"""
		def squareFunc(arr):
			return num.power(arr, 2)
		self.setScaleFunc(squareFunc)
	
	def scaleSqrt(self):
		"""Apply a square root scale
		"""
		self.setScaleFunc(num.sqrt)
	
	def setRange(self, minVal, maxVal, redisplay=True):
		"""Specify the black and white values for the scaled data.
		"""
		self.dispScale = 256.0 / max(float(maxVal - minVal), 0.001)
		self.dispOffset = - minVal * float(self.dispScale)
#		print "setRange(%r, %r); dispOffset=%r; dispScale=%r" % (minVal, maxVal, self.dispOffset, self.dispScale)
		if redisplay:
			self.tkIm.paste(self.scaledIm.point(self._dispFromScaled))
	
	def setScaleFunc(self, func, minInput=0.0):
		"""Set a new scale function and redisplay.
		
		scaled value = func(max(minInput, data - offset))
		
		where offset is determined by range
		
		The default offset is the minimum data value.
		"""
		self.scaleFuncMinInput = float(minInput)
		self.scaleFunc = func
#		print "scaleFunc = %r; scaleFuncMinInput = %r" % (self.scaleFunc, self.scaleFuncMinInput)
		self.redisplay()
	
	def setZoomFac(self, zoomFac):
		"""Set the zoom factor.
		
		0.5 shows every other pixel, starting with the 2nd pixel
		1 shows the image at original size
		2 shows each pixel 2x as large as it should be
		etc.
		"""
		oldZoomFac = self.zoomFac
		self.zoomFac = float(zoomFac)
		
		oldScrollGet = (
			self.hsb.get(),
			self.vsb.get(),
		)
		
		self.redisplay()
		
		if not oldZoomFac:
			print "no old zoom factor"
			return

		funcSet = (
			self.cnv.xview_moveto,
			self.cnv.yview_moveto,
		)
		for ii in (0,1):
			oldStart, oldEnd = oldScrollGet[ii]
			ctr = (oldStart + oldEnd) / 2.0
			oldSize = oldEnd - oldStart
			newSize = min(oldSize * oldZoomFac / float(self.zoomFac), 1.0)
			newStart = ctr - (newSize / 2.0)
#			print "ii=%s, oldStart=%s, oldSize=%s, ctr=%s, newSize=%s, newStart=%s" % (ii, oldStart, oldSize, ctr, newSize, newStart)
			funcSet[ii](newStart)
		
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
			self.cnvHeight - self.bdWidth - cnvLLPos[1] - 1,
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
			self.cnvHeight - self.bdWidth - cnvPos[1] - 1,
		)
		
		imPos = [(cnvLL + 0.5) / float(self.zoomFac) for cnvLL in cnvLLPos]
		
		return imPos
	
	def cnvPosFromEvt(self, evt):
		"""Computed canvas x,y from an event.

		Note: event position is relative to the upper-right *visible*
		portion of the canvas. It matches the canvas position
		if and only if the upper-left corner of the canvas is visible.
		"""
		
		return (
			self.cnv.canvasx(evt.x),
			self.cnv.canvasy(evt.y),
		)
	

if __name__ == "__main__":
	import RO.DS9
	root = RO.Wdg.PythonTk()

	testFrame = GrayImageWdg(root)
	testFrame.pack(expand="yes", fill="both")
	arrSize = 255
	
	arr = num.arange(arrSize**2, shape=(arrSize,arrSize))
	# put marks at center
	ctr = (arrSize - 1) / 2
	arr[ctr] = 0
	arr[:,ctr] = 0
	xwid, ywid = arr.shape[1], arr.shape[0]
	testFrame.showArr(arr)
	
#	ds9 = RO.DS9.DS9Win()
#	ds9.showArray(arr)
	
	root.mainloop()


