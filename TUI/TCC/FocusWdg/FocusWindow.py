#!/usr/local/bin/python
"""Secondary mirror focus control.

History:
2004-01-09 ROwen	first draft
2004-02-23 ROwen	Modified to play cmdDone/cmdFailed for commands.
2004-03-11 ROwen	Bug fix: assumed the secondary mirror would start moving
					within 10 seconds (a poor assumption if others are moving
					the mirror). Fixed by removing the time limit.
2004-05-18 ROwen	Eliminated redundant import in test code.
2004-06-22 ROwen	Modified for RO.Keyvariable.KeyCommand->CmdVar
2005-01-05 ROwen	Changed level to severity for RO.Wdg.StatusBar.
"""
import Tkinter
import RO.Constants
import RO.Wdg
import InputWdg
import TUI.TUIModel
import TUI.Sounds

_HelpPrefix = "Telescope/FocusWin.html#"

def addWindow(tlSet):
	"""Create the window for TUI.
	"""
	tlSet.createToplevel(
		name = "TCC.Secondary Focus",
		defGeom = "+240+507",
		resizable = False,
		visible = False,
		wdgFunc = SecFocusWdg,
	)

class SecFocusWdg(Tkinter.Frame):
	def __init__ (self,
		master = None,
	 **kargs):
		"""creates a new widget for specifying secondary focus

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		Tkinter.Frame.__init__(self, master, **kargs)

		self.inputWdg = InputWdg.InputWdg(self)
		self.inputWdg.pack(side="top", anchor="nw")
		self.inputWdg.addCallback(self._applyEnableShim)
		
		tuiModel = TUI.TUIModel.getModel()

		# set up the command monitor
		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			dispatcher = tuiModel.dispatcher,
			prefs = tuiModel.prefs,
			playCmdSounds = True,
			helpURL = _HelpPrefix + "StatusBar",
		)
		self.statusBar.pack(side="top", anchor="nw", expand="yes", fill="x")
		
		# command buttons
		self.buttonFrame = Tkinter.Frame(self)
		self.applyButton = RO.Wdg.Button(
			master=self.buttonFrame,
			text="Apply",
			command=self.doFocus,
			helpText = "Apply requested focus",
			helpURL=_HelpPrefix + "ApplyButton",
		)
		self.applyButton.pack(side="left")

		self.currButton = RO.Wdg.Button(
			master=self.buttonFrame,
			text="Current",
			command=self.inputWdg.restoreDefault,
			helpText = "Show current focus",
			helpURL=_HelpPrefix + "CurrentButton",
		)
		self.currButton.pack(side="left")

		self.buttonFrame.pack(side="top", anchor="nw")
		
	def doFocus(self):
		"""Adjust the focus.
		"""
		self._applyEnable(False)
		try:
			cmdStr = self.inputWdg.getString()
		except ValueError, e:
			self.statusBar.setMsg(
				"Rejected: %s" % e,
				severity = RO.Constants.sevError,
				isTemp = True,
			)
			TUI.Sounds.cmdFailed()
			return

		cmdVar = RO.KeyVariable.CmdVar (
			actor = "tcc",
			cmdStr = cmdStr,
			timeLim = 0,
			timeLimKeyword="CmdDTime",
			isRefresh = False,
			callFunc = self._applyEnableShim,
		)
		self.statusBar.doCmd(cmdVar)
	
	def _applyEnable(self, doEnable=True):
		"""Enables or disables the Apply button
		"""
#		print "_applyEnable(%r)" % (doEnable,)
		if doEnable:
			self.applyButton["state"] = "normal"
		else:
			self.applyButton["state"] = "disabled"
	
	def _applyEnableShim(self, *args, **kargs):
		"""Enable the Apply button.
		Used as a callback shim. Ignores all arguments.
		"""
		self._applyEnable(True)


if __name__ == "__main__":
	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = SecFocusWdg(root)
	testFrame.pack(anchor="nw")

	dataDict = {
		"SecFocus": (325.0,),
	}
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
	kd.dispatch(msgDict)

	root.mainloop()
