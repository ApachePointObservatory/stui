#!/usr/local/bin/python
from __future__ import generators
"""Configuration input panel for NICFPS.

To do:
- Add some kind of status summary string (output only)
- Re-add the etalon controls (once an etalon is available)
  and make them less clumsy than they were, specifically:
  - show basic controls always, but disable user controls
    if etalon is out (that way when somebody else puts the etalon
    in, you can see the basics of what it is doing w/out having
    to toggle your "In/Out" button to In.
  - make the mode more obvious (need the NICFPS folks for this)
  - use nm instead of steps for Z if at all possible
    (i.e. if the NICFPS folks agree)
    or else display the equivalent nm?
  - if advanced etalon controls only used in one mode
    (as I sincerely hope!) then only show them when
    the user mode control is in this mode

History:
2004-09-08 ROwen	preliminary
2004-09-23 ROwen	Modified to allow callNow as the default for keyVars.
2004-10-22 ROwen	Bug fix: some help URLs were missing _HelpPrefix.
					Changed default format for FP ZW from %.3f to %.0f.
2004-11-15 ROwen	Changed Z units to steps.
					Added pressure to environ display.
					Display/hide etalon controls when user in-beam widget = In/Out
					(and do not hide the advanced etalon widget controls, for now).
					Added countdown timer support.
					Filter and Etalon In/Out show error color for error value.
2004-11-16 ROwen	Changed pressure units to torr (stopped converting to mtorr)
					and fixed temperature units (temp. is in K, not C).
					Improved environment error display: the limit that
					has not been exceeded is shown in the normal color.
2004-11-29 ROwen	Removed etalon response time display and controls.
					Commented out etalon mode display and controls.
2005-01-05 ROwen	Modified to use autoIsCurrent for input widgets.
					Modified to use severity instead of state.
					Fixed environment summary to show if info not current.
2005-01-24 ROwen	Modified so environment show/hide doesn't shift config widgets.
2005-05-09 ROwen	Added window support. Thanks to Stephane Beland
					for taking the first cut at this!
2005-06-16 ROwen	Changed severity of "temps inconsistent" log message from normal to warning.
					Removed unused variables (found by pychecker).
2005-09-14 ROwen	Added controls for slit in/out, slit focus and Fowler sampling.
2005-09-15 ROwen	Moved fowler samples into detector widgets.
					Fixed a few incorrect html help anchors.
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import TUI.TUIModel
import NICFPSModel

_HelpPrefix = 'Instruments/NICFPS/NICFPSWin.html#'

_DataWidth = 8	# width of data columns
_EnvWidth = 6 # width of environment value columns

# category names
_ConfigCat = RO.Wdg.StatusConfigGridder.ConfigCat
_EtalonCat = 'etalon'
_EnvironCat = 'environ'
_SlitCat = 'slit'
_DetectCat = 'window'

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to show status for and configure NICFPS
		"""
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		self.model = NICFPSModel.getModel()
		self.tuiModel = TUI.TUIModel.getModel()
		
		self.settingCurrWin = False
	
		gr = RO.Wdg.StatusConfigGridder(
			master = self,
			sticky = 'w',
			clearMenu = None,
			defMenu = 'Current',
		)
		self.gridder = gr
		
		# filter (plus blank label to maintain minimum width)
		blankLabel = Tkinter.Label(self, width=_DataWidth)

		self.filterCurrWdg = RO.Wdg.StrLabel(self,
			helpText = "current filter",
			helpURL = _HelpPrefix + "Filter",
		)
		
		self.filterTimerWdg = RO.Wdg.TimeBar(self, valueFormat = "%3.0f")
		
		self.filterUserWdg = RO.Wdg.OptionMenu(self,
			items=[],
			helpText = "requested filter",
			helpURL = _HelpPrefix + "Filter",
			defMenu = "Current",
			autoIsCurrent = True,
			isCurrent = False,
		)

		filtRow = gr.getNextRow()
		# reserve _DataWidth width
		blankLabel.grid(
			row = filtRow,
			column = 1,
			columnspan = 2,
		)
		gr.gridWdg (
			label = 'Filter',
			dataWdg = self.filterCurrWdg,
			units = False,
			cfgWdg = self.filterUserWdg,
			colSpan = 2,
		)
		self.filterTimerWdg.grid(
			row = filtRow,
			column = 1,
			columnspan = 2,
			sticky = "w",
		)
		self._showFilterTimer(False)

		self.model.filter.addIndexedCallback(self._updFilter)
		self.model.filterTime.addIndexedCallback(self._updFilterTime)

		# Slit widgets

		self.slitOPathCurrWdg = RO.Wdg.StrLabel(self,
			anchor = "w",
			helpText = "is slit in or out of the beam?",
			helpURL = _HelpPrefix + "SlitInBeam",
		)
		
		self.slitTimerWdg = RO.Wdg.TimeBar(self, valueFormat = "%3.0f")

		self.slitOPathUserWdg = RO.Wdg.Checkbutton(self,
			helpText = "put Slit in or out of the beam?",
			helpURL = _HelpPrefix + "SlitInBeam",
			onvalue = "In",
			offvalue = "Out",
			showValue = True,
			autoIsCurrent = True,
			isCurrent = False,
		)

		slitOPathRow = gr.getNextRow()
		gr.gridWdg(
			label = 'Slit',
			dataWdg = self.slitOPathCurrWdg,
			units = False,
			cfgWdg = self.slitOPathUserWdg,
			colSpan = 2,
		)
		self.slitTimerWdg.grid(
			row = slitOPathRow,
			column = 1,
			columnspan = 2,
			sticky = "w",
		)
		self._showSlitTimer(False)
		
		maxFocusWidth = max(
			[len("%s" % val) for val in self.model.slitFocusMinMaxConst]
		)
		
		self.slitFocusCurrWdg = RO.Wdg.IntLabel(
			self,
			width = maxFocusWidth,
			helpText = "slit focus (steps)",
			helpURL = _HelpPrefix + "SlitFocus",
		)
		
		self.slitFocusUserWdg = RO.Wdg.IntEntry(
			self,
			helpText = "slit focus (steps)",
			helpURL = _HelpPrefix + "SlitFocus",
			defValue = 0,
			minValue = self.model.slitFocusMinMaxConst[0],
			maxValue = self.model.slitFocusMinMaxConst[1],
		)

		gr.gridWdg(
			label = 'Slit Focus',
			dataWdg = self.slitFocusCurrWdg,
			units = "steps",
			cfgWdg = self.slitFocusUserWdg,
			cat = _SlitCat,
		)

		self.model.slitOPath.addIndexedCallback(self._updSlitOPath)
		self.model.slitTime.addIndexedCallback(self._updSlitTime)
		
		self.model.slitFocus.addROWdg(self.slitFocusCurrWdg)
		self.model.slitFocus.addROWdg(self.slitFocusUserWdg, setDefault=True)

		# Fabry-Perot Etalon in or out of beam (optical path)
		
		self.fpOPathCurrWdg = RO.Wdg.StrLabel(self,
			anchor = "w",
			helpText = "is Etalon in or out of the beam?",
			helpURL = _HelpPrefix + "EtalonInBeam",
		)

		self.fpTimerWdg = RO.Wdg.TimeBar(self, valueFormat = "%3.0f")

		self.fpOPathUserWdg = RO.Wdg.Checkbutton(self,
			helpText = "put Etalon in or out of the beam?",
			helpURL = _HelpPrefix + "EtalonInBeam",
			onvalue = "In",
			offvalue = "Out",
			showValue = True,
			autoIsCurrent = True,
			isCurrent = False,
		)

		fpOPathRow = gr.getNextRow()
		gr.gridWdg (
			label = 'Etalon',
			dataWdg = self.fpOPathCurrWdg,
			units = False,
			cfgWdg = self.fpOPathUserWdg,
			colSpan = 2,
		)
		self.fpTimerWdg.grid(
			row = fpOPathRow,
			column = 1,
			columnspan = 2,
			sticky = "w",
		)
		self._showFPTimer(False)

		self.model.fpOPath.addIndexedCallback(self._updFPOPath)
		self.model.fpTime.addIndexedCallback(self._updFPTime)
		
		# Fabry-Perot Etalon position and spacing
		
		maxFPPosWidth = max(
			[len("%s" % val) for val in self.model.fpXYZLimConst]
		)

		self.fpXCurrWdg = RO.Wdg.IntLabel(self,
			helpText = "current Etalon X parallelism",
			helpURL = _HelpPrefix + "EtalonX",
			anchor = "e",
			width = maxFPPosWidth,
		)
		
		self.fpXUserWdg = RO.Wdg.IntEntry(self,
			helpText = "requested Etalon X parallelism",
			helpURL = _HelpPrefix + "EtalonX",
			minValue = self.model.fpXYZLimConst[0],
			maxValue = self.model.fpXYZLimConst[1],
			minMenu = "Minimum",
			maxMenu = "Maximum",
			autoIsCurrent = True,
			isCurrent = False,
		)

		gr.gridWdg (
			label = 'X Position',
			dataWdg = self.fpXCurrWdg,
			units = "steps",
			cfgWdg = self.fpXUserWdg,
			cat = _EtalonCat,
		)

		self.model.fpX.addROWdg(self.fpXCurrWdg)
		self.model.fpX.addROWdg(self.fpXUserWdg, setDefault=True)
		
		self.fpYCurrWdg = RO.Wdg.IntLabel(self,
			helpText = "current Etalon Y parallelism",
			helpURL = _HelpPrefix + "EtalonY",
			anchor = "e",
			width = maxFPPosWidth,
		)
		
		self.fpYUserWdg = RO.Wdg.IntEntry(self,
			helpText = "requested Etalon Y parallelism",
			helpURL = _HelpPrefix + "EtalonY",
			minValue = self.model.fpXYZLimConst[0],
			maxValue = self.model.fpXYZLimConst[1],
			minMenu = "Minimum",
			maxMenu = "Maximum",
			autoIsCurrent = True,
			isCurrent = False,
		)

		gr.gridWdg (
			label = 'Y Position',
			dataWdg = self.fpYCurrWdg,
			units = "steps",
			cfgWdg = self.fpYUserWdg,
			cat = _EtalonCat,
		)

		self.model.fpY.addROWdg(self.fpYCurrWdg)
		self.model.fpY.addROWdg(self.fpYUserWdg, setDefault=True)

		self.fpZCurrWdg = RO.Wdg.FloatLabel(self,
			precision = 0,
			helpText = "current Etalon Z spacing",
			helpURL = _HelpPrefix + "EtalonZ",
			anchor = "e",
			width = maxFPPosWidth,
		)
		
		self.fpZUserWdg = RO.Wdg.FloatEntry(self,
			defFormat = "%.0f",
			helpText = "requested Etalon Z spacing",
			helpURL = _HelpPrefix + "EtalonZ",
			minValue = self.model.fpXYZLimConst[0],
			maxValue = self.model.fpXYZLimConst[1],
			minMenu = "Minimum",
			maxMenu = "Maximum",
			autoIsCurrent = True,
			isCurrent = False,
		)

		gr.gridWdg (
			label = 'Z Spacing',
			dataWdg = self.fpZCurrWdg,
			units = 'steps',
			cfgWdg = self.fpZUserWdg,
			cat = _EtalonCat,
		)

		self.model.fpZ.addROWdg(self.fpZCurrWdg)
		self.model.fpZ.addROWdg(self.fpZUserWdg, setDefault=True)

		# Detector widgets
		
		# detector image header; the label is a toggle button
		# for showing detector image info
		# grid that first as it is always displayed
		self.showDetectWdg = RO.Wdg.Checkbutton(self,
			onvalue = "Hide Detector",
			offvalue = "Show Detector",
			defValue = False,
			showValue = True,
			helpText = "show/hide window mode",
			helpURL = _HelpPrefix + "ShowDetector",
		)
		gr.addShowHideControl(_DetectCat, self.showDetectWdg)
		gr.gridWdg (
			label = self.showDetectWdg,
		)
		
		# grid detector labels; these show/hide along with all other detector data
		detectLabelDict = {}
		for setName in ("data", "cfg"):
			detectLabelDict[setName] = [
				Tkinter.Label(self,
					text=axis,
				)
				for axis in ("X", "Y")
			]
		gr.gridWdg (
			label = None,
			dataWdg = detectLabelDict["data"],
			cfgWdg = detectLabelDict["cfg"],
			sticky = "e",
			cat = _DetectCat,
			row = -1,
		)
		
		# Detector window

		winDescr = (
			"smallest x",
			"smallest y",
			"largest x",
			"largest y",
		)
		self.detWindowCurrWdgSet = [
			RO.Wdg.IntLabel(
				master = self,
				width = 4,
				helpText = "%s of current window (pix)" % winDescr[ii],
				helpURL = _HelpPrefix + "Window",
			)
			for ii in range(4)
		]
		
		self.detWindowUserWdgSet = [
			RO.Wdg.IntEntry(
				master = self,
				minValue = 1,
				maxValue = self.model.detSizeConst[(0, 1, 0, 1)[ii]],
				width = 4,
				helpText = "%s of requested window (pix)" % winDescr[ii],
				helpURL = _HelpPrefix + "Window",
				clearMenu = None,
				defMenu = "Current",
				minMenu = ("Mininum", "Minimum", None, None)[ii],
				maxMenu = (None, None, "Maximum", "Maximum")[ii],
				callFunc = self._newUserWindow,
				autoIsCurrent = True,
				isCurrent = False,
			) for ii in range(4)
		]
		gr.gridWdg (
			label = "Window",
			dataWdg = self.detWindowCurrWdgSet[0:2],
			cfgWdg = self.detWindowUserWdgSet[0:2],
			units = "LL pix",
			cat = _DetectCat,
		)
		gr.gridWdg (
			label = None,
			dataWdg = self.detWindowCurrWdgSet[2:4],
			cfgWdg = self.detWindowUserWdgSet[2:4],
			units = "UR pix",
			cat = _DetectCat,
		)

		# Image size, in pixels
		self.imageSizeCurrWdgSet = [RO.Wdg.IntLabel(
			master = self,
			width = 4,
			helpText = "current %s size of image (pix)" % winDescr[ii],
			helpURL = _HelpPrefix + "ImageSize",
		)
			for ii in range(2)
		]

		self.imageSizeUserWdgSet = [
			RO.Wdg.IntLabel(self,
				width = 4,
				helpText = "requested %s size of image (pix)" % ("X", "Y")[ii],
				helpURL = _HelpPrefix + "ImageSize",
			) for ii in range(2)
		]
		gr.gridWdg (
			label = "Image Size",
			dataWdg = self.imageSizeCurrWdgSet,
			cfgWdg = self.imageSizeUserWdgSet,
			units = "pix",
			cat = _DetectCat,
		)
		
		self.fowlerSamplesCurrWdg = RO.Wdg.IntLabel(self,
			helpText = "current number of samples",
			helpURL = _HelpPrefix + "FowlerSamples",
		)
		
		sampLim = list(self.model.fowlerSamplesLimConst)
		sampLim[1] += 1
		sampleValues = [str(val) for val in range(*sampLim)]
		self.fowlerSamplesUserWdg = RO.Wdg.OptionMenu(self,
			items=sampleValues,
			helpText = "requested number of samples",
			helpURL = _HelpPrefix + "FowlerSamples",
			defMenu = "Current",
			autoIsCurrent = True,
			isCurrent = False,
		)

		gr.gridWdg (
			label = 'Fowler Samples',
			dataWdg = self.fowlerSamplesCurrWdg,
			units = False,
			cfgWdg = self.fowlerSamplesUserWdg,
			cat = _DetectCat,
		)

		self.model.fowlerSamples.addIndexedCallback(self._updFowlerSamples)

		# Temperature warning and individual temperatures
		
		self.environShowHideWdg = RO.Wdg.Checkbutton(
			master = self,
			text = "Environment",
			indicatoron = False,
			helpText = "Show/hide pressure and temps",
			helpURL = _HelpPrefix + "Environment",
		)
		
		self.environStatusWdg = RO.Wdg.StrLabel(
			master = self,
			anchor = "w",
			helpText = "Are pressure and temps OK?",
			helpURL = _HelpPrefix + "Environment",
		)

		gr.gridWdg (
			label = self.environShowHideWdg,
			dataWdg = self.environStatusWdg,
			colSpan = 2,
		)
		
		# hidable frame showing current pressure and temperatures

		self.envFrameWdg = Tkinter.Frame(self, borderwidth=1, relief="solid")
		
		# create header
		headStrSet = (
			"Sensor",
			"Curr",
			"Min",
			"Max",
		)
		
		for ind in range(len(headStrSet)):
			headLabel = RO.Wdg.Label(
				master = self.envFrameWdg,
				text = headStrSet[ind],
				anchor = "e",
				helpURL = _HelpPrefix + "Environment",
			)
			headLabel.grid(row=0, column=ind, sticky="e")

		# create pressure widgets
		
		pressHelpStrs = (
			"pressure",
			"current pressure",
			None,
			"maximum safe pressure",
		)

		rowInd = 1
		colInd = 0
		wdg = RO.Wdg.StrLabel(
			master = self.envFrameWdg,
			text = "Pressure",
			anchor = "e",
			helpText = pressHelpStrs[0],
			helpURL = _HelpPrefix + "Environment",
		)
		wdg.grid(row = rowInd, column = colInd, sticky="e")
		newWdgSet = [wdg]
		for colInd in range(1, 4):
			wdg = RO.Wdg.Label(
				master = self.envFrameWdg,
				formatFunc = fmtExp,
				width = _EnvWidth,
				anchor = "e",
				helpText = pressHelpStrs[colInd],
				helpURL = _HelpPrefix + "Environment",
			)
			wdg.grid(row = rowInd, column = colInd, sticky="ew")
			newWdgSet.append(wdg)
		colInd += 1
		wdg = RO.Wdg.StrLabel(
			master = self.envFrameWdg,
			text = "torr",
			anchor = "w",
		)
		wdg.grid(row = rowInd, column = colInd, sticky="w")
		newWdgSet.append(wdg)
		self.pressWdgSet = newWdgSet


		# temperatures

		self.tempHelpStrSet = (
			"temperature sensor",
			"current temperature",
			"minimum safe temperature",
			"maximum safe temperature",
		)
		
		# create blank widgets to display temperatures
		# this set is indexed by row (sensor)
		# and then by column (name, current temp, min temp, max temp)
		self.tempWdgSet = []
		nextCol = gr.getNextCol()
		
		gr.gridWdg (
			label = False,
			dataWdg = self.envFrameWdg,
			cfgWdg = False,
			colSpan = nextCol + 1,
			sticky = "w",
			cat = _EnvironCat,
		)
		
		self.columnconfigure(nextCol, weight=1)
			
		
		gr.allGridded()
		
		# add callbacks that deal with multiple widgets
		self.model.filterNames.addCallback(self.filterUserWdg.setItems)
		self.environShowHideWdg.addCallback(self._doShowHide, callNow = False)
		self.fpOPathUserWdg.addCallback(self._doShowHide, callNow = False)
		self.slitOPathUserWdg.addCallback(self._doShowHide, callNow = False)
		self.model.press.addCallback(self._updEnviron, callNow = False)
		self.model.pressMax.addCallback(self._updEnviron, callNow = False)
		self.model.temp.addCallback(self._updEnviron, callNow = False)
		self.model.detWindow.addCallback(self._newCurrWindow)
		self._updEnviron()
		self._doShowHide()
		
		eqFmtFunc = RO.InputCont.BasicFmt(
			nameSep="=",
		)

		# set up the input container set
		self.inputCont = RO.InputCont.ContList (
			conts = [
				RO.InputCont.WdgCont (
					name = 'filters set',
					wdgs = self.filterUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'slit opath',
					wdgs = self.slitOPathUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'slit focus',
					wdgs = self.slitFocusUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fp opath',
					wdgs = self.fpOPathUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fp setz',
					wdgs = self.fpZUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fp setx',
					wdgs = self.fpXUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fp sety',
					wdgs = self.fpYUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fowler nfs',
					wdgs = self.fowlerSamplesUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'window',
					wdgs = self.detWindowUserWdgSet,
					formatFunc = RO.InputCont.BasicFmt(
						rejectBlanks = True,
					),
				),
			],
		)
		
		def repaint(evt):
			self.restoreDefault()
		self.bind('<Map>', repaint)
	
	def _addTempWdgRow(self):
		"""Add a row of temperature widgets"""
		rowInd = len(self.tempWdgSet) + 2
		colInd = 0
		wdg = RO.Wdg.StrLabel(
			master = self.envFrameWdg,
			anchor = "e",
			helpText = self.tempHelpStrSet[colInd],
			helpURL = _HelpPrefix + "Environment",
		)
		wdg.grid(row = rowInd, column = colInd, sticky="e")
		newWdgSet = [wdg]
		for colInd in range(1, 4):
			wdg = RO.Wdg.FloatLabel(
				master = self.envFrameWdg,
				precision = 1,
				anchor = "e",
				helpText = self.tempHelpStrSet[colInd],
				helpURL = _HelpPrefix + "Environment",
			)
			wdg.grid(row = rowInd, column = colInd, sticky="ew")
			newWdgSet.append(wdg)
		colInd += 1
		wdg = RO.Wdg.StrLabel(
			master = self.envFrameWdg,
			text = "K",
			anchor = "w",
		)
		wdg.grid(row = rowInd, column = colInd, sticky="w")
		newWdgSet.append(wdg)
		self.tempWdgSet.append(newWdgSet)

	def _doShowHide(self, wdg=None):
		showEtalon = self.fpOPathUserWdg.getBool()
		showTemps = self.environShowHideWdg.getBool()
		showSlitFocus = self.slitOPathUserWdg.getBool()
		argDict = {_EtalonCat: showEtalon, _EnvironCat: showTemps, _SlitCat: showSlitFocus}
		self.gridder.showHideWdg (**argDict)
	
	def _showFilterTimer(self, doShow):
		"""Show or hide the filter timer
		(and thus hide or show the current filter name).
		"""
		if doShow:
			self.filterTimerWdg.grid()
			self.filterCurrWdg.grid_remove()
		else:
			self.filterCurrWdg.grid()
			self.filterTimerWdg.grid_remove()
		
	def _showFPTimer(self, doShow):
		"""Show or hide the etalon in/out timer
		(and thus hide or show the current in/out state).
		"""
		if doShow:
			self.fpTimerWdg.grid()
			self.fpOPathCurrWdg.grid_remove()
		else:
			self.fpOPathCurrWdg.grid()
			self.fpTimerWdg.grid_remove()
		
	def _showSlitTimer(self, doShow):
		"""Show or hide the slit in/out timer """
		print "_showSlitTimer(%s)" % (doShow,)
		if doShow:
			self.slitTimerWdg.grid()
			self.slitOPathCurrWdg.grid_remove()
		else:
			self.slitOPathCurrWdg.grid()
			self.slitTimerWdg.grid_remove()
		
	def _updEnviron(self, *args, **kargs):
		# handle pressure
		isCurrent = True

		press, pressCurr = self.model.press.getInd(0)
		pressMax, pressMaxCurr = self.model.pressMax.getInd(0)
		isCurrent = isCurrent and pressCurr and pressMaxCurr

		pressSev = RO.Constants.sevNormal
		pressOK = True
		if press != None and pressMax != None and press > pressMax:
			pressSev = RO.Constants.sevError
			pressOK = False
		self.pressWdgSet[0].setSeverity(pressSev)
		self.pressWdgSet[1].set(press, isCurrent = pressCurr, severity = pressSev)
		self.pressWdgSet[3].set(pressMax, isCurrent = pressMaxCurr, severity = pressSev)
		
		# handle temperatures

		tempNames, namesCurr = self.model.tempNames.get()
		temps, tempsCurr = self.model.temp.get()
		tempMin, minCurr = self.model.tempMin.get()
		tempMax, maxCurr = self.model.tempMax.get()
		isCurrent = isCurrent and namesCurr and tempsCurr and minCurr and maxCurr

		if not (len(temps) == len(tempNames) == len(tempMin) == len(tempMax)):
			# temp data not self-consistent
			self.tuiModel.logMsg(
				"NICFPS temperature data not self-consistent; cannot test temperature limits",
				severity = RO.Constants.sevWarning,
			)
			for wdgSet in self.tempWdgSet:
				for wdg in wdgSet:
					wdg.setNotCurrent()
			return
			
		tempSet = zip(tempNames, temps, tempMin, tempMax)
		isCurrSet = namesCurr, tempsCurr, minCurr, maxCurr

		# add new widgets if necessary
		for ind in range(len(self.tempWdgSet), len(tempSet)):
			self._addTempWdgRow()
		
		# set widgets
		allTempsOK = True
		for ind in range(len(tempSet)):
			wdgSet = self.tempWdgSet[ind]
			infoSet = tempSet[ind]
			tName, tCurr, tMin, tMax = infoSet
			
			okInd = None
			if tCurr != None:
				if tMin != None and tCurr < tMin:
					allTempsOK = False
					okInd = 3
				elif tMax != None and tCurr > tMax:
					allTempsOK = False
					okInd = 2
			if okInd == None:
				sevSet = [RO.Constants.sevNormal] * 4
			else:
				sevSet = [RO.Constants.sevError] * 4
				sevSet[okInd] = RO.Constants.sevNormal

			for wdg, info, isCurr, severity in zip(wdgSet, infoSet, isCurrSet, sevSet):
				wdg.set(info, isCurrent = isCurr, severity = severity)

		if pressOK and allTempsOK:
			self.environStatusWdg.set(
				"OK",
				isCurrent = isCurrent,
				severity = RO.Constants.sevNormal,
			)
		else:
			self.environStatusWdg.set(
				"Bad", 
				isCurrent = isCurrent,
				severity = RO.Constants.sevError,
			)
	
		# delete extra widgets, if any
		for ind in range(len(tempSet), len(self.tempWdgSet)):
			wdgSet = self.tempWdgSet.pop(ind)
			for wdg in wdgSet:
				wdg.grid_forget()
				del(wdg)
		
	def _updFilter(self, filterName, isCurrent, keyVar=None):
		self._showFilterTimer(False)
		if filterName != None and filterName.lower() == "unknown":
			severity = RO.Constants.sevError
			self.filterUserWdg.setDefault(
				None,
				isCurrent = isCurrent,
			)
		else:
			severity = RO.Constants.sevNormal
			self.filterUserWdg.setDefault(
				filterName,
				isCurrent = isCurrent,
			)

		self.filterCurrWdg.set(
			filterName,
			isCurrent = isCurrent,
			severity = severity,
		)

	def _updFilterTime(self, filterTime, isCurrent, keyVar=None):
		if filterTime == None or not isCurrent:
			self._showFilterTimer(False)
			return
		
		self._showFilterTimer(True)
		self.filterTimerWdg.start(filterTime, newMax = filterTime)
	
	def _updFowlerSamples(self, fowlerSamples, isCurrent, keyVar=None):
		self.fowlerSamplesCurrWdg.set(fowlerSamples, isCurrent)
		if fowlerSamples != None:
			strVal = str(fowlerSamples)
		else:
			strVal = None
		self.fowlerSamplesUserWdg.setDefault(strVal, isCurrent=isCurrent)
	
	def _updFPOPath(self, fpOPath, isCurrent, keyVar=None):
		self._showFPTimer(False)
		if fpOPath == '?':
			severity = RO.Constants.sevError
		else:
			severity = RO.Constants.sevNormal
		
		self.fpOPathCurrWdg.set(fpOPath,
			isCurrent = isCurrent,
			severity = severity,
		)
		self.fpOPathUserWdg.setDefault(fpOPath, isCurrent)
	
	def _updFPTime(self, fpTime, isCurrent, keyVar=None):
		if fpTime == None or not isCurrent:
			self._showFPTimer(False)
			return
		
		self._showFPTimer(True)
		self.fpTimerWdg.start(fpTime, newMax = fpTime)

	def _updSlitOPath(self, slitOPath, isCurrent, keyVar=None):
		print "_updSlitOPath(%s, %s)" % (slitOPath, isCurrent)
		self._showSlitTimer(False)
		if slitOPath == '?':
			severity = RO.Constants.sevError
		else:
			severity = RO.Constants.sevNormal
		
		self.slitOPathCurrWdg.set(slitOPath,
			isCurrent = isCurrent,
			severity = severity,
		)
		self.slitOPathUserWdg.setDefault(slitOPath, isCurrent)

	def _updSlitTime(self, slitTime, isCurrent, keyVar=None):
		if slitTime == None or not isCurrent:
			self._showSlitTimer(False)
			return
		
		self._showSlitTimer(True)
		self.slitTimerWdg.start(slitTime, newMax=slitTime)

	def _newUserWindow(self, *args, **kargs):
		"""User window changed. Update user window size.
		"""
		if self.settingCurrWin:
			return

		# update user detector image size
		actUserWindow = [wdg.getNum() for wdg in self.detWindowUserWdgSet]

		if 0 in actUserWindow:
			for ind in range(2):
				self.imageSizeUserWdgSet[ind].set(None)
		else:
			for ind in range(2):
				imSize = 1 + actUserWindow[ind+2] - actUserWindow[ind]
				self.imageSizeUserWdgSet[ind].set(imSize)

	def _newCurrWindow(self, window, isCurrent, **kargs):
		"""Current window changed.
		
		Update current window, default window and current image size.
		"""
		try:
			# set settingCurrWin while executing to allow _newUserWindow
			# to do nothing (it is called even though we're setting
			# default value not displayed value)
			self.settingCurrWin = True
		
			for ind in range(4):
				self.detWindowCurrWdgSet[ind].set(
					window[ind],
					isCurrent = isCurrent,
				)
				self.detWindowUserWdgSet[ind].setDefault(
					window[ind],
				)
	
			try:
				imageSize = [1 + window[ind+2] - window[ind] for ind in range(2)]
			except TypeError:
				imageSize = (None, None)
	
			for ind in range(2):
				self.imageSizeCurrWdgSet[ind].set(
					imageSize[ind],
					isCurrent = isCurrent
				)
		finally:
			self.settingCurrWin = False


def fmtExp(num):
	"""Formats a floating-point number as x.xe-x"""
	retStr = "%.1e" % (num,)
	if retStr[-2] == '0':
		retStr = retStr[0:-2] + retStr[-1]
	return retStr


if __name__ == '__main__':
	root = RO.Wdg.PythonTk()

	import TestData
		
	testFrame = StatusConfigInputWdg (root)
	testFrame.pack()
	
	TestData.dispatch()
	
	testFrame.restoreDefault()

	def printCmds():
		try:
			cmdList = testFrame.getStringList()
		except ValueError, e:
			print "Command error:", e
			return
		if cmdList:
			print "Commands:"
			for cmd in cmdList:
				print cmd
		else:
			print "(no commands)"
	
	bf = Tkinter.Frame(root)
	cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
	cfgWdg.pack(side="left")
	Tkinter.Button(bf, text='Cmds', command=printCmds).pack(side='left')
	Tkinter.Button(bf, text='Current', command=testFrame.restoreDefault).pack(side='left')
	Tkinter.Button(bf, text='Demo', command=TestData.animate).pack(side='left')
	bf.pack()
	
	testFrame.gridder.addShowHideControl(_ConfigCat, cfgWdg)
	
	root.mainloop()
