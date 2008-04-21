#!/usr/bin/env python
"""Code to run scripts that can wait for various things
without messing up the main Tk event loop
(and thus starving the rest of your program).

ScriptRunner allows your script to wait for the following:
- wait for a given time interval using: yield waitMS(...)
- run a slow computation as a background thread using waitThread
- run a command via the keyword dispatcher using waitCmd
- run multiple commands at the same time:
  - start each command with startCmd,
  - wait for one or more commands to finish using waitCmdVars
- wait for a keyword variable to be set using waitKeyVar
- wait for a subscript by yielding it (i.e. yield subscript(...))
  note that the subscript must contain a yield for this to work;
  if it has no yield then just call it directly

An example is given as the test code at the end.
  
Code comments:
- Wait functions use a class to do all the work. This standardizes
  some tricky internals (such as registering and deregistering
  cancel functions) and allows the class to easily keep track
  of private internal data.
- The wait class is created but is not explicitly kept around.
  Why doesn't it immediately vanish? Because the wait class
  registers a method as a completion callback and usual
  another method as a cancel function. As long as somebody
  has a pointer to an method then the instance is kept alive.
- waitThread originally relied on generating an event when the script ended.
  Unfortunately, that proved unreliable; if the thread was very short,
  it could actually start trying to continue before the current
  iteration of the generator was finished! I'm surprised that was
  possible (I expected the event to get queued), but in any case
  it was bad news. The current scheme is a kludge -- poll the thread.
  I hope I can figure out something better.

History:
2004-08-12 ROwen
2004-09-10 ROwen    Modified for RO.Wdg.Constants->RO.Constants.
                    Bug fix: _WaitMS cancel used afterID instead of self.afterID.
                    Bug fix: test for resume while wait callback pending was broken,
                    leading to false "You forgot the 'yield'" errors.
2004-10-01 ROwen    Bug fix: waitKeyVar was totally broken.
2004-10-08 ROwen    Bug fix: waitThread could fail if the thread was too short.
2004-12-16 ROwen    Added a debug mode that prints diagnostics to stdout
                    and does not wait for commands or keyword variables.
2005-01-05 ROwen    showMsg: changed level to severity.
2005-06-16 ROwen    Changed default cmdStatusBar from statusBar to no bar.
2005-06-24 ROwen    Changed to use new CmdVar.lastReply instead of .replies.
2005-08-22 ROwen    Clarified _WaitCmdVars.getState() doc string.
2006-03-09 ROwen    Added scriptClass argument to ScriptRunner.
2006-03-28 ROwen    Modified to allow scripts to call subscripts.
2006-04-24 ROwen    Improved error handling in _continue.
                    Bug fixes to debug mode:
                    - waitCmd miscomputed iterID
                    - startCmd dispatched commands
2006-11-02 ROwen    Added checkFail argument to waitCmd and waitCmdVars methods.
                    waitCmd now returns the cmdVar in sr.value.
                    Added keyVars argument to startCmd and waitCmd.
2006-11-13 ROwen    Added waitUser and resumeUser methods.
2006-12-12 ROwen    Bug fix: start did not initialize waitUser instance vars.
                    Added initVars method to centralize initialization.
2008-04-21 ROwen    Improved debug mode output:
                    - showMsg prints messages
                    - _setState prints requested state
                    - _end prints the end function
                    
"""
import sys
import threading
import Queue
import traceback
import Tkinter
import RO.AddCallback
import RO.Constants
import RO.KeyVariable
import RO.SeqUtil

# state constants
Ready = 2
Paused = 1
Running = 0
Done = -1
Cancelled = -2
Failed = -3

_DebugState = False

# a dictionary that describes the various values for the connection state
_StateDict = {
    Ready: "Ready",
    Paused: "Paused",
    Running: "Running",
    Done: "Done",
    Cancelled: "Cancelled",
    Failed: "Failed",
}

# internal constants
_PollDelayMS = 100 # polling interval (in ms)

# a list of possible keywords that hold reasons for a command failure
# in the order in which they are checked
_ErrKeys = ("text", "txt", "exposetxt")

class _Blank(object):
    def __init__(self):
        object.__init__(self)

class ScriptError (RuntimeError):
    """Use to raise exceptions in your script
    when you don't want a traceback.
    """
    pass

class ScriptRunner(RO.AddCallback.BaseMixin):
    """Execute a script.

    Allows waiting for various things without messing up Tkinter's event loop.
    
    Inputs:
    - master        master Tk widget; when that widget is destroyed
                    the script function is cancelled.
    - name          script name; used to report status
    - runFunc       the main script function; executed whenever
                    the start button is pressed
    - scriptClass   a class with a run method and an optional end method;
                    if specified, runFunc, initFunc and endFunc may not be specified.
    - dispatcher    keyword dispatcher (see RO.KeyDispatcher);
                    required to use the waitCmd and startCmd methods
    - initFunc      function to call ONCE when the ScriptRunner is constructed
    - endFunc       function to call when runFunc ends for any reason
                    (finishes, fails or is cancelled); used for cleanup
    - stateFunc     function to call when the ScriptRunner changes state
    - startNow      if True, starts executing the script immediately
                    instead of waiting for user to call start.
    - statusBar     status bar, if available. Used by showMsg
    - cmdStatusBar  command status bar, if available.
                    Used to show the status of executing commands.
                    May be the same as statusBar.
    - debug         if True, startCmd and wait... print diagnostic messages to stdout
                    and there is no waiting for commands or keyword variables. Thus:
                    - waitCmd and waitCmdVars return success immediately
                    - waitKeyVar returns defVal (or None if not specified) immediately

    All functions (runFunc, initFunc, endFunc and stateFunc) receive one argument: sr,
    this ScriptRunner object. The functions can pass information using sr.globals,
    an initially empty object (to which you can add instance variables and set or read them).
    
    Only runFunc is allowed to call sr methods that wait.
    The other functions may only run non-waiting code.

    WARNING: when runFunc calls any of the ScriptRunner methods that wait,
    IT MUST YIELD THE RESULT, as in:
        def runFunc(sr):
            ...
            yield sr.waitMS(500)
            ...
    All such methods are marked "yield required".
    
    If you forget to yield, your script will not wait. Your script will then halt
    with an error message when it calls the next ScriptRunner method that involves waiting
    (but by the time it gets that far it may have done some strange things).
    
    If your script yields when it should not, it will simply halt.

    Using commands or keyword variables requires a dispatcher
    (see RO.KeyDispatcher and RO.KeyVariable).
    """
    def __init__(self,
        master,
        name,
        runFunc = None,
        scriptClass = None,
        dispatcher = None,
        initFunc = None,
        endFunc = None,
        stateFunc = None,
        startNow = False,
        statusBar = None,
        cmdStatusBar = None,
        debug = False,
    ):
        if scriptClass:
            if runFunc or initFunc or endFunc:
                raise ValueError("Cannot specify runFunc, initFunc or endFunc with scriptClass")
            if not hasattr(scriptClass, "run"):
                raise ValueError("scriptClass=%r has no run method" % scriptClass)
        elif runFunc == None:
            raise ValueError("Must specify runFunc or scriptClass")
        elif not callable(runFunc):
            raise ValueError("runFunc=%r not callable" % (runFunc,))

        self.master = master
        self.runFunc = runFunc
        self.name = name
        self.dispatcher = dispatcher
        self.initFunc = initFunc
        self.endFunc = endFunc
        self.debug = bool(debug)
        self._statusBar = statusBar
        self._cmdStatusBar = cmdStatusBar
        
        # useful constant for script writers
        self.ScriptError = ScriptError
        
        RO.AddCallback.BaseMixin.__init__(self)

        self.globals = _Blank()
        
        self.initVars()
        
        """create a private widget and bind <Delete> to it
        to kill the script when the master widget is destroyed.
        This makes sure the script halts when the master toplevel closes
        and avoids wait_variable hanging forever when the application is killed.
        Binding <Destroy> to a special widget instead of master avoids two problems:
        - If the user creates a widget and then destroys it
          <Delete> would be called, mysteriously halting the script.
        - When the master is deleted it also gets a <Delete> event for every
          child widget. Thus the <Delete> binding would be called repeatedly,
          which is needlessly inefficient.
        """
        self._privateWdg = Tkinter.Frame()
        self._privateWdg.bind("<Destroy>", self.__del__)

        if stateFunc:
            self.addCallback(stateFunc)
        
        # initialize, as appropriate
        if scriptClass:
            self.scriptObj = scriptClass(self)
            self.runFunc = self.scriptObj.run
            self.endFunc = getattr(self.scriptObj, "end", None)
        elif self.initFunc:
            res = self.initFunc(self)
            if hasattr(res, "next"):
                raise RuntimeError("init function tried to wait")
        
        if startNow:
            self.start()
    
    # methods for starting, pausing and aborting script
    # and for getting the current state of execution.
    
    def cancel(self):
        """Cancel the script.

        The script will not actually halt until the next
        waitXXX or doXXX method is called, but this should
        occur quickly.
        """
        if self.isExecuting():
            self._setState(Cancelled, "")

    def getFullState(self):
        """Returns the current state as a tuple:
        - state: a numeric value; named constants are available
        - stateStr: a short string describing the state
        - reason: the reason for the state ("" if none)
        """
        state, reason = self._state, self._reason
        try:
            stateStr = _StateDict[state]
        except KeyError:
            stateStr = "Unknown (%r)" % (state,)
        return (state, stateStr, reason)
    
    def getState(self):
        """Return the current state as a numeric value.
        See the state constants defined in RO.ScriptRunner.
        See also getFullState.
        """
        return self._state
    
    def initVars(self):
        """Initialize variables.
        Call at construction and when starting a new run.
        """
        self._cancelFuncs = []
        self._endingState = None
        self._state = Ready
        self._reason = ""
        self._iterID = [0]
        self._iterStack = []
        self._waiting = False # set when waiting for a callback
        self._userWaitID = None
        self.value = None
        
    def isAborting(self):
        """Return True if script is aborting or cancelling"""
        return self._endingState in (Cancelled, Failed)
    
    def isDone(self):
        """Return True if script is finished, successfully or otherwise.
        """
        return self._state <= Done
    
    def isExecuting(self):
        """Returns True if script is running or paused."""
        return self._state in (Running, Paused)
    
    def pause(self):
        """Pause execution.
        
        Note that the script must be waiting for something when the pause occurs
        (because that's when the GUI will be freed up to get the request to pause).
        If the thing being waited for fails then the script will fail (thus going
        from Paused to Failed with no user interation).

        Has no effect unless the script is running.
        """
        self._printState("pause")
        if not self._state == Running:
            return

        self._setState(Paused)
    
    def resume(self):
        """Resume execution after a pause.

        Has no effect if not paused.
        """
        self._printState("resume")
        if not self._state == Paused:
            return

        self._setState(Running)
        if not self._waiting:
            self._continue(self._iterID)

    def resumeUser(self):
        """Resume execution from waitUser
        """
        if self._userWaitID == None:
            raise RuntimeError("Not in user wait mode")
            
        iterID = self._userWaitID
        self._userWaitID = None
        self._continue(iterID)

    def start(self):
        """Start executing runFunc.
        
        If already running, rases RuntimeError
        """
        if self.isExecuting():
            raise RuntimeError("already executing")
    
        if self._statusBar:
            self._statusBar.setMsg("")
        if self._cmdStatusBar:
            self._cmdStatusBar.setMsg("")
        
        self.initVars()
    
        self._iterID = [0]
        self._iterStack = []
        self._setState(Running)
        self._continue(self._iterID)
    
    # methods for use in scripts
    # with few exceptions all wait for something
    # and thus require a "yield"
    
    def getKeyVar(self,
        keyVar,
        ind=0,
        defVal=Exception,
    ):
        """Return the current value of keyVar.
        See also waitKeyVar, which can wait for a value.

        Do not use yield because it does not wait for anything.

        Inputs:
        - keyVar    keyword variable
        - ind       which value is wanted? (None for all values)
        - defVal    value to return if value cannot be determined
                    (if omitted, the script halts)
        """
        if self.debug:
            argList = ["keyVar=%s" % (keyVar,)]
            if ind != 0:
                argList.append("ind=%s" % (ind,))
            if defVal != Exception:
                argList.append("defVal=%r" % (defVal,))
            if defVal == Exception:
                defVal = None

        currVal, isCurrent = keyVar.get()
        if isCurrent:
            if ind != None:
                retVal = currVal[ind]
            else:
                retVal = currVal
        else:
            if defVal==Exception:
                raise ScriptError("Value of %s invalid" % (keyVar,))
            else:
                retVal = defVal

        if self.debug:
            print "getKeyVar(%s); returning %r" % (", ".join(argList), retVal)
        return retVal
    
    def showMsg(self, msg, severity=RO.Constants.sevNormal):
        """Display a message--on the status bar, if available,
        else sys.stdout.

        Do not use yield because it does not wait for anything.
        
        Inputs:
        - msg: string to display, without a final \n
        - severity: one of RO.Constants.sevNormal (default), sevWarning or sevError
        """
        if self._statusBar:
            self._statusBar.setMsg(msg, severity)
            if self.debug:
                print msg
        else:
            print msg
    
    def startCmd(self,
        actor="",
        cmdStr = "",
        timeLim = 0,
        callFunc = None,
        callTypes = RO.KeyVariable.DoneTypes,
        timeLimKeyword = None,
        abortCmdStr = None,
        keyVars = None,
        checkFail = True,
    ):
        """Start a command using the same arguments as waitCmd (which see).
        Returns a command variable that you can wait for using waitCmdVars.

        Do not use yield because it does not wait for anything.
        
        Inputs: same as waitCmd, which see.
        
        Returns a command variable which you can wait for using waitCmdVars.
        """
        cmdVar = RO.KeyVariable.CmdVar(
            actor=actor,
            cmdStr = cmdStr,
            timeLim = timeLim,
            callFunc = callFunc,
            callTypes = callTypes,
            timeLimKeyword = timeLimKeyword,
            abortCmdStr = abortCmdStr,
            keyVars = keyVars,
        )
        if checkFail:
            cmdVar.addCallback(
                callFunc = self._cmdFailCallback,
                callTypes = RO.KeyVariable.FailTypes,
            )
        if self.debug:
            argList = ["actor=%r, cmdStr=%r" % (actor, cmdStr)]
            if timeLim != 0:
                argList.append("timeLim=%s" % (timeLim,))
            if callFunc != None:
                argList.append("callFunc=%r" % (callFunc,))
            if callTypes != RO.KeyVariable.DoneTypes:
                argList.append("callTypes=%r" % (callTypes,))
            if timeLimKeyword != None:
                argList.append("timeLimKeyword=%r" % (timeLimKeyword,))
            if abortCmdStr != None:
                argList.append("abortCmdStr=%r" % (abortCmdStr,))
            if checkFail != True:
                argList.append("checkFail=%r" % (checkFail,))
            print "startCmd(%s)" % ", ".join(argList)

            self._showCmdMsg("%s started" % cmdStr)
            

            # set up command completion callback
            def endCmd(self=self, cmdVar=cmdVar):
                endMsgDict = self.dispatcher.makeMsgDict(
                    cmdr = None,
                    actor = cmdVar.actor,
                    type = ":",
                    
                )
                cmdVar.reply(endMsgDict)
                msgStr = "%s finished" % cmdVar.cmdStr
                self._showCmdMsg("%s finished" % cmdVar.cmdStr)
            self.master.after(1000, endCmd)

        else:
            if self._cmdStatusBar:
                self._cmdStatusBar.doCmd(cmdVar)
            else:
                self.dispatcher.executeCmd(cmdVar)
                
        return cmdVar
    
    def waitCmd(self,
        actor="",
        cmdStr = "",
        timeLim = 0,
        callFunc=None,
        callTypes = RO.KeyVariable.DoneTypes,
        timeLimKeyword = None,
        abortCmdStr = None,
        keyVars = None,
        checkFail = True,
    ):
        """Start a command and wait for it to finish.
        Returns the cmdVar in sr.value.

        A yield is required.
        
        Inputs:
        - actor: the name of the device to command
        - cmdStr: the command (without a terminating \n)
        - timeLim: maximum time before command expires, in sec; 0 for no limit
        - callFunc: a function to call when the command changes state;
            see below for details.
        - callTypes: the message types for which to call the callback;
            a string of one or more choices; see RO.KeyVariable.TypeDict for the choices;
            useful constants include DoneTypes (command finished or failed)
            and AllTypes (all message types, thus any reply).
            Not case sensitive (the string you supply will be lowercased).
        - timeLimKeyword: a keyword specifying a delta-time by which the command must finish
        - abortCmdStr: a command string that will abort the command.
        - keyVars: a sequence of 0 or more keyword variables to monitor.
            If data for those variables arrives in response to this command
            the data is saved and can be retrieved from the cmdVar.
        - checkFail: check for command failure?
            if True (the default) command failure will halt your script

        Callback arguments:
            msgType: the message type, a character (e.g. "i", "w" or ":");
                see RO.KeyVariable.TypeDict for the various types.
            msgDict: the entire message dictionary
            cmdVar (by name): the key command object
                see RO.KeyVariable.CmdVar for details
        
        Note: timeLim and timeLimKeyword work together as follows:
        - The initial time limit for the command is timeLim
        - If timeLimKeyword is seen before timeLim seconds have passed
          then self.maxEndTime is updated with the new value
          
        Also the time limit is a lower limit. The command is guaranteed to
        expire no sooner than this but it may take a second longer.
        """
        self._waitCheck(setWait = False)
        
        if self.debug:
            print "waitCmd calling startCmd"

        cmdVar = self.startCmd (
            actor = actor,
            cmdStr = cmdStr,
            timeLim = timeLim,
            callFunc = callFunc,
            callTypes = callTypes,
            timeLimKeyword = timeLimKeyword,
            abortCmdStr = abortCmdStr,
            keyVars = keyVars,
            checkFail = False,
        )
        
        self.waitCmdVars(cmdVar, checkFail=checkFail, retVal=cmdVar)
        
    def waitCmdVars(self, cmdVars, checkFail=True, retVal=None):
        """Wait for one or more command variables to finish.
        Command variables are the objects returned by startCmd.

        A yield is required.
        
        Returns successfully if all commands succeed.
        Fails as soon as any command fails.
        
        Inputs:
        - one or more command variables (RO.KeyVariable.CmdVar objects)
        - checkFail: check for command failure?
            if True (the default) command failure will halt your script
        - retVal: value to return at the end; defaults to None
        """
        _WaitCmdVars(self, cmdVars, checkFail=checkFail, retVal=retVal)
        
    def waitKeyVar(self,
        keyVar,
        ind=0,
        defVal=Exception,
        waitNext=False,
    ):
        """Get the value of keyVar in self.value.
        If it is currently unknown or if waitNext is true,
        wait for the variable to be updated.
        See also getKeyVar (which does not wait).

        A yield is required.
        
        Inputs:
        - keyVar    keyword variable
        - ind       which value is wanted? (None for all values)
        - defVal    value to return if value cannot be determined
                    (if omitted, the script halts)
        - waitNext  if True, ignores the current value and waits
                    for the next transition.
        """
        _WaitKeyVar(
            scriptRunner = self,
            keyVar = keyVar,
            ind = ind,
            defVal = defVal,
            waitNext = waitNext,
        )

    def waitMS(self, msec):
        """Waits for msec milliseconds.
        
        A yield is required.

        Inputs:
        - msec  number of milliseconds to pause
        """
        if self.debug:
            print "waitMS(msec=%s)" % (msec,)

        _WaitMS(self, msec)
    
    def waitThread(self, func, *args, **kargs):
        """Run func as a background thread, waits for completion
        and sets self.value = the result of that function call.

        A yield is required.
        
        Warning: func must NOT interact with Tkinter widgets or variables
        (not even reading them) because Tkinter is not thread-safe.
        (The only thing I'm sure a background thread can safely do with Tkinter
        is generate an event, a technique that is used to detect end of thread).
        """
        if self.debug:
            print "waitThread(func=%r, args=%s, keyArgs=%s)" % (func, args, kargs)

        _WaitThread(self, func, *args, **kargs)
    
    def waitUser(self):
        """Wait until resumeUser called.
        
        Typically used if waiting for user input
        but can be used for any external trigger.
        """
        self._waitCheck(setWait=True)

        if self._userWaitID != None:
            raise RuntimeError("Already in user wait mode")
            
        self._userWaitID = self._getNextID()
        
    # private methods

    def _cmdFailCallback(self, msgType, msgDict, cmdVar):
        """Use as a callback for when an asynchronous command fails.
        """
#       print "ScriptRunner._cmdFailCallback(%r, %r, %r)" % (msgType, msgDict, cmdVar)
        if not msgType in RO.KeyVariable.FailTypes:
            errMsg = "Bug! RO.ScriptRunner._cmdFail(%r, %r, %r) called for non-failed command" % (msgType, msgDict, cmdVar)
            raise RuntimeError(errMsg)
        MaxLen = 10
        if len(cmdVar.cmdStr) > MaxLen:
            cmdDescr = "%s %s..." % (cmdVar.actor, cmdVar.cmdStr[0:MaxLen])
        else:
            cmdDescr = "%s %s" % (cmdVar.actor, cmdVar.cmdStr)
        for key, values in msgDict.get("data", {}).iteritems():
            if key.lower() in _ErrKeys:
                reason = values[0]
                break
        else:
            reason = msgDict.get("data")
            if not reason:
                reason = str(msgDict)
        self._setState(Failed, reason="%s failed: %s" % (cmdDescr, reason))
    
    def _waitEndFunc(self, cancelFunc, cleanupFunc):
        """Register the specified cancel function
        and return a wait end function that should be called
        when the wait ends successfully.
        """
        return _WaitEnd(self, cancelFunc, cleanupFunc)

    def _continue(self, iterID, val=None):
        """Continue executing the script.
        
        Inputs:
        - iterID: ID of iterator that is continuing
        - val: self.value is set to val
        """
        self._printState("_continue(%r, %r)" % (iterID, val))
        if not self.isExecuting():
            raise RuntimeError('%s: bug! _continue called but script not executing' % (self,))
        
        try:
            if iterID != self._iterID:
                #print "Warning: _continue called with iterID=%s; expected %s" % (iterID, self._iterID)
                raise RuntimeError("%s: bug! _continue called with bad id; got %r, expected %r" % (self, iterID, self._iterID))
    
            self.value = val
            
            self._waiting = False
            
            if self._state == Paused:
                #print "_continue: still paused"
                return
        
            if not self._iterStack:
                # just started; call run function,
                # and if it's an iterator, put it on the stack
                res = self.runFunc(self)
                if not hasattr(res, "next"):
                    # function was a function, not a generator; all done
                    self._setState(Done)
                    return

                self._iterStack = [res]
            
            self._printState("_continue: before iteration")
            self._state = 0
            possIter = self._iterStack[-1].next()
            if hasattr(possIter, "next"):
                self._iterStack.append(possIter)
                self._iterID = self._getNextID(addLevel = True)
#               print "Iteration yielded an iterator"
                self._continue(self._iterID)
            else:
                self._iterID = self._getNextID()
            
            self._printState("_continue: after iteration")

        except StopIteration:
#           print "StopIteration seen in _continue"
            self._iterStack.pop(-1)
            if not self._iterStack:
                self._setState(Done)
            else:
                self._continue(self._iterID, val=self.value)
        except KeyboardInterrupt:
            self._setState(Cancelled, "keyboard interrupt")
        except SystemExit:
            self.__del__()
            sys.exit(0)
        except ScriptError, e:
            self._setState(Failed, str(e))
        except Exception, e:
            traceback.print_exc(file=sys.stderr)
            self._setState(Failed, str(e))
    
    def _printState(self, prefix):
        """Print the state at various times.
        Ignored unless _DebugState or self.debug true.
        """
        if _DebugState:
            print "Script %s: %s: state=%s, iterID=%s, waiting=%s, iterStack depth=%s" % \
                (self.name, prefix, self._state, self._iterID, self._waiting, len(self._iterStack))

    def _showCmdMsg(self, msg, severity=RO.Constants.sevNormal):
        """Display a message--on the command status bar, if available,
        else sys.stdout.

        Do not use yield because it does not wait for anything.
        
        Inputs:
        - msg: string to display, without a final \n
        - severity: one of RO.Constants.sevNormal (default), sevWarning or sevError
        """
        if self._cmdStatusBar:
            self._cmdStatusBar.setMsg(msg, severity)
        else:
            print msg
    
    def __del__(self, evt=None):
        """Called just before the object is deleted.
        Deletes any state callbacks and then cancels script execution.
        The evt argument is ignored, but allows __del__ to be
        called from a Tk event binding.
        """
        self._callbacks = []
        self.cancel()
    
    def _end(self):
        """Call the end function (if any).
        """
        # Warning: this code must not execute _setState or __del__
        # to avoid infinite loops. It also need not execute _cancelFuncs.
        if self.endFunc:
            if self.debug:
                print "ScriptRunner._end: calling end function"
            try:
                res = self.endFunc(self)
                if hasattr(res, "next"):
                    self._state = Failed
                    self._reason = "endFunc tried to wait"
            except KeyboardInterrupt:
                self._state = Cancelled
                self._reason = "keyboard interrupt"
            except SystemExit:
                raise
            except Exception, e:
                self._state = Failed
                self._reason = "endFunc failed: %s" % (str(e),)
                traceback.print_exc(file=sys.stderr)
        elif self.debug:
            print "ScriptRunner._end: no end function to call"
    
    def _getNextID(self, addLevel=False):
        """Return the next iterator ID"""
        self._printState("_getNextID(addLevel=%s)" % (addLevel,))
        newID = self._iterID[:]
        if addLevel:
            newID += [0]
        else:
            newID[-1] = (newID[-1] + 1) % 10000
        return newID
    
    def _setState(self, newState, reason=None):
        """Update the state of the script runner.

        If the new state is Cancelled or Failed
        then any existing cancel function is called
        to abort outstanding callbacks.
        """
        self._printState("_setState(%r, %r)" % (newState, reason))
        if self.debug:
            newStateName = _StateDict.get(newState, "?")
            print "ScriptRunner._setState(newState=%s=%s, reason=%r)" % (newState, newStateName, reason)
        
        # if ending, clean up appropriately
        if self.isExecuting() and newState <= Done:
            self._endingState = newState
            # if aborting and a cancel function exists, call it
            if newState < Done:
                for func in self._cancelFuncs:
#                   print "%s _setState calling cancel function %r" % (self, func)
                    func()
            self._cancelFuncs = []
            self._end()
            
        self._state = newState
        if reason != None:
            self._reason = reason
        self._doCallbacks()
    
    def __str__(self):
        """String representation of script"""
        return "script %s" % (self.name,)
    
    def _waitCheck(self, setWait=False):
        """Verifies that the script runner is running and not already waiting
        (as can easily happen if the script is missing a "yield").
        
        Call at the beginning of every waitXXX method.
        
        Inputs:
        - setWait: if True, sets the _waiting flag True
        """
        if self._state != Running:
            raise RuntimeError("Tried to wait when not running")
        
        if self._waiting:
            raise RuntimeError("Already waiting; did you forget the 'yield' when calling a ScriptRunner method?")
        
        if setWait:
            self._waiting = True


class _WaitBase:
    """Base class for waiting.
    Handles verifying iterID, registering the termination function,
    registering and unregistering the cancel function, etc.
    """
    def __init__(self, scriptRunner):
        scriptRunner._printState("%s init" % (self.__class__.__name__))
        scriptRunner._waitCheck(setWait = True)
        self.scriptRunner = scriptRunner
        self.master = scriptRunner.master
        self._iterID = scriptRunner._getNextID()
        self.scriptRunner._cancelFuncs.append(self.cancelWait)

    def cancelWait(self):
        """Call to cancel waiting.
        Perform necessary cleanup but do not set state.
        Subclasses can override and should usually call cleanup.
        """
        self.cleanup()
    
    def fail(self, reason):
        """Call if waiting fails.
        """
        # report failure; this causes the scriptRunner to call
        # all pending cancelWait functions, so don't do that here
        self.scriptRunner._setState(Failed, reason)
    
    def cleanup(self):
        """Called when ending for any reason
        (unless overridden cancelWait does not call cleanup).
        """
        pass
    
    def _continue(self, val=None):
        """Call to resume execution."""
        self.cleanup()
        try:
            self.scriptRunner._cancelFuncs.remove(self.cancelWait)
        except ValueError:
            raise RuntimeError("Cancel function missing; did you forgot the 'yield' when calling a ScriptRunner method?")
        if self.scriptRunner.debug and val != None:
            print "wait returns %r" % (val,)
        self.scriptRunner._continue(self._iterID, val)


class _WaitMS(_WaitBase):
    def __init__(self, scriptRunner, msec):
        _WaitBase.__init__(self, scriptRunner)

        self.msec = int(msec)

        self.afterID = self.master.after(self.msec, self._continue)
    
    def cancelWait(self):
        self.master.after_cancel(self.afterID)


class _WaitCmdVars(_WaitBase):
    """Wait for one or more command variables to finish.
    
    Inputs:
    - scriptRunner: the script runner
    - one or more command variables (RO.KeyVariable.CmdVar objects)
    - checkFail: check for command failure?
        if True (the default) command failure will halt your script
    - retVal: the value to return at the end (in scriptRunner.value)
    """
    def __init__(self, scriptRunner, cmdVars, checkFail=True, retVal=None):
        self.cmdVars = RO.SeqUtil.asSequence(cmdVars)
        self.checkFail = bool(checkFail)
        self.retVal = retVal
        self.addedCallback = False
        _WaitBase.__init__(self, scriptRunner)

        if self.getState()[0] != 0:
            # no need to wait; commands are already done or one has failed
            # schedule a callback for asap
            print "_WaitCmdVars: no need to wait"
            self.master.after(1, self.varCallback)
        else:
            # need to wait; add self as callback to each cmdVar
            for cmdVar in self.cmdVars:
                cmdVar.removeCallback(self.scriptRunner._cmdFailCallback, doRaise=False)
                cmdVar.addCallback(self.varCallback)
            self.addedCallback = True

    def getState(self):
        """Return one of:
        - (-1, failedCmdVar) if a command has failed and checkFail True
        - (1, None) if all commands are done (and possibly failed if checkFail False)
        - (0, None) not finished yet
        Note that getState()[0] is logically True if done waiting.
        """
        allDone = 1
        for var in self.cmdVars:
            if var.isDone():
                if var.lastType != ":" and self.checkFail:
                    return (-1, var)
            else:
                allDone = 0
        return (allDone, None)
    
    def varCallback(self, *args, **kargs):
        """Check all command variables;
        if any has failed, remove all callbacks and fail
        """
        currState, cmdVar = self.getState()
        if currState < 0:
            self.fail(cmdVar)
        elif currState > 0:
            self._continue(self.retVal)
    
    def cancelWait(self):
        """Call when aborting early.
        """
#       print "_WaitCmdVars.cancelWait"
        self.cleanup()
        for cmdVar in self.cmdVars:
            cmdVar.abort()
    
    def cleanup(self):
        """Called when ending for any reason.
        """
#       print "_WaitCmdVars.cleanup"
        if self.addedCallback:
            for cmdVar in self.cmdVars:
                didRemove = cmdVar.removeCallback(self.varCallback, doRaise=False)
                if not didRemove:
                    sys.stderr.write("_WaitCmdVar cleanup could not remove callback from %s\n" % \
                        (cmdVar,))

    def fail(self, cmdVar):
        """A command var failed.
        """
#       print "_WaitCmdVars.fail(%s)" % (cmdVar,)
        msgDict = cmdVar.lastReply
        msgType = msgDict["type"]
        self.scriptRunner._cmdFailCallback(msgType, msgDict, cmdVar)


class _WaitKeyVar(_WaitBase):
    """Wait for one keyword variable, returning the value in scriptRunner.value.
    """
    def __init__(self,
        scriptRunner,
        keyVar,
        ind,
        defVal,
        waitNext,
    ):
        self.keyVar = keyVar
        self.ind = ind
        self.defVal = defVal
        self.waitNext = bool(waitNext)
        self.addedCallback = False
        _WaitBase.__init__(self, scriptRunner)
        
        if self.keyVar.isCurrent() and not self.waitNext:
            # no need to wait; value already known
            # schedule a wakeup for asap
            self.master.after(1, self.varCallback)
        elif self.scriptRunner.debug:
            # display message
            argList = ["keyVar=%s" % (keyVar,)]
            if ind != 0:
                argList.append("ind=%s" % (ind,))
            if defVal != Exception:
                argList.append("defVal=%r" % (defVal,))
            if waitNext != False:
                argList.append("waitNext=%r" % (waitNext,))
            print "waitKeyVar(%s)" % ", ".join(argList)

            # prevent the call from failing by using None instead of Exception
            if self.defVal == Exception:
                self.defVal = None

            self.master.after(1, self.varCallback)
        else:
            # need to wait; set self as a callback
#           print "_WaitKeyVar adding callback"
            self.keyVar.addCallback(self.varCallback, callNow=False)
            self.addedCallback = True
    
    def varCallback(self, *args, **kargs):
        """Set scriptRunner.value to value. If value is invalid,
        use defVal (if specified) else cancel the wait and fail.
        """
        currVal, isCurrent = self.getVal()
#       print "_WaitKeyVar.varCallback; currVal=%r; isCurrent=%r" % (currVal, isCurrent)
        if isCurrent:
            self._continue(currVal)
        elif self.defVal != Exception:
            self._continue(self.defVal)
        else:
            self.fail("Value of %s invalid" % (self.keyVar,))
    
    def cleanup(self):
        """Called when ending for any reason.
        """
#       print "_WaitKeyVar.cleanup"
        if self.addedCallback:
            self.keyVar.removeCallback(self.varCallback)
        
    def getVal(self):
        """Return isCurrent, currVal, where currVal
        is the current value[ind] or value tuple (if ind=None).
        Ignores defVal.
        """
        currVal, isCurrent = self.keyVar.get()
        if self.ind != None:
            return currVal[self.ind], isCurrent
        else:
            return currVal, isCurrent


class _WaitThread(_WaitBase):
    def __init__(self, scriptRunner, func, *args, **kargs):
#       print "_WaitThread.__init__(%r, *%r, **%r)" % (func, args, kargs)
        _WaitBase.__init__(self, scriptRunner)
        
        if not callable(func):
            raise ValueError("%r is not callable" % func)

        self.queue = Queue.Queue()
        self.func = func

        self.threadObj = threading.Thread(target=self.threadFunc, args=args, kwargs=kargs)
        self.threadObj.setDaemon(True)
        self.threadObj.start()
        self.afterID = self.master.after(_PollDelayMS, self.checkEnd)
#       print "_WaitThread__init__(%r) done" % self.func
    
    def checkEnd(self):
        if self.threadObj.isAlive():
            self.afterID = self.master.after(_PollDelayMS, self.checkEnd)
            return
#       print "_WaitThread(%r).checkEnd: thread done" % self.func
        
        retVal = self.queue.get()
#       print "_WaitThread(%r).checkEnd; retVal=%r" % (self.func, retVal)
        self._continue(val=retVal)
        
    def cleanup(self):
#       print "_WaitThread(%r).cleanup" % self.func
        if self.afterID:
            self.master.after_cancel(self.afterID)
        self.threadObj = None

    def threadFunc(self, *args, **kargs):
        retVal = self.func(*args, **kargs)
        self.queue.put(retVal)


if __name__ == "__main__":
    import RO.KeyDispatcher
    import time

    root = Tkinter.Tk()
    
    dispatcher = RO.KeyDispatcher.KeyDispatcher()
    
    scriptList = []

    def initFunc(sr):
        global scriptList
        print "%s init function called" % (sr,)
        scriptList.append(sr)

    def endFunc(sr):
        print "%s end function called" % (sr,)
    
    def script(sr):
        def threadFunc(nSec):
            time.sleep(nSec)
        nSec = 1.0
        sr.showMsg("%s waiting in a thread for %s sec" % (sr, nSec))
        yield sr.waitThread(threadFunc, 1.0)
        
        for val in range(5):
            sr.showMsg("%s value = %s" % (sr, val))
            yield sr.waitMS(1000)
    
    def stateFunc(sr):
        state, stateStr, reason = sr.getFullState()
        if reason:
            msgStr = "%s state=%s: %s" % (sr, stateStr, reason)
        else:
            msgStr = "%s state=%s" % (sr, stateStr)
        sr.showMsg(msgStr)
        for sr in scriptList:
            if not sr.isDone():
                return
        root.quit()

    sr1 = ScriptRunner(
        master = root,
        runFunc = script,
        name = "Script 1",
        dispatcher = dispatcher,
        initFunc = initFunc,
        endFunc = endFunc,
        stateFunc = stateFunc,
    )
    
    sr2 = ScriptRunner(
        master = root,
        runFunc = script,
        name = "Script 2",
        dispatcher = dispatcher,
        initFunc = initFunc,
        endFunc = endFunc,
        stateFunc = stateFunc,
    )
    
    # start the scripts in a staggared fashion
    sr1.start()
    root.after(1500, sr1.pause)
    root.after(3000, sr1.resume)
    root.after(2500, sr2.start)
    
    root.mainloop()
