#!/usr/bin/env python
"""A rectangle that the user can resize or drag around.

Tkinter implementation of Keith Vetter's "PrintBox" with a few refinements.

Notes:
- If you want a full sized rectangle to completely fill the canvas,
  the do the following:
  - Configure your canvas with:
    selectborderwidth=0, highlightthickness=0, borderwidth=0

Known Issues; both have been seen on MacOS X with Aqua Tk 8.4.11
and may not be present on other platforms or newer versions of Aqua Tk:
- If the fill is None, you cannot drag the box (the <Enter> binding never fires).
- The rectangle is displayed one pixel too high (as are all rectangles)

Implementation note:
- I would have used width=1 for the region rectangles, making the
  location of the boundaries more obvious. But if outline=None
  you see a black outline, which is unacceptable.
  
History:
2006-08-04 ROwen
"""
__all__ = ["ResizableRect"]

import Tkinter
import RO.SeqUtil
from RO.Alg import GenericCallback

Debug = False

class ResizableRect(object):
	"""Resizable box
	
	Inputs:
	- cnv: canvas onto which to put box
	- x0, y0, x1, y1: initial box coords
	- grabSize (inner, outer): thickness of grab area inside and outside the rectangle
		(in addition to a line of width 1 for the rectangle itself).
		If one value is specified, it is used for both.
	- minSize: minimum box size; if None, a nice value is computed
	- width: width of rectangle outline
	- fill: fill color of rectangle. Warning: None may prevent dragging the rectangle.
	all other keyword arguments are used for the rectangle
	(see Tkinter.Canvas's create_rectangle method for more info).
	
	Notes:
	- Make sure the canvas has the normal cursor you want when you call this
	  (or else change attribute defaultCursor)
	"""
	def __init__(self,
		cnv, x0, y0, x1, y1,
		tags = None,
		grabSize = 3,
		minSize = None,
		width = 1,
		fill = "white",
	**kargs):
		self.cnv = cnv
		self.grabSize = RO.SeqUtil.oneOrNAsList(grabSize, 2, "grab (inner, outer) size")
		
		self.mousePos = [] # coords of button-down
		if minSize == None:
			# 3 = 2 lines of width 1 + 1 for delta-coord - size
			minSize = 3 + (3 * self.grabSize[0]) + self.grabSize[1]
		self.minSizeLess1 = minSize - 1
		self.btnDown = False # button down flag
		
		self.defaultCursor = cnv["cursor"]
		
		# dict of region name: cursor
		self.cursorDict = {
			"L": "sb_h_double_arrow",
			"R": "sb_h_double_arrow",
			"B": "sb_v_double_arrow",
			"T": "sb_v_double_arrow",
			"TL": "top_left_corner",
			"BR": "bottom_right_corner",
			"TR": "top_right_corner",
			"BL": "bottom_left_corner",
		}
		
		# dict of region name: region ID
		self.idDict = {}
		
		# Create stubs items that ::ResizableRect::Resize will size correctly
		self.rectID = self.cnv.create_rectangle(
			0, 0, 1, 1,
			tags = tags,
			width = width,
			fill = fill,
		**kargs)
		
		self.cnv.tag_bind(self.rectID, "<Enter>", GenericCallback(self._setCursor, "hand2"))
		self.cnv.tag_bind(self.rectID, "<ButtonPress-1>", self._doDown)
		self.cnv.tag_bind(self.rectID, "<B1-Motion>", self._doMove)
		
		# Hidden rectangles that we bind to for resizing
		# (and they can be shown for debugging)
		if Debug:
			sideColor, cornerColor = "yellow", "blue"
		else:
			sideColor = cornerColor = None
		for regionName in ("L", "R", "T", "B"):
			self.idDict[regionName] = self.cnv.create_rectangle(
				0, 0, 0, 0,
				fill = sideColor,
				stipple = "gray25",
				width = 0,
				tags = tags,
			)
		for regionName in ("TL", "TR", "BL", "BR"):
			self.idDict[regionName] = self.cnv.create_rectangle(
				0, 0, 0, 0,
				fill = cornerColor,
				stipple = "gray25",
				width = 0,
				tags = tags,
			)

		for regionName, cursor in self.cursorDict.iteritems():
			regionID = self.idDict[regionName]
			self.cnv.tag_bind(regionID, "<Enter>", GenericCallback(self._setCursor, cursor))
			self.cnv.tag_bind(regionID, "<Leave>", self._restoreDefaultCursor)
			self.cnv.tag_bind(regionID, "<B1-Motion>", GenericCallback(self._doResize, regionName))
			self.cnv.tag_bind(regionID, "<ButtonRelease-1>", self._doUp)
			self.cnv.tag_bind(regionID, "<ButtonPress-1>", self._doDown)

		self.setCoords(x0, y0, x1, y1)

	def getCoords(self):
		"""Return a copy of the current coordinates."""
		return tuple(self.rectCoords)
	
	def setCoords(self, x0, y0, x1, y1, doRaise=False):
		"""Set rectangle coordinates.
		Inputs:
		- x0, y0, x1, y1: new coordinates
		- doRaise: if True: raise ValueError if coords out of bounds;
			else silently constrain coords to be in bounds.
		"""
		newRectCoords = [
			min(x0, x1),
			min(y0, y1),
			max(x0, x1),
			max(x0, x1),
		]
		
		maxCoord = [self.cnv.winfo_width() - 1, self.cnv.winfo_height() - 1]
		
		# constrain the outer limits
		for ii in range(4):
			if newRectCoords[ii] < 0:
				if doRaise:
					raise ValueError("Coord %d=%s out of bounds" % (ii, newRectCoords[ii]))
				newRectCoords[ii] = 0
			elif newRectCoords[ii] > maxCoord[ii%2]:
				if doRaise:
					raise ValueError("Coord %d=%s out of bounds" % (ii+2, newRectCoords[ii+2]))
				newRectCoords[ii] = maxCoord[ii%2]
		for ii in range(2):
			if (newRectCoords[ii+2] - newRectCoords[ii]) < self.minSizeLess1:
				# grow the box; try to split the difference
				# but move the box if necessary
				addSize = self.minSizeLess1 - (newRectCoords[ii+2] - newRectCoords[ii])
				addTL = addSize / 2
				addBR = addSize - addTL
				newRectCoords[ii] -= addTL
				newRectCoords[ii+2] += addBR
				if newRectCoords[ii] < 0:
					nudgeAmt =  -newRectCoords[ii]
					newRectCoords[ii] += nudgeAmt
					newRectCoords[ii+2] += nudgeAmt
				elif newRectCoords[ii+2] > maxCoord[ii]:
					nudgeAmt = maxCoord[ii] - newRectCoords[ii+2]
					newRectCoords[ii] += nudgeAmt
					newRectCoords[ii+2] += nudgeAmt

		self.rectCoords = newRectCoords
		self.redraw()
		
	def redraw(self, evt=None):
		self.cnv.coords(self.rectID, *self.rectCoords)
				
		ix0, iy0, ix1, iy1 = self._expandRect(self.rectCoords, -self.grabSize[0])
		ox0, oy0, ox1, oy1 = self._expandRect(self.rectCoords, self.grabSize[1])
		self._setRegionCoords("L",  ox0, iy0, ix0, iy1)
		self._setRegionCoords("R",  ix1, oy0, ox1, iy1)
		self._setRegionCoords("T",  ix0, oy0, ix1, iy0)
		self._setRegionCoords("B",  ix0, iy1, ix1, oy1)
		self._setRegionCoords("TL", ox0, oy0, ix0, iy0)
		self._setRegionCoords("TR", ix1, oy0, ox1, iy0)
		self._setRegionCoords("BL", ox0, iy1, ix0, oy1)
		self._setRegionCoords("BR", ix1, iy1, ox1, oy1)
	
	
	def _doDown(self, evt):
		"""Handle mouse button down"""
		self.mousePos = [evt.x, evt.y]
		self.btnDown = True
	
	def _doUp(self, evt=None):
		"""Handle mouse button up"""
		self.btnDown = False
	
	def _doMove(self, evt):
		"""Handle <Motion> event to move the box"""
		newMousePos = [evt.x, evt.y]
		dPos = [newMousePos[ii] - self.mousePos[ii] for ii in range(2)]
		newRectCoords = [self.rectCoords[ii] + dPos[ii%2] for ii in range(4)]
		
		maxCoord = [self.cnv.winfo_width() - 1, self.cnv.winfo_height() - 1]
		
		# constrain the move
		for ii in range(2):
			if newRectCoords[ii] < 0:
				overshoot = 0 - newRectCoords[ii]
				newRectCoords[ii] += overshoot
				newRectCoords[ii+2] += overshoot
				newMousePos[ii] += overshoot
			elif newRectCoords[ii+2] > maxCoord[ii]:
				overshoot = newRectCoords[ii+2] - maxCoord[ii]
				newRectCoords[ii] -= overshoot
				newRectCoords[ii+2] -= overshoot
				newMousePos[ii] -= overshoot
			
		self.rectCoords = newRectCoords
		self.mousePos = newMousePos
		self.redraw()

	def _doResize(self, regionName, evt):
		"""Handle <Motion> event to resize the box"""
		newMousePos = [evt.x, evt.y]
		dPos = [newMousePos[ii] - self.mousePos[ii] for ii in range(2)]
		newRectCoords = list(self.rectCoords)
		
		maxCoord = [self.cnv.winfo_width() - 1, self.cnv.winfo_height() - 1]
		
		# compute the resize
		for (ii, charLT, charRB) in [(0, "L", "R"), (1, "T", "B")]:
			if charLT in regionName:
				adj = 0
				# apply left or top resize
				newRectCoords[ii] += dPos[ii]
				if newRectCoords[ii] < 0:
					adj = -newRectCoords[ii]
				elif newRectCoords[ii] > newRectCoords[ii+2] - self.minSizeLess1:
					adj = (newRectCoords[ii+2] - self.minSizeLess1) - newRectCoords[ii]
				newRectCoords[ii] += adj
				newMousePos[ii] += adj
			if charRB in regionName:
				# apply right or bottom resize
				adj = 0
				newRectCoords[ii+2] += dPos[ii]
				if newRectCoords[ii+2] > maxCoord[ii]:
					adj = maxCoord[ii] - newRectCoords[ii+2]
				elif newRectCoords[ii+2] < newRectCoords[ii] + self.minSizeLess1:
					adj = (newRectCoords[ii] + self.minSizeLess1) - newRectCoords[ii+2]
				newRectCoords[ii+2] += adj
				newMousePos[ii] += adj
		
		self.rectCoords = newRectCoords
		self.mousePos = newMousePos
		self.redraw()
	
	def _expandRect(self, rectCoords, d):
		"""Return a new rect that is d bigger than rectCoords
		on all sides (or smaller if d < 0).
		"""
		x0, y0, x1, y1 = rectCoords
		return (x0 - d, y0 - d, x1 + d, y1 + d)

	def _restoreDefaultCursor(self, evt=None):
		"""Restore default cursor"""
		self.cnv["cursor"] = self.defaultCursor
					
	def _setCursor(self, cursor, evt=None):
		"""Handle <Enter> event by displaying the appropriate cursor."""
		self.cnv["cursor"] = cursor

	def _setRegionCoords(self, regionName, x0, y0, x1, y1):
		"""Set coords of one region"""
		self.cnv.coords(self.idDict[regionName], x0, y0, x1, y1)


if __name__ == "__main__":
	import PythonTk
	root = PythonTk.PythonTk()
	cnv = Tkinter.Canvas(root, selectborderwidth=0, highlightthickness=0, borderwidth=1) #, relief="ridge")
	cnv.pack()
	root.update_idletasks() # else canvas not mapped yet
	rr = ResizableRect(cnv, 50, 50, 100, 100, grabSize=(5,0), fill="white")
	
	root.mainloop()