#!/usr/local/bin/python
"""Display a cartoon of the focal plane showing:
* Instrument nominal center and x and y axes
* Boresight position
* Object orientation
* Spider orientation

To do:
- modify to use preferences for colors (need 3 colors for 3 axes,
  also colors for current, target and ?potential? position).
- implement proper handling of TAI time in the angle tuplets;
  for now angle is ignored
- add zero tick-mark to rotator wrap scale
- add display for boresight, scale, image limits,
  or remove the stuff (it should be displayed somewhere, but how????)
  
History:
2002-12-05 ROwen	Added URL-based help.
2002-12-23 ROwen	Fixed a bug in setInstLim exposed by pychecker.
2003-03-05 ROwen	Modified to use simplified KeyVariables.
2003-04-02 ROwen	Modified to use the TCC model; added inst axis.
2003-04-12 ROwen	Modified to open its own window with addWindow.
2003-06-09 ROwen	Modified to not require dispatcher.
2003-06-25 ROwen	Modified test case to handle message data as a dict
2003-10-30 ROwen	Added display of rotator target position.
2004-05-18 ROwen	Bug fix: resize was not handled well (I'm not sure why,
					but I fixed it by switching from pack to grid).
					Changed FocalPlaneWdg.configure to _configureEvt.
					Stopped importing sys since it wasn't used.
2004-08-11 ROwen	Modified for updated RO.Wdg.CtxMenu.
2004-10-22 ROwen	Stopped using RO.Wdg.PatchedCanvas; it's no longer needed.
2005-06-06 ROwen	Bug fix: if rotator limits changed the current and target
					rotator position might not be centered on the spiral.
"""
import Tkinter
import tkFont
import RO.MathUtil
import RO.Wdg
import RO.CanvasUtil
import TUI.TCC.TCCModel

_HelpPage = "Telescope/FocalPlaneWin.html"

def addWindow(tlSet):
	"""Create the window for TUI.
	"""
	tlSet.createToplevel(
		name = "TCC.Focal Plane",
		defGeom = "201x201+636+22",
		wdgFunc = FocalPlaneWdg,
	)

class Axis:
	def __init__(self,
		cnv,
		name,
		lengths,
		labels,
		ctr = [None, None],
		color = "black",
		arrowShape = (3,5,1),
		longestLabel = None,	# longest label this axis will ever have;
								# if unspecified, uses the longest label in labels
		mirrors = (1, 1),
	):
		"""Creates an axis display.
		Inputs:
		cnv: canvas on which to draw
		name: name of axis (used as a tag on the canvas)
		lengths (duple): length of axis display along x, y (pix)
		labels (duple): text for x, y axis label
		ctr (duple): center point on canvas (pix)
		color: Tk color name
		arrowShape: see Tkinter create_line arrowshape parameter; used for x and y
		maxLabelWidth: the widest a label can be (in pixels)
		mirrors (duple): controls (left-right, up-down) mirroring;
			1 to not mirror, -1 to mirror
		"""
		self.ang = None
		self.cnv = cnv
		self.name = name
		self.lengths = lengths
		self.labels = labels
		self.ctr = ctr
		self.color = color
		self.arrowShape = arrowShape
		self.mirrors = mirrors
		
		self.font = Tkinter.Entry()["font"]
		self.fontObj = tkFont.Font(font = self.font)
		if longestLabel:
			self.maxLabelWidth = self.fontObj.measure(longestLabel)
		else:
			self.maxLabelWidth = max(
				self.fontObj.measure(labels[0]),
				self.fontObj.measure(labels[1]),
			)
	
	def setAng(self, ang, isCurrent=True, **kargs):
		self.ang = ang
		self.draw()

	def setMirrors(self, mirrors):
		self.mirrors = mirrors
		self.draw()

	def getRadius(self):
		return self.maxLabelWidth + max(self.lengths)

	def draw(self):
		self.cnv.delete(self.name)
		if (None in self.ctr) or (self.ang ==  None):
			return

		self.cnv.create_line(
			self.ctr[0] + self.lengths[0] * RO.MathUtil.cosd(self.ang) * self.mirrors[0],
			self.ctr[1] - self.lengths[0] * RO.MathUtil.sind(self.ang) * self.mirrors[1],
			self.ctr[0], self.ctr[1],
			self.ctr[0] - self.lengths[1] * RO.MathUtil.sind(self.ang) * self.mirrors[0],
			self.ctr[1] - self.lengths[1] * RO.MathUtil.cosd(self.ang) * self.mirrors[1],
			arrow = "both",
			arrowshape = self.arrowShape,
			fill = self.color,
			tag = self.name,
		)

		labelRads = [2 + (self.fontObj.measure(label) / 2) for label in self.labels]
		self.cnv.create_text(
			self.ctr[0] + (self.lengths[0] + labelRads[0]) * RO.MathUtil.cosd(self.ang) * self.mirrors[0],
			self.ctr[1] - (self.lengths[0] + labelRads[0]) * RO.MathUtil.sind(self.ang) * self.mirrors[1],
			text = self.labels[0],
			font = self.font,
			fill = self.color,
			tag = self.name,
		)
		self.cnv.create_text(
			self.ctr[0] - (self.lengths[1] + labelRads[1]) * RO.MathUtil.sind(self.ang) * self.mirrors[0],
			self.ctr[1] - (self.lengths[1] + labelRads[1]) * RO.MathUtil.cosd(self.ang) * self.mirrors[1],
			text = self.labels[1],
			font = self.font,
			fill = self.color,
			tag = self.name,
		)
	
class FocalPlaneWdg (Tkinter.Frame):
	"""A widget for displaying relative angles on the focal plane,
	e.g. the direction of North, and whether there is a mirror-image flip
	(based on instrument scale).
	
	To be done:
	- Add boresight position and focal plane shape IF I can figure out
	  a way display this info without wasting a ton of space.
	- Be smarter about sizing the widget or don't make it resizable.
	  At present axes are drawn at a fixed length and the rotator wrap
	  is drawn outside that area (and resizes with the window).
	- Display numeric values for the various things.
	- Allow showing north-based azimuth
	- Consider moving rotator wrap elsewhere.
	"""
	FPMargin = 15 # number of pixels between FP and wrap displays
	WrapMargin = 2 # number of pixels outside wrap display
	WrapItemRad = 3 # radius of largest indicator in wrap display
	WrapScaleDRad = 10 # change in radius from beginning to end of wrap scale
	WrapDRad = WrapScaleDRad + (2 * WrapItemRad) # number of pixels for wrap display annulus, excluding margin

	def __init__(self,
		master,
		width = 201,
		height = 201,
		**kargs
	):
		Tkinter.Frame.__init__(self, master)
		
		self.model = TUI.TCC.TCCModel.getModel()
		
		self.instNameWdg = RO.Wdg.StrLabel(
			master = self,
			helpURL = _HelpPage,
			anchor="c",
		)
		self.instNameWdg.grid(row=0, column=0)

		self.cnv = Tkinter.Canvas(
			master = self,
			width = width,
			height = height,
			selectborderwidth = 0,
			highlightthickness = 0)
		RO.Wdg.addCtxMenu(
			wdg = self.cnv,
			helpURL = _HelpPage,
		)
		self.cnv.grid(row=1, column=0, sticky="nsew")
		self.rowconfigure(1, weight=1)
		self.columnconfigure(0, weight=1)

		# instance variables:
		# ctr: position of center of canvas, in pixels
		# size: size of canvas, in pixels
		# scale: scale of canvas, in pixels per deg
		# boresight: position of boresight, in deg
		self.ctr = [None, None]
		self.frameSize = [None, None]
		self.fpRad = None
		self.wrapRadIn = None
		self.wrapRadOut = None
		self.scale = None
		self.border = int(self.cnv["highlightthickness"]) + int(self.cnv["selectborderwidth"])
		self.rotCurrent = None
		self.rotTarget = None
		
		self.instAxis = Axis(
			cnv = self.cnv,
			name = "inst",
			lengths = (50, 50),
			labels = ("X", "Y"),
			ctr = self.ctr,
			color = "dark green",
		)
		self.instAxis.setAng(0.0)
		self.horizonAxis = Axis(
			cnv = self.cnv,
			name = "horizon",
			lengths = (20, 20),
			labels = ("Az", "Alt"),
			ctr = self.ctr,
			color = "blue",
		)
		self.userAxis = Axis(
			cnv = self.cnv,
			name = "user",
			lengths = (35, 35),
			labels = ("E", "N"),
			ctr = self.ctr,
			color = "black",
			longestLabel = "long",  # longitude for galactic coords
		)

		self.sign = [None, None]

		self.boresight = None
		self.instScale = None
		self.instCtr = None
		self.instLim = None
		self.instName = None
		self.objInstAng = None
		self.spiderInstAng = None

		self.rotWrapGauge = RO.CanvasUtil.Spiral (
			cnv = self.cnv,
			xctr = 1, yctr = 1,
			begRad = 0, endRad = 0,  # not yet ready to draw; canvas size unknown
			begAng = None, endAng = None,	# rotator limits unknown
			angOff = +90.0,
			angScale = -1.0,
		)

		self.cnv.bind('<Configure>', self._configureEvt)

		# create RO key variables for the various quanities being displayed
		self.model.instName.addROWdg(self.instNameWdg)

		self.model.objInstAng.addPosCallback(self.userAxis.setAng)

		self.model.spiderInstAng.addPosCallback(self.horizonAxis.setAng)
		
		self.model.axePos.addIndexedCallback(self.setRotCurrent, 2)
		self.model.tccPos.addIndexedCallback(self.setRotTarget, 2)

		self.model.rotLim.addCallback(self.setRotLim)
		
		self.model.iimScale.addCallback(self.setInstScale)

		self._setSize()

#	def setBoresight(self, posDeg, isCurrent=True, **kargs):
#		"""Set the boresight position: degrees"""
#		self.boresight = posDeg
#		self.draw()
		
	def setCoordSys(self, coordSys, isCurrent=True, **kargs):
		"""Sets the coordinate system

		Inputs:
			coordSys: a duple consisting of:
				coordinate system name
				date (a number)
		"""
		lcname = coordSys[0].lower()
		if lcname in ("icrs", "fk4", "fk5", "geo"):
			userLabels = ("E", "N")
		elif lcname in ("gal", "ecl"):
			userLabels = ("Long", "Lat")
		else:
			# user coordinate system is az/alt, but that is already shown
			userLabels = (None, None)
		self.userAxis.labels = userLabels
		self.userAxis.draw()

	def setInstScale(self, instScale, isCurrent=True, **kargs):
		"""Set the instrument scale: instrument pixels/degree on the sky"""
		self.instScale = instScale
		mirrors = [1, 1]
		for ind in range(2):
			if instScale[ind]:
				mirrors[ind] = RO.MathUtil.sign(instScale[ind])
		self.horizonAxis.setMirrors(mirrors)
		self.userAxis.setMirrors(mirrors)
		self.instAxis.setMirrors(mirrors)
		self.draw()

#	def setInstCtr(self, instCtr, isCurrent=True, **kargs):
#		"""Set the instrument center: instrument pixels"""
#		self.instCtr = instCtr
#		self.draw()
#
#	def setInstLim(self, instLim, isCurrent=True, **kargs):
#		"""Set the instrument limits: [min x, min y, max x, max y] in inst pixels"""
#		self.instLim = instLim
#		self.draw()

	def setRotLim(self, rotLim, isCurrent=True, **kargs):
		"""Sets the rotator limits. rotLim = minPos, maxPos and other values which are ignored"""
		self.rotWrapGauge.setAngLim(rotLim[0], rotLim[1])
		self._drawRotCurrent()
		self._drawRotTarget()
	
	def setRotCurrent(self, rotCurrent, isCurrent=True, **kargs):
		"""Update rotator's current mount position.
		"""
		self.rotCurrent = rotCurrent
		self._drawRotCurrent()
	
	def setRotTarget(self, rotTarget, isCurrent=True, **kargs):
		"""Update rotator's target mount position.
		"""
		self.rotTarget = rotTarget
		self._drawRotTarget()
			
	def _setSize(self):
		self.frameSize[0] = self.cnv.winfo_width() - (2 * self.border)
		self.frameSize[1] = self.cnv.winfo_height() - (2 * self.border)
		frameRad = min(self.frameSize) / 2
		for ind in range(2):
			self.ctr[ind] = self.frameSize[ind] / 2

		endRad = frameRad - (FocalPlaneWdg.WrapMargin + FocalPlaneWdg.WrapItemRad)
		endRad = max (endRad, 0)
		begRad = endRad - FocalPlaneWdg.WrapScaleDRad
		begRad = max (begRad, 0)
		self.fpRad = begRad - (FocalPlaneWdg.WrapItemRad + FocalPlaneWdg.FPMargin)
		self.fpRad = max(self.fpRad, 0)
		# rotWrapGauge geometry; beg and end radius only refer to the spiral;
		# WrapItemRad provides additional room for the items on the spiral
		self.rotWrapGauge.setGeom(
			xctr = self.ctr[0],
			yctr = self.ctr[1],
			begRad = begRad,
			endRad = endRad,
			redraw = 0,
		)
		# self._printInfo()

	def _printInfo(self):
		print "FocalPlaneWdg"
		print "window size = ", self.cnv.winfo_width(), self.cnv.winfo_height()
		print "frameSize   = ", self.frameSize, "pixels"
		print "ctr         = ", self.ctr
		print "fpRad       = ", self.fpRad
		print "border      = ", self.border
		print ""
		print "boresight      = ", self.boresight, "deg"
		print "instScale      = ", self.instScale
		print "instCtr        = ", self.instCtr
		print "instLim        = ", self.instLim
		print "instName       = ", self.instName
		print "objInstAng     = ", self.objInstAng
		print "spiderInstAng  = ", self.spiderInstAng
	
# drawing methods

	def clear(self):
		self.cnv.delete('all')

	def _configureEvt(self, event = None):
		"""Handle the <Configure> event.
		"""
		self._setSize()
		self.clear()
		self.draw()

	def _drawRotCurrent(self):
		"""Draw current rotator mount position on wrap gauge display"""
		color = "black"
		tag = "rotCurrent"

		self.cnv.delete(tag)

		if self.rotCurrent ==  None:
			return
		x, y = self.rotWrapGauge.angToXY(self.rotCurrent)
		if None in (x, y):
			return
		RO.CanvasUtil.ctrCircle (self.cnv, x, y,
			rad = FocalPlaneWdg.WrapItemRad,
			width = 3,
			outline = color,
			tag = tag,
		)
	
	def _drawRotTarget(self):
		"""Draw target rotator mount position on wrap gauge display"""
		color = "black"
		tag = "rotTarget"

		self.cnv.delete(tag)

		if self.rotTarget ==  None:
			return
		x, y = self.rotWrapGauge.angToXY(self.rotTarget)
		if None in (x, y):
			return
		RO.CanvasUtil.ctrPlus (self.cnv, x, y,
			rad = FocalPlaneWdg.WrapItemRad,
			holeRad = 0,
			width = 3,
			fill = color,
			tag = tag,
		)
	
	def _drawAxes(self):
		"""Draw the focal plane x/y axes
		(everything except the rotator wrap and points displayed on it).
		"""
		self.horizonAxis.draw()
		self.userAxis.draw()
		self.instAxis.draw()
		
	def draw(self):
		"""Redraw everything on the canvas.
		"""
#		print "draw called"
#		self._printInfo()
		self._drawAxes()
		self.rotWrapGauge.draw()
		self._drawRotCurrent()
		self._drawRotTarget()

if __name__ ==  '__main__':
	import random
	import TUI.TUIModel

	root = RO.Wdg.PythonTk()
	# root = Tkinter.Tk()

	kd = TUI.TUIModel.getModel(True).dispatcher
	
	minAng = -350.0
	maxAng =  350.0

	def animFunc(ang1=0, ang2=0):
		ang1 = ang1 + 45
		if ang1 > 360:
			ang1 = 45
			ang2 = ang2 + 45
			if ang2 > 360:
				return

		rotAng = float(random.randint(int(minAng), int(maxAng)))
		
		dataDict = {
			"ObjInstAng": (ang1, 0, 1),
			"SpiderInstAng": (ang2, 0, 1),
			"AxePos": (0, 0, rotAng),
			"inst": ("SPICam",),
		}

		msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
		kd.dispatch(msgDict)
		root.update_idletasks()

		root.after(200, animFunc, ang1, ang2)

	testFrame = FocalPlaneWdg (root)
	testFrame.pack(fill = "both", expand = "yes")
	Tkinter.Button(root, text="Demo", command=animFunc).pack(side="top")

	# initial data
	dataDict = {
		"CoordSys": ("ICRS", None),
		"RotLim": (-360, 360, 3, 0.3, 0.3),
		"ObjInstAng": (0, 0, 1),
		"SpiderInstAng": (0, 0, 1),
		"AxePos": (0, 0, 45),
		"inst": ("SPICam",),
		"IImScale": (-3000, 3000),
	}

	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
	kd.dispatch(msgDict)


	root.mainloop()
