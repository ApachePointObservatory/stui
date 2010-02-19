#!/usr/bin/env python
"""Widgets to load and run opscore.actor.ScriptRunner scripts.

ScriptModuleWdg loads a script from a specified module.
ScriptFileWdg loads a script from a python source file
  (i.e. a module, but one that need not be on the python path)

History:
2004-07-20 ROwen
2004-08-12 ROwen    Added 2nd status bar to separate script and cmd status.
                    Bug fix: some error msgs referenced nonexisting var "filename".
                    Define __all__ to restrict import.
2004-09-14 ROwen    Added BasicScriptWdg. Fixed bug in reload.
                    Bug fix: ScriptModuleWdg and ScriptFileWdg ignored helpURL.
2005-01-05 ROwen    Changed level to severity (internal change).
2005-06-16 ROwen    Documented change of default cmdStatusBar from statusBar to no bar.
2006-03-09 ROwen    Added support for ScriptRunner's scriptClass argument.
2006-04-24 ROwen    Modified to report reload failures.
2006-10-31 ROwen    Bug fix: if a script paused itself, the pause button
                    still showed "Pause" instead of "Resume".
2007-07-02 ROwen    Overhauled helpURL handling. Now it looks in the script
                    for a variable named HelpURL.
2007-07-25 ROwen    Bug fix: script reloading was broken by the helpURL overhaul.
2008-05-02 ROwen    Add __file__ local variable to each loaded script file;
                    this makes it easier to find help files.
2010-02-17 ROwen    Adapted from RO.Wdg.ScriptWdg.
"""
__all__ = ['BasicScriptWdg', 'ScriptModuleWdg', 'ScriptFileWdg']

import os.path
import Tkinter
import RO.Constants
import RO.AddCallback
import RO.Wdg
import opscore.actor
import StatusBar

# compute _StateSevDict which contains
# state:severity for non-normal severities
_StateSevDict = {}
_StateSevDict[opscore.actor.ScriptRunner.Paused] = RO.Constants.sevWarning
_StateSevDict[opscore.actor.ScriptRunner.Cancelled] = RO.Constants.sevWarning
_StateSevDict[opscore.actor.ScriptRunner.Failed] = RO.Constants.sevError

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
    - master        master widget; the script functions may pack or grid stuff into this
    - name          script name; used to report status
    - dispatcher    keyword dispatcher; required to use the doCmd and startCmd methods
    - runFunc       run function (run when the start button pressed)
    - statusBar     script status bar, if any
    - startButton   button to start the script
        The following inputs are optional:
    - initFunc      a function run once when the script is first loaded
    - endFunc       a function run when the script ends for any reason; None of undefined)
    - cmdStatusBar  command status bar, if any; may be the same as statusBar
    - pauseButton   button to pause/resume the script
    - cancelButton  button to cancel the script
    - stateFunc     function to call when the script runner changes state.
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
        statusBar,
        startButton,
        scriptClass = None,
        runFunc = None,
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
        self.cancelButton["command"] = self._doCancel
    
        self._makeScriptRunner(
            master = master,
            scriptClass = scriptClass,
            initFunc = initFunc,
            runFunc = runFunc,
            endFunc = endFunc,
        )
        
        if stateFunc:
            self.addCallback(stateFunc)
    
    def _makeScriptRunner(self, master, scriptClass=None, initFunc=None, runFunc=None, endFunc=None):
        """Create a new script runner.
        See ScriptRunner for the meaning of the arguments.
        """
        self.scriptRunner = opscore.actor.ScriptRunner(
            name = self.name,
            dispatcher = self.dispatcher,
            master = master,
            scriptClass = scriptClass,
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
        
        Note: the pause button's text is updated by _stateFunc.
        """
        if self.pauseButton["text"] == "Resume":
            self.scriptRunner.resume()
        else:
            self.scriptRunner.pause()
    
    def _doStart(self):
        """Start script.
        """
        self.scriptRunner.start()
    
    def _setButtonState(self):
        """Set the state of the various buttons.
        """
        print "_setButtonState(); state=%r; isExecuting=%r" % (self.scriptRunner.state, self.scriptRunner.isExecuting,)
        if self.scriptRunner.isExecuting:
            self.startButton["state"] = "disabled"
            self.pauseButton["state"] = "normal"
            self.cancelButton["state"] = "normal"
        else:
            self.startButton["state"] = "normal"
            self.pauseButton["state"] = "disabled"
            self.cancelButton["state"] = "disabled"

        if self.scriptRunner.isPaused:
            self._setPauseText("Resume")
        else:
            self._setPauseText("Pause")
    
    def _setPauseText(self, text):
        """Set the text and help text of the pause button.
        """
        self.pauseButton["text"] = text
        self.pauseButton.helpText = "%s the script" % text
    
    def _stateFunc(self, *args):
        """Script state function callback.
        """
        state, reason = self.scriptRunner.fullState
        if reason:
            msgStr = "%s: %s" % (state, reason)
        else:
            msgStr = state
        
        severity = _StateSevDict.get(state, RO.Constants.sevNormal)

        self.scriptStatusBar.setMsg(msgStr, severity)
        self._setButtonState()
        
        if self.scriptRunner.isDone:
            if self.scriptRunner.didFail:
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
    
    Subclasses must override _getScriptFuncs.
    
    Inputs:
    - master        master Tk widget; when that widget is destroyed
                    the script function is cancelled.
    - name          script name; used to report status
    - dispatcher    keyword dispatcher; required to use the doCmd and startCmd methods
    All remaining keyword arguments are sent to Tkinter.Frame.__init__
    """
    def __init__(self,
        master,
        name,
        dispatcher = None,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)

        
        srArgs = self._getScriptFuncs(isFirst=True)
        helpURL = srArgs.pop("HelpURL", None)

        row = 0
        
        self.scriptFrame = Tkinter.Frame(self)
        self.scriptFrame.grid(row=row, column=0, sticky="news")
        self.scriptFrameRow = row
        self.rowconfigure(row, weight=1)
        self.columnconfigure(0, weight=1)
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
            summaryLen = 30,
            playCmdSounds = False,
            helpURL = helpURL,
        )
        cmdStatusBar.grid(row=row, column=0, sticky="ew")
        row += 1
        
        buttonFrame = Tkinter.Frame(self)
        startButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Start",
            helpText = "Start the script",
            helpURL = helpURL,
        )
        startButton.pack(side="left")
        pauseButton = RO.Wdg.Button(
            master = buttonFrame,
            helpURL = helpURL,
        )
        pauseButton.pack(side="left")
        cancelButton = RO.Wdg.Button(
            master = buttonFrame,
            text = "Cancel",
            helpText = "Halt the script",
            helpURL = helpURL,
        )
        cancelButton.pack(side="left")
        buttonFrame.grid(row=row, column=0, sticky="w")
        row += 1

        # set up contextual menu functions for all widgets
        # (except script frame, which is handled in reload)
        startButton.ctxSetConfigFunc(self._setCtxMenu)
        pauseButton.ctxSetConfigFunc(self._setCtxMenu)
        cancelButton.ctxSetConfigFunc(self._setCtxMenu)
        scriptStatusBar.ctxSetConfigFunc(self._setCtxMenu)
        cmdStatusBar.ctxSetConfigFunc(self._setCtxMenu)
        
        BasicScriptWdg.__init__(self,
            master = self.scriptFrame,
            name = name,
            dispatcher = dispatcher,
            statusBar = scriptStatusBar,
            cmdStatusBar = cmdStatusBar,
            startButton = startButton,
            pauseButton = pauseButton,
            cancelButton = cancelButton,
        **srArgs)
    
    def reload(self):
        """Create or recreate the script frame and script runner.
        """
#       print "reload"
        self.scriptStatusBar.setMsg("Reloading", RO.Constants.sevNormal)
        try:
            srArgs = self._getScriptFuncs(isFirst = False)
            srArgs.pop("HelpURL", None) # don't send HelpURL arg to _makeScriptRunner
    
            # destroy the script frame,
            # which also cancels the script and its state callback
            self.scriptFrame.grid_forget()
            self.scriptFrame.destroy()
            self.scriptRunner = None
    
            self.scriptFrame = Tkinter.Frame(self)
            self.scriptFrame.grid(row=self.scriptFrameRow, column=0, sticky="news")
            self._makeScriptRunner(self.scriptFrame, **srArgs)
            self.scriptStatusBar.setMsg("Reloaded", RO.Constants.sevNormal)
        except (SystemExit, KeyboardInterrupt):
            raise
        except:
            self.scriptStatusBar.setMsg("Reload failed; see error log", RO.Constants.sevError)
            raise
            
    
    def _getScriptFuncs(self, isFirst):
        """Return a dictionary containing either scriptClass
        or one or more of initFunc, runFunc, endFunc;
        it may also contain HelpURL.

        Details:
        - the script class is instantiated or initFunc called:
            - once when this widget is built
            - again each time the script is reloaded
        - scriptObj.run or runFunc is called whenever the Start button is pushed.
        - scriptObj.end or endFunc is called when runFunc ends for any reason
            (finishes, fails or is cancelled); used for cleanup
        where scriptObj represents the instantiated script class.
        
        Specify None for init or end if undefined (run is required).

        All functions receive one argument: sr, a ScriptRunner object.
        The functions can pass information using sr.globals,
        an initially empty object (to which you can add
        instance variables and set or read them).

        Inputs:
        - isFirst   True if the first execution
        
        Warning: only the run function may call sr methods that wait.
        The other functions may only run non-waiting code.
        
        Must be defined by all subclasses.
        """
        raise RuntimeError("Class %s must define _getScriptFuncs" % \
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
    ):
        """Widget that runs a script from a module.
        
        The module must contain either:
        - a script class named ScriptClass
            with a run method and an optional end method
        or
        - a function named "run" and optional functions:
        - "init", if present, will be run once as the module is read
        - "end", if present, will be run whenever "run" ends
            (whether it succeeded, failed or was cancelled)
        
        run, init and end all receive one argument: sr, an opscore.actor.ScriptRunner object.
        
        ScriptClass.__init__ or init may populate sr.master with widgets.
        sr.master is an empty frame above the status bar intended for this purpose.
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
        )
    
    def _getScriptFuncs(self, isFirst):
        """Return a dictionary containing either scriptClass
        or one or more of initFunc, runFunc, endFunc;
        it may also contain HelpURL.
        """
        if not isFirst:
            reload(self.module)

        scriptClass = getattr(self.module, "ScriptClass", None)
        if scriptClass:
            return {"scriptClass": scriptClass}
        
        retDict = {}
        for attrName in ("run", "init", "end", "HelpURL"):
            attr = getattr(self.module, attrName, None)
            if attr:
                retDict["%sFunc" % attrName] = attr
            elif attrName == "run":
                raise RuntimeError("%r has no %s function" % (self.module, attrName))

        return retDict


class ScriptFileWdg(_BaseUserScriptWdg):
    def __init__(self,
        master,
        filename,
        dispatcher,
        helpURL = None,
    ):
        """Widget that runs a script python source code file
        (a python module, but one that need not be on the python path).
        
        The file must contain either:
        - a script class named ScriptClass
            with a run method and an optional end method
        or
        - a function named "run" and optional functions:
        - "init", if present, will be run once as the module is read
        - "end", if present, will be run whenever "run" ends
            (whether it succeeded, failed or was cancelled)
        
        run, init and end all receive one argument: sr, an opscore.actor.ScriptRunner object.
        
        ScriptClass.__init__ or init may populate sr.master with widgets.
        sr.master is an empty frame above the status bar intended for this purpose.
        (The run and end functions probably should NOT populate sr.master
        with widgets because they are not initially executed and they
        may be executed multiple times)
        
        The file name must end in .py (any case)
        """
#       print "ScriptFileWdg(%r, %r, %r)" % (master, filename, dispatcher)
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
#       print "copyPath"
        self.clipboard_clear()
        self.clipboard_append(self.fullPath)

    def _setCtxMenu(self, menu):
        """Set the contextual menu for the status bar,
        backgound frame and control buttons.
        """
#       print "_setCtxMenu(%r)" % menu
        menu.add_command(label = self.fullPath, state = "disabled")
        menu.add_command(label = "Copy Path", command = self.copyPath)
        menu.add_command(label = "Reload", command = self.reload)
        return True
    
    def _getScriptFuncs(self, isFirst=None):
        """Return a dictionary containing either scriptClass
        or one or more of initFunc, runFunc, endFunc;
        it may also contain HelpURL.
        """
#       print "_getScriptFuncs(%s)" % isFirst
        scriptLocals = {"__file__": self.fullPath}
        execfile(self.filename, scriptLocals)
        
        retDict = {}
        helpURL = scriptLocals.get("HelpURL")
        if helpURL:
            retDict["HelpURL"] = helpURL

        scriptClass = scriptLocals.get("ScriptClass")
        if scriptClass:
            retDict["scriptClass"] = scriptClass
            return retDict
        
        for attrName in ("run", "init", "end"):
            attr = scriptLocals.get(attrName)
            if attr:
                retDict["%sFunc" % attrName] = attr
            elif attrName == "run":
                raise RuntimeError("%r has no %s function" % (self.filename, attrName))

        return retDict

if __name__ == "__main__":
    import os.path
    import TUI.Models.TUIModel
    import RO.Wdg
    import TestScriptWdg

    tuiModel = TUI.Models.TUIModel.Model(True)
    dispatcher = tuiModel.dispatcher

    tuiModel.tkRoot.title('Script 1 (tuiModel.tkRoot)')
    
    testTL1 = tuiModel.tkRoot
    sr1 = ScriptModuleWdg(
        master = testTL1,
        module = TestScriptWdg,
        dispatcher = dispatcher,
    )
    sr1.pack()
    testTL1.title(sr1.scriptRunner.name)
    testTL1.resizable(False, False)

    
    testTL2 = Tkinter.Toplevel()
    currDir = os.path.dirname(__file__)
    sr2 = ScriptFileWdg(
        master = testTL2,
        filename = os.path.join(currDir, 'TestScriptWdg.py'),
        dispatcher = dispatcher,
    )
    sr2.pack()
    testTL2.title(sr2.scriptRunner.name)
    tuiModel.tkRoot.resizable(False, False)

    tuiModel.reactor.run()
