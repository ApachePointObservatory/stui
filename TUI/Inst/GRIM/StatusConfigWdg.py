#!/usr/local/bin/python
from __future__ import generators
"""Status and configuration for GRIM.

History:
2003-08-04 ROwen
2003-08-11 ROwen	Modified to use enhanced Gridder.
2003-11-17 ROwen	Modified to use TUI.Sounds.
2003-12-09 ROwen	Use new showValue flag in RO.Wdg.Checkbutton.
2004-06-22 ROwen	Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-09-14 ROwen	Tweaked _cmdCallback to make pychecker happier.
2004-11-15 ROwen	Modified to use RO.Wdg.Checkbutton's improved defaults.
"""
import Tkinter
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import TUI.Sounds
import TUI.TUIModel
import StatusConfigInputWdg

_HelpPrefix = "Instruments/GRIM/GRIMWin.html#"

class StatusConfigWdg (Tkinter.Frame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to configure GRIM
		"""
		Tkinter.Frame.__init__(self, master, **kargs)

		tuiModel = TUI.TUIModel.getModel()
		self.tlSet = tuiModel.tlSet
		self.configShowing = False

		self.inputWdg = StatusConfigInputWdg.StatusConfigInputWdg(self)
		self.inputWdg.grid(row=0, column=0, sticky="w")
	
		# create and pack command monitor
		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			helpURL = _HelpPrefix + "StatusBar",
			dispatcher = tuiModel.dispatcher,
			prefs = tuiModel.prefs,
			summaryLen = 10,
		)
		self.statusBar.grid(row=1, column=0, sticky="ew")

		# create and pack the buttons
		buttonFrame = Tkinter.Frame(self)

		self.exposeButton = RO.Wdg.Button(
			master = buttonFrame,
			text = "Expose...",
			command = self.showExpose,
			helpText = "open the GRIM Expose window",
			helpURL = _HelpPrefix + "Expose",
		)
		self.exposeButton.grid(row=0, column=0, sticky="w")

		self.showConfigWdg = RO.Wdg.Checkbutton(
			master = buttonFrame,
			onvalue = "Hide Config",
			offvalue = "Show Config",
			callFunc = self._showConfigCallback,
			showValue = True,
			helpText = "show/hide config. controls",
			helpURL = _HelpPrefix + "ShowConfig",
		)
		self.showConfigWdg.grid(row=0, column=2)

		buttonFrame.columnconfigure(2, weight=1)

		self.applyButton = RO.Wdg.Button(
			master = buttonFrame,
			text = "Apply",
			command = self.doApply,
			helpText = "apply the config. changes",
			helpURL = _HelpPrefix + "Apply",
		)
	 	self.applyButton.grid(row=0, column=3)

		spacerFrame = Tkinter.Frame(buttonFrame, width=5)
		spacerFrame.grid(row=0, column=5)

		self.currentButton = RO.Wdg.Button(
			master = buttonFrame,
			text = "Current",
			command = self.doCurrent,
			helpText = "reset controls to current GRIM config.",
			helpURL = _HelpPrefix + "Current",
		)
		self.currentButton.grid(row=0, column=6)

		buttonFrame.grid(row=2, column=0, sticky="ew")
		
		self.inputWdg.gridder.addShowHideWdg (
			StatusConfigInputWdg._ConfigCat,
			[self.applyButton, spacerFrame, self.currentButton],
		)
		self.inputWdg.gridder.addShowHideControl (
			StatusConfigInputWdg._ConfigCat,
			self.showConfigWdg,
		)

		self._setApplyState(True)
	
	def doApply(self):
		try:
			cmd = self.inputWdg.getString()
		except ValueError, e:
			self.statusBar.setMsg(e, level=2, isTemp=True)
			return
		cmdVar = RO.KeyVariable.CmdVar(
			cmdStr = cmd,
			actor = "grim",
			timeLim = 80,
			callFunc = self._cmdCallback,
		)
		self.statusBar.doCmd(cmdVar)
		
	def doCurrent(self):
		"""Disable all input widgets and the status window;
		if no commands are queued then enable the apply button.
		"""
		self.inputWdg.restoreDefault()
		self.statusBar.clear()

	def showExpose(self):
		self.tlSet.makeVisible("None.GRIM Expose")
	
	def _cmdCallback(self, msgType, msgDict=None, cmdVar=None):
		"""Callback for the currently executing command
		"""
		if msgType == ":":
			# current command finished
			self._setApplyState(True)
			TUI.Sounds.cmdDone()
		elif msgType in ("f!"):
			# current command failed; give up on the others
			self._setApplyState(True)
			TUI.Sounds.cmdFailed()
	
	def _setApplyState(self, doEnable):
		"""Sets the state of the apply button
		"""
		if doEnable:
			self.applyButton["state"] = "normal"
		else:
			self.applyButton["state"] = "disabled"

	def _showConfigCallback(self, wdg=None):
		"""Callback for show/hide config toggle.
		Restores defaults if config newly shown."""
		showConfig = self.showConfigWdg.getBool()
		restoreConfig = showConfig and not self.configShowing
		self.configShowing = showConfig
		if restoreConfig:
			self.inputWdg.restoreDefault()


if __name__ == "__main__":
	root = RO.Wdg.PythonTk()

	import TestData
		
	testFrame = StatusConfigWdg (root)
	testFrame.pack(side="top")
	
	TestData.dispatch()
	testFrame.doCurrent()
	
	def printCmds():
		try:
			cmd = testFrame.inputWdg.getString()
		except ValueError, e:
			print "Invalid command:", e
			return
		print "Command:"
		print cmd
	
	butFrame = Tkinter.Frame()
	Tkinter.Button(butFrame, text="Cmds", command=printCmds).pack(side="left")
	Tkinter.Button(butFrame, text="Demo", command=TestData.animate).pack(side="left")
	butFrame.pack(side="top")
	root.mainloop()
