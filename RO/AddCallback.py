#!/usr/bin/env python
"""Mixing class(es) for adding callback capabilities.

History:
2003-07-09 ROwen
2003-08-04 ROwen    Added TkButtonMixin.
2003-10-29 ROwen    Modified TkVarMixin to store the tk var in self._var.
2004-03-04 ROwen    Modified addCallback to first to try to delete the function.
2004-05-21 ROwen    Modified to continue with other callbacks if one callback fails
                    (after printing a message and a traceback).
2004-06-15 ROwen    Bug fix: used sys and traceback for error reporting but did not import them.
2004-07-21 ROwen    Modified _doCallbacks to pass *args and **kargs to the callback functions;
                    this makes BaseMixin easier to subclass.
                    Overhauled removeCallback:
                    - added doRaise argument
                    - returns True on success, False or exception on failure
                    - fail if callbacks are being executed
2004-09-14 ROwen    Bug fix: TkButtonMixin.__init__ did not obey callNow.
                    Bug fix: removeCallback spelled a class attribute wrong.
2004-09-23 ROwen    Added defCallNow argument.
2004-09-28 ROwen    Modified to allow removing callbacks while executing.
                    Removed use of attribute _inCallbacks.
2004-10-07 ROwen    Modified addCallback to not add a function
                    if it is already in the callback list.
2005-06-08 ROwen    Changed BaseMixin to a new style class.
2005-06-13 ROwen    Added method _removeAllCallbacks().
"""
import re
import sys
import traceback

class BaseMixin(object):
    """Add support for callback functions.
    
    Inputs:
    - callFunc      see addCallback
    - callNow       see addCallback
    - defCallNow    default for callNow

    Subclasses may wish to override _doCallbacks
    
    Adds the following attributes:
    _defCallNow: default value for callNow
    _callbacks: a list of one or more callback functions
    """
    def __init__(self,
        callFunc = None,
        callNow = None,
        defCallNow = False,
    ):
        self._defCallNow = bool(defCallNow)
        self._callbacks = []
        if callFunc != None:
            self.addCallback(callFunc, callNow)
    
    def addCallback(self,
        callFunc,
        callNow = None,
    ):
        """Add a callback function to the list.

        If the callback is already present, it is not re-added.
        
        Inputs:
        - callFunc  a callback function.
            It will receive one argument: self (the object doing the calling);
            If None, no callback function is added.
        - callNow   if True, calls the function immediately
                    if omitted or None, the default is used
        
        Raises ValueError if callFunc is not callable
        """
        if callFunc == None:
            return

        if not callable(callFunc):
            raise ValueError, "callFunc %r is not callable" % (callFunc,)
        
        # add new function
        if callFunc not in self._callbacks:
            self._callbacks.append(callFunc)
        
        # if wanted, call the new function
        if callNow or (callNow == None and self._defCallNow):
            # use _doCallbacks in case it was overridden,
            # but only call this one function
            currCallbacks = self._callbacks
            self._callbacks = (callFunc,)
            self._doCallbacks()
            self._callbacks = currCallbacks

    def removeCallback(self, callFunc, doRaise=True):
        """Delete the callback function.
        Return True if successful, raise error or return False otherwise.

        Inputs:
        - callFunc  callback function to remove
        - doRaise   raise exception if unsuccessful? True by default.
        
        If doRaise true:
        - Raises ValueError if callback not found
        - Raises RuntimeError if executing callbacks when called
        Otherwise returns False in either case.
        """
        try:
            self._callbacks.remove(callFunc)
            return True
        except ValueError:
            if doRaise:
                raise ValueError("Callback %r not found" % callFunc)
            return False
    
    def _basicDoCallbacks(self, *args, **kargs):
        """Execute the callbacks, passing *args and **kargs
        to the callback functions.
        """
        for func in self._callbacks[:]:
            try:
                func(*args, **kargs)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                sys.stderr.write("Callback of %s by %s failed: %s\n" % (func, self, e,))
                traceback.print_exc(file=sys.stderr)
    
    def _doCallbacks(self):
        """Execute the callback functions, passing self as the argument.
        
        Subclass this to return something else.
        """
        self._basicDoCallbacks(self)
    
    def _removeAllCallbacks(self):
        """Remove all callbacks.
        If you know there will be no more callbacks
        then call this to avoid memory leaks.
        """
        self._callbacks = []


class TkButtonMixin(BaseMixin):
    """Add support for callback functions triggered by a Tk button's command.
    Use instead of TkVarMixin for Tk buttons so the callback is fired
    at the right time (when the button's "command" is executed).
    
    Inputs:
    - callFunc  a callback function.
        It will receive one argument: self (the object doing the calling);
        If None, no callback function is added.
    - callNow   if True, calls callFunc (but not command) immediately
    - command: conventional Tk button callback taking no args;
        this allows a conventional Tk button interface; as such,
        command is not called immediately even if callNow is true
    - all remaining keyword arguments are ignored; they are accepted so one can
      easily handle subclasses of Tk buttons by accepting arbitrary keywords
      that might include command
    """
    def __init__(self,
        callFunc = None,
        callNow = None,
        command = None,
        defCallNow = False,
    **kargs):
        self["command"] = self._doCallbacks
        BaseMixin.__init__(self,
            callFunc = callFunc,
            callNow = callNow,
            defCallNow = defCallNow,
        )

        if command != None:
            if not callable(command):
                raise ValueError, "command %r is not callable" % (command,)
            def doCommand(wdg):
                return command()
            self.addCallback(doCommand)

            
class TkVarMixin(BaseMixin):
    """Add support for callback functions triggered by a tk variable.
    
    The functions are called whenever the specified tk variable changes.
    The user may also call _doCallback when desired.

    Inputs:
    - tkVar: the tk variable to watch
    - callFunc  a callback function.
        It will receive one argument: self (the object doing the calling);
        If None, no callback function is added.
    - callNow   if True, calls the function immediately
    
    Adds the following attribute:
    _callbacks: a list of 0 or more callback functions
    _var: the tk variable
    """
    def __init__(self,
        tkVar,
        callFunc = None,
        callNow = False,
        defCallNow = False,
    ):
        self._var = tkVar
        BaseMixin.__init__(self,
            callFunc = callFunc,
            callNow = callNow,
            defCallNow = defCallNow,
        )
        def doTraceVar(*args):
            """ignore trace_variable callback arguments"""
            self._doCallbacks()
        tkVar.trace_variable("w", doTraceVar)
