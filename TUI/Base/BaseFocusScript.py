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
- Fix graph y limits to include minimum of fit curve
  (which occasionally may be lower than anything else)
  and the final measured focus (ditto).
- Finish ImagerFocusScript;
  make sure it can handle an instrument (no guide camera)
  and the NA2 guider (can send gcam commands).
  This may be best done by creating a 3rd class, but I hope not.
  Still...exposures are very different for the two cases
  because an instrument requires first taking an exposure
  by talking to the instrument and then using nfocus to analyse the image.
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
					Created SlitviewerFocusScript and ImagerFocusScript classes;
					the latter is not yet fully written.
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
MaxFocSigma = 100 # maximum allowed sigma of best fit focus, in um

MicronStr = RO.StringUtil.MuStr + "m"

class BaseFocusScript(object):
	"""Basic focus script object.
	
	This is a virtual base class. The inheritor must:
	- Provide widgets
	- Provide a "run" method
	
	Inputs:
	- gcamName: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- defRadius: default centroid radius, in arcsec
	- helpURL: URL of help file
	- debug: if True, run in debug mode, which uses fake data
		and does not communicate with the hub.
	"""
	def __init__(self,
		sr,
		gcamName,
		instName,
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
		self.defRadius = defRadius
		self.helpURL = helpURL
		
		# fake data for debug mode
		self.debugIterFWHM = None
		
		# get various models
		self.tccModel = TUI.TCC.TCCModel.getModel()
		self.tuiModel = TUI.TUIModel.getModel()
		self.guideModel = TUI.Guide.GuideModel.getModel(self.gcamName)
		
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
#		setCurrFocusWdg.grid(
#			row = self.gr.getNextRow() - 1,
#			column = self.gr.getNextCol(),
#		)
	
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
		self.gr.gridWdg(False, (self.exposeBtn, self.sweepBtn))
		
		if sr.debug:
			self.expTimeWdg.set("1")
			self.centerFocPosWdg.set(0)
			self.focusRangeWdg.set(200)
			self.numFocusPosWdg.set(5)
	
	def doExposeBtn(self, wdg=None):
		self.doSweep = False
		self.sr.resumeUser()
		
	def doSweepBtn(self, wdg=None):
		self.doSweep = True
		self.sr.resumeUser()
		
	def enableCmdBtns(self, doEnable):
		"""Enable or disable command buttons (e.g. Expose and Sweep).
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

	def graphFocusMeas(self, focPosFWHMList, rescaleX=False):
		"""Graph measured fwhm vs focus.
		
		Inputs:
		- focPosFWHMList: list of data items:
			- focus position (um)
			- measured FWHM (binned pixels)
		- rescaleX: adjust x axis limits?
		"""
		#print "graphFocusMeas(focPosFWHMList=%s, rescaleX=%r)" % (focPosFWHMList, rescaleX)
		numMeas = len(focPosFWHMList)
		if numMeas == 0:
			return

		focPosList, fwhmList = zip(*focPosFWHMList)
		if not self.plotLine:
			self.plotLine = self.plotAxis.plot(focPosList, fwhmList, 'bo')[0]
		else:
			self.plotLine.set_data(focPosList[:], fwhmList[:])
		
		if rescaleX:
			minFoc = min(focPosList) - FocGraphMargin
			maxFoc = max(focPosList) + FocGraphMargin
			self.plotAxis.set_xlim(minFoc, maxFoc)
		
		minFWHM = min(fwhmList) * 0.95
		maxFWHM = max(fwhmList) * 1.05
		self.plotAxis.set_ylim(minFWHM, maxFWHM)
		
		self.figCanvas.draw()
		
	def run(self, sr):
		"""Take the series of focus exposures.
		"""
		raise NotImplementedError("Subclass must implement run")
	
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
	
	def waitFocusSweep(self, focPosFWHMList=None):
		"""Conduct a focus sweep.
		
		Inputs:
		- focPosFWHMList: initial list of data items:
			- focus position (um)
			- measured FWHM (binned pixels)
			None if no such data
		"""
		sr = self.sr

		if focPosFWHMList == None:
			focPosFWHMList = []
		else:
			focPosFWHMList = list(focPosFWHMList)

		# record parameters that cannot be changed while script is running
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
		
		plotMin = startFocPos
		plotMax = startFocPos + focusRange
		if focPosFWHMList:
			focPosList, fwhmList = zip(*focPosFWHMList)
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
				focPosFWHMList.append((focPos, fwhm))
				self.graphFocusMeas(focPosFWHMList, rescaleX=False)
		
		if len(focPosFWHMList) < 3:
			raise sr.ScriptError("Need >=3 measurements to fit best focus")
		
		# Fit a curve to the data
		# arrays for holding values as we take exposures
		numMeas = len(focPosFWHMList)
		focPosList, fwhmList = zip(*focPosFWHMList)
		focPosArr = num.array(focPosList, num.Float)
		fwhmArr  = num.array(fwhmList, num.Float)
		weightArr = num.ones(numMeas, num.Float)
		coeffs, yfit, yband, sigma, corrMatrix = polyfitw(focPosArr, fwhmArr, weightArr, 2, True)
		print "FWHM sigma=", sigma
		
		# See if fit is good enough to use
		if coeffs[2] <= 0.0:
			sr.showMsg("Could not fit best focus: no minimum")
			return
		
		focSigma = math.sqrt(sigma / coeffs[2])
		print "foc sigma=", focSigma
		if focSigma > MaxFocSigma:
			sr.showMsg(u"Best focus \N{GREEK SMALL LETTER SIGMA} too large: %.0f > %.0f" % (focSigma, MaxFocSigma))
			return
		
		# find the best focus position
		minFoc = min(focPosList)
		maxFoc = max(focPosList)
		bestEstFocPos = (-1.0*coeffs[1])/(2.0*coeffs[2])
		bestEstFWHM = coeffs[0]+coeffs[1]*bestEstFocPos+coeffs[2]*bestEstFocPos*bestEstFocPos
#		if not min(minFoc, maxFoc) <= bestEstFocPos <= max(minFoc, maxFoc):
#			# best estimate is no good; reject it
#			bestEstFWHM = None
#			self.logFocusMeas("BestEst", bestEstFocPos, bestEstFWHM)
#			sr.showMsg("Best focus=%.0f out of sweep range" % (bestEstFocPos,))
#			return
		
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
	- gcamName: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- guideTLName: name of guide toplevel (e.g. "Guide.DIS Slitviewer")
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
		self.guideTLName = guideTLName
		if len(defBoreXY) != 2:
			raise ValueError("defBoreXY=%s must be a pair of values" % defBoreXY)
		self.defBoreXY = defBoreXY
		
		BaseFocusScript.__init__(self,
			sr = sr,
			gcamName = gcamName,
			instName = instName,
			defRadius = defRadius,
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
				self.gr.gridWdg(wdgName, boreWdg, "arcsec")
			self.boreNameWdgSet.append((wdgName, boreWdg))

	def run(self, sr):
		"""Take the series of focus exposures.
		"""
		self.initAll()
		
		# open slitviewer window
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
		
		focPosFWHMList = []
		
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
				focPosFWHMList.append((focPos, fwhm))
				self.graphFocusMeas(focPosFWHMList, rescaleX=True)
				msgStr = "Press Expose or Sweep to continue"

			# wait for user to press the Expose or Sweep button
			# note: the only time they should be enabled is during this wait
			self.enableCmdBtns(True)
			sr.showMsg(msgStr, RO.Constants.sevWarning)
			yield sr.waitUser()
			self.enableCmdBtns(False)

		
		yield self.waitFocusSweep(focPosFWHMList = focPosFWHMList)
	
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




class ImagerFocusScript(BaseFocusScript):
	"""Focus script for imagers (non slitviewers)
	
	Inputs:
	- gcamName: name of guide camera actor (e.g. "dcam")
	- instName: name of instrument (e.g. "DIS")
	- guideTLName: name of guide toplevel (e.g. "Guide.DIS Slitviewer")
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
		self.guideTLName = guideTLName
		if len(defBoreXY) != 2:
			raise ValueError("defBoreXY=%s must be a pair of values" % defBoreXY)
		self.defBoreXY = defBoreXY
		
		BaseFocusScript.__init__(self,
			sr = sr,
			gcamName = gcamName,
			instName = instName,
			defRadius = defRadius,
			helpURL = helpURL,
			debug = debug,
		)

	def createSpecialWdg(self):
		# create star position widgets
		sr = self.sr
		self.starPosWdgSet = []
		for ii in range(2):
			letter = ("X", "Y")[ii]
			wdgName = "Star Pos %s" % (letter,)
			starPosWdg = RO.Wdg.FloatEntry(
				master = sr.master,
				minValue = 0,
				maxValue = 5000,
				helpText = wdgName + " position",
				helpURL = self.helpURL,
			)
			if showWdg:
				self.gr.gridWdg(wdgName, starPosWdg, "pix")
			self.starPosWdgSet.append((wdgName, starPosWdg))

	def run(self, sr):
		"""Run the focus script.
		"""
		self.initAll()
		
		# fake data for debug mode
		# iteration #, FWHM
		self.debugIterFWHM = (1, 2.0)
		
		self.getInstInfo()

		# set starXYPix
		self.starXYPix = [self.getEntryNum(wdg, name) for (name, wdg) in self.starPosWdgSet]
		
		focPosFWHMList = []
		
		# take exposure and find best star
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
				focPosFWHMList.append((focPos, fwhm))
				self.graphFocusMeas(focPosFWHMList, rescaleX=True)
				msgStr = "Press Expose or Sweep to continue"

			# wait for user to press the Expose or Sweep button
			# note: the only time they should be enabled is during this wait
			self.enableCmdBtns(True)
			sr.showMsg(msgStr, RO.Constants.sevWarning)
			yield sr.waitUser()
			self.enableCmdBtns(False)

		
		yield self.waitFocusSweep(focPosFWHMList = focPosFWHMList)

	def waitFindStar(self):
		"""Take an exposure and find the best star that can be centroided.
		"""
		sr = self.sr
		expTime = self.getEntryNum(self.expTimeWdg, "Exposure Time")
		self.logMsg("Exposing %s sec to find best star" % (expTime,))
		findStarCmdStr = "findstars time=%s bin=1 on=%.1f,%.1f" % \
			(expTime, offsetStarXYPix[0], offsetStarXYPix[1], findStarRadPix,
			windowMinXY[0], windowMinXY[1], windowMaxXY[0], windowMaxXY[1])
		
		yield sr.waitCmd(
		   actor = self.gcamName,
		   cmdStr = findStarCmdStr,
		   keyVars = (self.guideModel.files, self.guideModel.star),
		   checkFail = False,
		)
		cmdVar = sr.value
		if not cmdVar.getKeyVarData(self.guideModel.files):
			sr.ScriptError("Exposure failed")
		starDataList = cmdVar.getKeyVarData(self.guideModel.star)
		if starDataList:
			# try to centroid each star in turn, starting from the first seen;
			# if none can be centroided, give up
			fileInfo = cmdVar.getKeyVarData(self.guideModel.files)[0]
			filePath = "".join(fileInfo[2:4])
			
			for starData in starDataList:
				starXYPos = starData[2:4]
				self.logMsg("Centroiding star at %.1f, %.1f" % tuple(starXYPos))
				centroidCmdStr = "centroid file=%s on=%.1f,%.1f cradius=%.1f" % \
					(filePath, starXYPos[0], starXYPos[1], centroidRadPix)
				yield sr.waitCmd(
				   actor = self.gcamName,
				   cmdStr = centroidCmdStr,
				   keyVars = (self.guideModel.star,),
				   checkFail = False,
				)
				cmdVar = sr.value
				starData = cmdVar.getKeyVarData(self.guideModel.star)
				if starData:
					self.starXYPix = starXYPos
					for ii in range(2):
						wdg = self.starPosWdgSet[ii][1]
						wdg.set(starXYPos[ii])
					return
					self.logMsg("Found star at %.1f, %.1f" % tuple(starXYPos))

		self.logMsg("No stars found", severity=RO.Constants.sevWarning)


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
