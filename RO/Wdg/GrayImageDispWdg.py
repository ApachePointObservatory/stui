#!/usr/local/bin/python
"""Code to display a grayscale image.

This is a work in progress as I attempt to emulate the
most important (to me) features of ds9.

Required packages:
- numarray
- PIM

Basic idea:
dataArr = input data converted to floating point
scaledArr = dataArr with a suitable offset
	and multiplied by a scaling function
	the offset is chosen such that the resulting min value is 0
scaledIm = image version of scaledArr with appropriate zoom factor
currIm = 8-bit display image = scaledIm with range applied
    to get display range of 0-256;
	the range can be quickly re-applied from scaledIm
	(using paste and the point function), which is why
	I keep a scaledIm around as well as currIm.

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
- Zoom should try to preserve pos of ctr pixel, if possible.
- Implement right-drag to change brightness and contrast.
- Implement histogram equalization.
- If possible, highlight saturated pixels in red
  (see PyImage and mixing)
- Allow a color preference variable for canvas background
  (naah...just use the standard background).
- Allow a self-updating color preference variable for annotations
- Add pan with mouse.
- Add pseudocolor options.

History:
2004-12-14 ROwen	Compute range based on sorting input data to handle data range;
					thus range changes need not resort (or recompute a histogram),
					but instead now must re-apply the scaling function.
2005-01-28 ROwen	Bug fix: was sorting the input data.
"""
import Tkinter
import numarray as num
import Image
import ImageTk
import RO.Wdg
import RO.SeqUtil

_AnnTag = "_gs_ann_"

class Annotation:
	"""Image annotation.

	Designed to allow easy redraw of the annotation when the image is zoomed.

	Inputs:
	- func	function to draw the annotation; must take these arguments:
			by position:
			- cnv	see below
			- pixPos	see below
			- rad	see below
			by name:
			- tags	see below
			- any additional keyword supplied when creating this Annotation
			The function must return the ID of the drawn object.
	- cnv	canvas on which to draw the annotation
	- pixPos	x,y pixel position of center, in unzoomed pixels
	- rad	overall radius of annotation, in unzoomed pixels.
			The visible portion of the annotation should be contained
			within this radius.
	- tags	0 or more tags for annotation; the tag _AnnTag will be added
	- doResize	resize object when zoom factor changes?
	all additional keyword arguments are sent to func.
	"""
	def __init__(self,
		cnv,
		func,
		pixPos,
		rad,
		tags = None,
		doResize = True,
	**kargs):
		self.cnv = cnv
		self.func = func
		self.pixPos = pixPos
		self.rad = rad
		if not tags:
			tags = ()
		else:
			tags = RO.SeqUtil.asSequence(tags)
		tags = tuple(tags) + (_AnnTag,)
		self.doResize = doResize
		self.kargs = kargs
		self.kargs["tags"] = tags

	def draw(self, zoomFac):
		"""Draw the annotation with the specified zoom factor.
		"""
		zoomedPixPos = [p * zoomFac for p in self.pixPos]
		
		if not self.doResize:
			zoomFac = 1.0
		return self.func(
			self.cnv,
			zoomedPixPos,
			self.rad * zoomFac,
		**self.kargs)
			
			
class GrayImageWdg(Tkinter.Frame):
	"""Display a grayscale image.
	
	Warning: under construction!
	"""
	def __init__(self,
		master,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		kargs.setdefault("width", 200)
		kargs.setdefault("height", 200)
		
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
		
		# annotation dictionary; keys are canvas IDs
		self.annDict = {}
		
		gr = RO.Wdg.Gridder(self)
		
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
			defValue = "100%",
			width = 4,
			callFunc = self.doRangeMenu,
			helpText = "range of scaled data relative to min/max",
		)
		self.rangeMenuWdg.pack(side="left")
		
		gr.gridWdg(False, toolFrame, colSpan = 10, sticky="w")
		
		# set up scrolling panel to display canvas
		self.scrollWdg = RO.Wdg.ScrolledWdg(
			master = self,
			hscroll = True,
			vscroll = True,
		)
		self.scrollWdg.grid(row=0, column=0)
		gr.gridWdg(False, self.scrollWdg, colSpan=10, sticky="news")
		self.rowconfigure(1, weight=1)
		self.columnconfigure(9, weight=1)
		
		# add canvas
		self.cnv = Tkinter.Canvas(
			master = self.scrollWdg.getWdgParent(),
			cursor="crosshair",
			bd = 0,
			selectborderwidth = 0,
			highlightthickness = 0,
		)
		self.scrollWdg.setWdg(self.cnv)
		
		bdWidth = 0
		for bdName in ("borderwidth", "selectborderwidth", "highlightthickness"):
			bdWidth += int(self.cnv[bdName])
		self.bdWidth = bdWidth
	
		# add current position and current value widgets
		self.currPosWdg = RO.Wdg.StrLabel(self)
		self.currValWdg = RO.Wdg.IntLabel(self)
		gr.gridWdg("Position", (self.currPosWdg, Tkinter.Label(self, text="Value"), self.currValWdg))
	
		# set up bindings
		self.cnv.bind("<Motion>", self._updCurrVal)
	
	def addAnnotation(self, func, pixPos, rad, tags=None, doResize=True, **kargs):
		"""Add an annotation (see the Annotation class for details).
		"""
		annObj = Annotation(
			self.cnv,
			func = func,
			pixPos = pixPos,
			rad = rad,
			tags = tags,
			doResize = doResize,
		**kargs)
		cnvID = annObj.draw(self.zoomFac)
		self.annDict[cnvID] = annObj
	
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
		self.setZoom(zoomFac)
		
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
		
		# set canvas size
		self.cnv.configure(
			width = imShapeXY[0],
			height = imShapeXY[1],
		)

		# display image
		self.imID = self.cnv.create_image(
			self.bdWidth, self.bdWidth,
			anchor="nw",
			image=self.tkIm,
		)
		
		# display annotations
		for ann in self.annDict.itervalues():
			ann.draw(self.zoomFac)
	
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
	
	def setZoom(self, zoomFac):
		"""Set the zoom factor.
		
		0.5 shows every other pixel, starting with the 2nd pixel
		1 shows the image at original size
		2 shows each pixel 2x as large as it should be
		etc.
		"""
		self.zoomFac = float(zoomFac)
		
		self.redisplay()
	
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
		try:
			ds9Pos, ijInd = self.ds9PosIJIndFromPixPos((evt.x, evt.y))
		except IndexError:
			return
		
#		print "evtxy=%s; ds9pos=%s; ijInd=%s" %  ((evt.x, evt.y), ds9Pos, ijInd)
				
		val = self.dataArr[ijInd[0], ijInd[1]]
		self.currPosWdg.set("%s, %s" % (ds9Pos[0], ds9Pos[1]))
		self.currValWdg.set(val)
	
	def ds9PosIJIndFromPixPos(self, pixPos):
		"""Convert pixel x,y position to ds9 x,y position and data i.j index.
		
		Returns (ds9 x, ds9 y), (ind i, ind j)
		
		Raises IndexError if out of range.
		"""
		# compute xyPos using ds9 conventions and array ij index
		# keep in mind that array indices are swapped: arr[i,j] = arr[y,x]
		pix0X = pixPos[0] - self.bdWidth
		pix0Y = self.cnv.winfo_height() - self.bdWidth - pixPos[1] - 1
		
		scaledPos = (
			(pixPos[0] - self.bdWidth) / self.zoomFac,
			(self.cnv.winfo_height() - self.bdWidth - pixPos[1] - 1) / self.zoomFac,
		)
		
		# int truncates towards zero, so test <0 first
		# (or use int(math.floor(pos)) to generate index)
		if scaledPos[0] < 0 or scaledPos[1] < 0:
			raise IndexError("%s out of range" % (pixPos,))
		
		ijInd = [int(pos) for pos in scaledPos[::-1]]
		
		if ijInd[0] >= self.dataArr.shape[0] \
			or ijInd[1] >= self.dataArr.shape[1]:
			raise IndexError("%s out of range" % (pixPos,))
		
		ds9Off = max((1.0 / self.zoomFac), 0.5)
		ds9Pos = [pos + ds9Off for pos in scaledPos]

		return ds9Pos, ijInd

if __name__ == "__main__":
	import RO.DS9
	root = RO.Wdg.PythonTk()

	testFrame = GrayImageWdg(root)
	testFrame.pack(expand="yes", fill="both")
	
	arr = num.arange(256**2, shape=(256,256))
	xwid, ywid = arr.shape[1], arr.shape[0]
	testFrame.showArr(arr)
	
	ds9 = RO.DS9.DS9Win()
	ds9.showArray(arr)

	root.mainloop()


