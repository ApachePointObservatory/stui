#!/usr/local/bin/python
from __future__ import generators
"""Configuration input panel for NICFPS.

To do:
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
"""
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.Wdg
import RO.StringUtil
import TUI.TUIModel
import NICFPSModel

_HelpPrefix = 'Instruments/NICFPS/NICFPSWin.html#'

_DataWidth = 8	# width of data columns

# category names
_ConfigCat = 'config'
_BalanceCat = 'mode'
_TempsCat = 'temps'

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
		
		# filter

		self.filterCurrWdg = RO.Wdg.StrLabel(self,
			helpText = "current filter",
			helpURL = _HelpPrefix + "Filter",
		)
		
		self.filterUserWdg = RO.Wdg.OptionMenu(self,
			items=[],
			helpText = "requested filter",
			helpURL = _HelpPrefix + "Filter",
			defMenu = "Current",
		)

		gr.gridWdg (
			label = 'Filter',
			dataWdg = self.filterCurrWdg,
			units = False,
			cfgWdg = self.filterUserWdg,
			colSpan = 2,
		)

		self.model.filter.addROWdg(self.filterCurrWdg)
		self.model.filter.addROWdg(self.filterUserWdg, setDefault=True)

		# Fabry-Perot Etalon in beam
		
		self.fpOPathCurrWdg = RO.Wdg.StrLabel(self,
			helpText = "is Etalon in or out of the beam?",
			helpURL = _HelpPrefix + "EtalonInBeam",
		)
		
		self.fpOPathUserWdg = RO.Wdg.Checkbutton(self,
			helpText = "put Etalon in or out of the beam?",
			helpURL = _HelpPrefix + "EtalonInBeam",
			onvalue = "In",
			offvalue = "Out",
			indicatoron = False,
			padx = 5,
			pady = 2,
		)
		self.fpOPathUserWdg["textvariable"] = self.fpOPathUserWdg.getVar()

		gr.gridWdg (
			label = 'Etalon',
			dataWdg = self.fpOPathCurrWdg,
			units = False,
			cfgWdg = self.fpOPathUserWdg,
			colSpan = 2,
		)

		self.model.fpOPath.addROWdg(self.fpOPathCurrWdg)
		self.model.fpOPath.addROWdg(self.fpOPathUserWdg, setDefault=True)

		# Fabry-Perot Etalon mode

		self.fpModeCurrWdg = RO.Wdg.StrLabel(self,
			helpText = "current Etalon mode",
			helpURL = _HelpPrefix + "EtalonMode",
		)
		
		self.fpModeUserWdg = RO.Wdg.OptionMenu(self,
			items = ("Operate", "Balance"),
			callFunc = self._doShowHide,
			helpText = "requested Etalon mode",
			helpURL = _HelpPrefix + "EtalonMode",
			width = _DataWidth,
		)

		gr.gridWdg (
			label = 'Mode',
			dataWdg = self.fpModeCurrWdg,
			units = False,
			cfgWdg = self.fpModeUserWdg,
			colSpan = 2,
		)

	
		#
		# Balance-mode controls (normally hidden)
		#
		
		self.fpRTimeCurrWdg = RO.Wdg.FloatLabel(self,
			precision = 1,
			helpText = "current Etalon response time",
			helpURL = _HelpPrefix + "EtalonRTime",
			anchor = "e",
			width = _DataWidth,
		)
		
		self.fpRTimeUserWdg = RO.Wdg.OptionMenu(self,
			items = ("0.2", "0.5", "1.0", "2.0"),
			helpText = "requested Etalon response time",
			helpURL = _HelpPrefix + "EtalonRTime",
		)

		gr.gridWdg (
			label = 'RTime',
			dataWdg = self.fpRTimeCurrWdg,
			units = "msec",
			cfgWdg = self.fpRTimeUserWdg,
			cat = _BalanceCat,
		)

		
		
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
			cat = _BalanceCat,
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
			cat = _BalanceCat,
		)

		self.model.fpY.addROWdg(self.fpYCurrWdg)
		self.model.fpY.addROWdg(self.fpYUserWdg, setDefault=True)

		# Fabry-Perot Etalon Z spacing
		
		self.fpZWCurrWdg = RO.Wdg.FloatLabel(self,
			precision = 0,
			helpText = "current Etalon Z spacing",
			helpURL = _HelpPrefix + "EtalonZ",
			anchor = "e",
			width = _DataWidth,
		)
		
		self.fpZWUserWdg = RO.Wdg.FloatEntry(self,
			defFormat = "%.0f",
			helpText = "requested Etalon Z spacing",
			helpURL = _HelpPrefix + "EtalonZ",
			minMenu = "Minimum",
			maxMenu = "Maximum",
			width = _DataWidth,
		)

		gr.gridWdg (
			label = 'Z Spacing',
			dataWdg = self.fpZWCurrWdg,
			units = RO.StringUtil.MuStr + "m",
			cfgWdg = self.fpZWUserWdg,
		)

		self.model.fpActZW.addROWdg(self.fpZWCurrWdg)
		self.model.fpDesZW.addROWdg(self.fpZWUserWdg, setDefault=True)
		
		# Temperature warning and individual temperatures
		
		self.tempShowHideWdg = RO.Wdg.Checkbutton(
			master = self,
			text = "Temps",
#			onvalue = "Temperatures",
#			offvalue = "Temperatures",
#			showValue = True,
			callFunc = self._doShowHide,
			indicatoron = False,
			padx = 5,
			pady = 2,
			helpText = "show/hide temperatures",
			helpURL = _HelpPrefix + "Temperatures",
		)
		
		self.tempStatusWdg = RO.Wdg.StrLabel(
			master = self,
			anchor = "e",
#			anchor = "c",	# use for longer error message
			helpText = "are all temperatures OK?",
			helpURL = _HelpPrefix + "Temperatures",
		)

		gr.gridWdg (
			label = self.tempShowHideWdg,
			dataWdg = self.tempStatusWdg,
#			colSpan = 2,	# use for longer error message
#			sticky = "ew",
		)
	
		# hidable frame showing current temperatures

		self.tempFrameWdg = Tkinter.Frame(self)
		
		self.tempHelpStrSet = (
			"name of temperature sensor",
			"current temperature",
			"minimum safe temperature",
			"maximum safe temperature",
		)
		headStrSet = (
			"Name",
			"Curr",
			"Min",
			"Max",
		)
		
		# create header
		for ind in range(len(headStrSet)):
			headLabel = RO.Wdg.Label(
				master = self.tempFrameWdg,
				text = headStrSet[ind],
				anchor = "e",
				helpText = self.tempHelpStrSet[ind],
				helpURL = _HelpPrefix + "Temperatures",
			)
			headLabel.grid(row=0, column=ind, sticky="e")
		
		# create blank widgets to display temperatures
		# this set is indexed by row (sensor)
		# and then by column (name, current temp, min temp, max temp)
		self.tempCurrWdgSet = []
		
		gr.gridWdg (
			label = False,
			dataWdg = self.tempFrameWdg,
			cfgWdg = False,
			colSpan = 6,
			sticky = "w",
			cat = _TempsCat,
		)
			
		
		gr.allGridded()
		
		# add callbacks that deal with multiple widgets
		self.model.filterNames.addCallback(self.filterUserWdg.setItems)
		self.model.fpMode.addIndexedCallback(self._updFPMode)
		self.model.fpRTime.addIndexedCallback(self._updFPRTime)
		self.model.fpZWLim.addCallback(self._updFPZWLim)
		self.model.temp.addCallback(self._updTemp)

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
					name = 'fp setzw',
					wdgs = self.fpZWUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fp mode',
					wdgs = self.fpModeUserWdg,
					formatFunc = eqFmtFunc,
				),
				RO.InputCont.WdgCont (
					name = 'fp rtime',
					wdgs = self.fpRTimeUserWdg,
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
	
	def _updFPZWLim(self, minMax, isCurrent, keyVar=None):
		"""ZW limits changed"""
		if not isCurrent:
			return
		
		self.fpZWUserWdg.setRange(
			minValue = minMax[0],
			maxValue = minMax[1],
		)
	
	def _updFPMode(self, fpMode, isCurrent, keyVar=None):
		if fpMode != None and fpMode.lower() != "operate":
			state = RO.Constants.st_Warning
		else:
			state = RO.Constants.st_Normal
		self.fpModeCurrWdg.set(fpMode, isCurrent = isCurrent, state = state)
		self.fpModeUserWdg.setDefault(fpMode)
	
	def _updFPRTime(self, fpRTime, isCurrent, keyVar=None):
		self.fpRTimeCurrWdg.set(fpRTime, isCurrent = isCurrent)
		if fpRTime != None:
			dispVal = "%.1f" % (fpRTime)
		else:
			dispVal = None
		self.fpRTimeUserWdg.setDefault(dispVal)
	
	def _updTemp(self, temps, isCurrent, keyVar=None):
		tempNames, namesCurr = self.model.tempNames.get()
		tempMin, minCurr = self.model.tempMin.get()
		tempMax, maxCurr = self.model.tempMax.get()
		
		if not (len(temps) == len(tempNames) == len(tempMin) == len(tempMax)):
			# temp data not self-consistent
			self.tuiModel.logMsg("NICFPS temperature data not self-consistent; cannot test temperature limits")
			for wdgSet in self.tempCurrWdgSet:
				for wdg in wdgSet:
					wdg.setNotCurrent()
			return
			
		tempSet = zip(tempNames, temps, tempMin, tempMax)
		isCurrSet = namesCurr, isCurrent, minCurr, maxCurr

		# add new widgets if necessary
		for ind in range(len(self.tempCurrWdgSet), len(tempSet)):
			self._addTempWdgRow()
		
		# set widgets
		allTempsOK = True
		for ind in range(len(tempSet)):
			wdgSet = self.tempCurrWdgSet[ind]
			infoSet = tempSet[ind]
			for wdg, info, isCurr in zip(wdgSet, infoSet, isCurrSet):
				tName, tCurr, tMin, tMax = infoSet
				try:
					if tCurr != None:
						RO.MathUtil.checkRange(tCurr, tMin, tMax)
					tempState = RO.Constants.st_Normal
				except ValueError:
					tempState = RO.Constants.st_Error
					allTempsOK = False
				wdg.set(info, isCurrent = isCurr, state = tempState)
		if allTempsOK:
			self.tempStatusWdg.set("OK", state=RO.Constants.st_Normal)
		else:
			self.tempStatusWdg.set("Bad", state=RO.Constants.st_Error)
	
		# delete extra widgets, if any
		for ind in range(len(tempSet), len(self.tempCurrWdgSet)):
			wdgSet = self.tempCurrWdgSet.pop(ind)
			for wdg in wdgSet:
				wdg.grid_forget()
				del(wdg)
		
		if allTempsOK:
			self.tempStatusWdg.set("OK", state=RO.Constants.st_Normal)
		else:
			self.tempStatusWdg.set("Bad", state=RO.Constants.st_Error)
	
	def _addTempWdgRow(self):
		"""Add a row of temperature widgets"""
		rowInd = len(self.tempCurrWdgSet) + 1
		colInd = 0
		wdg = RO.Wdg.StrLabel(
			master = self.tempFrameWdg,
			anchor = "e",
			helpText = self.tempHelpStrSet[colInd],
			helpURL = _HelpPrefix + "Temperatures",
		)
		wdg.grid(row = rowInd, column = colInd, sticky="e")
		newWdgSet = [wdg]
		for colInd in range(1, 4):
			wdg = RO.Wdg.FloatLabel(
				master = self.tempFrameWdg,
				precision = 1,
				anchor = "e",
				helpText = self.tempHelpStrSet[colInd],
				helpURL = _HelpPrefix + "Temperatures",
			)
			wdg.grid(row = rowInd, column = colInd, sticky="ew")
			newWdgSet.append(wdg)
		colInd += 1
		wdg = RO.Wdg.StrLabel(
			master = self.tempFrameWdg,
			text = "C",
			anchor = "w",
		)
		wdg.grid(row = rowInd, column = colInd, sticky="w")
		newWdgSet.append(wdg)
		self.tempCurrWdgSet.append(newWdgSet)
		
	
	def _doShowHide(self, wdg=None):
		showMode = self.fpModeUserWdg.getString().lower() == "balance"
		showTemps = self.tempShowHideWdg.getBool()
		argDict = {_BalanceCat: showMode, _TempsCat: showTemps}
		self.gridder.showHideWdg (**argDict)
		
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
