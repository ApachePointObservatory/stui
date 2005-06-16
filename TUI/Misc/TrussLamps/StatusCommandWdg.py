#!/usr/local/bin/python
from __future__ import generators
"""Status and control for tlamps.

To do:
- Use icons instead of text?

History:
2004-10-01 ROwen
2004-10-11 ROwen	Bug fix: handles no-privs better.
2004-11-15 ROwen	Modified to use RO.Wdg.Checkbutton's improved defaults.
2004-12-27 ROwen	Fixed the test code.
2005-01-05 ROwen	Modified for RO.Wdg.Label state->severity and RO.Constants.st_... -> sev...
2005-01-18 ROwen	Modified to use background color instead of a separate "!" box to indicate "changing".
					Bug fix: if a command failed instantly then the widget display was wrong.
2005-06-56 ROwen	Removed unused variables (found by pychecker).
"""
import Tkinter
import RO.Alg
import RO.Constants
import RO.Wdg
import TUI.TUIModel
import TrussLampsModel

_HelpURL = "Misc/TrussLampsWin.html"

_TimeLim = 30

class StatusCommandWdg (Tkinter.Frame):
	def __init__(self,
		master,
		statusBar,
	**kargs):
		"""Create a new widget to show status for and configure the truss lamps
		"""
		Tkinter.Frame.__init__(self, master, **kargs)
		self.statusBar = statusBar
		self.model = TrussLampsModel.getModel()
		self.tuiModel = TUI.TUIModel.getModel()
		
		self._updating = False

		# each element of lampWdgSet is a tuple of widgets for one lamp:
		# name label, status/control checkbutton
		self.lampWdgSet = []
	
		self.model.lampStates.addCallback(self._updLampStates)
		

	def refresh(self, *args, **kargs):
		"""Refresh the display.
		"""
		lampStates, isCurrent = self.model.lampStates.get()
		self._updLampStates(lampStates, isCurrent)

	def _updLampStates(self, lampStates, isCurrent, keyVar=None):
		"""New lampStates data.
		"""
		self._updating = True
		try:
			lampNames, namesCurr = self.model.lampNames.get()
			
			if len(lampStates) != len(lampNames):
				# lamp data not self-consistent
				self.tuiModel.logMsg(
					"tlamp data not self-consistent; cannot display",
					severity = RO.Constants.sevWarning,
				)
				for wdgSet in self.lampWdgSet:
					for wdg in wdgSet[0:1]:
						wdg.setNotCurrent()
				return
				
	
			newNumLamps = len(lampNames)
			oldNumLamps = len(self.lampWdgSet)
	
			# add new widgets if necessary
			for lampName in lampNames[oldNumLamps:]:
				self._addLampWdgs(lampName)
		
			# delete extra widgets, if any
			oldNumLamps = len(self.lampWdgSet)
			for ind in range(newNumLamps, oldNumLamps):
				wdgSet = self.lampWdgSet.pop()
				for wdg in wdgSet:
					wdg.grid_forget()
					del(wdg)
			
			# set widgets
			for wdgSet, lampName, lampState in zip(self.lampWdgSet, lampNames, lampStates):
				labelWdg, ctrlWdg = wdgSet
				
				# set lamp name
				labelWdg.set(lampName, isCurrent = namesCurr)

				# set lamp state
				stateLow = lampState.lower()
				
				logState, severity = {
					"off": (False, RO.Constants.sevNormal),
					"on":  (True,  RO.Constants.sevWarning),
				}.get(stateLow, (True, RO.Constants.sevError))
				ctrlWdg.set(logState, severity = severity)
				ctrlWdg.setDefault(logState)
				
				ctrlWdg["text"] = lampState
		finally:
			self._updating = False
	
	def _addLampWdgs(self, lampName):
		"""Add a set of widgets for one lamp"""
		rowInd = len(self.lampWdgSet) + 1
		colInd = 0
		labelWdg = RO.Wdg.StrLabel(
			master = self,
			anchor = "e",
			helpText = None,
			helpURL = _HelpURL,
		)
		
		ctrlWdg = RO.Wdg.Checkbutton(
			master = self,
			onvalue = "On",
			offvalue = "Off",
			indicatoron = False,
			autoIsCurrent = True,
			callFunc = RO.Alg.GenericCallback(self._doCmd, rowInd, lampName),
			helpText = "Toggle %s lamp" % (lampName,),
			helpURL = _HelpURL,
		)
		
		labelWdg.grid(row = rowInd, column = colInd, sticky="e")
		colInd += 1
		ctrlWdg.grid(row = rowInd, column = colInd, sticky="w")
		colInd += 1
		
		# set of widgets for lamp status and control
		# one entry per lamp
		# each entry consists of:
		# name label, status label, changed indicator, control checkbutton
		self.lampWdgSet.append((labelWdg, ctrlWdg))
	
	def _doCmd(self, lampNum, lampName, ctrlWdg):
		if self._updating:
			return

		isOn = ctrlWdg.getBool()
		if isOn:
			stateStr = "On"
		else:
			stateStr = "Off"
		ctrlWdg["text"] = stateStr
		lampCmdVar = RO.KeyVariable.CmdVar(
			actor = self.model.actor,
			cmdStr = "%s %d" % (stateStr.lower(), lampNum),
			timeLim = _TimeLim,
			callFunc = self._cmdFailed,
			callTypes = RO.KeyVariable.FailTypes,
		)
		self.statusBar.doCmd(lampCmdVar)
	
	def _cmdFailed(self, *args, **kargs):
		self.after(10, self.refresh)

		
if __name__ == '__main__':
	root = RO.Wdg.PythonTk()

	import TestData
		
	statusBar = RO.Wdg.StatusBar(root, dispatcher=TestData.dispatcher)
	testFrame = StatusCommandWdg (root, statusBar)
	testFrame.pack()
	statusBar.pack(expand="yes", fill="x")

	Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
	
	TestData.dispatch()
	
	root.mainloop()
