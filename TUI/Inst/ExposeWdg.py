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
"""
import Tkinter
import RO.Alg
import RO.InputCont
import RO.Wdg
import RO.KeyVariable
import ExposeStatusWdg
import ExposeInputWdg
import TUI.TUIModel
import TUI.Sounds
import ExposeModel

# name and help for each exposure command
_StopCmdInfo = (
	("pause", "Pause or resume the exposure"),
	("resume", "Pause or resume the exposure"),
	("stop", "Stop the exposure and save the data"),
	("abort", "Stop the exposure and discard the data"),
)
_StopCmds = [info[0] for info in _StopCmdInfo]
_StopHelpDict = dict(_StopCmdInfo)

_HelpPrefix = "Instruments/ExposeWin.html#"

class ExposeWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
		instName,
	**kargs):

		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		
		self.tuiModel = TUI.TUIModel.getModel()
		self.expModel = ExposeModel.getModel(instName)
		
		# set the following true when Expose is pushed
		# and set false again as soon as the sequence starts
		# or the command is rejected
		# this prevents a status word from a previous sequence
		# from causing buttons to be incorrectly disabled
		self.exposeStarting = False

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
		
		def makeStopWdg(name):
			"""Creates and packs a stop button;
			name is one of pause, stop or abort (lowercase!)
			"""
			wdg = RO.Wdg.Button(butFrame,
					text = name.capitalize(),
					helpText = _StopHelpDict[name],
					helpURL = _HelpPrefix + "%sButton" % (name,),
				)
			if name == "pause":
				wdg["width"] = 6
			wdg["command"] = RO.Alg.GenericCallback(
				self.doStop,
				wdg,
			)
			wdg.pack(side="left")
			return wdg

		self.pauseWdg = makeStopWdg("pause")
		self.stopWdg = makeStopWdg("stop")
		self.abortWdg = makeStopWdg("abort")
		self.stopWdgSet = (self.pauseWdg, self.stopWdg, self.abortWdg)

		self.configWdg = RO.Wdg.Button(butFrame,
			text = "Config...",
			command = self.doConfig,
			helpText = "Open the %s configure window" % self.expModel.instName,
			helpURL = _HelpPrefix + "ConfigButton",
		)
		self.configWdg.pack(side="right")

		butFrame.pack(side="top", expand="yes", fill="x")
		
		self.expModel.seqState.addCallback(self._seqStateCallback)
		
		self._sequenceEnds()
		
	def doExpose(self):
		"""Starts an exposure sequence.
		"""
		cmdStr = self.expInputWdg.getString()
		if cmdStr == None:
			return

		cmdVar = RO.KeyVariable.CmdVar(
			cmdStr = cmdStr,
			actor = self.expModel.actor,
			timeLim = None,
			callFunc = self._exposeCallback,
			callTypes = RO.KeyVariable.AllTypes,
		)
		self.exposeStarting = True
		self.statusBar.doCmd(cmdVar)
		self.pauseWdg["text"] = "Pause"
		self.startWdg.setEnable(False)
		for wdg in self.stopWdgSet:
			wdg.setEnable(True)

	def doStop(self, wdg):
		"""Handles the Pause, resume, Stop and Abort buttons;
		wdg is the button that was pressed.
		"""
		cmd = wdg["text"]
		lcmd = cmd.lower()
		
		if lcmd not in _StopCmds:
			raise ValueError, "unknown command %r" % (cmd,)
			
		cmdStr = lcmd
		if lcmd in ("abort", "stop"):
			self._sequenceEnds()

		elif lcmd == "pause":
			# if the logic is changed so only EXPOSURES can be paused,
			# not sequences, then remove the following line,
			# thus leaving the button enabled and allowing the user
			# to repeatedly try to pause until the pause succeeds
			self.pauseWdg.setEnable(False)

		elif lcmd == "resume":
			self.pauseWdg.setEnable(False)
		
		cmdVar = RO.KeyVariable.CmdVar(
			cmdStr = cmdStr,
			actor = self.expModel.actor,
			timeLim = None,
		)
		self.statusBar.doCmd(cmdVar)
		
	def doConfig(self):
		"""Brings up the configuration window.
		"""
		self.tuiModel.tlSet.makeVisible("Inst.%s" % self.expModel.instName)
	
	def _exposeCallback(self, msgType, *args, **kargs):
		"""Call for any replies to the expose command.
		"""
		self.exposeStarting = False
		if msgType in (RO.KeyVariable.DoneTypes):
			self._sequenceEnds()

	def _sequenceEnds(self, *args, **kargs):
		"""Call when:
		- The expose command ends (succeeds or fails)
		- The user presses Stop or Abort
		- seqState indicates the sequence is over
		  and not self.exposeStarting
		"""
		self.pauseWdg["text"] = "Pause"
		for wdg in self.stopWdgSet:
			wdg.setEnable(False)
		self.startWdg.setEnable(True)

	def _seqStateCallback(self, seqState, isCurrent, **kargs):
		"""Called with the <inst>SeqState state keyword (the 7th value)
		seqState consist of:
		- cmdr (progID.username)
		- exposure type
		- exposure duration
		- exposure number
		- number of exposures requested
		- sequence status (a short string)
		  can be any of: running, paused, aborted, stopped, done, failed
		  and perhaps others
		"""
		if not isCurrent:
			return

		cmdr, expType, expDur, expNum, totExp, status = seqState
		progID, username = cmdr.split('.')

		if progID.lower() != self.tuiModel.getProgID().lower():
			# may want to return later, after disabing buttons, but meanwhile....
			return

		status = status.lower()
		
		# enable or disable stop and abort as appropriate
		if not self.exposeStarting:
			if status in ("running", "paused"):
				self.stopWdg.setEnable(True)
				self.abortWdg.setEnable(True)
			else:
				self.stopWdg.setEnable(False)
				self.abortWdg.setEnable(False)
		
		# handle pause widget
		if status == "paused":
			self.pauseWdg["text"] = "Resume"
			self.pauseWdg.setEnable(True)
		elif not self.exposeStarting:
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
