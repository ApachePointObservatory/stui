#!/usr/local/bin/python
"""
A LogWdg log widget coupled with a command entry field at the bottom.
The command entry field has command history.

To do:
* Add more key bindings for editing the command history.
* See if gridding could be improved to work around the Tk bug.

Warning:
This widget will not pack reliably on MacOS X
unless you specify an initial size for the widget.
For an example of how to do this, see the example script at the bottom.
(This is due to a bug in Tk which I reported for aqua Tk 8.4.1 on 2002-11-15
and verified with aqua Tk 8.4.6 and MacOS X 10.3.4 on 2004-07-16.)

History:
2002-11-13 ROwen	Added history. Bug fix: entering a command would not
					scroll all the way to the bottom if data was coming in; fixed using
					a carefully placed update_idletasks (we'll see if this always works).
					Bug fix: command history recall appended an extra character
					to the end of the recalled command; fixed by not propogating key events.
2002-11-15 ROwen	Fixed the example by specifying an initial window geometry
					and updated the comments to explain why this is necessary
2002-12-05 ROwen	Added support for URL-based help
2003-03-07 ROwen	Changed RO.Wdg.StringEntry to RO.Wdg.StrEntry.
2003-04-15 ROwen	Removed unused import of CtxMenu.
2004-05-18 ROwen	Bug fix: didn't set self.cmdText if no helpURL.
					Stopped importing sys since it was not being used.
2004-07-16 ROwen	Deleted redundant method showCmd.
					Added support for the user's command being rejected
					by the command callback function.
					Renamed all event handlers, including adding a leading _
					to make it clear they are internal functions
					and to avoid name collisions with subclasses.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-08-25 ROwen	Removed support for user's command being rejected. It was confusing to users.
import Tkinter
2004-09-14 ROwen	Tweaked the imports.
"""
__all__ = ['CmdReplyWdg']

import Tkinter
import LogWdg
import Entry

class CmdReplyWdg (Tkinter.Frame):
	"""Widget to receive text commands from a user and display replies similar information.
	The input field includes a command history.
	"""
	def __init__ (self,
		master,
		cmdFunc=None,
		maxCmds=50,
		cmdCatList=(),
		replyCatList=(),
		maxLines=1000,
		helpURL = None,
	**kargs):
		"""Create a widget for entering commands and viewing replies.
		Inputs:
		- cmdFunc: called when <return> is pressed in the command entry window;
		  takes one argument: cmdStr, the string in the command entry window
		  warning: cmdStr will NOT have a terminating <return> or <newline>
		- maxCmds: the maximum # of commands to save in the command history buffer
		- cmdCatList: a list of (category name, color-or-colorPref) tuples for commands,
		  where color-or-colorPref is either a string or a ColorPrefVar
		- replyCatList: list of (category name, color-or-colorPref) tuples for replies
		- maxLines: the max number of lines to display, ignoring wrapping
		- helpURL: the URL of a help page; it may include anchors for:
		  - "Command:" for the command pop-up menu
		  - "Reply:" for the reply pop-up menu
		  - "Find" for the Find button
		  - "LogDisplay" for the log display area
		  - "CommandEntry" for the command entry area
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		
		self.cmdHistory = []
		
		if not cmdFunc:
			cmdFunc = self.addOutputNL
		self.cmdFunc = cmdFunc

		self.histIndex = -1
		self.maxCmds = int(maxCmds)
		self.currCmd = ""
		
		self.outText = LogWdg.LogWdg(self,
			catSet = (("Commands:", cmdCatList),
				("Replies:", replyCatList)),
			maxLines=maxLines,
			helpURL = helpURL,
		)
		if helpURL:
			helpURL += "#CommandEntry"
		self.cmdText = Entry.StrEntry(self,
			helpURL = helpURL,
			takefocus = 1,
		)
		self.cmdVar = self.cmdText.getVar()

		self.cmdText.bind('<KeyPress-Return>', self._doCmd)
		self.cmdText.bind('<KeyPress-Up>', self._doHistUp)
		self.cmdText.bind('<Control-p>', self._doHistUp)
		self.cmdText.bind('<KeyPress-Down>', self._doHistDown)
		self.cmdText.bind('<Control-n>', self._doHistDown)

		self.cmdText.grid(row=1, column=0, sticky="ew")
		self.outText.grid(row=0, column=0, sticky="nsew")
		
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
			

		self.cmdText.focus_set()
	
	def addOutput(self, astr, category=None):
		"""Write the specified string to the output.
		No \n is appended.
		"""
		self.outText.addOutput(astr, category)
	
	def addOutputNL(self, astr, category=None):
		"""Write the specified string to the output.
		A newline (\n) is appended.
		"""
		self.outText.addOutput(astr + "\n", category)

	def clearOutput(self):
		"""Clear the output"""
		self.outText.clearOutput()

	def _doCmd(self, *args, **kargs):
		"""Execute the user's command, calling the command callback.
		
		Also save the command in the history
		(if not blank and not a copy of the previous command)
		and clear the command area.
		"""
		# obtain the command and clear the display
		cmdStr = self.cmdText.get()

		# execute command function, if any
		if self.cmdFunc:
			try:
				self.cmdFunc(cmdStr)
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				self.bell()
				self.addOutputNL("Command %r failed: %s" % (cmdStr, e))

		# clear display
		self.cmdText.delete(0,Tkinter.END)
		
		# insert command in history (if not blank and not a copy of the most recent command)
		# and reset the history index
		if cmdStr:
			if self.cmdHistory == [] or cmdStr != self.cmdHistory[0]:
				self.cmdHistory.insert(0, cmdStr)
		self.histIndex = -1

		# purge excess commands, if any
		del(self.cmdHistory[self.maxCmds:])
		self.currCmd = ""
		
		# scroll log window to end
		self.outText.text.see(Tkinter.END)
		self.update_idletasks()
	
	def _doHistDown(self, *args, **kargs):
		"""Go down one place in the history index;
		if at the bottom, then:
		- if a current command was tempoarily saved, redisplay it
		- otherwise do nothing
		"""
		if self.histIndex > 0:
			self.histIndex -= 1
			self.cmdVar.set(self.cmdHistory[self.histIndex])
			self.cmdText.icursor(Tkinter.END)
		elif self.histIndex == 0:
			self.cmdVar.set(self.currCmd)
			self.histIndex = -1
			self.cmdText.icursor(Tkinter.END)
		return "break" # prevent event from being propogated			
	
	def _doHistUp(self, *args, **kargs):
		"""Go up one place in the history index.
		If at the top, display a blank line.
		"""
		if self.histIndex == -1:
			# current command is showing; save it (but not in the history buffer),
			# so it can be retrieved with down-arrow or discarded by issuing some other cmd
			self.currCmd = self.cmdVar.get()

		# if there is a next command up, index and retrieve it
		# else clear the line
		if self.histIndex < len(self.cmdHistory) - 1:
			self.histIndex += 1
			self.cmdVar.set(self.cmdHistory[self.histIndex])
			self.cmdText.icursor(Tkinter.END)
		else:
			self.histIndex = len(self.cmdHistory)
			self.cmdVar.set("")
		return "break" # prevent event from being propogated			

	def _showKeyEvent(self, evt):
		"""Show the details of a keystroke; for debugging and development.
		"""
		print "Key event=%r" % (evt.__dict__, )
	
	

if __name__ == "__main__":
	from RO.Wdg.PythonTk import PythonTk
	import random
	root = PythonTk()
	# specifying an initial size for the parent window
	# is necessary to avoid a bug in Tk's grid handling on Macs
	root.geometry("600x400")
	
	FailCmd = 'fail'

	cmdCatList = (("User","black"), ("Refresh","black"))
	replyCatList = (("Error","red"), ("Warning","orange"), ("Information","black"))
	replyCatOnlyList = [item[0] for item in replyCatList]
	
	def doCmd(cmdStr):
		if cmdStr == FailCmd:
			raise RuntimeError("%r triggers the error test" % cmdStr)
		testFrame.addOutputNL(cmdStr, category=random.choice(replyCatOnlyList))

	testFrame = CmdReplyWdg (root,
		cmdFunc=doCmd,
		cmdCatList=cmdCatList,
		replyCatList=replyCatList,
	)
	testFrame.pack(fill=Tkinter.BOTH, expand=Tkinter.YES)
	
	testFrame.addOutputNL("Command %r will trigger an error test" % FailCmd)

	root.mainloop()
