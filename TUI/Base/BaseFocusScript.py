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
- Consider a separate button to clear boresight offset;
  then the user can keep hacking at the problem
  until they like the focus.
  Or only clear boresight if focus succeeds.
  Or...? It's probably safer as it is.
- Fix truncation of text around edge of graph;
  would it help to ditch axis labels?
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
"""
import math
import numarray
import Numeric
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
DefFocusNPos = 5  # number of focus positions
DefDeltaFoc = 200 # default focus range around current focus
FocusWaitMS = 1000 # time to wait after every focus adjustment (ms)
BacklashComp = 0 # amount of backlash compensation, in microns (0 for none)

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

		self.expTimeWdg = RO.Wdg.FloatEntry(
			sr.master,
			minValue = self.guideModel.gcamInfo.minExpTime,
			maxValue = self.guideModel.gcamInfo.maxExpTime,
			defValue = self.guideModel.gcamInfo.defExpTime,
			defFormat = "%.1f",
			defMenu = "Current",
			minMenu = "Minimum",
			helpText = "Exposure time",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Exposure Time", self.expTimeWdg, "sec")
		
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
				helpText = wdgName + " position",
				helpURL = self.helpURL,
			)
			if showWdg:
				gr.gridWdg(wdgName, boreWdg, "arcsec")
			self.boreNameWdgSet.append((wdgName, boreWdg))


		self.centroidRadWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = 5,
			maxValue = 1024,
			defValue = defRadius,
			helpText = "Centroid radius; don't skimp",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Centroid Radius", self.centroidRadWdg, "arcsec", sticky="ew")

		setDefFocusWdg = RO.Wdg.Button(
			master = sr.master,
			text = "Start Focus",
			callFunc = self.setDefFocus,
			helpText = "Set default focus values",
			helpURL = self.helpURL,
		)
	
		self.startFocusPosWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = -2000,
			helpText = "Initial focus offset",
			helpURL = self.helpURL,
		)
		gr.gridWdg(setDefFocusWdg, self.startFocusPosWdg, MicronStr)
#		setDefFocusWdg.grid(
#			row = gr.getNextRow() - 1,
#			column = gr.getNextCol(),
#		)
	
		self.endFocusPosWdg = RO.Wdg.IntEntry(
			master = sr.master,
			maxValue = 2000,
			helpText = "Final focus offset",
			helpURL = self.helpURL,
		)
		gr.gridWdg("End Focus", self.endFocusPosWdg, MicronStr)
	
		self.numFocusPosWdg = RO.Wdg.IntEntry(
			master = sr.master,
			minValue = 2,
			defValue = DefFocusNPos,
			helpText = "Number of focus positions",
			helpURL = self.helpURL,
		)
		gr.gridWdg("Focus Positions", self.numFocusPosWdg, "")
		
		self.focusIncrWdg = RO.Wdg.FloatEntry(
			master = sr.master,
			defFormat = "%.0f",
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
			helpText = "Move to Best Focus when done?",
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

		self.endFocusPosWdg.addCallback(self.updFocusIncr, callNow=False)
		self.startFocusPosWdg.addCallback(self.updFocusIncr, callNow=False)
		self.numFocusPosWdg.addCallback(self.updFocusIncr, callNow=True)
		
		if sr.debug:
			self.expTimeWdg.set("1")
			self.startFocusPosWdg.set(-50)
			self.endFocusPosWdg.set(100)
			self.numFocusPosWdg.set(3)
		
		self.initAll()
		# try to get focus away from graph (but it doesn't work; why?)
		self.expTimeWdg.focus_set()
		self.setDefFocus()
		
	def end(self, sr):
		"""If telescope moved, restore original boresight position.
		"""
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
		self.starXYPos = None
		self.begBoreXY = [None, None]
		self.instScale = None
		self.arcsecPerPixel = None
		self.instCtr = None
		self.instLim = None

		# clear the table
		self.logWdg.clearOutput()
		self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
		self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
		
		# clear the graph
		self.plotAxis.clear()
		self.plotAxis.grid(True)
		self.figCanvas.draw()
		
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
		self.logWdg.addOutput("%s\t%d\t%s\t%s\n" % \
			(name, focPos, fwhmStr, fwhmArcSecStr)
		)

	def run(self, sr):
		"""Take the series of focus exposures.
		"""
		print "sr.debug=", sr.debug
		self.initAll()
		
		# open DIS Slitviewer window
		self.tuiModel.tlSet.makeVisible(self.guideTLName)
		
		# fake data for debug mode
		# iteration #, FWHM
		self.debugIterFWHM = (1, 2.0)
		
		self.getInstInfo()

		# set starXYPix and shift boresight
		self.boreXYDeg = [self.getEntryNum(wdg, name) / 3600.0 for (name, wdg) in self.boreNameWdgSet]
		self.starXYPix = [(self.boreXYDeg[ii] * self.instScale[ii]) + self.instCtr[ii] for ii in range(2)]
		yield self.waitMoveBoresight()
		
		# take exposure and try to centroid
		# if centroid fails, ask user to acquire a star
		sr.showMsg("Taking a test exposure.")
		yield self.waitCentroid()
		if sr.value == None:
			msgStr = "No star found; please fix and then Resume"
		else:
			msgStr = "Press Resume to start the focus sweep"
		sr.pause()
		sr.master.after(1, sr.showMsg, "Put a star on the boresight, then Resume", RO.Constants.sevWarning)
		
		# at this point a suitable star should be on the boresight...
			
		# record parameters that cannot be changed while script is running
		startFocPos	= self.getEntryNum(self.startFocusPosWdg, "Start Focus")
		endFocPos   = self.getEntryNum(self.endFocusPosWdg, "End Focus")
		numFocPos   = self.getEntryNum(self.numFocusPosWdg, "Focus Positions")
		if numFocPos < 2:
			raise sr.ScriptError("# Focus Positions < 2")
		incFocus    = self.focusIncrWdg.getNum()
		numExpPerFoc = 1
		self.focDir = (endFocPos > startFocPos)
		
		# arrays for holding values as we take exposures
		focPosArr = numarray.zeros(numFocPos, "Float")
		fwhmArr  = numarray.zeros(numFocPos, "Float")
		coeffArr = numarray.zeros(numFocPos, "Float")
		weightArr = numarray.ones(numFocPos, "Float")

		minFoc = startFocPos
		maxFoc = int(startFocPos + round((numFocPos-1)*incFocus))

		plotLine = self.plotAxis.plot([], [], 'bo')[0]
		self.plotAxis.set_xlim((minFoc, maxFoc))
		self.figCanvas.draw()
		
		numMeas = 0
		for focInd in range(numFocPos):
			focPos = int(startFocPos + round(focInd*incFocus))

			doBacklashComp = (focInd == 0)
			yield self.waitSetFocus(focPos, doBacklashComp)
			sr.showMsg("Exposing at focus %d %sm" % \
				(focPos, RO.StringUtil.MuStr))
			yield self.waitCentroid()
			fwhm = sr.value

			self.logFocusMeas("Exp %d" % focInd, focPos, fwhm)
			
			if fwhm != None:
				numMeas += 1
				focPosArr[numMeas-1] = focPos
				fwhmArr[numMeas-1] = fwhm
				minFWHM = fwhmArr[:numMeas].min()
				maxFWHM = fwhmArr[:numMeas].max()
				if minFWHM == maxFWHM:
					minFWHM *= 0.95
					maxFWHM *= 1.05
				plotLine.set_data(focPosArr[:numMeas], fwhmArr[:numMeas])
				self.plotAxis.set_xlim(minFoc, maxFoc)
				self.plotAxis.set_ylim(minFWHM, maxFWHM)
				self.figCanvas.draw()
		
		if numMeas < 3:
			raise sr.ScriptError("Need >=3 measurements to fit best focus")
	
		# Fit a curve to the data
		coeffArr = polyfitw(focPosArr[:numMeas], fwhmArr[:numMeas], weightArr[:numMeas], 2, 0)
		
		# find the best focus position
		bestEstFocPos = (-1.0*coeffArr[1])/(2.0*coeffArr[2])
		bestEstFWHM = coeffArr[0]+coeffArr[1]*bestEstFocPos+coeffArr[2]*bestEstFocPos*bestEstFocPos
		if not minFoc <= bestEstFocPos <= maxFoc:
			# best estimate is no good; reject it
			bestEstFWHM = None
			self.logFocusMeas("BestEst", bestEstFocPos, bestEstFWHM)
			sr.showMsg("Could not fit a best focus")
			return
		
		self.logFocusMeas("BestEst", bestEstFocPos, bestEstFWHM)

		# generate the data from the 2nd order fit
		x = numarray.arange(min(focPosArr),max(focPosArr),1)
		y = coeffArr[0] + coeffArr[1]*x + coeffArr[2]*(x**2.0)
		
		# plot the fit, and the chosen focus position in green
		self.plotAxis.plot(x, y, '-k', linewidth=2)
		self.plotAxis.plot([bestEstFocPos], [bestEstFWHM], 'go')
		self.figCanvas.draw()
	
		# move to best focus if "Move to best Focus" checked
		movebest = self.moveBestFocus.getBool()
		if movebest:
			yield self.waitSetFocus(bestEstFocPos, doBacklashComp=True)
			sr.showMsg("Exposing at estimated best focus %d %sm" % \
				(bestEstFocPos, RO.StringUtil.MuStr))
			yield self.waitCentroid()
			finalFWHM = sr.value
			
			self.logFocusMeas("BestMeas", bestEstFocPos, finalFWHM)
			
			if finalFWHM != None:
				self.plotAxis.plot([bestEstFocPos], [finalFWHM], 'ro')
				self.figCanvas.draw()
			else:
				self.sr.showMsg("Could not measure FWHM at estimated best focus",
					severity=RO.Constants.sevWarning,
				)
	
	def setDefFocus(self, *args):
		"""Set focus start and end widgets to default values
		based on the current focus.
		"""
		currFocus = self.sr.getKeyVar(self.tccModel.secFocus, defVal=None)
		if currFocus == None:
			self.sr.showMsg("Current focus not known",
				severity=RO.Constants.sevWarning,
			)
			return
		
		startFocus = int(round(currFocus - (DefDeltaFoc / 2)))
		endFocus = startFocus + DefDeltaFoc
		self.startFocusPosWdg.set(startFocus)
		self.endFocusPosWdg.set(endFocus)
		self.numFocusPosWdg.set(DefFocusNPos)
	
	def updFocusIncr(self, *args):
		"""Update focus increment widget.
		"""
		startPos = self.startFocusPosWdg.getNumOrNone()
		endPos = self.endFocusPosWdg.getNumOrNone()
		numPos = self.numFocusPosWdg.getNumOrNone()
		if None in (startPos, endPos, numPos):
			self.focusIncrWdg.set(None, isCurrent = False)
			return

		focusIncr = (endPos - startPos) / (numPos - 1)
		self.focusIncrWdg.set(focusIncr, isCurrent = True)

	def waitCentroid(self):
		"""Take an exposure and centroid at the current position"""
		sr = self.sr
		expTime = self.getEntryNum(self.expTimeWdg, "Exposure Time")
		centroidRadArcSec = self.getEntryNum(self.centroidRadWdg, "Centroid Radius")
		centroidRadPix =  centroidRadArcSec / self.arcsecPerPixel
		centroidCmdStr = "centroid time=%s bin=1 on=%.1f,%.1f cradius=%.1f" % \
			(expTime, self.starXYPix[0], self.starXYPix[1], centroidRadPix)
		yield sr.waitCmd(
		   actor = self.gcamName,
		   cmdStr = centroidCmdStr,
		   keyVars = (self.guideModel.files, self.guideModel.star),
		   checkFail = False,
		)
		if not sr.debug:
			cmdVar = sr.value
			starData = cmdVar.getKeyVarData(self.guideModel.star)
			if starData:
				sr.value = starData[0][8]
				return
	
			if not cmdVar.getKeyVarData(self.guideModel.files):
				sr.ScriptError("Exposure failed")
			sr.value = None
		else:
			iterNum, fwhm = self.debugIterFWHM
			sr.value = fwhm
			if iterNum < 3:
				nextFWHM = fwhm - 0.2
			else:
				nextFWHM = fwhm + 0.2
			self.debugIterFWHM = (iterNum + 1, nextFWHM)
	
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
		
		# to try to eliminate the backlash in the secondary mirror drive move back 1/2 the
		# distance between the start and end position from the bestEstFocPos
		if doBacklashComp and BacklashComp:
			backlashFocPos = focPos - (abs(BacklashComp) * self.focDir)
			sr.showMsg("Backlash comp: moving focus to %d %sm" % (backlashFocPos, RO.StringUtil.MuStr))
			yield sr.waitCmd(
			   actor = "tcc",
			   cmdStr = "set focus=%d" % (backlashFocPos),
			)
			yield sr.waitMS(FocusWaitMS)
		
		# move to desired focus position
		sr.showMsg("Moving focus to %d %sm" % (focPos, RO.StringUtil.MuStr))
		yield sr.waitCmd(
		   actor = "tcc",
		   cmdStr = "set focus=%d" % (focPos),
		)
		yield sr.waitMS(FocusWaitMS)
	
	
def polyfitw(x, y, w, ndegree, return_fit=0):
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
		If return_fit==0 (the default) then polyfitw returns only C, a vector of 
		coefficients of length ndegree+1.
		If return_fit!=0 then polyfitw returns a tuple (c, yfit, yband, sigma, a)
			yfit:	
			The vector of calculated Y's.  Has an error of + or - Yband.

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
	a = Numeric.zeros((m,m),Numeric.Float)  # least square matrix, weighted matrix
	b = Numeric.zeros(m,Numeric.Float)	 # will contain sum w*y*x^j
	z = Numeric.ones(n,Numeric.Float)	 # basis vector for constant term

	a[0,0] = Numeric.sum(w)
	b[0] = Numeric.sum(w*y)

	for p in range(1, 2*ndegree+1):		 # power loop
		z = z*x	# z is now x^p
		if (p < m):  b[p] = Numeric.sum(w*y*z)	# b is sum w*y*x^j
		sum = Numeric.sum(w*z)
		for j in range(max(0,(p-ndegree)), min(ndegree,p)+1):
			a[j,p-j] = sum

	a = LinearAlgebra.inverse(a)
	c = Numeric.matrixmultiply(b, a)
	if (return_fit == 0):
		return c		 # exit if only fit coefficients are wanted

	# compute optional output parameters.
	yfit = Numeric.zeros(n,Numeric.Float)+c[0]	# one-sigma error estimates, init
	for k in range(1, ndegree +1):
		yfit = yfit + c[k]*(x**k)  # sum basis vectors
	var = Numeric.sum((yfit-y)**2 )/(n-m)  # variance estimate, unbiased
	sigma = Numeric.sqrt(var)
	yband = Numeric.zeros(n,Numeric.Float) + a[0,0]
	z = Numeric.ones(n,Numeric.Float)
	for p in range(1,2*ndegree+1):		# compute correlated error estimates on y
		z = z*x		 # z is now x^p
		sum = 0.
		for j in range(max(0, (p - ndegree)), min(ndegree, p)+1):
			sum = sum + a[j,p-j]
		yband = yband + sum * z		 # add in all the error sources
	yband = yband*var
	yband = Numeric.sqrt(yband)
	return c, yfit, yband, sigma, a
