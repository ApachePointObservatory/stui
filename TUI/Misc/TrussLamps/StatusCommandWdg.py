#!/usr/local/bin/python
from __future__ import generators
"""Status and control for tlamps.

To do:
- Use icons instead of text.
- Use colors to indicate unknown current state and also On (warning),
  and Unknown or Rebooting (error). At the moment RO.Wdg.Checkbuttons
  have no means for any of this without hard-coding it
  (though icons should solve that problem).

History:
2004-10-01 ROwen
2004-10-11 ROwen	Bug fix: handles no-privs better.
"""
import Tkinter
import RO.Alg
import RO.Constants
import RO.Wdg
import TUI.TUIModel
import TrussLampsModel

_HelpURL = "Misc/TrussLampsWin.html"

_TimeLim = 30

_DataWidth = 8	# width of data columns


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
		# name label, status/control checkbutton, changed indicator
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
				self.tuiModel.logMsg("tlamp data not self-consistent; cannot display")
				for wdgSet in self.lampWdgSet:
					for wdg in wdgSet[0:1]:
						wdg.setNotCurrent()
				return
				
			nameStateSet = zip(lampNames, lampStates)
			isCurrSet = namesCurr, isCurrent
	
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
				labelWdg, ctrlWdg, changedInd = wdgSet
				
				# set lamp name
				labelWdg.set(lampName, isCurrent = namesCurr)

				# set lamp state
				stateLow = lampState.lower()
				
				if stateLow == "off":
					dispState = RO.Constants.st_Normal
				elif stateLow == "on":
					dispState = RO.Constants.st_Warning
				else:
					dispState = RO.Constants.st_Error
				ctrlWdg["text"] = lampState
				
				if stateLow == "off":
					ctrlWdg.set(False)
				elif stateLow == "on":
					ctrlWdg.set(True)
				else:
					ctrlWdg.set(True)
				
#				if stateLow in ("on", "off"):
#					ctrlWdg.setDefault(lampState)
#					ctrlWdg.set(lampState)
#					if stateLow == "off":
#						lampStateState = RO.Constants.st_Normal
#					else:
#						lampStateState = RO.Constants.st_Warning
#				else:
#					ctrlWdg.setDefault(None)
#					lampStateState = RO.Constants.st_Error
#				
#				# set lamp state
#				statusWdg.set(lampState, isCurrent = isCurrent, state = lampStateState)
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
		
		changedWdg = RO.Wdg.StrLabel(
			master = self,
			width = 1,
			helpText = "! if %s toggling" % (lampName,),
			helpURL = _HelpURL,
		)

		ctrlWdg = RO.Wdg.Checkbutton(
			master = self,
			onvalue = "On",
			offvalue = "Off",
			indicatoron = False,
			padx = 5,
			pady = 2,
			callFunc = RO.Alg.GenericCallback(self._doCmd, rowInd, lampName, changedWdg),
			helpText = "Toggle %s lamp" % (lampName,),
			helpURL = _HelpURL,
		)
		
		labelWdg.grid(row = rowInd, column = colInd, sticky="e")
		colInd += 1
		changedWdg.grid(row = rowInd, column = colInd)
		colInd += 1
		ctrlWdg.grid(row = rowInd, column = colInd, sticky="w")
		colInd += 1
		
		# set of widgets for lamp status and control
		# one entry per lamp
		# each entry consists of:
		# name label, status label, changed indicator, control checkbutton
		self.lampWdgSet.append((labelWdg, ctrlWdg, changedWdg))
	
	def _doCmd(self, lampNum, lampName, changedWdg, ctrlWdg):
		if ctrlWdg["text"] == ctrlWdg.getString():
			changedWdg["text"] = ""
			changedWdg.helpText = None
		else:
			changedWdg["text"] = "!"
			changedWdg.helpText = "%s toggling" % (lampName,)

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
			callFunc = self.refresh,
			callTypes = RO.KeyVariable.FailTypes,
		)
		self.statusBar.doCmd(lampCmdVar)

		
if __name__ == '__main__':
	root = RO.Wdg.PythonTk()

	import TestData
		
	testFrame = StatusCommandWdg (root)
	testFrame.pack()

	Tkinter.Button(root, text="Demo", command=TestData.animate).pack()
	
	TestData.dispatch()
	
	root.mainloop()
