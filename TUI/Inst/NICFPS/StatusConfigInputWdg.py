#!/usr/local/bin/python
from __future__ import generators
"""Configuration input panel for NICFPS.

To do:
- Make the etalon controls less clumsy:
  - show basic controls always, but disable user controls
    if etalon is out (that way when somebody else puts the etalon
    in, you can see the basics of what it is doing w/out having
    to toggle your "In/Out" button to In.
  - make the mode more obvious (need the NICFPS folks for this)
  - use nm instead of steps for Z if at all possible
    (i.e. if the NICFPS folks agree)
    or else display the equivalent um?
  - if advanced etalon controls only used in one mode
    (as I sincerely hope!) then only show them when
    the user mode control is in this mode

- add countdown timers for:
  - filter changes
  - etalon moving in our out
  if both cannot move at the same time, consider one timer
- add some kind of status summary string (output only)

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

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to show status for and configure NICFPS
		"""
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		self.model = NICFPSModel.getModel()
		self.tuiModel = TUI.TUIModel.getModel()
	
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
		
		# Fabry-Perot Etalon X and Y position

		self.fpXCurrWdg = RO.Wdg.IntLabel(self,
			helpText = "current Etalon X parallelism",
			helpURL = _HelpPrefix + "EtalonX",
			anchor = "e",
			width = _DataWidth,
		)
		
		self.fpXUserWdg = RO.Wdg.IntEntry(self,
			helpText = "requested Etalon X parallelism",
			helpURL = _HelpPrefix + "EtalonX",
			minValue = self.model.fpXYZLimConst[0],
			maxValue = self.model.fpXYZLimConst[1],
			minMenu = "Minimum",
			maxMenu = "Maximum",
			width = _DataWidth,
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
			width = _DataWidth,
		)
		
		self.fpYUserWdg = RO.Wdg.IntEntry(self,
			helpText = "requested Etalon Y parallelism",
			helpURL = _HelpPrefix + "EtalonY",
			minValue = self.model.fpXYZLimConst[0],
			maxValue = self.model.fpXYZLimConst[1],
			minMenu = "Minimum",
			maxMenu = "Maximum",
			width = _DataWidth,
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

		# Fabry-Perot Etalon Z spacing
		
		self.fpZCurrWdg = RO.Wdg.FloatLabel(self,
			precision = 0,
			helpText = "current Etalon Z spacing",
			helpURL = _HelpPrefix + "EtalonZ",
			anchor = "e",
			width = _DataWidth,
		)
		
		self.fpZUserWdg = RO.Wdg.FloatEntry(self,
			defFormat = "%.0f",
			helpText = "requested Etalon Z spacing",
			helpURL = _HelpPrefix + "EtalonZ",
			minValue = self.model.fpXYZLimConst[0],
			maxValue = self.model.fpXYZLimConst[1],
			minMenu = "Minimum",
			maxMenu = "Maximum",
			width = _DataWidth,
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
			helpURL = _HelpPrefix + "Pressure",
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
				helpURL = _HelpPrefix + "Pressure",
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
		
		gr.gridWdg (
			label = False,
			dataWdg = self.envFrameWdg,
			cfgWdg = False,
			colSpan = 3,
			sticky = "w",
			cat = _EnvironCat,
		)
		
		self.columnconfigure(2, weight=1)
			
		
		gr.allGridded()
		
		# add callbacks that deal with multiple widgets
		self.model.filterNames.addCallback(self.filterUserWdg.setItems)
		self.fpOPathUserWdg.addCallback(self._doShowHide, callNow = False)
		self.environShowHideWdg.addCallback(self._doShowHide)
		self.model.press.addCallback(self._updEnviron)
		self.model.pressMax.addCallback(self._updEnviron)
		self.model.temp.addCallback(self._updEnviron)
		
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
		argDict = {_EtalonCat: showEtalon, _EnvironCat: showTemps}
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
		
	def _updEnviron(self, *args, **kargs):
		# handle pressure

		press, pressCurr = self.model.press.getInd(0)
		pressMax, pressMaxCurr = self.model.pressMax.getInd(0)

		pressState = RO.Constants.st_Normal
		pressOK = True
		if press != None and pressMax != None and press > pressMax:
			pressState = RO.Constants.st_Error
			pressOK = False
		self.pressWdgSet[0].setState(pressState)
		self.pressWdgSet[1].set(press, isCurrent = pressCurr, state = pressState)
		self.pressWdgSet[3].set(pressMax, isCurrent = pressMaxCurr, state = pressState)
		
		# handle temperatures

		tempNames, namesCurr = self.model.tempNames.get()
		temps, tempsCurr = self.model.temp.get()
		tempMin, minCurr = self.model.tempMin.get()
		tempMax, maxCurr = self.model.tempMax.get()
		
		if not (len(temps) == len(tempNames) == len(tempMin) == len(tempMax)):
			# temp data not self-consistent
			self.tuiModel.logMsg("NICFPS temperature data not self-consistent; cannot test temperature limits")
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
				stateSet = [RO.Constants.st_Normal] * 4
			else:
				stateSet = [RO.Constants.st_Error] * 4
				stateSet[okInd] = RO.Constants.st_Normal

			for wdg, info, isCurr, state in zip(wdgSet, infoSet, isCurrSet, stateSet):
				wdg.set(info, isCurrent = isCurr, state = state)
		if pressOK and allTempsOK:
			self.environStatusWdg.set("OK", state=RO.Constants.st_Normal)
		else:
			self.environStatusWdg.set("Bad", state=RO.Constants.st_Error)
	
		# delete extra widgets, if any
		for ind in range(len(tempSet), len(self.tempWdgSet)):
			wdgSet = self.tempWdgSet.pop(ind)
			for wdg in wdgSet:
				wdg.grid_forget()
				del(wdg)
		
	def _updFilter(self, filterName, isCurrent, keyVar=None):
		self._showFilterTimer(False)
		if filterName != None and filterName.lower() == "unknown":
			state = RO.Constants.st_Error
		else:
			state = RO.Constants.st_Normal

		self.filterCurrWdg.set(
			filterName,
			isCurrent = isCurrent,
			state = state,
		)
		self.filterUserWdg.setDefault(filterName)

	def _updFilterTime(self, filterTime, isCurrent, keyVar=None):
		if filterTime == None or not isCurrent:
			self._showFilterTimer(False)
			return
		
		self._showFilterTimer(True)
		self.filterTimerWdg.start(filterTime, newMax = filterTime)
	
	def _updFPOPath(self, fpOPath, isCurrent, keyVar=None):
		self._showFPTimer(False)
		if fpOPath == '?':
			state = RO.Constants.st_Error
		else:
			state = RO.Constants.st_Normal
		
		self.fpOPathCurrWdg.set(fpOPath,
			isCurrent = isCurrent,
			state = state,
		)
		self.fpOPathUserWdg.setDefault(fpOPath)
	
	def _updFPTime(self, fpTime, isCurrent, keyVar=None):
		if fpTime == None or not isCurrent:
			self._showFPTimer(False)
			return
		
		self._showFPTimer(True)
		self.fpTimerWdg.start(fpTime, newMax = fpTime)


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
			cmdList = testFrame.inputWdg.getStringList()
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
