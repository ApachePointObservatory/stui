"""A basic focus script for slitviewers
(changes will be required for gcam and instruments).

Subclass for more functionality.

Take a series of exposures at different focus positions to estimate best focus.

Note:
- The script runs in two phases:
  1) If a slitviewer:
  		Move the boresight and take an exposure. Then pause.
		The user is expected to acquire a suitable star before resuming.
		Once this phase begins (i.e. once you start the script)
		changes to boresight offset are ignored.
	Other imagers:
		Take an exposure and look for the best centroidable star. Then pause.
		The user is expected to acquire a suitable star before resuming.
  2) Take the focus sweep.
	Once this phase begins all inputs are ignored.
  
To do:
- If script fails, restore original focus
- Show star brightness after each measurement;
  flag dangerously bright stars (whatever that means...
  it's much more critical for NICFPS than others)
- Pick the best star much more carefully for NICFPS;
  saturated stars get a hole in the middle and have to be avoided.
- Ask for centroiding of NICFPS images to be improved in the hub;
  if a star saturates it should not be centroided,
  but that's hard to detect for NICFPS!

- Fix the fact that the graph initially has focus
  when it should never get focus at all.
  Unfortunately, the simplest thing I tried--handing focus
  to the exposure time widget -- failed. Why?
- Consider disabling widgets that are ignored, when they are ignored.
  It gives a cue as to what can be changed and have any effect.

History:
2006-11-07 ROwen	From DIS:Focus, which was from NICFPS:Focus.
2006-11-09 ROwen	Removed use of plotAxis.autoscale_view(scalex=False, scaley=True)
					since it was not compatible with older versions of matplotlib.
					Stopped using float("nan") since it doesn't work on all pythons.
					Modified to always pause before the focus sweep.
					Modified to window the exposure.
2006-11-13 ROwen	Modified to have user set center focus and range.
					Added Expose and Sweep buttons.
2006-12-01 ROwen	Refactored to make it easier to use for non-slitviewers:
					- Added waitFocusSweep method.
					- Modified to use focPosFWHMList instead of two lists.
					Improved sanity-checking the best focus fit.
					Created SlitviewerFocusScript and OffsetGuiderFocusScript classes;
					the latter is not yet fully written.
2006-12-08 ROwen	More refactoring. Created ImagerFocusScript class.
					Needs extensive testing.
2006-12-13 ROwen	Added Find button and changed Centroid to Measure.
					Data is always nulled at start of sweep. This is much easier than
					trying to be figure out when I can safely keep existing data.
					Fit error is logged.
					Fit is logged and graphed even if fit is rejected (unless fit is a maximum).
					Changed from Numeric to numarray to avoid a bug in matplotlib 0.87.7
					Changed test for max fit focus error to a multiple of the focus range.
2006-12-28 ROwen	Bug fix: tried to send <inst>Expose time=<time> bin=<binfac>
					command for imaging instruments. The correct command is:
					<inst>Expose object time=<time>.
					Noted that bin factor and window must be configured via special
					instrument-specific commands.
					ImagerFocusScript no longer makes use of windowing (while centroiding),
					though a subclass could do so.
2006-12-28 ROwen	ImagerFocusScript.waitExpose now aborts the exposure if the script is aborted.
					This change did not get into TUI 1.3a11. Note that this fix only applies to imaging
					instruments; there is not yet any documented way to abort a guider exposure.
2007-01-02 ROwen	Fixed a bug in waitExpose: <inst> <inst>Expose -> <instExpose>.
					Fixed a bug in waitFindStar: centroidRad used but not supplied.
					Improved help text for Star Pos entry widgets.
2007-01-03 ROwen	Bug fixes:
					- Used sr instead of self.sr in two places.
					- ImagerFocusScript.getCentroidArgs returned bad
					  starpos due to wanting to window.
					- ImagerFocusScript.waitCentroid failed if no star found
					  rather than returning sr.value = None.
"""
import math
import random # for debug
import numarray as num
import LinearAlgebra
import Tkinter
import RO.Wdg
import RO.Constants
import RO.StringUtil
import TUI.TUIModel
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Guide.GuideModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

import matplotlib
matplotlib.use("TkAgg")
matplotlib.rcParams["numerix"] = "numarray"
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# constants
DefRadius = 5.0 # centroid radius, in arcsec
NewStarRad = 2.0 # amount of star position change to be considered a new star
DefFocusNPos = 5  # number of focus positions
DefFocusRange = 200 # default focus range around current focus
FocusWaitMS = 1000 # time to wait after every focus adjustment (ms)
BacklashComp = 0 # amount of backlash compensation, in microns (0 for none)
WinSizeMult = 2.5 # window radius = centroid radius * WinSizeMult
FocGraphMargin = 5 # margin on graph for x axis limits, in um
MaxFocSigmaFac = 0.5 # maximum allowed sigma of best fit focus as a multiple of focus range

MicronStr = RO.StringUtil.MuStr + "m"

class BaseFocusScript(object):
	"""Basic focus script object.
	
	This is a virtual base class. The inheritor must:
	- Provide widgets
	- Provide a "run" method
	
	Inputs:
	- gcamActor: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
	- defRadius: default centroid radius, in arcsec
	- canSetStarPos: if True the user can set the star position;
		if False then the Star Pos entries and Find button are not shown.
	- helpURL: URL of help file
	- debug: if True, run in debug mode, which uses fake data
		and does not communicate with the hub.
	"""
	cmd_Find = "find"
	cmd_Measure = "measure"
	cmd_Sweep = "sweep"
	def __init__(self,
		sr,
		gcamActor,
		instName,
		imageViewerTLName = None,
		defRadius = 5.0,
		canSetStarPos = True,
		helpURL = None,
		debug = False,
	):
		"""The setup script; run once when the script runner
		window is created.
		"""
		self.sr = sr
		sr.debug = debug
		self.gcamActor = gcamActor
		self.instName = instName
		self.imageViewerTLName = imageViewerTLName
		self.defRadius = defRadius
		self.helpURL = helpURL
		self.canSetStarPos = canSetStarPos
		
		# fake data for debug mode
		self.debugIterFWHM = None
		
		# get various models
		self.tccModel = TUI.TCC.TCCModel.getModel()
		self.tuiModel = TUI.TUIModel.getModel()
		self.guideModel = TUI.Guide.GuideModel.getModel(self.gcamActor)
		
		# create and grid widgets
		self.gr = RO.Wdg.Gridder(sr.master, sticky="ew")
		
		self.createSpecialWdg()
		
		self.createStdWdg()
		
		self.initAll()
		# try to get focus away from graph (but it doesn't work; why?)
		self.expTimeWdg.focus_set()
		self.setCurrFocus()
	
	def createSpecialWdg(self):
		"""Create script-specific widgets.
		"""
		pass
	
	def createStdWdg(self):
		"""Create the standard widgets.
		"""
		sr = self.sr
		self.starPosWdgSet = []
		for ii in range(2):
			letter = ("X", "Y")[ii]
			wdgLabel = "Star Pos %s" % (letter,)
			starPosWdg = RO.Wdg.FloatEntry(
				master = sr.master,
				minValue = 0,
				maxValue = 5000,
				helpText = "Star %s position on full frame" % (letter,),
				helpURL = self.helpURL,
			)
			if self.canSetStarPos:
				self.gr.gridWdg(wdgLabel, starPosWdg, "pix")
			self.starPosWdgSet.append((starPosWdg, wdgLabel))
		
		self.expTimeWdg = RO.Wdg.FloatEntry(
			sr.master,
			minValue = self.guideModel.gcamInfo.minExpTime,
			maxValue = self.guideModel.gcamInfo.maxExpTime,
			defValue = self.guideModel.gcamInfo.defExpTime,
			defFormat = "%.1f",
			defMenu = "Default",
			minMenu = "Minimum",
			helpText = "Exposure time",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg("Exposure Time", self.expTimeWdg, "sec")
		
		self.centroidRadWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = 5,
			maxValue = 1024,
			defValue = self.defRadius,
			defMenu = "Default",
			helpText = "Centroid radius; don't skimp",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg("Centroid Radius", self.centroidRadWdg, "arcsec", sticky="ew")

		setCurrFocusWdg = RO.Wdg.Button(
			master = sr.master,
			text = "Center Focus",
			callFunc = self.setCurrFocus,
			helpText = "Set to current focus",
			helpURL = self.helpURL,
		)
	
		self.centerFocPosWdg = RO.Wdg.IntEntry(
			master = sr.master,
			defValue = 0,
			defMenu = "Default",
			helpText = "Center of focus sweep",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg(setCurrFocusWdg, self.centerFocPosWdg, MicronStr)
	
		self.focusRangeWdg = RO.Wdg.IntEntry(
			master = sr.master,
			maxValue = 2000,
			defValue = DefFocusRange,
			defMenu = "Default",
			helpText = "Range of focus sweep",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg("Focus Range", self.focusRangeWdg, MicronStr)
	
		self.numFocusPosWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = 2,
			defValue = DefFocusNPos,
			defMenu = "Default",
			helpText = "Number of focus positions for sweep",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg("Focus Positions", self.numFocusPosWdg, "")
		
		self.focusIncrWdg = RO.Wdg.FloatEntry(
			master = sr.master,
			defFormat = "%.1f",
			readOnly = True,
			relief = "flat",
			helpText = "Focus step size",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg("Focus Increment", self.focusIncrWdg, MicronStr)
		
		# create the move to best focus checkbox
		self.moveBestFocus = RO.Wdg.Checkbutton(
			master = sr.master,
			text = "Move to Best Focus",
			defValue = True,
			relief = "flat",
			helpText = "Move to estimated best focus and measure FWHM after sweep?",
			helpURL = self.helpURL,
		)
		self.gr.gridWdg(None, self.moveBestFocus, colSpan = 3, sticky="w")
			
		# table of measurements
		self.logWdg = RO.Wdg.LogWdg(
			master = sr.master,
			height = 10,
			width = 32,
			helpText = "Measured and fit results",
			helpURL = self.helpURL,
			relief = "sunken",
			bd = 2,
		)
		self.gr.gridWdg(False, self.logWdg, sticky="ew", colSpan = 10)
		self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
		self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
		
		# graph of measurements
		plotFig = Figure(figsize=(4,1), frameon=True)
		self.figCanvas = FigureCanvasTkAgg(plotFig, sr.master)
		col = self.gr.getNextCol()
		row = self.gr.getNextRow()
		self.figCanvas.get_tk_widget().grid(row=0, column=col, rowspan=row, sticky="news")
		self.plotAxis = plotFig.add_subplot(1, 1, 1)

		self.focusRangeWdg.addCallback(self.updFocusIncr, callNow=False)
		self.numFocusPosWdg.addCallback(self.updFocusIncr, callNow=True)
		
		# add Expose and Sweep command buttons
		cmdBtnFrame = Tkinter.Frame(sr.master)
		self.findBtn = RO.Wdg.Button(
			master = cmdBtnFrame,
			text = "Find",
			callFunc = RO.Alg.GenericCallback(self.doCmd, self.cmd_Find),
			helpText = "Update focus, expose and find best star",
			helpURL = self.helpURL,
		)
		if self.canSetStarPos:
			self.findBtn.pack(side="left")
		self.measureBtn = RO.Wdg.Button(
			master = cmdBtnFrame,
			text = "Measure",
			callFunc = RO.Alg.GenericCallback(self.doCmd, self.cmd_Measure),
			helpText = "Update focus, expose and measure FWHM",
			helpURL = self.helpURL,
		)
		self.measureBtn.pack(side="left")
		self.sweepBtn = RO.Wdg.Button(
			master = cmdBtnFrame,
			text = "Sweep",
			callFunc = RO.Alg.GenericCallback(self.doCmd, self.cmd_Sweep),
			helpText = "Start focus sweep",
			helpURL = self.helpURL,
		)
		self.sweepBtn.pack(side="left")
		self.gr.gridWdg(False, cmdBtnFrame, colSpan=3)
		
		if sr.debug:
			self.expTimeWdg.set("1")
			self.centerFocPosWdg.set(0)
			self.focusRangeWdg.set(200)
			self.numFocusPosWdg.set(5)
	
	def clearGraph(self):
		self.plotAxis.clear()
		self.plotAxis.grid(True)
		# start with autoscale disabled due to bug in matplotlib
		self.plotAxis.set_autoscale_on(False)
		self.figCanvas.draw()
		self.plotLine = None
	
	def clearTable(self):
		self.logWdg.clearOutput()
		self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
		self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
		
	def doCmd(self, cmdMode, wdg=None):
		if cmdMode not in (
			self.cmd_Measure,
			self.cmd_Find,
			self.cmd_Sweep,
		):
			raise self.sr.RuntimeError("Unknown command mode %r" % (cmdMode,))
		self.cmdMode = cmdMode
		self.sr.resumeUser()
		
	def enableCmdBtns(self, doEnable):
		"""Enable or disable command buttons (e.g. Expose and Sweep).
		"""
		if doEnable:
			self.findBtn["state"] = "normal"
			self.measureBtn["state"] = "normal"
			self.sweepBtn["state"] = "normal"
		else:
			self.findBtn["state"] = "disabled"
			self.measureBtn["state"] = "disabled"
			self.sweepBtn["state"] = "disabled"

	def end(self, sr):
		"""If telescope moved, restore original boresight position.
		"""
		self.enableCmdBtns(False)

		if self.didMove:
			# restore original boresight position
			if None in self.begBoreXY:
				return
				
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
				(self.begBoreXY[0], self.begBoreXY[1])
			#print "sending tcc command %r" % tccCmdStr
			sr.startCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
	
	def extraSetup(self):
		"""Executed once at the start of each run
		after calling initAll and getInstInfo but before doing anything else.
		
		Override to do things such as put the instrument into a particular mode.
		"""
		pass

	def getInstInfo(self):
		"""Obtains instrument data.
		
		Verifies the correct instrument and sets these attributes:
		- instScale: x,y image scale in unbinned pixels/degree
		- instCtr: x,y image center in unbinned pixels
		- instLim: xmin, ymin, xmax, ymax image limits, inclusive, in unbinned pixels
		- arcsecPerPixel: image scale in arcsec/unbinned pixel;
			average of x and y scales
		
		Raises ScriptError if wrong instrument.
		"""
		sr = self.sr
		if not sr.debug:
			# Make sure current instrument is correct
			try:
				currInstName = sr.getKeyVar(self.tccModel.instName)
			except sr.ScriptError:
				raise sr.ScriptError("Current instrument unknown")
			if not currInstName.lower().startswith(self.instName.lower()):
				raise sr.ScriptError("%s is not the current instrument (%s)!" % (self.instName, currInstName))
			
			self.instScale = sr.getKeyVar(self.tccModel.iimScale, ind=None)
			self.instCtr = sr.getKeyVar(self.tccModel.iimCtr, ind=None)
			self.instLim = sr.getKeyVar(self.tccModel.iimLim, ind=None)
		else:
			# data from tcc tinst:I_NA2_DIS.DAT 18-OCT-2006
			self.instScale = [-12066.6, 12090.5] # unbinned pixels/deg
			self.instCtr = [240, 224]
			self.instLim = [0, 0, 524, 511]
		
		self.arcsecPerPixel = 3600.0 * 2 / (abs(self.instScale[0]) + abs(self.instScale[1]))
		
	
	def getEntryNum(self, wdg, descr):
		"""Return the numeric value of a widget, or raise ScriptError if blank.
		"""
		numVal = wdg.getNumOrNone()
		if numVal != None:
			return numVal
		raise self.sr.ScriptError(descr + " not specified")
	
	def getCentroidArgs(self):
		"""Return an argument dict that can be used for waitCentroid;
		thus entries are: expTime, centroidRad, starPos and window.
		"""
		retDict = self.getFindStarArgs()
		centroidRad = retDict["centroidRad"]
		winRad = centroidRad * WinSizeMult
		starPos = [None, None]
		for ii in range(2):
			wdg, descr = self.starPosWdgSet[ii]
			starPos[ii] = self.getEntryNum(wdg, descr)
		windowMinXY = [max(self.instLim[ii], starPos[ii] - winRad) for ii in range(2)]
		windowMaxXY = [min(self.instLim[ii-2], starPos[ii] + winRad) for ii in range(2)]
		# adjust starPos to be relative to subframe
		relStarPos = [starPos[ii] - windowMinXY[ii] for ii in range(2)]
		retDict["starPos"] = relStarPos
		retDict["window"] = windowMinXY + windowMaxXY
		return retDict
	
	def getFindStarArgs(self):
		"""Return an argument dict that can be used for waitFindStar;
		thus entries are: expTime and centroidRad.
		"""
		expTime = self.getEntryNum(self.expTimeWdg, "Exposure Time")
		centroidRadArcSec = self.getEntryNum(self.centroidRadWdg, "Centroid Radius")
		centroidRadPix =  centroidRadArcSec / self.arcsecPerPixel
		return dict(
			expTime = expTime,
			centroidRad = centroidRadPix,
		)
	
	def graphFocusMeas(self, focPosFWHMList, setFocRange=False):
		"""Graph measured fwhm vs focus.
		
		Inputs:
		- focPosFWHMList: list of data items:
			- focus position (um)
			- measured FWHM (binned pixels)
		- setFocRange: adjust displayed focus range?
		"""
		#print "graphFocusMeas(focPosFWHMList=%s, setFocRange=%r)" % (focPosFWHMList, setFocRange)
		numMeas = len(focPosFWHMList)
		if numMeas == 0:
			return

		focList, fwhmList = zip(*focPosFWHMList)
		if not self.plotLine:
			self.plotLine = self.plotAxis.plot(focList, fwhmList, 'bo')[0]
		else:
			self.plotLine.set_data(focList[:], fwhmList[:])
		
		if setFocRange:
			self.setGraphRange(focList=focList, fwhmList=fwhmList)
		else:
			self.setGraphRange(fwhmList=fwhmList)
		
		self.figCanvas.draw()
		
	def initAll(self):
		"""Initialize variables, table and graph.
		"""
		# initialize shared variables
		self.didMove = False
		self.focDir = None
		self.boreXYDeg = None
		self.begBoreXY = [None, None]
		self.instScale = None
		self.arcsecPerPixel = None
		self.instCtr = None
		self.instLim = None
		self.cmdMode = None

		self.clearTable()
		self.clearGraph()
		self.enableCmdBtns(False)
	
	def logFocusMeas(self, name, focPos, fwhm):
		"""Log a focus measurement.
		The name should be less than 8 characters long.
		
		If fwhm is None, it is reported as NaN.
		"""
		if fwhm == None:
			fwhmStr = "NaN"
			fwhmArcSecStr = "NaN"
		else:
			fwhmStr = "%0.1f" % (fwhm,)
			fwhmArcSecStr = "%0.1f" % (fwhm * self.arcsecPerPixel,)
		self.logWdg.addOutput("%s\t%.1f\t%s\t%s\n" % \
			(name, focPos, fwhmStr, fwhmArcSecStr)
		)
	
	def run(self, sr):
		"""Take the series of focus exposures.
		"""
		raise NotImplementedError("Subclass must implement")
	
	def setCurrFocus(self, *args):
		"""Set center focus to current focus.
		"""
		currFocus = self.sr.getKeyVar(self.tccModel.secFocus, defVal=None)
		if currFocus == None:
			self.sr.showMsg("Current focus not known",
				severity=RO.Constants.sevWarning,
			)
			return

		self.centerFocPosWdg.set(currFocus)
	
	def setGraphRange(self, focList=None, fwhmList=None):
		"""Sets the displayed range of the graph.
		
		Inputs:
		- focList: a sequence of focus values; if None then no change
		- fwhmList: a sequence of FWHM values; if None then no change
		"""
		if focList:
			minFoc = min(focList) - FocGraphMargin
			maxFoc = max(focList) + FocGraphMargin
			if maxFoc - minFoc < 50:
				minFoc -= 25
				maxFoc += 25
			self.plotAxis.set_xlim(minFoc, maxFoc)
			
		if fwhmList:
			minFWHM = min(fwhmList) * 0.95
			maxFWHM = max(fwhmList) * 1.05
			self.plotAxis.set_ylim(minFWHM, maxFWHM)
	
	def setStarPos(self, starXYPix):
		"""Set star position widgets.
		
		Inputs:
		- starXYPix: star x, y position (binned pixels)
		"""
		for ii in range(2):
			wdg = self.starPosWdgSet[ii][0]
			wdg.set(starXYPix[ii])
	
	def updFocusIncr(self, *args):
		"""Update focus increment widget.
		"""
		focusRange = self.focusRangeWdg.getNumOrNone()
		numPos = self.numFocusPosWdg.getNumOrNone()
		if None in (focusRange, numPos):
			self.focusIncrWdg.set(None, isCurrent = False)
			return

		focusIncr = int(round(focusRange / (numPos - 1)))
		self.focusIncrWdg.set(focusIncr, isCurrent = True)

	def waitCentroid(self, expTime, starPos, centroidRad, window):
		"""Take an exposure and centroid using 1x1 binning.
		
		Inputs:
		- expTime: exposure time (sec)
		- starPos: star position (x,y pix) **relative to window**
		- centroidRad: centroid radius (pix)
		- window: (xmin, ymin, xmax, ymax) of subframe corners (inclusive, pix)
		
		If the centroid is found, sets sr.value to the FWHM.
		Otherwise sets sr.value to None.
		"""
		sr = self.sr
		centroidCmdStr = "centroid time=%s bin=1 on=%.1f,%.1f cradius=%.1f window=%d,%d,%d,%d" % \
			(expTime, starPos[0], starPos[1], centroidRad,
			window[0], window[1], window[2], window[3])
		
		yield sr.waitCmd(
		   actor = self.gcamActor,
		   cmdStr = centroidCmdStr,
		   keyVars = (self.guideModel.files, self.guideModel.star),
		   checkFail = False,
		)
		cmdVar = sr.value
		if sr.debug:
			sr.value = 2.5
			return
		starData = cmdVar.getKeyVarData(self.guideModel.star)
		if starData:
			sr.value = starData[0][8]
			return
		else:
			sr.value = None

		if not cmdVar.getKeyVarData(self.guideModel.files):
			raise sr.ScriptError("Exposure failed")

	def waitFindStar(self, expTime, centroidRad):
		"""Take an exposure and find the best star that can be centroided.

		If a suitable star is found: set starPos widgets accordingly
		and set sr.value to the star FWHM.
		Otherwise displays a warning and sets sr.value to None.
		
		Inputs:
		- expTime: exposure time (sec)
		- centroidRad: centroid radius (pix)
		"""
		sr = self.sr
		self.sr.showMsg("Exposing %s sec to find best star" % (expTime,))
		findStarCmdStr = "findstars time=%s bin=1" % \
			(expTime,)
		
		yield sr.waitCmd(
		   actor = self.gcamActor,
		   cmdStr = findStarCmdStr,
		   keyVars = (self.guideModel.files, self.guideModel.star),
		   checkFail = False,
		)
		cmdVar = sr.value
		if self.sr.debug:
			self.setStarPos((50.0, 75.0))
			sr.value = 2.5
			return
		if not cmdVar.getKeyVarData(self.guideModel.files):
			raise sr.ScriptError("Exposure failed")
			
		starDataList = cmdVar.getKeyVarData(self.guideModel.star)
		if not starDataList:
			self.sr.showMsg("No stars found", severity=RO.Constants.sevWarning)
			return
			
		fileInfo = cmdVar.getKeyVarData(self.guideModel.files)[0]
		filePath = "".join(fileInfo[2:4])
		
		yield self.waitFindStarInList(filePath, centroidRad, starDataList)

	def waitFindStarInList(self, filePath, centroidRad, starDataList):
		"""Find best centroidable star in starDataList.

		If a suitable star is found: set starXYPos to position
		and sr.value to the star FWHM.
		Otherwise log a warning and set sr.value to None.
		
		Inputs:
		- filePath: image file path on hub, relative to image root
			(e.g. concatenate items 2:4 of the guider Files keyword)
		- centroidRad: centroid radius (pix)
		- starDataList: list of star keyword data
		"""
		sr = self.sr
		
		for starData in starDataList:
			starXYPos = starData[2:4]
			sr.showMsg("Centroiding star at %.1f, %.1f" % tuple(starXYPos))
			centroidCmdStr = "centroid file=%s on=%.1f,%.1f cradius=%.1f" % \
				(filePath, starXYPos[0], starXYPos[1], centroidRad)
			yield sr.waitCmd(
			   actor = self.gcamActor,
			   cmdStr = centroidCmdStr,
			   keyVars = (self.guideModel.star,),
			   checkFail = False,
			)
			cmdVar = sr.value
			starData = cmdVar.getKeyVarData(self.guideModel.star)
			if starData:
				sr.showMsg("Found star at %.1f, %.1f" % tuple(starXYPos))
				self.setStarPos(starXYPos)
				sr.value = starData[0][8] # FWHM
				return

		sr.showMsg("No suitable star found", severity=RO.Constants.sevWarning)
		sr.value = None
	
	def waitFocusSweep(self):
		"""Conduct a focus sweep.
		"""
		sr = self.sr

		# record parameters that cannot be changed while script is running
		centroidArgs = self.getCentroidArgs()

		focPosFWHMList = []
		self.clearTable()
		self.clearGraph()

		centerFocPos = float(self.getEntryNum(self.centerFocPosWdg, "Center Focus"))
		focusRange	 = float(self.getEntryNum(self.focusRangeWdg, "Focus Range"))
		startFocPos = centerFocPos - (focusRange / 2.0)
		endFocPos = startFocPos + focusRange
		numFocPos	= self.getEntryNum(self.numFocusPosWdg, "Focus Positions")
		if numFocPos < 2:
			raise sr.ScriptError("# Focus Positions < 2")
		focusIncr	 = self.focusIncrWdg.getNum()
		numExpPerFoc = 1
		self.focDir = (endFocPos > startFocPos)
		
		self.setGraphRange(focList = [startFocPos, startFocPos + focusRange])
		self.figCanvas.draw()
		
		numMeas = 0
		for focInd in range(numFocPos):
			focPos = float(startFocPos + (focInd*focusIncr))

			doBacklashComp = (focInd == 0)
			yield self.waitSetFocus(focPos, doBacklashComp)
			sr.showMsg("Exposing at focus %.1f %sm" % \
				(focPos, RO.StringUtil.MuStr))
			yield self.waitCentroid(**centroidArgs)
			if sr.debug:
				fwhm = 0.0001 * (focPos - centerFocPos) ** 2
				fwhm += random.gauss(1.0, 0.25)
			else:
				fwhm = sr.value

			self.logFocusMeas("Sw %d" % (focInd+1,), focPos, fwhm)
			
			if fwhm != None:
				focPosFWHMList.append((focPos, fwhm))
				self.graphFocusMeas(focPosFWHMList, setFocRange=False)
		
		if len(focPosFWHMList) < 3:
			raise sr.ScriptError("Need >=3 measurements to fit best focus")
		
		# Fit a curve to the data
		# arrays for holding values as we take exposures
		numMeas = len(focPosFWHMList)
		focList, fwhmList = zip(*focPosFWHMList)
		focPosArr = num.array(focList, num.Float)
		fwhmArr  = num.array(fwhmList, num.Float)
		weightArr = num.ones(numMeas, num.Float)
		coeffs, yfit, yband, sigma, corrMatrix = polyfitw(focPosArr, fwhmArr, weightArr, 2, True)
		
		# Make sure fit curve has a minimum
		if coeffs[2] <= 0.0:
			raise sr.ScriptError("Could not find minimum focus")
		
		# find the best focus position
		bestEstFocPos = (-1.0*coeffs[1])/(2.0*coeffs[2])
		bestEstFWHM = coeffs[0]+coeffs[1]*bestEstFocPos+coeffs[2]*bestEstFocPos*bestEstFocPos
		self.logFocusMeas("Fit", bestEstFocPos, bestEstFWHM)

		# compute and log standard deviation
		focSigma = math.sqrt(sigma / coeffs[2])
		self.logFocusMeas(u"Fit \N{GREEK SMALL LETTER SIGMA}", focSigma, sigma)

		# generate data from fit
		x = num.arange(min(focPosArr), max(focPosArr), 1)
		y = coeffs[0] + coeffs[1]*x + coeffs[2]*(x**2.0)
		
		# plot the fit, and the chosen focus position in green
		self.plotAxis.plot(x, y, '-k', linewidth=2)
		self.plotAxis.plot([bestEstFocPos], [bestEstFWHM], 'go')
		allFWHMList = list(fwhmList)
		allFWHMList.append(bestEstFWHM)
		allFocList = list(focList)
		allFocList.append(bestEstFocPos)
		self.setGraphRange(focList=allFocList, fwhmList=allFWHMList)
		self.figCanvas.draw()

		# check fit error
		minFoc = min(focList)
		maxFoc = max(focList)
		maxFocSigma = MaxFocSigmaFac * (maxFoc - minFoc)
		if focSigma > maxFocSigma:
			raise sr.ScriptError("Focus std. dev. too large: %.0f > %.0f" % (focSigma, maxFocSigma))
		
		# check that estimated best focus is in sweep range
		minFoc = min(focList)
		maxFoc = max(focList)
		if not minFoc <= bestEstFocPos <= maxFoc:
			bestEstFWHM = None
			raise sr.ScriptError("Best focus=%.0f out of sweep range" % (bestEstFocPos,))

		# move to best focus if "Move to best Focus" checked
		moveBest = self.moveBestFocus.getBool()
		if not moveBest:
			return
			
		self.setCurrFocus()
		yield self.waitSetFocus(bestEstFocPos, doBacklashComp=True)
		sr.showMsg("Exposing at estimated best focus %d %sm" % \
			(bestEstFocPos, RO.StringUtil.MuStr))
		yield self.waitCentroid(**centroidArgs)
		if sr.debug:
			finalFWHM = 1.1
		else:
			finalFWHM = sr.value
		
		self.logFocusMeas("Meas", bestEstFocPos, finalFWHM)
		
		if finalFWHM != None:
			self.plotAxis.plot([bestEstFocPos], [finalFWHM], 'ro')
			allFWHMList.append(finalFWHM)
			minFWHM = min(allFWHMList) * 0.95
			maxFWHM = max(allFWHMList) * 1.05
			self.setGraphRange(fwhmList=allFWHMList)
			self.figCanvas.draw()
		else:
			raise sr.ScriptError("Could not measure FWHM at estimated best focus")
	
	def waitMoveBoresight(self):
		"""Move the boresight.
		
		Records the initial boresight position in self.begBoreXY
		and sets self.didMove when the move begins.
		"""
		sr = self.sr
		
		# record the current boresight position (in a global area
		# so "end" can restore it).
		begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
		if not sr.debug:
			self.begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
			if None in self.begBoreXY:
				raise sr.ScriptError("Current boresight position unknown")
		else:
			self.begBoreXY = [0.0, 0.0]
		#print "self.begBoreXY=%r" % self.begBoreXY
		
		# move boresight
		sr.showMsg("Moving the boresight")
		self.didMove = True
		cmdStr = "offset boresight %.7f, %.7f/pabs" % \
			(self.boreXYDeg[0], self.boreXYDeg[1])
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = cmdStr,
		)
	
	def waitSetFocus(self, focPos, doBacklashComp=False):
		"""Adjust focus.

		To use: yield waitSetFocus(...)
		
		Inputs:
		- focPos: new focus position in um
		- doBacklashComp: if True, perform backlash compensation
		"""
		sr = self.sr

		focPos = float(focPos)
		
		# to try to eliminate the backlash in the secondary mirror drive move back 1/2 the
		# distance between the start and end position from the bestEstFocPos
		if doBacklashComp and BacklashComp:
			backlashFocPos = int(focPos - (abs(BacklashComp) * self.focDir))
			sr.showMsg("Backlash comp: moving focus to %.1f %sm" % (backlashFocPos, RO.StringUtil.MuStr))
			yield sr.waitCmd(
			   actor = "tcc",
			   cmdStr = "set focus=%d" % (backlashFocPos),
			)
			yield sr.waitMS(FocusWaitMS)
		
		# move to desired focus position
		sr.showMsg("Moving focus to %.1f %sm" % (focPos, RO.StringUtil.MuStr))
		yield sr.waitCmd(
		   actor = "tcc",
		   cmdStr = "set focus=%.1f" % (focPos),
		)
		yield sr.waitMS(FocusWaitMS)


class SlitviewerFocusScript(BaseFocusScript):
	"""Focus script for slitviewers
	
	Inputs:
	- gcamActor: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
	- defBoreXY: default boresight position in [x, y] arcsec;
		If an entry is None then no offset widget is shown for that axis
		and 0 is used.
	- defRadius: default centroid radius, in arcsec
	- helpURL: URL of help file
	- debug: if True, run in debug mode, which uses fake data
		and does not communicate with the hub.
	"""
	def __init__(self,
		sr,
		gcamActor,
		instName,
		imageViewerTLName,
		defBoreXY,
		defRadius = 5.0,
		helpURL = None,
		debug = False,
	):
		"""The setup script; run once when the script runner
		window is created.
		"""
		if len(defBoreXY) != 2:
			raise ValueError("defBoreXY=%s must be a pair of values" % defBoreXY)
		self.defBoreXY = defBoreXY
		
		BaseFocusScript.__init__(self,
			sr = sr,
			gcamActor = gcamActor,
			instName = instName,
			imageViewerTLName = imageViewerTLName,
			defRadius = defRadius,
			canSetStarPos = False,
			helpURL = helpURL,
			debug = debug,
		)

	def createSpecialWdg(self):
		"""Create boresight widget(s).
		"""
		sr = self.sr

		self.boreNameWdgSet = []
		for ii in range(2):
			showWdg = (self.defBoreXY[ii] != None)
			if showWdg:
				defVal = float(self.defBoreXY[ii])
			else:
				defVal = 0.0

			letter = ("X", "Y")[ii]
			wdgLabel = "Boresight %s" % (letter,)
			boreWdg = RO.Wdg.FloatEntry(
				master = sr.master,
				minValue = -60.0,
				maxValue = 60.0,
				defValue = defVal,
				defMenu = "Default",
				helpText = wdgLabel + " position",
				helpURL = self.helpURL,
			)
			if showWdg:
				self.gr.gridWdg(wdgLabel, boreWdg, "arcsec")
			self.boreNameWdgSet.append((wdgLabel, boreWdg))

	def run(self, sr):
		"""Take the series of focus exposures.
		"""
		self.initAll()
		
		# open slitviewer window
		if self.imageViewerTLName:
			self.tuiModel.tlSet.makeVisible(self.imageViewerTLName)
		self.sr.master.winfo_toplevel().lift()
		
		# fake data for debug mode
		# iteration #, FWHM
		self.debugIterFWHM = (1, 2.0)
		
		self.getInstInfo()
		self.extraSetup()

		# set boresight and star position and shift boresight
		self.boreXYDeg = [self.getEntryNum(wdg, name) / 3600.0 for (name, wdg) in self.boreNameWdgSet]
		starXYPix = [(self.boreXYDeg[ii] * self.instScale[ii]) + self.instCtr[ii] for ii in range(2)]
		self.setStarPos(starXYPix)
		yield self.waitMoveBoresight()
		
		focPosFWHMList = []
		
		# take exposure and try to centroid
		# if centroid fails, ask user to acquire a star
		self.cmdMode = self.cmd_Measure
		testNum = 0
		while self.cmdMode != self.cmd_Sweep:
			testNum += 1
			focPos = float(self.centerFocPosWdg.get())
			if focPos == None:
				raise sr.ScriptError("Must specify center focus")
			yield self.waitSetFocus(focPos, False)
			sr.showMsg("Taking test exposure at focus %.1f %sm" % \
				(focPos, RO.StringUtil.MuStr))
			centroidArgs = self.getCentroidArgs()
			yield self.waitCentroid(**centroidArgs)

			fwhm = sr.value
			self.logFocusMeas("Meas %d" % (testNum,), focPos, fwhm)
			if fwhm == None:
				msgStr = "No star found! Fix and then press Expose or Sweep"
			else:
				focPosFWHMList.append((focPos, fwhm))
				self.graphFocusMeas(focPosFWHMList, setFocRange=True)
				msgStr = "Press Centroid or Sweep to continue"

			# wait for user to press the Expose or Sweep button
			# note: the only time they should be enabled is during this wait
			self.enableCmdBtns(True)
			sr.showMsg(msgStr, RO.Constants.sevWarning)
			yield sr.waitUser()
			self.enableCmdBtns(False)

		yield self.waitFocusSweep()
	
	def waitMoveBoresight(self):
		"""Move the boresight.
		
		Records the initial boresight position in self.begBoreXY
		and sets self.didMove when the move begins.
		"""
		sr = self.sr
		
		# record the current boresight position (in a global area
		# so "end" can restore it).
		begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
		if not sr.debug:
			self.begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
			if None in self.begBoreXY:
				raise sr.ScriptError("Current boresight position unknown")
		else:
			self.begBoreXY = [0.0, 0.0]
		#print "self.begBoreXY=%r" % self.begBoreXY
		
		# move boresight
		sr.showMsg("Moving the boresight")
		self.didMove = True
		cmdStr = "offset boresight %.7f, %.7f/pabs" % \
			(self.boreXYDeg[0], self.boreXYDeg[1])
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = cmdStr,
		)


class OffsetGuiderFocusScript(BaseFocusScript):
	"""Focus script for offset guiders
	
	Inputs:
	- gcamActor: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
	- defBoreXY: default boresight position in [x, y] arcsec;
		If an entry is None then no offset widget is shown for that axis
		and 0 is used.
	- defRadius: default centroid radius, in arcsec
	- helpURL: URL of help file
	- debug: if True, run in debug mode, which uses fake data
		and does not communicate with the hub.
	"""
	def __init__(self,
		sr,
		gcamActor,
		instName,
		imageViewerTLName,
		defRadius = 5.0,
		helpURL = None,
		debug = False,
	):
		"""The setup script; run once when the script runner
		window is created.
		"""
		BaseFocusScript.__init__(self,
			sr = sr,
			gcamActor = gcamActor,
			instName = instName,
			imageViewerTLName = imageViewerTLName,
			defRadius = defRadius,
			helpURL = helpURL,
			debug = debug,
		)

	def run(self, sr):
		"""Run the focus script.
		"""
		self.initAll()

		# open image viewer window, if any
		if self.imageViewerTLName:
			self.tuiModel.tlSet.makeVisible(self.imageViewerTLName)
		self.sr.master.winfo_toplevel().lift()
		
		# fake data for debug mode
		# iteration #, FWHM
		self.debugIterFWHM = (1, 2.0)
		
		self.getInstInfo()
		self.extraSetup()

		focPosFWHMList = []
		
		# take exposure and find best star
		self.cmdMode = self.cmd_Find
		testNum = 0
		while self.cmdMode != self.cmd_Sweep:
			testNum += 1
			focPos = float(self.centerFocPosWdg.get())
			if focPos == None:
				raise sr.ScriptError("Must specify center focus")
			yield self.waitSetFocus(focPos, False)

			if self.cmdMode == self.cmd_Measure:
				measName = "Meas %d" % (testNum,)
				centroidArgs = self.getCentroidArgs()
				yield self.waitCentroid(**centroidArgs)
			elif self.cmdMode == self.cmd_Find:
				measName = "Find %d" % (testNum,)
				findStarArgs = self.getFindStarArgs()
				yield self.waitFindStar(**findStarArgs)
			else:
				raise RuntimeError("Unknown command mode: %r" % (self.cmdMode,))

			fwhm = sr.value
			self.logFocusMeas(measName, focPos, fwhm)
			if fwhm == None:
				msgStr = "No star found! Fix and then press Expose or Sweep"
			else:
				focPosFWHMList.append((focPos, fwhm))
				self.graphFocusMeas(focPosFWHMList, setFocRange=True)
				msgStr = "Press Find, Centroid or Sweep to continue"

			# wait for user to press the Expose or Sweep button
			# note: the only time they should be enabled is during this wait
			self.enableCmdBtns(True)
			sr.showMsg(msgStr, RO.Constants.sevWarning)
			yield sr.waitUser()
			self.enableCmdBtns(False)

		yield self.waitFocusSweep()
	

class ImagerFocusScript(OffsetGuiderFocusScript):
	"""Focus script for imaging instrument.
	
	This is like an Offset Guider but the exposure commands
	are sent to the instrument actor and centroid and findstars commands
	are sent to nexpose using the image just taken.
	
	Also note that bin factor cannot be specified as part of the exposure command
	and every instrument has the bin factor configured differently.
	
	Inputs:
	- instName: name of instrument actor, using display case (e.g. "DIS")
	- imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
	- defRadius: default centroid radius, in arcsec
	- helpURL: URL of help file
	- debug: if True, run in debug mode, which uses fake data
		and does not communicate with the hub.
	"""
	def __init__(self,
		sr,
		instName,
		imageViewerTLName = None,
		defRadius = 5.0,
		helpURL = None,
		debug = False,
	):
		"""The setup script; run once when the script runner
		window is created.
		"""
		OffsetGuiderFocusScript.__init__(self,
			sr = sr,
			gcamActor = "nfocus",
			instName = instName,
			imageViewerTLName = imageViewerTLName,
			defRadius = defRadius,
			helpURL = helpURL,
			debug = debug,
		)
		self.instActor = self.instName.lower()
		self.exposeModel = TUI.Inst.ExposeModel.getModel(instName)

	def getCentroidArgs(self):
		"""Return an argument dict that can be used for waitCentroid;
		thus entries are: expTime, centroidRad, starPos and window.
		
		Unlike the standard version, this one does not include window.
		"""
		retDict = self.getFindStarArgs()
		starPos = [None, None]
		for ii in range(2):
			wdg, descr = self.starPosWdgSet[ii]
			starPos[ii] = self.getEntryNum(wdg, descr)
		retDict["starPos"] = starPos
		return retDict
	
	def waitExpose(self, expTime, window=None):
		"""Take an exposure using 1x1 binning.
		Returns the file path of the exposure.
		
		Inputs:
		- expTime: exposure time (sec)
		- window: (xmin, ymin, xmax, ymax) of subframe corners (inclusive, pix).
			warning: ignored by default because the commands to take a sub-framed exposure
			are instrument-specific. To use window, override this function in a subclass.
		"""
		sr = self.sr
		
		self.sr.showMsg("Exposing for %s sec" % (expTime,))
		actorStr = "%sExpose" % (self.instActor,)
		expCmdStr = "object time=%s" % (expTime,)
		yield sr.waitCmd(
		   actor = actorStr,
		   cmdStr = expCmdStr,
		   abortCmdStr = "abort",
		   keyVars = (self.exposeModel.files,),
		   checkFail = False,
		)
		cmdVar = sr.value
		fileInfoList = cmdVar.getKeyVarData(self.exposeModel.files)
		if self.sr.debug:
			fileInfoList = [("me", "localhost", "tmp", "debug", "me", "test.fits")]
		if not fileInfoList:
			raise self.sr.ScriptError("Exposure failed")
		filePath = "".join(fileInfoList[0][2:6])
		sr.value = filePath

	def waitCentroid(self, expTime, starPos, centroidRad, window=None):
		"""Take an exposure and centroid using 1x1 binning.
		
		Inputs:
		- expTime: exposure time (sec)
		- starPos: star position (x,y pix) **relative to window**
		- centroidRad: centroid radius (pix)
		- window: (xmin, ymin, xmax, ymax) of subframe corners (inclusive, pix);
			warning: window is ignored by default (see waitExpose).
		
		If the centroid is found, sets sr.value to the FWHM.
		Otherwise sets sr.value to None.
		"""
		sr = self.sr
		
		yield self.waitExpose(expTime, window=window)
		filePath = sr.value
		
		centroidCmdStr = "centroid file=%s on=%.1f,%.1f cradius=%.1f" % \
			(filePath, starPos[0], starPos[1], centroidRad)
		yield sr.waitCmd(
		   actor = self.gcamActor,
		   cmdStr = centroidCmdStr,
		   keyVars = (self.guideModel.star,),
		   checkFail = False,
		)
		cmdVar = sr.value
		if sr.debug:
			sr.value = 2.5
			return
		starData = cmdVar.getKeyVarData(self.guideModel.star)
		if starData:
			sr.value = starData[0][8]
		else:
			sr.value = None

	def waitFindStar(self, expTime, centroidRad):
		"""Take an exposure and find the best star that can be centroided.

		If a suitable star is found: set starPos widgets accordingly
		and set sr.value to the star FWHM.
		Otherwise displays a warning and sets sr.value to None.
		
		Inputs:
		- expTime: exposure time (sec)
		- centroidRad: centroid radius (pix)
		"""
		sr = self.sr
		
		yield self.waitExpose(expTime)
		filePath = sr.value
		
		findStarCmdStr = "findstars file=%s" % (filePath,)
		
		yield sr.waitCmd(
		   actor = self.gcamActor,
		   cmdStr = findStarCmdStr,
		   keyVars = (self.guideModel.star,),
		   checkFail = False,
		)
		cmdVar = sr.value
		if self.sr.debug:
			self.setStarPos((50.0, 75.0))
			sr.value = 2.5
			return
		starDataList = cmdVar.getKeyVarData(self.guideModel.star)
		if not starDataList:
			raise sr.ScriptError("No stars found")
		
		yield self.waitFindStarInList(filePath, centroidRad, starDataList)


def polyfitw(x, y, w, ndegree, return_fit=False):
	"""
	Performs a weighted least-squares polynomial fit with optional error estimates.

	Inputs:
		x: 
			The independent variable vector.

		y: 
			The dependent variable vector.	This vector should be the same 
			length as X.

		w: 
			The vector of weights.	This vector should be same length as 
			X and Y.

		ndegree: 
			The degree of polynomial to fit.

	Outputs:
		If return_fit is false (the default) then polyfitw returns only C, a vector of 
		coefficients of length ndegree+1.
		If return_fit is true then polyfitw returns a tuple (c, yfit, yband, sigma, a)
			yfit:	
			The vector of calculated Y's.  Has an error of + or - yband.

			yband: 
			Error estimate for each point = 1 sigma.

			sigma: 
			The standard deviation in Y units.

			a: 
			Correlation matrix of the coefficients.

	Written by:  George Lawrence, LASP, University of Colorado,
					December, 1981 in IDL.
					Weights added, April, 1987,  G. Lawrence
					Fixed bug with checking number of params, November, 1998, 
					Mark Rivers.  
					Python version, May 2002, Mark Rivers
	"""
	n = min(len(x), len(y)) # size = smaller of x,y
	m = ndegree + 1 			# number of elements in coeff vector
	a = num.zeros((m,m), num.Float)  # least square matrix, weighted matrix
	b = num.zeros(m, num.Float)  # will contain sum w*y*x^j
	z = num.ones(n, num.Float)	 # basis vector for constant term

	a[0,0] = num.sum(w)
	b[0] = num.sum(w*y)

	for p in range(1, 2*ndegree+1): 	 # power loop
		z = z*x # z is now x^p
		if (p < m):  b[p] = num.sum(w*y*z)	# b is sum w*y*x^j
		sum = num.sum(w*z)
		for j in range(max(0,(p-ndegree)), min(ndegree,p)+1):
			a[j,p-j] = sum

	a = LinearAlgebra.inverse(a)
	c = num.matrixmultiply(b, a)
	if not return_fit:
		return c		 # exit if only fit coefficients are wanted

	# compute optional output parameters.
	yfit = num.zeros(n,num.Float)+c[0]	# one-sigma error estimates, init
	for k in range(1, ndegree +1):
		yfit = yfit + c[k]*(x**k)  # sum basis vectors
	var = num.sum((yfit-y)**2 )/(n-m)  # variance estimate, unbiased
	sigma = num.sqrt(var)
	yband = num.zeros(n,num.Float) + a[0,0]
	z = num.ones(n,num.Float)
	for p in range(1,2*ndegree+1):		# compute correlated error estimates on y
		z = z*x 	 # z is now x^p
		sum = 0.
		for j in range(max(0, (p - ndegree)), min(ndegree, p)+1):
			sum = sum + a[j,p-j]
		yband = yband + sum * z 	 # add in all the error sources
	yband = yband*var
	yband = num.sqrt(yband)
	return c, yfit, yband, sigma, a
