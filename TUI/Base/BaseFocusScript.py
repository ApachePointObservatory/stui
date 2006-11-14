"""A basic focus script for slitviewers
(changes will be required for gcam and instruments).

Subclass for more functionality.

Take a series of exposures at different focus positions to estimate best focus.

Note:
- The script runs in two phases:
  1) Move the boresight and take an exposure. Then pause.
  	The user is expected to acquire a suitable star before resuming.
  	Once this phase begins changes to Bore Y are ignored.
  2) Take the exposure sequence.
  	Once this phase begins changes to Focus Begin, Focus End
  	and Focus Increment are ignored.
  
To do:
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
"""
import math
import random # for debug
import Numeric as num
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
matplotlib.rcParams["numerix"] = "Numeric"
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# constants
DefRadius = 5.0 # centroid radius, in arcsec
DefFocusNPos = 5  # number of focus positions
DefFocusRange = 200 # default focus range around current focus
FocusWaitMS = 1000 # time to wait after every focus adjustment (ms)
BacklashComp = 0 # amount of backlash compensation, in microns (0 for none)
WinSizeMult = 2.5 # window radius = centroid radius * WinSizeMult
FocGraphMargin = 5 # margin on graph for x axis limits, in um

MicronStr = RO.StringUtil.MuStr + "m"

class BaseFocusScript(object):
	"""Basic focus script object
	
	Inputs:
	- gcamName: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- guideTLName: name of guide toplevel (e.g. "Guide.DIS Slitviewer")
	- defBoreXY: default boresight position in [x, y] arcsec;
		If one entry is None then no offset widget is shown for that axis.
		Both entries cannot be None.
	- defRadius: default centroid radius, in arcsec
	- helpURL: URL of help file
	- debug: if True, run in debug mode, which uses fake data
		and does not communicate with the hub.
	"""
	def __init__(self,
		sr,
		gcamName,
		instName,
		guideTLName,
		defBoreXY,
		defRadius = 5.0,
		helpURL = None,
		debug = False,
	):
		"""The setup script; run once when the script runner
		window is created.
		"""
		self.sr = sr
		sr.debug = debug
		self.gcamName = gcamName
		self.instName = instName
		self.guideTLName = guideTLName
		self.helpURL = helpURL
		
		# fake data for debug mode
		self.debugIterFWHM = None
		
		# get various models
		self.tccModel = TUI.TCC.TCCModel.getModel()
		self.tuiModel = TUI.TUIModel.getModel()
		self.guideModel = TUI.Guide.GuideModel.getModel(self.gcamName)
		
		row=0
		
		# create and grid widgets
		gr = RO.Wdg.Gridder(sr.master, sticky="ew")

		# create boresight widgets, if wanted
		self.boreNameWdgSet = []
		if len(defBoreXY) != 2:
			raise ValueError("defBoreXY=%s must be a list of two values" % defBoreXY)
		if defBoreXY == [None, None]:
			raise RuntimeError("defBoreXY=%s; at least one entry must be non-None" % defBoreXY)
		for ii in range(2):
			showWdg = (defBoreXY[ii] != None)
			if showWdg:
				defVal = float(defBoreXY[ii])
			else:
				defVal = 0.0

			letter = ("X", "Y")[ii]
			wdgName = "Boresight %s" % (letter,)
			boreWdg = RO.Wdg.FloatEntry(
				master = sr.master,
				minValue = -60.0,
				maxValue = 60.0,
				defValue = defVal,
				defMenu = "Default",
				helpText = wdgName + " position",
				helpURL = self.helpURL,
			)
			if showWdg:
				gr.gridWdg(wdgName, boreWdg, "arcsec")
			self.boreNameWdgSet.append((wdgName, boreWdg))


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
		gr.gridWdg("Exposure Time", self.expTimeWdg, "sec")
		
		self.centroidRadWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = 5,
			maxValue = 1024,
			defValue = defRadius,
			defMenu = "Default",
			helpText = "Centroid radius; don't skimp",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Centroid Radius", self.centroidRadWdg, "arcsec", sticky="ew")

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
		gr.gridWdg(setCurrFocusWdg, self.centerFocPosWdg, MicronStr)
#		setCurrFocusWdg.grid(
#			row = gr.getNextRow() - 1,
#			column = gr.getNextCol(),
#		)
	
		self.focusRangeWdg = RO.Wdg.IntEntry(
			master = sr.master,
			maxValue = 2000,
			defValue = DefFocusRange,
			defMenu = "Default",
			helpText = "Range of focus sweep",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Focus Range", self.focusRangeWdg, MicronStr)
	
		self.numFocusPosWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = 2,
			defValue = DefFocusNPos,
			defMenu = "Default",
			helpText = "Number of focus positions for sweep",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Focus Positions", self.numFocusPosWdg, "")
		
		self.focusIncrWdg = RO.Wdg.FloatEntry(
			master = sr.master,
			defFormat = "%.1f",
			readOnly = True,
			relief = "flat",
			helpText = "Focus step size",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Focus Increment", self.focusIncrWdg, MicronStr)
		
		# create the move to best focus checkbox
		self.moveBestFocus = RO.Wdg.Checkbutton(
			master = sr.master,
			text = "Move to Best Focus",
			defValue = True,
			relief = "flat",
			helpText = "Move to estimated best focus and measure FWHM after sweep?",
			helpURL = self.helpURL,
		)
		gr.gridWdg(None, self.moveBestFocus, colSpan = 3, sticky="w")
			
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
		gr.gridWdg(False, self.logWdg, sticky="ew", colSpan = 10)
		self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
		self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
		
		# graph of measurements
		plotFig = Figure(figsize=(4,1), frameon=True)
		self.figCanvas = FigureCanvasTkAgg(plotFig, sr.master)
		col = gr.getNextCol()
		row = gr.getNextRow()
		self.figCanvas.get_tk_widget().grid(row=0, column=col, rowspan=row, sticky="news")
		self.plotAxis = plotFig.add_subplot(1, 1, 1)

		self.focusRangeWdg.addCallback(self.updFocusIncr, callNow=False)
		self.numFocusPosWdg.addCallback(self.updFocusIncr, callNow=True)
		
		# add Expose and Sweep buttons
		self.exposeBtn = RO.Wdg.Button(
			master = sr.master,
			text = "Expose",
			callFunc = self.doExposeBtn,
			helpText = "Expose and measure FWHM at current focus",
			helpURL = self.helpURL,
		)
		self.sweepBtn = RO.Wdg.Button(
			master = sr.master,
			text = "Sweep",
			callFunc = self.doSweepBtn,
			helpText = "Start focus sweep",
			helpURL = self.helpURL,
		)
		gr.gridWdg(False, (self.exposeBtn, self.sweepBtn))
		
		if sr.debug:
			self.expTimeWdg.set("1")
			self.centerFocPosWdg.set(0)
			self.focusRangeWdg.set(200)
			self.numFocusPosWdg.set(5)
		
		self.initAll()
		# try to get focus away from graph (but it doesn't work; why?)
		self.expTimeWdg.focus_set()
		self.setCurrFocus()
	
	def doExposeBtn(self, wdg=None):
		self.doSweep = False
		self.sr.resumeUser()
		
	def doSweepBtn(self, wdg=None):
		self.doSweep = True
		self.sr.resumeUser()
		
	def enableBtns(self, doEnable):
		"""Enable or disable Expose and Sweep buttons.
		"""
		if doEnable:
			self.exposeBtn["state"] = "normal"
			self.sweepBtn["state"] = "normal"
		else:
			self.exposeBtn["state"] = "disabled"
			self.sweepBtn["state"] = "disabled"

	def end(self, sr):
		"""If telescope moved, restore original boresight position.
		"""
		self.enableBtns(False)

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
	
	def getInstInfo(self):
		"""Obtains instrument data.
		
		Verifies the correct instrumen and sets:
		- self.instScale
		- self.instCtr
		- self.instLim
		- self.arcsecPerPixel
		
		Raises ScriptError if wrong instrument.
		"""
		sr = self.sr
		if not sr.debug:
			# Make sure current instrument is DIS
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
		"""Return the numeric value of a widget, or raise ScriptError if blank"""
		numVal = wdg.getNumOrNone()
		if numVal != None:
			return numVal
		raise self.sr.ScriptError(descr + " not specified")
	
	def initAll(self):
		"""Initialize variables, table and graph.
		"""
		# initialize shared variables
		self.didMove = False
		self.focDir = None
		self.boreXYDeg = None
		self.starXYPix = None
		self.begBoreXY = [None, None]
		self.instScale = None
		self.arcsecPerPixel = None
		self.instCtr = None
		self.instLim = None
		self.doSweep = False
		self.plotLine = None

		# clear the table
		self.logWdg.clearOutput()
		self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
		self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
		
		# clear the graph
		self.plotAxis.clear()
		self.plotAxis.grid(True)
		# start with autoscale disabled due to bug in matplotlib
		self.plotAxis.set_autoscale_on(False)
		self.figCanvas.draw()
		
		# disable Enable and Sweep buttons
		self.enableBtns(False)
		
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

	def graphFocusMeas(self, focList, fwhmList, scalex=False):
		"""Graph measured fwhm vs focus"""
		print "graphFocusMeas(focList=%s, fwhmList=%s)" % (focList, fwhmList)
		
		numMeas = len(focList)
		if len(fwhmList) != numMeas:
			raise RuntimeError("length of focList and fwhmList don't match; focList=%s, fwhmList=%s" % (focList, fwhmList))
		if numMeas == 0:
			return

		minFoc = min(focList) - FocGraphMargin
		maxFoc = max(focList) + FocGraphMargin
		minFWHM = min(fwhmList) * 0.95
		maxFWHM = max(fwhmList) * 1.05
		if not self.plotLine:
			self.plotLine = self.plotAxis.plot(focList, fwhmList, 'bo')[0]
		else:
			self.plotLine.set_data(focList[:], fwhmList[:])
		if scalex:
			self.plotAxis.set_xlim(minFoc, maxFoc)
		self.plotAxis.set_ylim(minFWHM, maxFWHM)
		self.figCanvas.draw()
		
	def run(self, sr):
		"""Take the series of focus exposures.
		"""
		print "sr.debug=", sr.debug
		self.initAll()
		
		# open DIS Slitviewer window
		self.tuiModel.tlSet.makeVisible(self.guideTLName)
		self.sr.master.winfo_toplevel().lift()
		
		# fake data for debug mode
		# iteration #, FWHM
		self.debugIterFWHM = (1, 2.0)
		
		self.getInstInfo()

		# set starXYPix and shift boresight
		self.boreXYDeg = [self.getEntryNum(wdg, name) / 3600.0 for (name, wdg) in self.boreNameWdgSet]
		self.starXYPix = [(self.boreXYDeg[ii] * self.instScale[ii]) + self.instCtr[ii] for ii in range(2)]
		yield self.waitMoveBoresight()

		focPosList = []
		fwhmList = []
		
		# take exposure and try to centroid
		# if centroid fails, ask user to acquire a star
		testNum = 0
		while not self.doSweep:
			testNum += 1
			focPos = float(self.centerFocPosWdg.get())
			if focPos == None:
				raise sr.ScriptError("Must specify center focus")
			yield self.waitSetFocus(focPos, False)
			sr.showMsg("Taking test exposure at focus %.1f %sm" % \
				(focPos, RO.StringUtil.MuStr))
			yield self.waitCentroid()

			fwhm = sr.value
			self.logFocusMeas("Exp %d" % (testNum,), focPos, fwhm)
			if fwhm == None:
				msgStr = "No star found! Fix and then press Expose or Sweep"
			else:
				focPosList.append(focPos)
				fwhmList.append(fwhm)
				self.graphFocusMeas(focPosList, fwhmList, scalex = True)
				msgStr = "Press Expose or Sweep to continue"

			# wait for user to press the Expose or Sweep button
			# note: the only time they should be enabled is during this wait
			self.enableBtns(True)
			sr.showMsg(msgStr, RO.Constants.sevWarning)
			yield sr.waitUser()
			self.enableBtns(False)

		
		# at this point a suitable star should be on the boresight...
			
		# record parameters that cannot be changed while script is running
		centerFocPos = float(self.getEntryNum(self.centerFocPosWdg, "Center Focus"))
		focusRange   = float(self.getEntryNum(self.focusRangeWdg, "Focus Range"))
		startFocPos = centerFocPos - (focusRange / 2.0)
		endFocPos = startFocPos + focusRange
		numFocPos   = self.getEntryNum(self.numFocusPosWdg, "Focus Positions")
		if numFocPos < 2:
			raise sr.ScriptError("# Focus Positions < 2")
		focusIncr    = self.focusIncrWdg.getNum()
		numExpPerFoc = 1
		self.focDir = (endFocPos > startFocPos)
		
		plotMin = startFocPos
		plotMax = startFocPos + focusRange
		if focPosList:
			plotMin = min(plotMin, min(focPosList))
			plotMax  = max(plotMax, max(focPosList))
		plotMin -= FocGraphMargin
		plotMax += FocGraphMargin

		self.plotAxis.set_xlim((plotMin, plotMax))
		self.figCanvas.draw()
		
		numMeas = 0
		for focInd in range(numFocPos):
			focPos = float(startFocPos + (focInd*focusIncr))

			doBacklashComp = (focInd == 0)
			yield self.waitSetFocus(focPos, doBacklashComp)
			sr.showMsg("Exposing at focus %.1f %sm" % \
				(focPos, RO.StringUtil.MuStr))
			yield self.waitCentroid()
			if sr.debug:
				fwhm = 0.0001 * (focPos - centerFocPos) ** 2
				fwhm += random.gauss(1.0, 0.25)
			else:
				fwhm = sr.value

			self.logFocusMeas("Sweep %d" % (focInd+1,), focPos, fwhm)
			
			if fwhm != None:
				focPosList.append(focPos)
				fwhmList.append(fwhm)
				self.graphFocusMeas(focPosList, fwhmList)
		
		if len(focPosList) < 3:
			raise sr.ScriptError("Need >=3 measurements to fit best focus")
	
		# Fit a curve to the data
		# arrays for holding values as we take exposures
		numMeas = len(focPosList)
		focPosArr = num.array(focPosList, num.Float)
		fwhmArr  = num.array(fwhmList, num.Float)
		weightArr = num.ones(numMeas, num.Float)
		coeffs = polyfitw(focPosArr, fwhmArr, weightArr, 2, False)
		
		# find the best focus position
		minFoc = min(focPosList)
		maxFoc = max(focPosList)
		bestEstFocPos = (-1.0*coeffs[1])/(2.0*coeffs[2])
		bestEstFWHM = coeffs[0]+coeffs[1]*bestEstFocPos+coeffs[2]*bestEstFocPos*bestEstFocPos
		if not min(minFoc, maxFoc) <= bestEstFocPos <= max(minFoc, maxFoc):
			# best estimate is no good; reject it
			bestEstFWHM = None
			self.logFocusMeas("BestEst", bestEstFocPos, bestEstFWHM)
			sr.showMsg("Could not fit a best focus")
			return
		
		self.logFocusMeas("BestEst", bestEstFocPos, bestEstFWHM)

		# generate the data from the 2nd order fit
		x = num.arange(min(focPosArr), max(focPosArr), 1)
		y = coeffs[0] + coeffs[1]*x + coeffs[2]*(x**2.0)
		
		# plot the fit, and the chosen focus position in green
		self.plotAxis.plot(x, y, '-k', linewidth=2)
		self.plotAxis.plot([bestEstFocPos], [bestEstFWHM], 'go')
		self.figCanvas.draw()
	
		# move to best focus if "Move to best Focus" checked
		movebest = self.moveBestFocus.getBool()
		if movebest:
			self.setCurrFocus()
			yield self.waitSetFocus(bestEstFocPos, doBacklashComp=True)
			sr.showMsg("Exposing at estimated best focus %d %sm" % \
				(bestEstFocPos, RO.StringUtil.MuStr))
			yield self.waitCentroid()
			if sr.debug:
				finalFWHM = 1.1
			else:
				finalFWHM = sr.value
			
			self.logFocusMeas("BestMeas", bestEstFocPos, finalFWHM)
			
			if finalFWHM != None:
				self.plotAxis.plot([bestEstFocPos], [finalFWHM], 'ro')
				self.figCanvas.draw()
			else:
				self.sr.showMsg("Could not measure FWHM at estimated best focus",
					severity=RO.Constants.sevWarning,
				)
	
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

	def waitCentroid(self):
		"""Take an exposure and centroid at the current position"""
		sr = self.sr
		expTime = self.getEntryNum(self.expTimeWdg, "Exposure Time")
		centroidRadArcSec = self.getEntryNum(self.centroidRadWdg, "Centroid Radius")
		centroidRadPix =  centroidRadArcSec / self.arcsecPerPixel
		winRad = centroidRadPix * WinSizeMult
		print "instLim=", self.instLim
		print "starXYPix=", self.starXYPix
		windowMinXY = [max(self.instLim[ii], self.starXYPix[ii] - winRad) for ii in range(2)]
		windowMaxXY = [min(self.instLim[ii-2], self.starXYPix[ii] + winRad) for ii in range(2)]
		offsetStarXYPix = [self.starXYPix[ii] - windowMinXY[ii] for ii in range(2)]
		centroidCmdStr = "centroid time=%s bin=1 on=%.1f,%.1f cradius=%.1f window=%d,%d,%d,%d" % \
			(expTime, offsetStarXYPix[0], offsetStarXYPix[1], centroidRadPix,
			windowMinXY[0], windowMinXY[1], windowMaxXY[0], windowMaxXY[1])
		
		yield sr.waitCmd(
		   actor = self.gcamName,
		   cmdStr = centroidCmdStr,
		   keyVars = (self.guideModel.files, self.guideModel.star),
		   checkFail = False,
		)
		cmdVar = sr.value
		starData = cmdVar.getKeyVarData(self.guideModel.star)
		if starData:
			sr.value = starData[0][8]
			return

		if not cmdVar.getKeyVarData(self.guideModel.files):
			sr.ScriptError("Exposure failed")
		sr.value = None
	
	def waitMoveBoresight(self):
		"""Move the boresight, take an exposure and pause the script.
		
		Records the initial boresight position in self.begBoreXY
		and sets self.didMove when the move begins.
		"""
		sr = self.sr
		
		# record the relevant parameters
		expTime = self.getEntryNum(self.expTimeWdg, "Exposure Time")
		centroidRad = self.getEntryNum(self.centroidRadWdg, "Centroid Radius")
			
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
	
	
def polyfitw(x, y, w, ndegree, return_fit=False):
	"""
	Performs a weighted least-squares polynomial fit with optional error estimates.

	Inputs:
		x: 
			The independent variable vector.

		y: 
			The dependent variable vector.  This vector should be the same 
			length as X.

		w: 
			The vector of weights.  This vector should be same length as 
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

	Written by:	 George Lawrence, LASP, University of Colorado,
					December, 1981 in IDL.
					Weights added, April, 1987,  G. Lawrence
					Fixed bug with checking number of params, November, 1998, 
					Mark Rivers.  
					Python version, May 2002, Mark Rivers
	"""
	n = min(len(x), len(y)) # size = smaller of x,y
	m = ndegree + 1				# number of elements in coeff vector
	a = num.zeros((m,m), num.Float)  # least square matrix, weighted matrix
	b = num.zeros(m, num.Float)	 # will contain sum w*y*x^j
	z = num.ones(n, num.Float)	 # basis vector for constant term

	a[0,0] = num.sum(w)
	b[0] = num.sum(w*y)

	for p in range(1, 2*ndegree+1):		 # power loop
		z = z*x	# z is now x^p
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
		z = z*x		 # z is now x^p
		sum = 0.
		for j in range(max(0, (p - ndegree)), min(ndegree, p)+1):
			sum = sum + a[j,p-j]
		yband = yband + sum * z		 # add in all the error sources
	yband = yband*var
	yband = num.sqrt(yband)
	return c, yfit, yband, sigma, a
