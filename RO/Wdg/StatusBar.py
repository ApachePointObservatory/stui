"""Displays hot help, error messages and monitors the progress of commands
of the class RO.KeyVariable.cmdVar

History:
2003-04-04 ROwen	Adapted from StatusWdg.
2003-04-09 ROwen	Modified clearTempMsg to use 0 for "clear any"
					and None for don't clear anything.
					Made clearTempMsg explicitly return None and documented why.
2003-04-11 ROwen	Added handlers for <<EntryError>>, <Enter> and <Leave>
					and automatically bind them to the toplevel.
2003-04-21 ROwen	Renamed StatusWdg to StatusBar to avoid conflicts.
2003-08-01 ROwen	Bug fix: _reset was not resetting self.permSeverity.
2003-08-11 ROwen	Modified because TypeDict and AllTypes were moved
					from KeyDispatcher to KeyVariable.
2003-10-20 ROwen	Modified <<EntryError>> handler to beep (instead of event sender),
					so other users can catch the event and notify in other ways.
2003-10-28 ROwen	Modified clear to clear permanent messages and reset everything.
2003-12-05 ROwen	Fixed some bugs associated with executing commands:
					when a cmd started any existing permanent message was not cleared,
					and the "command starting" message was not permanent.
2004-02-20 ROwen	Bug fix: clear did not set the current text color,
					which caused incorrect color in some situations.
					Ditched _reset after adding remaining functionality to clear.
2004-02-23 ROwen	Added support for playing a sound when a command ends.
2004-05-18 ROwen	Bug fix: missing import of sys for writing error messages.
					Modified _cmdCallback to use dataStr (it was computed and ignored).
2004-07-20 ROwen	StatusBar now inherits from CtxMenu, making it easier to customize
					the contextual menu.
2004-08-12 ROwen	Added helpText argument (which disables hot help display;
					see documentation for helpText for more information).
					Modified to no longer display informational messages for commands;
					still displays warnings, failures and done.
					Added playCmdDone, playCmdFailed methods.
					Modified to use st_Normal, etc. constants for message level.
					Define __all__ to restrict import.
2004-09-03 ROwen	Modified for RO.Wdg.sev... -> RO.Constants.sev...
2004-10-01 ROwen	Bug fix: width arg was being ignored.
2005-01-05 ROwen	setMsg: changed level to severity.
2005-05-12 ROwen	Mod. to use the default borderwidth.
2005-06-16 ROwen	Added cmdSummary argument to doCmd.
					Modified to use severity built into RO.Wdg.EntryWdg
					(prefs no longer need color prefs and the code is simpler).
					Modified command output to ignore info messages
					unless they contain a "Text" keyword.
"""
__all__ = ['StatusBar']

import sys
import Tkinter
import RO.Alg
import RO.Constants
import RO.KeyVariable
import RO.Prefs.PrefVar
import CtxMenu
import Sound
import Entry

def _getSound(playCmdSounds, prefs, prefName):
	noPlay = Sound.NoPlay()
	if not playCmdSounds:
		return noPlay
	soundPref = prefs.getPrefVar(prefName)
	if soundPref == None:
		sys.stderr.write("StatusBar cannot play %r; no such preference" % prefName)
		return noPlay
	elif not hasattr(soundPref, "play"):
		sys.stderr.write("StatusBar cannot play %r; preference exists but is not a sound" % prefName)
		return noPlay
	return soundPref		


class StatusBar(Tkinter.Frame, CtxMenu.CtxMenu):
	"""Display hot help and error messages and execute commands
	and display their progress.

	Inputs:
	- dispatcher	an RO.KeyDispatcher
	- summaryLen	max # of characters of command to show, excluding final "..."
	- prefs			a RO.Prefs.PrefSet of preferences; uses:
					- "Command Done" and "Command Failed" sounds if playCmdSounds true
	- playCmdSounds	if true, play "Command Done", "Command Failed" sounds
					when a command started by doCmd succeeds or fails.
					if true and these prefs aren't available or are available but aren't sounds,
					prints a warning to stderr.
	- helpText		Warning: if specified then the status bar will NOT display
					help text and entry errors. This is typically only used if you have
					more than one status bar in a window, in which case one should show
					help and the others should have helpText strings.
	"""
	def __init__(self,
		master,
		dispatcher = None,
		prefs = None,
		playCmdSounds = False,
		summaryLen = 10,
		helpURL = None,
		helpText = None,
		width = 20,
	**kargs):
		self.dispatcher = dispatcher
		self.summaryLen = int(summaryLen)
		self.cmdDoneSound = _getSound(playCmdSounds, prefs, "Command Done")
		self.cmdFailedSound = _getSound(playCmdSounds, prefs, "Command Failed")
		
		Tkinter.Frame.__init__(self, master, **kargs)
		self.displayWdg = Entry.StrEntry(
			master = self,
			readOnly = True,
			width = width,
		)
		self.displayWdg.pack(expand="yes", fill="x")
		
		CtxMenu.CtxMenu.__init__(self,
			wdg = self.displayWdg,
			helpURL = helpURL,
		)

		self.clear()
		
		# bind to catch events
		self.helpText = helpText
		if not helpText:
			tl = self.winfo_toplevel()
			tl.bind("<<EntryError>>", self.handleEntryError)
			tl.bind("<Enter>", self.handleEnter)
			tl.bind("<Leave>", self.handleLeave)
	
	def clear(self):
		"""Clear the display and cancels all messages.
		"""
		self.displayWdg.set("", severity=RO.Constants.sevNormal)
		self.permSeverity = RO.Constants.sevNormal
		self.permMsg = None
		self.currID = None
		self.tempID = 0
		self.entryErrorID = None
		self.helpID = None
		self.cmdVar = None
		self.cmdSummary = ""
	
	def clearTempMsg(self, msgID=0):
		"""Clear a temporary message, if any.

		Returns None, so a common paradigm to avoid saving a stale ID is:
		savedID = statusBar.clearTempMsg(savedID)
		
		Input:
		- msgID:	ID of message to clear;
				0 will clear any temporary message,
				None will not clear anything
		"""
		if self.currID == None or msgID == None:
			return None

		if msgID == 0 or self.currID == msgID:
			self.setMsg(self.permMsg, self.permSeverity)
			self.currID = None
		return None
	
	def doCmd(self, cmdVar, cmdSummary=None):
		"""Execute the given command and display progress reports
		for command start warnings and command completion or failure.
		"""
		self.clear()

		self.cmdVar = cmdVar
		if cmdSummary == None:
			if len(self.cmdVar.cmdStr) > self.summaryLen + 3:
				cmdSummary = self.cmdVar.cmdStr[0:self.summaryLen] + "..."
			else:
				cmdSummary = self.cmdVar.cmdStr
		self.cmdSummary = cmdSummary
	
		if self.dispatcher:
			cmdVar.addCallback(self._cmdCallback, ":wf!")
			self.setMsg("%s started" % self.cmdSummary)
			self.dispatcher.executeCmd(self.cmdVar)
		else:
			self._cmdCallback(msgType = "f", msgDict = {
				"type":"f",
				"msgStr":"No dispatcher",
				"dataStart":0,
			})
	
	def handleEntryError(self, evt):
		"""Handle the <<EntryError>> event to report a data entry error.
		To do anything useful, the sender must have a getEntryError method.
		"""
		msgStr = evt.widget.getEntryError()
		if msgStr:
			self.entryErrorID = self.setMsg(
				msgStr = msgStr,
				severity = RO.Constants.sevWarning,
				isTemp = True,
			)
			self.bell()
		else:
			self.entryErrorID = self.clearTempMsg(self.entryErrorID)			
	
	def handleEnter(self, evt):
		"""Handle the <Enter> event to show help.
		To do anything useful, the sender must have a helpText attribute.
		"""
		try:
			msgStr = evt.widget.helpText
		except AttributeError:
			return
		if msgStr:
			self.helpID = self.setMsg(msgStr, severity=RO.Constants.sevNormal, isTemp=True)
	
	def handleLeave(self, evt):
		"""Handle the <Leave> event to erase help.
		"""
		if self.helpID:
			self.helpID = self.clearTempMsg(self.helpID)
	
	def playCmdDone(self):
		"""Play "command done" sound.
		"""
		self.cmdDoneSound.play()
	
	def playCmdFailed(self):
		"""Play "command failed" sound.
		"""
		self.cmdFailedSound.play()

	def setMsg(self, msgStr, severity=RO.Constants.sevNormal, isTemp=False, duration=None):
		"""Display a new message.
		
		Inputs:
		- msgStr	the new string to display
		- severity	one of RO.Constants.sevNormal (default), sevWarning or sevError
		- isTemp	if true, message is temporary and can be cleared with clearTempMsg;
					if false, any existing temp info is ditched
		- duration	the amount of time (msec?) to leave a temporary message;
					if omitted, there is no time limit;
					ignored if isTemp false
		
		Returns None if a permanent message, else a unique positive message ID.
		"""
		self.displayWdg.set(msgStr, severity=severity)
		if isTemp:
			self.tempID += 1
			self.currID = self.tempID
			if duration != None:
				self.displayWdg.after(duration, self.clearTempMsg, self.tempID)
			return self.tempID
		else:
			self.permMsg = msgStr
			self.permSeverity = severity
			self.currID = None
		return self.currID

	def _cmdCallback(self, msgType, msgDict, cmdVar=None):
		# print "StatusBar _cmdCallback(%r, %r, %r)" % (msgType, msgDict, cmdVar)
		msgDescr, newSeverity = RO.KeyVariable.TypeDict[msgType]
		msgSeverity = max(newSeverity, self.permSeverity)
		if msgType == ":":
			# command finished; omit associated text
			# but append "with warnings" if there were warnings
			if msgSeverity == RO.Constants.sevWarning:
				msgDescr += " with warnings"
			infoText = "%s %s" % (
				self.cmdSummary,
				msgDescr,
			)
			self.playCmdDone()
			self.setMsg(infoText, msgSeverity)
			return

		dataStr = msgDict.get("data", {}).get("text", None)
		if not dataStr:
			if newSeverity == RO.Constants.Normal:
				# info message with no textual info; skip it
				return
			dataStr = msgDict.get("msgStr", "")[msgDict.get("dataStart", 0):]
		infoText = "%s %s: %s" % (self.cmdSummary, msgDescr, dataStr)
		self.setMsg(infoText, msgSeverity)
		if msgType in RO.KeyVariable.DoneTypes:
			self.playCmdFailed()
