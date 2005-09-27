#!/usr/local/bin/python
"""Exposure widget.

History:
2003-04-21 ROwen	first draft, starting from a copy of the input widget
2003-06-09 ROwen	removed most args; still first draft status.
2003-06-25 ROwen	Modified test case to handle message data as a dict
2003-07-21 ROwen	First version that does anything
2003-07-30 ROwen	Modified to be generic for all instruments and to use Inst.ExposeModel
2003-08-01 ROwen	Cleaned up the button logic; more to be done
2003-08-13 ROwen	Finished button logic cleanup using new seqState state element.
2003-09-30 ROwen	Updated the help prefix.
2003-10-01 ROwen	Modified to use new versions of seqState and expState (for new hub).
2003-10-06 ROwen	Modified to use unified progID, etc. naming convention.
2003-10-10 ROwen	Modified to use expose model actor, for new hub.
2003-10-16 ROwen	Bug fix: some refresh commands had not been updated for the new hub.
2004-02-23 ROwen	Modified to play cmdDone/cmdFailed for commands.
2004-06-22 ROwen	Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-08-13 ROwen	Increased the separation of status and input panels.
2004-09-10 ROwen	Modified doExpose to stop asking for the exposure time.
					It wasn't using the time for anything.
2005-07-21 ROwen	Modified to disable Expose and enable stop buttons
					when any sequence is running, regardless of who started it.
2005-08-02 ROwen	Modified for TUI.Sounds->TUI.PlaySound.
2005-09-12 ROwen	Fix PR 256: if a command failed without inducing status,
					the button state would not be restored.
2005-09-26 ROwen	Fix PR 274: stop and abort failed.
					Added support for new inst info: canPause, canStop, canAbort and
					improved help text for Pause, Stop, Abort accordingly.
"""
import Tkinter
import RO.Alg
import RO.InputCont
import RO.Wdg
import RO.KeyVariable
import ExposeStatusWdg
import ExposeInputWdg
import TUI.TUIModel
import TUI.PlaySound
import ExposeModel

# dict of stop command: desired new sequence state
_StopCmdStateDict = dict(
	pause = "paused",
	resume = "running",
	stop = "stopped",
	abort = "aborted",
)

_HelpPrefix = "Instruments/ExposeWin.html#"

class ExposeWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
		instName,
	**kargs):

		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		
		self.tuiModel = TUI.TUIModel.getModel()
		self.expModel = ExposeModel.getModel(instName)

		self.expStatusWdg = ExposeStatusWdg.ExposeStatusWdg(
			self,
			instName,
		)
		self.expStatusWdg.pack(side="top", pady=2, expand="yes", fill="x")
		
		Tkinter.Frame(self,
#			relief="ridge",	# doesn't do anything; why not?
#			border=2,		# doesn't do anything; why not?
			bg = "black",
		).pack(side="top", expand="yes", fill="x")

		self.expInputWdg = ExposeInputWdg.ExposeInputWdg(
			self,
			instName,
#			relief="ridge",
#			border=1,
		)
		self.expInputWdg.pack(side="top", expand="yes", fill="x")

		self.statusBar = RO.Wdg.StatusBar(self,
			dispatcher = self.tuiModel.dispatcher,
			prefs = self.tuiModel.prefs,
			playCmdSounds = True,
		)
		self.statusBar.pack(side="top", expand="yes", fill="x")
		
		butFrame = Tkinter.Frame(self)

		self.startWdg = RO.Wdg.Button(butFrame,
			text = "Start",
			command = self.doExpose,
			helpURL = _HelpPrefix + "StartButton",
		)
		self.startWdg.pack(side="left")
		
		def makeStopWdg(name, doShow=True, canDoExp=True):
			"""Creates and packs a stop button;
			Inputs:
			- name		one of pause, stop or abort (lowercase!)
			- doShow	show this widget?
			- canDoExp	if false, can only handle sequence (for help string)
			"""
			helpText = {
				("pause", True):  "Pause or resume the exposure",
				("pause", False): "Pause or resume the exposure sequence",
				("stop",  True):  "Stop the exposure and save the data",
				("stop",  False): "Stop the exposure sequence",
				("abort", True):  "Stop the exposure and discard the data",
				("abort", False): "Stop the exposure sequence",
			}[(name, canDoExp)]
			wdg = RO.Wdg.Button(butFrame,
					text = name.capitalize(),
					helpText = helpText,
					helpURL = _HelpPrefix + "%sButton" % (name,),
				)
			if name == "pause":
				wdg["width"] = 6
			wdg["command"] = RO.Alg.GenericCallback(
				self.doStop,
				wdg,
			)
			if doShow:
				wdg.pack(side="left")
			return wdg

		instInfo = self.expModel.instInfo
		# Always display pause. If the instrument can't pause an exposure,
		# at least the user can pause a sequence.
		self.pauseWdg = makeStopWdg("pause", True, instInfo.canPause)
		# If instrument can neither stop or abort an exposure,
		# then display stop so the user can stop a sequence
		showStop = instInfo.canStop or not instInfo.canAbort
		self.stopWdg = makeStopWdg("stop", showStop, instInfo.canStop)
		self.abortWdg = makeStopWdg("abort", instInfo.canAbort, instInfo.canAbort)

		self.configWdg = RO.Wdg.Button(butFrame,
			text = "Config...",
			command = self.doConfig,
			helpText = "Open the %s configure window" % self.expModel.instName,
			helpURL = _HelpPrefix + "ConfigButton",
		)
		self.configWdg.pack(side="right")

		butFrame.pack(side="top", expand="yes", fill="x")
		
		self.expModel.seqState.addIndexedCallback(self._seqStatusCallback, 5)
	
	def doCmd(self, cmdStr, nextState):
		"""Execute an <inst>Expose command. Handle button state.
		
		Inputs:
		- cmdStr	the <inst>Expose command
		- nextState	the expected next state as a result of this command
		"""
		cmdVar = RO.KeyVariable.CmdVar(
			actor = self.expModel.actor,
			cmdStr = cmdStr,
			timeLim = None,
			callFunc = self._cmdFailed,
			callTypes = RO.KeyVariable.FailTypes,			
		)
		self.statusBar.doCmd(cmdVar)
		self._seqStatusCallback(nextState)
		
	def doConfig(self):
		"""Brings up the configuration window.
		"""
		self.tuiModel.tlSet.makeVisible("Inst.%s" % self.expModel.instName)
		
	def doExpose(self):
		"""Starts an exposure sequence.
		"""
		cmdStr = self.expInputWdg.getString()
		if cmdStr == None:
			return
		
		self.doCmd(cmdStr, "running")

	def doStop(self, wdg):
		"""Handles the Pause, Resume, Stop and Abort buttons.
		
		Inputs:
		- wdg	the button that was pressed
		"""
		cmdStr = wdg["text"].lower()
		
		try:
			nextState = _StopCmdStateDict[cmdStr]
		except LookupError:
			raise ValueError("ExposeWdg.doStop: unknown command %r" % (cmdStr,))

		self.doCmd(cmdStr, nextState)
	
	def _cmdFailed(self, *args, **kargs):
		"""Call when a command fails. Sets button state based on current state.
		"""
		currState, isCurrent = self.expModel.seqState.getInd(0)
		self._seqStatusCallback(currState, isCurrent)

	def _seqStatusCallback(self, status, isCurrent=True, **kargs):
		"""Called with the status field of the <inst>SeqState state keyword.
		status will be one of: running, paused, aborted, stopped, done, failed
		"""
		#print "_seqStatusCallback(self, status=%r, isCurrent=%r)" % (status, isCurrent)
		if status != None:
			status = status.lower()
		
		# enable or disable stop and abort as appropriate
		if status in ("running", "paused"):
			self.startWdg.setEnable(False)
			self.stopWdg.setEnable(True)
			self.abortWdg.setEnable(True)
		else:
			self.startWdg.setEnable(True)
			self.stopWdg.setEnable(False)
			self.abortWdg.setEnable(False)
		
		# handle pause widget
		if status == "paused":
			self.pauseWdg["text"] = "Resume"
			self.pauseWdg.setEnable(True)
		else:
			self.pauseWdg["text"] = "Pause"
			self.pauseWdg.setEnable(status == "running")
		

if __name__ == '__main__':
	root = RO.Wdg.PythonTk()
	root.resizable(width=False, height=False)

	import ExposeTestData

	testFrame = ExposeWdg(root, "DIS")
	testFrame.pack(side="top", expand="yes")

	Tkinter.Button(text="Demo", command=ExposeTestData.animate).pack(side="top")

	ExposeTestData.dispatch()

	root.mainloop()
