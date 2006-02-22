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
2006-02-22 ROwen	Modified to use new CmdWdg.
"""
__all__ = ['CmdReplyWdg']

import Tkinter
import CmdWdg
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
		
		if not cmdFunc:
			cmdFunc = self.addOutputNL
		self._rawCmdFunc = cmdFunc

		self.cmdText = CmdWdg.CmdWdg(self,
			cmdFunc = self._cmdWrapper,
			helpURL = helpURL,
		)
		self.cmdVar = self.cmdText.getVar()

		self.outText = LogWdg.LogWdg(self,
			catSet = (("Commands:", cmdCatList),
				("Replies:", replyCatList)),
			maxLines=maxLines,
			helpURL = helpURL,
		)

		self.outText.grid(row=0, column=0, sticky="nsew")
		self.cmdText.grid(row=1, column=0, sticky="ew")
		
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
	
	def _cmdWrapper(self, cmdStr):
		"""Wrapper for the command function that handles errors"""
		if self._rawCmdFunc:
			try:
				self._rawCmdFunc(cmdStr)
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				self.bell()
				self.addOutputNL("Command %r failed: %s" % (cmdStr, e))
	
	

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
