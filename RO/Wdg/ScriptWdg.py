#!/usr/local/bin/python
"""Widgets to load and run RO.ScriptRunner scripts.

ScriptModuleWdg loads a script from a specified module.
ScriptFileWdg loads a script from a python source file
  (i.e. a module, but one that need not be on the python path)

History:
2004-07-20 ROwen
2004-08-12 ROwen	Added 2nd status bar to separate script and cmd status.
					Bug fix: some error msgs referenced nonexisting var "filename".
					Define __all__ to restrict import.
2004-09-14 ROwen	Added BasicScriptWdg. Fixed bug in reload.
					Bug fix: ScriptModuleWdg and ScriptFileWdg ignored helpURL.
2005-01-05 ROwen	Changed level to severity (internal change).
"""
__all__ = ['BasicScriptWdg', 'ScriptModuleWdg', 'ScriptFileWdg']

import os.path
import Tkinter
from RO.Constants import *
import RO.AddCallback
import RO.OS
import RO.ScriptRunner
import RO.SeqUtil
import Button
import CtxMenu
import StatusBar

# compute _StateSevDict which contains
# state:severity for non-normal severities
_StateSevDict = {}
_StateSevDict[RO.ScriptRunner.Paused] = sevWarning
_StateSevDict[RO.ScriptRunner.Cancelled] = sevWarning
_StateSevDict[RO.ScriptRunner.Failed] = sevError

class _Blank(object):
	def __init__(self):
		object.__init__(self)
		
class _FakeButton:
	def noop(self, *args, **kargs):
		return
	__init__ = noop
	__setitem__ = noop
	pack = noop
	ctxSetConfigFunc = noop

class BasicScriptWdg(RO.AddCallback.BaseMixin):
	"""Handles button enable/disable and such for a ScriptRunner.
	You are responsible for creating and displaying the status bar(s)
	and start, pause and cancel buttons.
	
	Inputs:
	- master		master widget; the script functions may pack or grid stuff into this
	- name			script name; used to report status
	- dispatcher	keyword dispatcher; required to use the doCmd and startCmd methods
	- runFunc		run function (run when the start button pressed)
	- statusBar		script status bar
	- startButton	button to start the script
		The following inputs are optional:
	- initFunc		a function run once when the script is first loaded
	- endFunc		a function run when the script ends for any reason; None of undefined)
	- cmdStatusBar	command status bar; if None, set to script status bar
	- pauseButton	button to pause/resume the script
	- cancelButton	button to cancel the script
	- stateFunc		function to call when the script runner changes state.
					The function receives one argument: the script runner.
	
	Notes:
	- The text of the Pause button is automatically set (to Pause or Resume, as appropriate).
	- You must set the text of the start and cancel buttons.
	- Supports the RO.AddCallback interface for state function callbacks,
	  including addCallback and removeCallback
	"""
	def __init__(self,
		master,
		name,
		dispatcher,
		runFunc,
		statusBar,
		startButton,
		initFunc = None,
		endFunc = None,
		cmdStatusBar = None,
		pauseButton = None,
		cancelButton = None,
		stateFunc = None,
	):
		RO.AddCallback.BaseMixin.__init__(self)

		self.name = name
		self.dispatcher = dispatcher
		
		self.scriptRunner = None
		
		if not pauseButton:
			pauseButton = _FakeButton()

		if not cancelButton:
			cancelButton = _FakeButton()
		
		self.scriptStatusBar = statusBar
		self.cmdStatusBar = cmdStatusBar or statusBar
		
		self.startButton = startButton
		self.pauseButton = pauseButton
		self.cancelButton = cancelButton
		
		self.startButton["command"] = self._doStart
		self.pauseButton["command"] = self._doPause
		self._setPauseText("Pause")
		self.cancelButton["command"] = self._doCancel
	
		self._makeScriptRunner(master, initFunc, runFunc, endFunc)
		
		if stateFunc:
			self.addCallback(stateFunc)
	
	def _makeScriptRunner(self, master, initFunc, runFunc, endFunc):
		"""Create a new script runner.
		"""
		self.scriptRunner = RO.ScriptRunner.ScriptRunner(
			master = master,
			name = self.name,
			dispatcher = self.dispatcher,
			initFunc = initFunc,
			runFunc = runFunc,
			endFunc = endFunc,
			stateFunc = self._stateFunc,
			statusBar = self.scriptStatusBar,
			cmdStatusBar = self.cmdStatusBar,
		)	

		self._setButtonState()
	
	def _doCancel(self):
		"""Cancel the script.
		"""
		self.scriptRunner.cancel()
	
	def _doPause(self):
		"""Pause or resume script (depending on Pause button's text).
		"""
		if self.pauseButton["text"] == "Resume":
			self.scriptRunner.resume()
			self._setPauseText("Pause")
		else:
			self.scriptRunner.pause()
			self._setPauseText("Resume")
	
	def _doStart(self):
		"""Start script.
		"""
		self.scriptRunner.start()
	
	def _setButtonState(self):
		"""Set the state of the various buttons.
		"""
		if not self.scriptRunner.isExecuting():
			self.startButton["state"] = "normal"
			self.pauseButton["state"] = "disabled"
			self._setPauseText("Pause")
			self.cancelButton["state"] = "disabled"
		else:
			self.startButton["state"] = "disabled"
			self.pauseButton["state"] = "normal"
			self.cancelButton["state"] = "normal"
	
	def _setPauseText(self, text):
		"""Set the text and help text of the pause button.
		"""
		self.pauseButton["text"] = text
		self.pauseButton.helpText = "%s the script" % text
	
	def _stateFunc(self, *args):
		"""Script state function callback.
		"""
		state, stateStr, reason = self.scriptRunner.getFullState()
		if reason:
			msgStr = "%s: %s" % (stateStr, reason)
		else:
			msgStr = stateStr
		
		severity = _StateSevDict.get(state, sevNormal)

		self.scriptStatusBar.setMsg(msgStr, severity)
		self._setButtonState()
		
		if self.scriptRunner.isDone():
			if stateStr == RO.ScriptRunner.Failed:
				self.scriptStatusBar.playCmdFailed()
			else:
				self.scriptStatusBar.playCmdDone()
		
		self._doCallbacks()
	
	def _doCallbacks(self):
		"""Execute the callback functions, passing the script runner as the argument.
		"""
		self._basicDoCallbacks(self.scriptRunner)


class _BaseUserScriptWdg(Tkinter.Frame, BasicScriptWdg):
	"""Base class widget that runs a function via a ScriptRunner.
	
	Subclasses must override _getIREFuncs.
	
	Inputs:
	- master		master Tk widget; when that widget is destroyed
					the script function is cancelled.
	- name			script name; used to report status
	- dispatcher	keyword dispatcher; required to use the doCmd and startCmd methods
	- helpURL		url for help
	All remaining keyword arguments are sent to Tkinter.Frame.__init__
	"""
	def __init__(self,
		master,
		name,
		dispatcher = None,
		helpURL = None,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		self.helpURL = helpURL

		row = 0

		self.scriptFrame = Tkinter.Frame(self)
		self.scriptFrame.grid(row=row, column=0, sticky="news")
		row += 1

		scriptStatusBar = StatusBar.StatusBar(
			master = self,
			helpURL = helpURL,
			helpText = "script status and messages",
		)
		scriptStatusBar.grid(row=row, column=0, sticky="ew")
		row += 1
		
		cmdStatusBar = StatusBar.StatusBar(
			master = self,
			dispatcher = dispatcher,
			summaryLen = 30,
			playCmdSounds = False,
			helpURL = helpURL,
		)
		cmdStatusBar.grid(row=row, column=0, sticky="ew")
		row += 1
		
		buttonFrame = Tkinter.Frame(self)
		startButton = Button.Button(
			master = buttonFrame,
			text = "Start",
			helpText = "Start the script",
			helpURL = helpURL,
		)
		startButton.pack(side="left")
		pauseButton = Button.Button(
			master = buttonFrame,
			helpURL = helpURL,
		)
		pauseButton.pack(side="left")
		cancelButton = Button.Button(
			master = buttonFrame,
			text = "Cancel",
			helpText = "Halt the script",
			helpURL = helpURL,
		)
		cancelButton.pack(side="left")
		buttonFrame.grid(row=row, column=0, sticky="w")
		row += 1
		
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)

		# set up contextual menu functions for all widgets
		# (except script frame, which is handled in reload)
		startButton.ctxSetConfigFunc(self._setCtxMenu)
		pauseButton.ctxSetConfigFunc(self._setCtxMenu)
		cancelButton.ctxSetConfigFunc(self._setCtxMenu)
		scriptStatusBar.ctxSetConfigFunc(self._setCtxMenu)
		cmdStatusBar.ctxSetConfigFunc(self._setCtxMenu)
		
		initFunc, runFunc, endFunc = self._getIREFuncs(isFirst=True)
		
		BasicScriptWdg.__init__(self,
			master = self.scriptFrame,
			name = name,
			dispatcher = dispatcher,
			initFunc = initFunc,
			runFunc = runFunc,
			endFunc = endFunc,
			statusBar = scriptStatusBar,
			cmdStatusBar = cmdStatusBar,
			startButton = startButton,
			pauseButton = pauseButton,
			cancelButton = cancelButton,
		)
	
	def reload(self):
		"""Create or recreate the script frame and script runner.
		"""
#		print "reload"
		funcs = self._getIREFuncs(isFirst = False)

		# destroy the script frame,
		# which also cancels the script and its state callback
		self.scriptFrame.grid_forget()
		self.scriptFrame.destroy()
		self.scriptRunner = None

		self.scriptFrame = Tkinter.Frame(self)
		self.scriptFrame.grid(row=0, column=0, sticky="nsew")

		self._makeScriptRunner(self.scriptFrame, *funcs)

		CtxMenu.addCtxMenu(
			wdg = self.scriptFrame,
			helpURL = self.helpURL,
			configFunc = self._setCtxMenu,
		)
		self.scriptStatusBar.setMsg("Reloaded", 0)
	
	def _getIREFuncs(self, isFirst):
		"""Return init, run and end functions.
		
		The functions are as follows:
		- init (optional) is called once when this widget is built
		and again if the script is reloaded.
		- run (required) is called whenever the Start button is pushed.
		- end (optional) is called when runFunc ends for any reason
		(finishes, fails or is cancelled); used for cleanup
		
		Specify None for init or end if undefined (run is required).

		All three functions receive one argument: sr, a ScriptRunner object.
		The functions can pass information using sr.globals,
		an initially empty object (to which you can add
		instance variables and set or read them).

		Inputs:
		- isFirst	True if the first execution
		
		Warning: only the run function may call sr methods that wait.
		The other functions may only run non-waiting code.
		
		Must be defined by all subclasses.
		"""
		raise RuntimeError("Class %s must define _getIREFuncs" % \
			(self.__class__.__name__,))
	
	def _setCtxMenu(self, menu):
		"""Set the contextual menu for the status bar,
		backgound frame and control buttons.
		Returning True makes it automatically show help.
		"""
		menu.add_command(label = "Reload", command = self.reload)
		return True


class ScriptModuleWdg(_BaseUserScriptWdg):
	def __init__(self,
		master,
		module,
		dispatcher,
		helpURL = None,
	):
		"""Widget that runs a script from a module.
		
		The module must contain a function named "run",
		which is the script controlled by the ScriptRunner.
		
		The module may also contain two other functions:
		- "init", if present, will be run once as the module is read
		- "end", if present, will be run whenever "run" ends
			(whether it succeeded, failed or was cancelled)
		
		run, init and end all receive one argument: sr,	an RO.ScriptRunner
		object. See RO.ScriptRunner for more information.
		
		init may populate sr.master with widgets. sr.master is
		an empty frame above the status bar intended for this purpose.
		(The run and end functions probably should NOT populate sr.master
		with widgets because they are not initially executed and they
		may be executed multiple times)
		"""
		self.module = module
		
		_BaseUserScriptWdg.__init__(
			self,
			master = master,
			name = module.__name__,
			dispatcher = dispatcher,
			helpURL = helpURL,
		)
	
	def _getIREFuncs(self, isFirst):
		"""Return init, run and end functions"""
		if not isFirst:
			reload(self.module)

		runFunc = getattr(self.module, "run", None)
		if not runFunc:
			raise RuntimeError("%r has no run function" % (self.module,))

		initFunc = getattr(self.module, "init", None)
		endFunc = getattr(self.module, "end", None)

		return initFunc, runFunc, endFunc


class ScriptFileWdg(_BaseUserScriptWdg):
	def __init__(self,
		master,
		filename,
		dispatcher,
		helpURL = None,
	):
		"""Widget that runs a script python source code file
		(a python module, but one that need not be on the python path).
		
		The file must contain a function named "run",
		which is the script controlled by the ScriptRunner.
		
		The file may also contain two other functions:
		- "init", if present, will be run once as the module is read
		- "end", if present, will be run whenever "run" ends
			(whether it succeeded, failed or was cancelled)
		
		run, init and end all receive one argument: sr,	an RO.ScriptRunner
		object. See RO.ScriptRunner for more information.
		
		init may populate sr.master with widgets. sr.master is
		an empty frame above the status bar intended for this purpose.
		(The run and end functions probably should NOT populate sr.master
		with widgets because they are not initially executed and they
		may be executed multiple times)
		
		The file name must end in .py (any case)
		"""
#		print "ScriptFileWdg(%r, %r, %r)" % (master, filename, dispatcher)
		self.filename = filename
		self.fullPath = os.path.abspath(self.filename)

		baseName = os.path.basename(self.filename)
		scriptName, fileExt = os.path.splitext(baseName)
		if fileExt.lower() != ".py":
			raise RuntimeError("file name %r does not end in '.py'" % (self.filename,))
		
		_BaseUserScriptWdg.__init__(
			self,
			master = master,
			name = scriptName,
			dispatcher = dispatcher,
			helpURL = helpURL,
		)
	
	def copyPath(self):
		"""Copy path to the clipboard.
		"""
#		print "copyPath"
		self.clipboard_clear()
		self.clipboard_append(self.fullPath)

	def _setCtxMenu(self, menu):
		"""Set the contextual menu for the status bar,
		backgound frame and control buttons.
		"""
#		print "_setCtxMenu(%r)" % menu
		menu.add_command(label = self.fullPath, state = "disabled")
		menu.add_command(label = "Copy Path", command = self.copyPath)
		menu.add_command(label = "Reload", command = self.reload)
		return True
	
	def _getIREFuncs(self, isFirst=None):
		"""Return init, run and end functions"""
#		print "_getIREFuncs(%s)" % isFirst
		scriptLocals = {}
		execfile(self.filename, scriptLocals)

		runFunc = scriptLocals.get("run", None)
		if not runFunc:
			raise RuntimeError("%r has no run function" % (self.filename,))

		initFunc = scriptLocals.get("init", None)
		endFunc = scriptLocals.get("end", None)

		return initFunc, runFunc, endFunc

if __name__ == "__main__":
	import RO.KeyDispatcher
	import PythonTk
	import TestScriptWdg
	root = PythonTk.PythonTk()
	root.title('Script 1 (root)')
	
	dispatcher = RO.KeyDispatcher.KeyDispatcher()
	
	testTL1 = root
	sr1 = ScriptModuleWdg(
		master = testTL1,
		module = TestScriptWdg,
		dispatcher = dispatcher,
	)
	sr1.pack()
	testTL1.title(sr1.scriptRunner.name)
	testTL1.resizable(False, False)

	
	testTL2 = Tkinter.Toplevel()
	sr2 = ScriptFileWdg(
		master = testTL2,
		filename = 'TestScriptWdg.py',
		dispatcher = dispatcher,
	)
	sr2.pack()
	testTL2.title(sr2.scriptRunner.name)
	root.resizable(False, False)
	
	root.mainloop()
