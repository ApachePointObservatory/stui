#!/usr/local/bin/python
"""Code to display a grayscale image.

This is a work in progress as I attempt to emulate the
most important (to me) features of ds9.

Required packages:
- numarray
- PIM

Basic idea:
(eventually) make a mask of values >= saturated values
convert to floating point
if nonlinear, first multiply by a scaling function
subtract the minimum
multiply by 256/desired max value
truncate values: set values < 0 to 0 and values > 256 to 256
convert values to unsigned 8 bit
return scaled values and saturated mask

To Do:
- Verify range menu with real data; see if it works like ds9
  (and, more importantly, if it seems to do anything useful!).
  Either try the % of min/max value calculation or else (more likely)
  adjust the percentages to give a more useful range, if needed.
- Verify that data is displayed in the correct orientation.
- Zoom scroll should try to preserve pos of ctr pixel, if possible.
- Implement right-drag to change brightness and contrast.
- Implement histogram equalization.
- If possible, highlight saturated pixels in red
  (see PyImage and mixing)
- Allow a color preference variable for canvas background
- Allow drawing lines that survive zoom and pan.
- Add pan with mouse.
- Add pseudocolor options.
"""
import Tkinter
import numarray as num
import Image
import ImageTk
import RO.Wdg

class GrayImageWdg(Tkinter.Frame):
	"""Display a grayscale image.
	
	Warning: under construction!
	"""
	def __init__(self,
		master,
		cnvBackground = "green",
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		kargs.setdefault("width", 200)
		kargs.setdefault("height", 200)
		
		# raw data array and attributes
		self.dataArr = None
		self.dataMin = None
		self.dataMax = None
		
		# scaled data array and attributes
		self.scaledArr = None
		self.scaleFuncOff = 0.0
		self.scaleFunc = None
		self.scaledMin = None
		self.scaledMax = None
		
		# displayed image attributes
		self.zoomFac = 1.0
		self.dispOffset = 0
		self.dispScale = 1.0
		self.imID = None
		
		gr = RO.Wdg.Gridder(self)
		
		# tool bar
		toolFrame = Tkinter.Frame(self)
		RO.Wdg.StrLabel(toolFrame, text="Zoom:").pack(side="left")
		self.zoomMenuWdg = RO.Wdg.OptionMenu(
			master = toolFrame,
			items = ("1/16", "1/8", "1/4", "1/2", "1", "2", "4", "8"),
			defValue = "1",
			callFunc = self.doZoomMenu,
		)
		self.zoomMenuWdg.pack(side="left")
		RO.Wdg.Button(
			master = toolFrame,
			text = "-",
			callFunc = self.doZoomOut,
		).pack(side="left")
		RO.Wdg.Button(
			master = toolFrame,
			text = "+",
			callFunc = self.doZoomIn,
		).pack(side="left")
		
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
		self.scrollWdg._cnv["background"] = cnvBackground
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
	
	def doRangeMenu(self, wdg=None, redisplay=True):
		"""Handle new selection from range menu."""
		valueStr = self.rangeMenuWdg.getString()
		numVal = float(valueStr[:-1]) / 100.0 # ignore % from end
		lowFrac = (1.0 - numVal) / 2.0
		highFrac = 1.0 - lowFrac
#		print "doRangeMenu; valueStr=%r; numVal=%r; lowFrac=%r; highFrac=%r" % (valueStr, numVal, lowFrac, highFrac)
		self.setRangeByFrac(lowFrac, highFrac, redisplay = redisplay)

# this variant uses % of min, max instead of median-like computation
# this may be more useful, but first figure out why setScale is so broken
#	def doRangeMenu(self, wdg=None, redisplay=True):
#		"""Handle new selection from range menu."""
#		valueStr = self.rangeMenuWdg.getString()
#		numVal = float(valueStr[:-1]) / 100.0 # ignore % from end
#		lowFrac = (1.0 - numVal) / 2.0
#		highFrac = 1.0 - lowFrac
#		print "doRangeMenu; valueStr=%r; numVal=%r; lowFrac=%r; highFrac=%r" % (valueStr, numVal, lowFrac, highFrac)
#		scaledRange = float(self.scaledMax - self.scaledMin)
#		minVal = self.scaledMin + (lowFrac * scaledRange)
#		maxVal = self.scaledMin + (highFrac * scaledRange)
#		self.setRange(minVal, maxVal, redisplay = redisplay)
		
	def doScaleMenu(self, *args):
		"""Handle new selection from scale menu."""
		valueStr = self.scaleMenuWdg.getString()
		funcName = "scale" + valueStr.replace(" ", "")
		try:
			func = getattr(self, funcName)
		except AttributeError:
			raise RuntimeError("Bug! No function named %r" % (funcName,))
		func()
	
	def doZoomMenu(self, *args):
		"""Handle new selection from zoom menu."""
		valueStr = self.zoomMenuWdg.getString()
		valueList = valueStr.split("/")
		if len(valueList) > 1:
			zoomFac = float(valueList[0]) / float(valueList[1])
		else:
			zoomFac = int(valueList[0])
		self.setZoom(zoomFac)
		
		# enable or disable zoom in/out widgets as appropriate
		if valueStr == self.zoomMenuWdg._items[0]:
			self.zoomInWdg["state"] = "disabled"
			self.zoomOutWdg["state"] = "normal"
		elif valueStr == self.zoomMenuWdg._items[-1]:
			self.zoomInWdg["state"] = "normal"
			self.zoomOutWdg["state"] = "disabled"
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
	
	def redisplay(self, autoScale=False):
		"""Starting from the data array, redisplay the data.
		"""
		dataShapeXY = self.dataArr.shape[::-1]
		
		# apply scaling function
		self.scaledArr = self.dataArr.astype(num.Float32)
		if self.scaleFunc:
			self.scaledArr = self.scaleFunc(self.scaledArr - self.scaleFuncOff)
			if self.scaledArr.type() == num.Float64:
				print "damn numarray, anyway"
				self.scaledArr = self.scaledArr.astype(num.Float32)
		self.scaledMin = self.scaledArr.min()
		self.scaledMax = max(self.scaledArr.max(), self.scaledMin + 1)
		
		# create raw image with scaled data
		self.scaledIm = Image.frombuffer("F", dataShapeXY, self.scaledArr.tostring())

		# apply zoom
		if self.zoomFac != 1.0:
			print "zoom factor =", self.zoomFac
			imShapeXY = [int(self.zoomFac * dim) for dim in dataShapeXY]
			self.scaledIm = self.scaledIm.resize(imShapeXY)
		else:
			imShapeXY = dataShapeXY
		
		# apply current range
		self.doRangeMenu(redisplay=False)

		# apply range (brightness and contrast for scaled data)
		currIm = self.scaledIm.point(self._dispFromScaled)

		# create PhotoImage objects for display on canvas
		# (must keep a reference, else it vanishes, plus the
		# local reference can be used for fast brightness/contrast changes)
		self.tkIm = ImageTk.PhotoImage(currIm)

		# delete currently displayedimage, if any
		if self.imID:
			self.cnv.delete(self.imID)
		
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
	
	def scaleLinear(self, offset=None, autoScale=True):
		"""Restore linear scaling and redisplay.
		"""
		self.setScaleFunc(None, offset, autoScale)

	def scaleLog(self, offset=None, autoScale=True):
		"""Apply a natural log scale and redisplay.
		
		The default scale is min value - 1,
		so that the minimum scaled value will be 0.
		"""
		if not offset:
			offset = self.dataMin - 1
		self.setScaleFunc(num.log, offset, autoScale)
	
	def scaleSquare(self, offset=None, autoScale=True):
		"""Apply a square scale and redisplay.
		
		The default scale is min value.
		"""
		def squareFunc(arr):
			return num.power(arr, 2)
		self.setScaleFunc(squareFunc, offset, autoScale)
	
	def scaleSqrt(self, offset=None, autoScale=True):
		"""Apply a square root scale and redisplay.
		
		The default scale is min value.
		"""
		self.setScaleFunc(num.sqrt, offset, autoScale)
	
	def setRangeByFrac(self, lowFrac, highFrac, redisplay=True):
		"""Specify the black and white values for the scaled data
		based on the fraction of distance along sorted values.
		
		For example: lowFrac = 0.1 means that the value at
		0.1 along the sorted scaled data is displayed as black.

		A fraction of 0.25 is the 1st quartile.
		A fraction of 0.5 is the median.
		"""
		sortedData = num.ravel(self.scaledArr)
		sortedData.sort()
		dataLen = len(sortedData)

		minVal = sortedData[int(lowFrac*(dataLen-1))]
		maxVal = sortedData[int(highFrac*(dataLen)-1)]
#		print "setRangeByFrac(%r, %r); minVal=%r; maxVal=%r" % (lowFrac, highFrac, minVal, maxVal)
		self.setRange(minVal, maxVal, redisplay = redisplay)
	
	def setRange(self, minVal, maxVal, redisplay=True):
		"""Specify the black and white values for the scaled data.
		"""
		self.dispScale = 256.0 / float(maxVal - minVal)
		self.dispOffset = - minVal * float(self.dispScale)
		print "setRange(%r, %r); dispOffset=%r; dispScale=%r" % (minVal, maxVal, self.dispOffset, self.dispScale)
		if redisplay:
			self.tkIm.paste(self.scaledIm.point(self._dispFromScaled))
	
	def setScaleFunc(self, func, offset=None, autoScale=True):
		"""Set a new scale function and offset and redisplay.
		
		scaled value = func(data - offset)
		
		The default offset is the minimum data value.
		"""
		if offset == None:
			offset = self.dataMin
		self.scaleFuncOff = float(offset)
		self.scaleFunc = func
		self.redisplay(autoScale)
	
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
		
		self.dataMin = arr.min()
		self.dataMax = max(arr.max(), self.dataMin + 1)
		
		self.redisplay(autoScale=True)
	
	def _dispFromScaled(self, val):
		"""Convert a scaled value or image to a display value or image
		using the current zero and scale.
		Note: the form of the equation must strictly be val * scale + offset
		with no variation allowed, else this equation will not work with images.
		"""
#		print "_dispFromScaled(%r); scale=%r; offset=%r" % (val, self.dispScale, self.dispOffset)
		return val * self.dispScale + self.dispOffset
	
	def _updCurrVal(self, evt):
		"""Show the value that the mouse pointer is over"""
		
		# compute xyPos using ds9 conventions and array ij index
		# keep in mind that array indices are swapped: arr[i,j] = arr[y,x]
		pix0X = evt.x - self.bdWidth
		pix0Y = self.cnv.winfo_height() - self.bdWidth - evt.y - 1
		
		scaledPos = (
			(evt.x - self.bdWidth) / self.zoomFac,
			(self.cnv.winfo_height() - self.bdWidth - evt.y - 1) / self.zoomFac,
		)
		
		if scaledPos[0] < 0 or scaledPos[1] < 0:
			return
		
		ijInd = [int(pos) for pos in scaledPos[::-1]]
		
		ds9Off = max((1.0 / self.zoomFac), 0.5)
		ds9Pos = [pos + ds9Off for pos in scaledPos]
		
#		print "evtxy=(%s, %s); scaledPos=%s; ds9pos=%s; ijInd=%s" % \
#			(evt.x, evt.y, scaledPos, ds9Pos, ijInd)
		
		try:
			# get value first; if out of range, skip it
			val = self.dataArr[ijInd[0], ijInd[1]]
		except StandardError, e:
			return
		self.currPosWdg.set("%s, %s" % (ds9Pos[0], ds9Pos[1]))
		self.currValWdg.set(val)


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


