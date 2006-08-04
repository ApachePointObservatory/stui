#!/usr/bin/env python
"""A rectangle that the user can resize or drag around.

Tkinter implementation of Keith Vetter's "PrintBox" with a few refinements.

Notes:
- If you want a full sized rectangle to completely fill the canvas,
  the do the following:
  - Configure your canvas with:
    selectborderwidth=0, highlightthickness=0, borderwidth=0

Known Issues:
- If the fill is None, you cannot drag the box (the <Enter> binding never fires).
  This was seen on MacOS X/Aqua Tk 8.4.11 and might not be an issue elsewhere,
  But to avoid trouble: specify fill = cnv["background"] instead of None.
- A box configured to go to the edges can go just beyond the edges
  on the right and top, just inside the edges on the other two sides.
  This seems a weird choice, but it's what I see on MacOS X/Aqua Tk 8.4.11
  with Aqua Tk. Anyway, it's probably not worth trying to work around.
"""
__all__ = ["ResizableRect"]

import Tkinter
import RO.SeqUtil
from RO.Alg import GenericCallback

class ResizableRect(object):
	"""Resizable box
	
	Inputs:
	- cnv: canvas onto which to put box
	- x0, y0, x1, y1: initial box coords
	- grabSize (inner, outer): thickness of grab area inside and outside the rectangle.
		If one value is specified, it is used for both.
	- minSize: minimum box size; if None, a nice value is computed
	- width: width of rectangle outline
	- fill: fill color of rectangle. Warning: None may prevent dragging the rectangle.
	all other keyword arguments are used for the rectangle
	(see Tkinter.Canvas's create_rectangle method for more info).
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
		
		self.rectCoords = (x0, y0, x1, y1) # coords of box
		self.mousePos = [] # coords of button-down
		if minSize == None:
			minSize = (2 * width) + (3 * self.grabSize[0]) + self.grabSize[1]
		self.minSize = minSize
		self.btnDown = False # button down flag
		
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
		
		self.cnv.tag_bind(self.rectID, "<Enter>", GenericCallback(self._doEnter, "hand2"))
		self.cnv.tag_bind(self.rectID, "<ButtonPress-1>", self._doDown)
		self.cnv.tag_bind(self.rectID, "<B1-Motion>", self._doMove)
		
		# Hidden rectangles that we bind to for resizing
		# (and they can be shown for debugging)
		sideColor = "yellow"
		cornerColor = "blue"
		cornerColor = sideColor = None
		self.idDict["L"] = self.cnv.create_rectangle(
			0, 0, 0, 1,
			fill = sideColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["R"] = self.cnv.create_rectangle(
			1, 0, 1, 1,
			fill = sideColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["T"] = self.cnv.create_rectangle(
			0, 0, 1, 0,
			fill = sideColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["B"] = self.cnv.create_rectangle(
			0, 1, 1, 1,
			fill = sideColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["TL"] = self.cnv.create_rectangle(
			0, 0, 0, 0,
			fill = cornerColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["TR"] = self.cnv.create_rectangle(
			1, 0, 1, 0,
			fill = cornerColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["BL"] = self.cnv.create_rectangle(
			0, 1, 0, 1,
			fill = cornerColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)
		self.idDict["BR"] = self.cnv.create_rectangle(
			1, 1, 1, 1,
			fill = cornerColor,
			stipple = "gray25",
			width = 0,
			tags = tags,
		)

		for regionName, cursor in self.cursorDict.iteritems():
			regionID = self.idDict[regionName]
			self.cnv.tag_bind(regionID, "<Enter>", GenericCallback(self._doEnter, cursor))
			self.cnv.tag_bind(regionID, "<Leave>", self._doLeave)
			self.cnv.tag_bind(regionID, "<B1-Motion>", GenericCallback(self.doResize, regionName))
			self.cnv.tag_bind(regionID, "<ButtonRelease-1>", self._doUp)
			self.cnv.tag_bind(regionID, "<ButtonPress-1>", self._doDown)

		self.redraw()
	
	def redraw(self, evt=None):
		self.cnv.coords(self.rectID, *self.rectCoords)
				
		ix0, iy0, ix1, iy1 = self._expandRect(self.rectCoords, -self.grabSize[0])
		ox0, oy0, ox1, oy1 = self._expandRect(self.rectCoords, self.grabSize[1])
		self._setCoords("L",  ox0, iy0, ix0, iy1)
		self._setCoords("R",  ix1, oy0, ox1, iy1)
		self._setCoords("T",  ix0, oy0, ix1, iy0)
		self._setCoords("B",  ix0, iy1, ix1, oy1)
		self._setCoords("TL", ox0, oy0, ix0, iy0)
		self._setCoords("TR", ix1, oy0, ox1, iy0)
		self._setCoords("BL", ox0, iy1, ix0, oy1)
		self._setCoords("BR", ix1, iy1, ox1, oy1)
	
	def _setCoords(self, regionName, x0, y0, x1, y1):
		self.cnv.coords(self.idDict[regionName], x0, y0, x1, y1)
	
	def _expandRect(self, rectCoords, d):
		x0, y0, x1, y1 = rectCoords
		return (x0 - d, y0 - d, x1 + d, y1 + d)

	def _doEnter(self, cursor, evt=None):
		self.cnv["cursor"] = cursor

	def _doLeave(self, evt=None):
		self.cnv["cursor"] = "crosshair"
					
	def _doUp(self, evt=None):
		self.btnDown = False
	
	def _doDown(self, evt):
		"""Handle mouse down"""
		self.mousePos = [evt.x, evt.y]
		self.btnDown = True
	
	def _doMove(self, evt):
		"""Handle <Motion> event to move the box"""
		newMousePos = [evt.x, evt.y]
		dPos = [newMousePos[ii] - self.mousePos[ii] for ii in range(2)]
		newRectCoords = [self.rectCoords[ii] + dPos[ii%2] for ii in range(4)]
		
		cnvSize = [self.cnv.winfo_width(), self.cnv.winfo_height()]
		
		# constrain the move
		for ii in range(2):
			if newRectCoords[ii] < 0:
				overshoot = 0 - newRectCoords[ii]
				newRectCoords[ii] += overshoot
				newRectCoords[ii+2] += overshoot
				newMousePos[ii] += overshoot
			elif newRectCoords[ii+2] > cnvSize[ii]:
				overshoot = newRectCoords[ii+2] - cnvSize[ii]
				newRectCoords[ii] -= overshoot
				newRectCoords[ii+2] -= overshoot
				newMousePos[ii] -= overshoot
			
		self.rectCoords = newRectCoords
		self.mousePos = newMousePos
		self.redraw()
	
	def doResize(self, regionName, evt):
		"""Handle <Motion> event to resize the box"""
		newMousePos = [evt.x, evt.y]
		dPos = [newMousePos[ii] - self.mousePos[ii] for ii in range(2)]
		newRectCoords = list(self.rectCoords)
		
		cnvSize = [self.cnv.winfo_width(), self.cnv.winfo_height()]
		
		# compute the resize
		for (ii, ltr0, ltr1) in [(0, "L", "R"), (1, "T", "B")]:
			if ltr0 in regionName:
				adj = 0
				# apply left or top resize
				newRectCoords[ii] += dPos[ii]
				if newRectCoords[ii] < 0:
					adj = -newRectCoords[ii]
				elif newRectCoords[ii] > newRectCoords[ii+2] - self.minSize:
					adj = (newRectCoords[ii+2] - self.minSize) - newRectCoords[ii]
				newRectCoords[ii] += adj
				newMousePos[ii] += adj
			if ltr1 in regionName:
				# apply right or lower resize
				adj = 0
				newRectCoords[ii+2] += dPos[ii]
				if newRectCoords[ii+2] > cnvSize[ii]:
					adj = cnvSize[ii] - newRectCoords[ii+2] # - cnvSize[ii]
				elif newRectCoords[ii+2] < newRectCoords[ii] + self.minSize:
					adj = (newRectCoords[ii] + self.minSize) - newRectCoords[ii+2]
				newRectCoords[ii+2] += adj
				newMousePos[ii] += adj
		
		self.rectCoords = newRectCoords
		self.mousePos = newMousePos
		self.redraw()


if __name__ == "__main__":
	root = Tkinter.Tk()
	cnv = Tkinter.Canvas(root, selectborderwidth=0, highlightthickness=0, borderwidth=0)
	cnv.pack()
	pb = ResizableRect(cnv, 50, 50, 100, 100, grabSize=(5,0), fill="white")
	
	root.mainloop()