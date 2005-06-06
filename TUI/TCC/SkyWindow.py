#!/usr/local/bin/python
"""An az/alt display of the telescope position and (optionally) catalog objects.

To Do:
- Improve positioning of E and N labels; right now I've hacked them
  a few pixels in the right direction, but should do better
  with some actual math that depends on font size.
- Provide prefs for SkyWdg colors.

History:
2002-12-05 ROwen	Added URL-based help; stop displaying the star display window
					until we figure out what to do with it.
2002-12-23 ROwen	Fixed two bugs in SkyWdg.removeCatalogByName exposed by pychecker.
2003-03-26 ROwen	Changed color scheme to match other widgets (white background)
2003-05-08 ROwen	Modified to use RO.CnvUtil.
2003-06-09 ROwen	Modified to use TUIModel.
2003-06-25 ROwen	Modified test case to handle message data as a dict
2003-10-30 ROwen	Re-added display of current star and changed to StatusBar;
					display telescope potential target (using a permanent msg);
					changed orientation so E is to the left (since stars
					are now displayed in normal use);
					renamed class Star to AzAltTarget and modified to handle
					TelTarget objects (the preferred contents for catalogs);
					auto-update object catalog and telPotential positions;
					cache object xy positions to speed up nearest object search
					(not an issue before because objects had fixed az,alt);
					added addWindow code;
					modified to use TCCModel instead of making keyvaribles directly.
2004-02-02 ROwen	Bug fix: catalog display did not update correctly (I was
					calling the wrong method when starting the animation).
2004-03-05 ROwen	Modified to support new TUIModel with multiple catalogs.
2004-05-18 ROwen	Changed SkyWdg.configure to _configureEvt to avoid shadowing normal configure.
					Stopped importing string and sys since they weren't used.
					Eliminated a redundant import in the test code.
2004-08-11 ROwen	Modified for updated RO.Wdg.CtxMenu.
2004-09-08 ROwen	Made the system more responsive while displaying large catalogs
					by computing catalog positions in the background.
2004-10-22 ROwen	Stopped using RO.Wdg.PatchedCanvas; it's no longer needed.
2005-06-03 ROwen	Improved uniformity of indentation.
2005-06-06 ROwen	Modified to use tcc-reported az limits instead of hard-coded.
"""
import math
import Tkinter
import RO.CanvasUtil
import RO.CnvUtil
import RO.MathUtil
import RO.ScriptRunner
import RO.Wdg
import TUI.TUIModel
import TUI.TCC.TCCModel
import TUI.TCC.UserModel

def addWindow(tlSet):
	"""Create the window for TUI.
	"""
	tlSet.createToplevel(
		name = "TCC.Sky",
		defGeom = "201x201+434+22",
		wdgFunc = SkyWdg,
	)

_HelpURL = "Telescope/SkyWin.html"

# constants regarding redraw of catalog objects
_CatRedrawDelayMS = 5000

def xyDegFromAzAlt (azAlt):
	"""converts a point from az,alt degrees (0 south, 90 east)
	to x,y degrees (x east, y north)
	"""
	theta = azAlt[0] - 90.0
	r = 90.0 - azAlt[1]
	xyDeg = (
		r * RO.MathUtil.cosd(theta),
		r * RO.MathUtil.sind(theta),
	)
	return xyDeg

def azAltFromXYDeg(xyDeg):
	"""converts a point from x,y deg (x east, y north)
	to az,alt degrees (0 south, 90 east)
	"""
	theta = RO.MathUtil.atan2d(xyDeg[1], xyDeg[0])
	r = math.sqrt((xyDeg[0]**2) + (xyDeg[1]**2))
#	print "xyDeg =", xyDeg, "r, theta =", r, theta
	azAlt = (theta + 90.0, 90.0 - r)
	return azAlt

class AzAltTarget:
	"""A minimal version of TUI.TCC.TelTarget objects
	intended for displaying telTarget and telCurrent positions"""
	def __init__(self, azAlt, name="", mag=None):
		self.posAzAlt = tuple(azAlt)
		self.posXY = xyDegFromAzAlt(azAlt)
		self.name = name
		self.mag = mag

	def getAzAlt(self):
		"""return the az,alt position (in deg) as a duple"""
		return self.posAzAlt

	def __str__(self):
		return "%r %7.2f, %5.2f Mount" % (self.name, self.posAzAlt[0], self.posAzAlt[1])

class SkyWdg (Tkinter.Frame):
	TELCURRENT = "telCurrent"
	TELTARGET = "telTarget"
	TELPOTENTIAL = "telPotential"
	CATOBJECT = "catObject"
	AzWrapSpiralDRad = 10
	AzWrapItemRad = 3
	AzWrapMargin = 5
	AzAltMargin = 10
	def __init__(self, master, width=201, height=201):
		Tkinter.Frame.__init__(self, master)
		
		self.tuiModel = TUI.TUIModel.getModel()
		self.tccModel = TUI.TCC.TCCModel.getModel()
		self.userModel = TUI.TCC.UserModel.getModel()

		# instance variables:
		# center: position of center of canvas, in pixels
		# size: size of canvas, in pixels
		# scale: scale of canvas, in pixels per deg
		self.currCatObjID = None

		self._catAnimID = None
		self._telPotentialAnimID = None
		
		self.eastLabelPos = AzAltTarget(azAlt=(90, 0))
		self.northLabelPos = AzAltTarget(azAlt=(180, 0))

		# pane on which to display current star info
		self.currStarDisp = RO.Wdg.StatusBar(master=self)
		self.currStarDisp.grid(row=1, column=0, sticky="ew")
		self.currStarMsgID = None

		# canvas on which to display stars
		self.cnv = Tkinter.Canvas(master=self,
			width=width, height=height,
#			background='black',
			selectborderwidth=0, highlightthickness=0)
		self.cnv.grid(row=0, column=0, sticky="nsew")
		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
		RO.Wdg.addCtxMenu(
			wdg = self.cnv,
			helpURL = _HelpURL,
		)

		# thickness of canvas border;
		# drawable width/height = winfo_width/height - (2 * border)
		self.cnvBorderWidth = int(self.cnv["highlightthickness"]) + int(self.cnv["selectborderwidth"])
		self.cnv.bind('<Configure>', self._configureEvt)
		# self.cnv.tag_bind('star', '<Enter>', self._enterStar)
		# self.cnv.tag_bind('star', '<Leave>', self._leaveStar)
		self.cnv.bind('<Motion>', self._enterStar)
		self.cnv.bind('<Leave>', self._leaveStar)
		# the following prevents the display from blanking
		# when the button is pressed once (I tried trapping and
		# discarding <Button>, as a faster solutionn, but it didn't work)
		self.cnv.bind('<Button>', self._enterStar)
		self.cnv.bind('<Double-Button-1>', self._setPotential)
		self.center = [None,None]
		self.size = [None,None]
		self.azAltRad = None
		self.azAltScale = None
		self.sizeDeg = [180.0, 180.0]
		
		# various dictionaries whose keys are catalog name
		# note: if a catalog is deleted, it is removed from catDict
		# and catPixPosObjDict, but not necessarily the others
		self.catDict = {}	# key=catalog name, value = catalog
		self.catAfterIDDict = {}	# key=catalog name, value = tk after id
		self.catColorDict = {}	# key=catalog name, value = color
		self.catPixPosObjDict = {}	# key=catalog name, value = list of (pix pos, obj) pairs
		self.catSRDict = {}	# key=catalog name, value = scriptrunner script to redisplay catalog

		self.telCurrent = None
		self.telTarget = None
		self.telPotential = None
		self.azWrapGauge = RO.CanvasUtil.Spiral (
			cnv = self.cnv,
			xctr = 1, yctr = 1,
			begRad = 0, endRad = 0,  # not yet ready to draw; canvas size unknown
			angScale = -1.0,
			angOff = -90.0,
		)
		self._setSize()
		
		# set up automatic update of current and target telescope position
		self.tccModel.axePos.addCallback(self.setTelCurrent)
		self.tccModel.tccPos.addCallback(self.setTelTarget)
		self.tccModel.azLim.addCallback(self.setAzLim)
		
		self.userModel.potentialTarget.addCallback(self.setTelPotential)
		self.userModel.userCatDict.addCallback(self._updUserCatDict)

	def _configureEvt(self, event=None):
		"""Handle the <Configure> event.
		"""
		self._setSize()
		self.redraw()

	def _setPotential(self, event):
		xyPix = (event.x, event.y)
		catObj = self.findNearestStar(xyPix, maxDistSq = 25.0)
		if catObj != None:
			self.userModel.potentialTarget.set(catObj)
			
			# note: evaluate when needed instead of at init
			# to make sure the window has been generated
			slewWin = self.tuiModel.tlSet.getToplevel("TCC.Slew")
			if slewWin:
				slewWin.makeVisible()
				slewWin.focus_set()

	def _enterStar(self, event):
		xyPix = (event.x, event.y)
		catObj = self.findNearestStar(xyPix, maxDistSq = 25.0)
		if catObj:
			self.currStarMsgID = self.currStarDisp.setMsg(
				msgStr = str(catObj),
				isTemp = True,
			)
		else:
			self.currStarMsgID = self.currStarDisp.clearTempMsg(self.currStarMsgID)
		
	def _leaveStar(self, event):
		self.currStarMsgID = self.currStarDisp.clearTempMsg(self.currStarMsgID)
		self.currCatObjID = None

	def _setSize(self):
		# size and center of canvas
		self.size[0] = self.cnv.winfo_width() - (2 * self.cnvBorderWidth)
		self.size[1] = self.cnv.winfo_height() - (2 * self.cnvBorderWidth)
		winRad = min(self.size) / 2
		for ind in range(2):
			self.center[ind] = (self.size[ind] / 2) + self.cnvBorderWidth
		
		# radius allocated to az/alt display
		self.azAltRad = winRad - (SkyWdg.AzAltMargin + SkyWdg.AzWrapItemRad + \
			SkyWdg.AzWrapSpiralDRad + SkyWdg.AzWrapItemRad + SkyWdg.AzWrapMargin)
		self.azAltRad = max(self.azAltRad, 0)
		self.azAltScale = self.azAltRad / 90.0
		
		# azWrapGauge geometry; beg and end radius only refer to the spiral;
		# AzWrapItemRad provides additional room for the items on the spiral
		begRad = self.azAltRad + SkyWdg.AzAltMargin + SkyWdg.AzWrapItemRad
		begRad = min(max(begRad, 0), winRad)
		endRad = winRad - SkyWdg.AzWrapItemRad - SkyWdg.AzWrapItemRad
		endRad = max(0, begRad, endRad)
		self.azWrapGauge.setGeom(
			xctr = self.center[0],
			yctr = self.center[1],
			begRad = begRad,
			endRad = endRad,
			redraw=0,
		)
#		print "_setSize called; winRad, azAltRad, begRad, endRad=", winRad, self.azAltRad, begRad, endRad

	def _printInfo(self):
		print "SkyWdg"
		print "size   = ", self.size, " pixels (excluding border)"
		print "center = ", self.center, " pixels"
		print "scale  = ", self.azAltScale, " pixels/deg"
		print "border = ", self.cnvBorderWidth, " pixels"

	def setAzLim(self, azLim, isCurrent=True, **kargs):
		"""Sets the azimuth limits: minPos, maxPos and other values which are ignored"""
		if not isCurrent:
			return
		self.azWrapGauge.setAngLim(azLim[0], azLim[1], redraw=True)
		self._drawTelCurrent()
		self._drawTelPotential()
		self._drawTelTarget()

	def setTelCurrent(self, azAlt, isCurrent=True, **kargs):
		"""Sets the telescope's current position.
		May be used as a keyword variable callback.

		Inputs:
			azAlt: az/alt position, in degrees (extra elements are ignored);
				use None if value is explicitly unknown (NaN)
			isCurrent: the data is current (up-to-date)
		"""
#		print "SkyWdg.setTelCurrent: az,alt =", azAlt
		if None in azAlt[0:2]:
			self.telCurrent = None
		else:
			self.telCurrent = AzAltTarget(azAlt[0:2])
		self._drawTelCurrent()

	def setTelTarget(self, azAlt, isCurrent=True, **kargs):
		"""Sets the telescope's target position.
		May be used as a keyword variable callback.

		Inputs:
			azAlt: az/alt position, in degrees (extra elements are ignored);
				use None if value is explicitly unknown (NaN)
			isCurrent: the data is current (up-to-date)
		"""
#		print "SkyWdg.setTelTarget: az,alt =", azAlt
		if None in azAlt[0:2]:
			self.telTarget = None
		else:
			self.telTarget = AzAltTarget(azAlt[0:2])
		self._drawTelTarget()

	def setTelPotential(self, telTarget=None):
		"""Sets or clears the telescope's potential position.
		
		Note: unlike setTelCurrent and setTelTarget;
		the telescope potential position may be a mean position.
		Hence the argument list is different (this function is not
		set up to be a keyword variable callback)

		Inputs:
		- telTarget: a TUI.TCC.TelTarget object; if None,
		  the current position (if any) is cleared
		"""
#		print "SkyWdg.setTelPotential(%s)" % (telTarget,)
		self.telPotential = telTarget
		self._drawTelPotential()
		if telTarget:
			msgStr = str(telTarget)
		else:
			msgStr = ""
		self.currStarDisp.setMsg(
			msgStr = msgStr,
			isTemp = False,
		)

	def addCatalog(self, catalog):
		"""Add a new catalog with a given name.
		If the catalog already exists, it is deleted.
		"""
#		print "addCatalog %r" % (catalog.name,)
		catName = catalog.name
		
		if catName in self.catDict:
			self.removeCatalogByName(catName)
		
		self.catDict[catName] = catalog
		self.catPixPosObjDict[catName] = []
		self.catAfterIDDict[catName] = None
		self.catColorDict[catName] = catalog.getDispColor()
		
		def updateCat(sr, self=self, catalog=catalog):
			catName = catalog.name
			
			catTag = "cat_%s" % (catName,)
			
			if not catalog.getDoDisplay():
				self.catPixPosObjDict[catName] = []
				self.cnv.delete(catTag)
				return
	
			# if color has changed, update it
			color = catalog.getDispColor()
			oldColor = self.catColorDict.get(catName)
			if color != oldColor:
				self.cnv.itemconfigure(catTag, fill = color, outline = color)
				self.catColorDict[catName] = color
				
#			print "compute %s thread starting" % catName
			yield sr.waitThread(_UpdateCatalog, catalog.objList, self.center, self.azAltScale)
			pixPosObjList = sr.value
#			print "compute %s thread done" % catName

			catName = catalog.name
			catTag = "cat_%s" % (catName,)
	
			self.catPixPosObjDict[catName] = []
			self.cnv.delete(catTag)
	
			color = catalog.getDispColor()		
			rad = 2 # for now, eventually may wish to vary by magnitude or window size or...?
			for pixPos, obj in pixPosObjList:
				self.cnv.create_oval(
					pixPos[0] - rad,     pixPos[1] - rad,
					pixPos[0] + rad + 1, pixPos[1] + rad + 1,
					tag = (SkyWdg.CATOBJECT, catTag),
					fill = color,
					outline = color,
				)
			self.catPixPosObjDict[catName] = pixPosObjList
			
			afterID = self.after(_CatRedrawDelayMS, self._drawCatalog, catalog)
			self.catAfterIDDict[catName] = afterID
		
		sr = RO.ScriptRunner.ScriptRunner(
			master = self,
			runFunc = updateCat,
			name = "updateCatalog",
		)
		
		self.catSRDict[catName] = sr
		catalog.addCallback(self._drawCatalog, callNow=True)

	def removeCatalogByName(self, catName):
		"""Remove the specified catalog.
		"""
#		print "removeCatalogByName %r" % (catName,)
		try:
			cat = self.catDict.pop(catName)
		except KeyError:
			raise RuntimeError("Catalog %r not found" % (catName,))
		
		cat.removeCallback(self._drawCatalog, doRaise=False)
		catTag = "cat_%s" % (catName,)
		self.cnv.delete(catTag)
		
		# cancel script runner and delete entry
		try:
			sr = self.catSRDict.pop(catName)
#			print "removeCatalogByName cancelling and deleting update script for %r" % catName
			sr.cancel()
		except KeyError:
			pass
		
		# cancel pending wakeup and delete entry
		try:
			afterID = self.catAfterIDDict.pop(catName)
			if afterID:
				self.after_cancel(afterID)
		except KeyError:
			pass
		
		# delete entry in other catalog dictionaries
		for catDict in self.catPixPosObjDict, self.catColorDict:
			try:
				del catDict[catName]
			except KeyError:
				pass

	def findNearestStar(self, xyPix, maxDistSq=9.0e99):
		"""Finds the catalog object nearest to xyPix, but only if
		the squared distance is within maxDistSq deg^2
		Returns the catalog object, or None if none found"""
		minStar = None
		minDistSq = maxDistSq
		for pixPosCatObjList in self.catPixPosObjDict.itervalues():
			for objPixPos, catObj in pixPosCatObjList:
				distSq = (objPixPos[0] - xyPix[0])**2 + (objPixPos[1] - xyPix[1])**2
				if distSq < minDistSq:
					minStar = catObj
					minDistSq = distSq
		return minStar
	
	def pixFromAzAlt(self, azAlt):
		"""Convert a point from az,alt degrees (0 south, 90 east)
		to x,y pixels, such that east is to the left and north is up.
		"""
		return self.pixFromDeg(xyDegFromAzAlt(azAlt))

	def azAltFromPix(self, xyPix):
		"""Convert a point from x,y pixels to az,alt degrees (0 south, 90 east)
		such that east is to the left and north is up.
		"""
		return azAltFromXYDeg(self.degFromPix(xyPix))

	def pixFromDeg(self, xyDeg):
		"""convert a point from x,y degrees (x/east left, y/north up)
		to x,y pixels, Tk style (x right, y down).
		"""
		xyPix = (
			self.center[0] + (xyDeg[0] * -self.azAltScale),
			self.center[1] + (xyDeg[1] * -self.azAltScale),
		)
		return xyPix

	def degFromPix(self, xyPix):
		"""converts a point from x,y pixels, Tk style (x right, y down)
		to x,y degrees (x/east left, y/north up)
		"""
		xyDeg = (
			(xyPix[0] - self.center[0]) / -self.azAltScale,
			(xyPix[1] - self.center[1]) / -self.azAltScale,
		)
		return xyDeg
	
	def _updUserCatDict(self, userCatDict):
		"""Called when the userCatDict is updated.
		userCatDict is a dictionary of catalog name:TelTarget.Catalog
		"""
		# delete any missing catalogs
		initialCatNames = self.catDict.keys()
		for catName in initialCatNames:
			if catName not in userCatDict:
				self.removeCatalogByName(catName)
		
		# add any new or changed catalogs
		# (adding deletes any existing copy)
		for catName, cat in userCatDict.iteritems():
			currCat = self.catDict.get(catName)
			if not currCat or currCat != cat or len(currCat.objList) != len(cat.objList):
				self.addCatalog(cat)

# drawing methods

	def redraw(self):
		"""Redraw everything using last recorded geometry info.
		If window size has changed, call _setSize first.
		"""
#		print "draw called"
#		self._printInfo()
		# clear canvas
		self.cnv.delete('all')
		
		# draw everything
		self._drawGrid()
		self._drawLabels()
		self.azWrapGauge.draw()
		self._drawTelCurrent()
		self._drawTelTarget()
		self._drawAllCatalogs()

	def _drawAllCatalogs(self):
		"""Draw all objects in all catalogs, erasing all stars first.
		"""
		self.catPixPosObjDict = {}
		self.cnv.delete(SkyWdg.CATOBJECT)
		for catalog in self.catDict.itervalues():
			self._drawCatalog(catalog)
			
	def _drawCatalog(self, catalog):
		"""Draw the next portion of a catalog.
		subind=0 for the first portion, 1 for the next, etc.
		"""
#		print "_drawCatalog(%r)" % (catalog.name)

		catName = catalog.name
		
		# cancel update script, if executing
		sr = self.catSRDict[catName]
		if sr.isExecuting():
#			print "_drawCatalog cancelling update script for catalog %r" % catName
			sr.cancel()

		# cancel scheduled wakeup, if any
		afterID = self.catAfterIDDict.get(catName)
		if afterID:
			self.after_cancel(afterID)
		
#		print "_drawCatalog starting update script for catalog %r" % catName
		sr.start()

	def _drawGrid(self):
		nCircles = 6
		# color = "green"
		x, y = self.center
		for circNum in range(nCircles):
			rad = self.azAltScale * (90 * (circNum + 1) / nCircles)
			RO.CanvasUtil.ctrCircle (self.cnv, x, y, rad) #, outline = color)
		RO.CanvasUtil.ctrPlus(self.cnv, x, y, rad) #, fill = color)
		RO.CanvasUtil.ctrX(self.cnv, x, y, rad) #, fill = color)
	
	def _drawLabels(self):
		font = Tkinter.Entry()["font"]
		ex, ey = self.pixFromAzAlt(self.eastLabelPos.getAzAlt())
		nx, ny = self.pixFromAzAlt(self.northLabelPos.getAzAlt())
		self.cnv.create_text(ex-8, ey, text=" E", font=font) #, fill="green")
		self.cnv.create_text(nx, ny-5, text="N", font=font) #, fill="green")
	
	def _drawTelCurrent(self):
		self.cnv.delete(SkyWdg.TELCURRENT)
		if self.telCurrent == None:
			return

		color = "red"
		tag = SkyWdg.TELCURRENT

		# draw current telescope position on az/alt grid
		x, y = self.pixFromAzAlt(self.telCurrent.getAzAlt())
		RO.CanvasUtil.ctrCircle (self.cnv, x, y,
			rad=9,
			outline=color,
			tag=tag,
		)

		# draw current telescope position on wrap gauge display
		az, alt = self.telCurrent.getAzAlt()
		x, y = self.azWrapGauge.angToXY(az)
		if None not in (x, y):
			RO.CanvasUtil.ctrCircle (self.cnv, x, y,
				rad=4,
				width = 3,
				outline=color,
				tag=tag,
			)

	def _drawTelTarget(self):
		self.cnv.delete(SkyWdg.TELTARGET)
		if self.telTarget == None:
			return

		color = "red"
		tag = SkyWdg.TELTARGET

		# draw target on az/alt grid
		x, y = self.pixFromAzAlt(self.telTarget.getAzAlt())
#		print "drawing target at", self.telTarget.getAzAlt(), "=", x, y
		RO.CanvasUtil.ctrPlus (self.cnv, x, y,
			rad=12,
			holeRad=3,
			fill=color,
			tag=tag,
		)

		# draw target on wrap gauge
		az, alt = self.telTarget.getAzAlt()
		x, y = self.azWrapGauge.angToXY(az)
		if None not in (x,y):
			RO.CanvasUtil.ctrPlus (self.cnv, x, y,
				rad=4,
				holeRad=0,
				width=3,
				fill=color,
				tag=tag,
			)

	def _drawTelPotential(self):
#		print "_drawTelPotential"
		self.cnv.delete(SkyWdg.TELPOTENTIAL)
		if self.telPotential == None:
			return

		color = "dark green"
		tag = SkyWdg.TELPOTENTIAL

		# draw potential target on az, alt grid
		x, y = self.pixFromAzAlt(self.telPotential.getAzAlt())
#		print "drawing potential at", self.telPotential.getAzAlt(), "=", x, y
		RO.CanvasUtil.ctrX (self.cnv, x, y,
			rad=9,
			holeRad=3,
			fill=color,
			tag=tag,
		)
		
		if self._telPotentialAnimID:
			self.after_cancel(self._telPotentialAnimID)
		self._telPotentialAnimID = self.after(_CatRedrawDelayMS, self._drawTelPotential)


def _UpdateCatalog(objList, center, azAltScale):
	"""Returns a list of [pixPos, obj] for the specified catalog.
	Can be run as a background thread.
	"""
	pixPosObjList = []
	for catObj in objList:
		azAlt = catObj.getAzAlt()
		if azAlt[1] < 0:
			continue
		
		xyDeg = xyDegFromAzAlt(azAlt)
		pixPos = (
			center[0] - (xyDeg[0] * azAltScale),
			center[1] - (xyDeg[1] * azAltScale),
		)

		pixPosObjList.append((pixPos, catObj))

	return pixPosObjList

if __name__ == '__main__':
	import random
	import TelTarget

	root = RO.Wdg.PythonTk()
	
	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = SkyWdg (root)
	testFrame.pack(fill="both", expand="yes")

	# create a catalog of 10 stars, random positions
	objList = []
	for ind in range(30):
		azAlt = [(random.random() - 0.5) * 360.0, random.random() * 90.0]
		objList.append(AzAltTarget(azAlt=azAlt))
	catalog = TelTarget.Catalog("randCat", objList)
	testFrame.addCatalog(catalog)

	dataDict = {
		"AxePos": objList[0].getAzAlt() + ("NaN",),
		"TCCPos": objList[1].getAzAlt() + ("NaN",),
	}
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}

	kd.dispatch(msgDict)

	root.mainloop()
