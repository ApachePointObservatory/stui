#!/usr/local/bin/python
"""Log window

Warning:
This widget will not pack reliably on MacOS X
unless you specify an initial size for the widget.
For an example of how to do this, see the example script at the bottom.
(This is due to a bug in Tk which I reported for aqua Tk 8.4.1 on 2002-11-15
and verified with aqua Tk 8.4.6 and MacOS X 10.3.4 on 2004-07-16.)

History:
2003-12-17 ROwen	Added addWindow and renamed to UsersWindow.py.
2004-05-18 ROwen	Stopped obtaining TUI model in addWindow; it was ignored.
2004-06-22 ROwen	Modified for RO.Keyvariable.KeyCommand->CmdVar
2004-07-22 ROwen	Play sound queue when user command finishes.
					Warn (message and sound queue) if user command has no actor.
2004-08-25 ROwen	Do not leave command around if user command has no actor. It was confusing.
2004-09-14 ROwen	Minor change to make pychecker happier.
"""
import Tkinter
import RO.KeyVariable
import RO.Wdg
import TUI.TUIModel
import TUI.HubModel
import TUI.Sounds

_HelpPage = "TUIMenu/LogWin.html"

def addWindow(tlSet):
	tlSet.createToplevel(
		name = "TUI.Log",
		defGeom = "603x413+430+280",
		resizable = True,
		visible = False,
		wdgFunc = LogWdg,
	)

# a list of message categories, default colors and color preference variables
_ReplyCatColorPrefList = (
	("Error",       "red",   "Error Color"),
	("Warning",     "blue2", "Warning Color"),
	("Information", "black", "Text Color"),
)

class LogWdg(RO.Wdg.CmdReplyWdg):
	"""
	Listens to the connection, parsing, logging and dispatching input.
	Also allows direct entry of commands.
	
	Uses the following preferences, if available:
	"Text Color", "Warning Color", "Error Color"
	"""
	def __init__(self,
		master,
		**kargs
	):
		"""Inputs:
		- master: master widget
		- **kargs: keyword arguments for RO.Wdg.CmdReplyWdg
		"""
		tuiModel = TUI.TUIModel.getModel()
		self.actorsKey = TUI.HubModel.getModel().actors

		tuiModel.dispatcher.setLogger(self)
		self.dispatcher = tuiModel.dispatcher
		
		cmdCatList = [("User", "black"), ("Refresh", "black")]
		replyCatList = [(catName, tuiModel.prefs.getPrefVar(prefName, defColor)) \
			for catName, defColor, prefName in _ReplyCatColorPrefList]
		
		RO.Wdg.CmdReplyWdg.__init__(
			self,
			master = master,
			cmdFunc = self.doCommand,
			cmdCatList = cmdCatList,
			replyCatList = replyCatList,
			helpURL = _HelpPage,
		**kargs)

		# make sure to exit gracefully
		self.bind("<Destroy>", self.__del__)
	
	def doCommand(self, actorCmdStr):
		"""Executes a command (if a dispatcher was specified).

		Inputs:
		- actorCmdStr: a string containing the actor
			and command, separated by white space.
		"""
		try:
			actor, cmdStr = actorCmdStr.split(None, 1)
		except ValueError:
			actor = actorCmdStr
			cmdStr = ""
		
#		# check actor if possible
#		currActors, isCurr = self.actorsKey.get()
#		if isCurr and actor not in currActors:
#			# unkown actor
#			errMsg = "Text=\"Cannot execute %r; Unknown actor %r\"" % (actorCmdStr, actor,)
#			self._reportError(errMsg)
#			return

		# no command (or no actor)
		if not cmdStr:			
			errMsg = "Text=\"Cannot execute %r; no command found!\"" % (actorCmdStr,)
			self._reportError(errMsg)
			return
		
		# issue the command
		RO.KeyVariable.CmdVar (
			actor = actor,
			cmdStr = cmdStr,
			callFunc = self._cmdCallback,
			dispatcher = self.dispatcher,
		)
	
	def _cmdCallback(self, msgType, msgDict, cmdVar):
		"""Command callback; called when a command finishes.
		"""
		if cmdVar.didFail():
			TUI.Sounds.cmdFailed()
		elif cmdVar.isDone():
			TUI.Sounds.cmdDone()

	def __del__ (self, *args):
		"""Going away; remove myself as the dispatcher's logger.
		"""
		self.dispatcher.setLogger()
	
	def _reportError(self, errMsg):
		"""Report a command input error.
		"""
		errMsgDict = self.dispatcher.makeMsgDict(
			type = "f",
			dataStr = errMsg,
		)
		self.dispatcher.logMsgDict(errMsgDict)
		TUI.Sounds.cmdFailed()


if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	# specifying an initial size for the parent window
	# is necessary to avoid a bug in Tk's grid handling on Macs
	root.geometry("600x400")

	testFrame = LogWdg(root)
	testFrame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	root.resizable(width=True, height=True)
	
	root.mainloop()
