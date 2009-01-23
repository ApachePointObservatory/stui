#!/usr/bin/env python
"""Serial connections optimized for use with Tkinter GUIs.

Known issues:
- At present TkSerial cannot detect read/write errors.
  As such it cannot close itself when it ought to
  and I'm not sure we really need a state callback.

TkSerial allows nonblocking event-driven operation:
- Connection and disconnection are done in the background.
- You may begin writing as soon as you start connecting.
- Written data is queued and sent as the connection permits.
- The read and readLine methods are nonblocking.
- You may specify a read callback, which is called when data is available,
  and a state callback, which is called when the connection state changed.

History:
2008-03-03 ROwen    First version (adapted from RO.Comm.TkSocket)
2008-03-06 ROwen    Removed timeout argument; renamed eolTranslation to translation;
                    fixed error in translation handling.
2009-01-23 ROwen    Bug fix: if a read or write error occurred, the exception would be thrown repeatedly.
                    Fixed by closing the connection on read or write error.
                    This is the only cross-platform solution I found, because the only way to detect an error
                    is to catch the error on read or write (except on Windows).
"""
__all__ = ["TkSerial", "NullSerial"]
import sys
import traceback
import Tkinter
import RO.SeqUtil
import RO.TkUtil
try:
    set
except NameError:
    from sets import Set as set


class TkBaseSerial(object):
    """Base class for communication via a serial port using the tcl event loop.
    This class handles state and supports TckSerial and NullSerial.
         
    Inputs:
    - chanID    the tk socket connection; if not None then sockArgs is ignored
    - state     the initial state
    """
    Open = "Open"
    Closed = "Closed"
    Failed = "Failed"
    
    _StateSet = set((Open, Closed, Failed))
    
    def __init__(self,
        portName,
        state,
        stateCallback = None,
    ):
        if state not in self._StateSet:
            raise RuntimeError("Invalid state %r" % (state,))
        self._portName = portName
        self._state = state
        self._reason = ""
        self._stateCallback = stateCallback
        self._tkCallbackDict = dict()
        
    def getState(self):
        """Returns the current state as a tuple:
        - state: state (as a string)
        - reason: the reason for the state ("" if none)
        """
        return (self._state, self._reason)

    def isOpen(self):
        """Return True if serial connection is open"
        """
        return (self._state != self.Open)
    
    def setStateCallback(self, callFunc=None):
        """Specifies a state callback function
        (replacing the current one, if one exists).
        
        Inputs:
        - callFunc: the callback function, or None if none wanted
                    The function is sent one argument: this TkSerial
        """
        self._stateCallback = callFunc

    def _clearCallbacks(self):
        """Clear any callbacks added by this class.
        Called just after the serial is closed.
        """
        #print "%s._clearCallbacks called" % (self.__class__.__name__,)
        for tclFunc in self._tkCallbackDict.itervalues():
            tclFunc.deregister()
        self._tkCallbackDict = dict()
        self._stateCallback = None

    def __del__(self):
        """At object deletion, make sure the socket is properly closed.
        """
        #print "TkSocket.__del__ called"
        self._stateCallback = None
    
    def _setState(self, newState, reason=None):
        """Change the state.
        
        Inputs:
        - newState: the new state
        - reason: an explanation (None to leave alone)
        """
        #print "_setState(%r, %r)" % (newState, reason)
        self._state = newState
        if reason != None:
            self._reason = str(reason)

        stateCallback = self._stateCallback
        if not self.isOpen():
            self._clearCallbacks()
        
        if stateCallback:
            try:
                stateCallback(self)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                sys.stderr.write("%s state callback %s failed: %s\n" % (self, self._stateCallback, e,))
                traceback.print_exc(file=sys.stderr)
    
    def __str__(self):
        return "%s %s:%s" % (self.__class__.__name__, self._portName)


class TkSerial(TkBaseSerial):
    """Connection via a serial port using the tcl event loop.
    
    Inputs:
    - portName      serial port (e.g. "/dev/tty...")
    - baud          desired baud rate
    - parity        desired parity; "n"=none, "o"=odd, "e"=even, "m"=mark, "s"=space
    - dataBits      number of data bits: [5,8]
    - stopBits      number of stop bits: 1 or 2
    - buffering     one of "none", "line", "full"; None for the system default
    - handshake     desired handshake: "none", "rtscts", "xonxoff"; None for system default
    - translation   controls EOL translation translation (though binary does more); you have three choices:
                    - one of: "auto", "binary", "cr", "crlf", "lf"
                    - "{<in> <out>}" to separately control input and output, e,g "{auto, crlf}"
                    - None for the system default
    - readCallback  function to call when data read; receives: self
    - stateCallback function to call when state or reason changes; receives: self
    **chanKArgs     any additional keywords are used to configure the serial channel
                    via Tcl's fconfigure command (after prepending "-" to each keyword).
                    Note: -mode is set using the keywords baud, parity, dataBits and stopBits;
                    it may not be overridden using mode=....
    
    For more information about the configuration options
    see the Tcl documentation for these two commands:
    - fconfigure (for options that are common to all types of connections)
    - open (for additional options that are specific to serial ports)
    """
    Open = "Open"
    Closed = "Closed"
    Failed = "Failed"
    
    _StateSet = set((Open, Closed, Failed))
        
    def __init__(self,
        portName,
        baud = 9600,
        parity = "n",
        dataBits = 8,
        stopBits = 1,
        buffering = "line",
        handshake = "none",
        translation = "lf",
        readCallback = None,
        stateCallback = None,
    **chanKArgs):
        TkBaseSerial.__init__(self,
            portName = portName,
            state = self.Open,
            stateCallback = stateCallback,
        )
        self._readCallback = readCallback
        
        self._tk = Tkinter.StringVar()._tk

        self._chanID = 0
        try:
            self._chanID = self._tk.call('open', portName, 'r+')
            if not self._chanID:
                raise RuntimeError("Failed to open serial port %r" % (portName,))
            
            cfgArgs = [
                "-blocking", 0,
            ]
            for key, value in chanKArgs.iteritems():
                cfgArgs += ["-" + key, value]
            cfgArgs += ["-mode", "%s,%s,%s,%s" % (int(baud), parity, int(dataBits), int(stopBits))]
            if buffering != None:
                cfgArgs += ["-buffering", str(buffering)]
            if handshake != None:
                cfgArgs += ["-handshake", str(handshake)]
            if translation != None:
                cfgArgs += ["-translation", str(translation)]
                
            self._tk.call("fconfigure", self._chanID, *cfgArgs)
                
            # add callbacks; the write callback indicates the serial is open
            # and is just used to detect state
            self._setSockCallback(self._doRead)

        except Tkinter.TclError, e:
            raise RuntimeError(e)

    def close(self, isOK=True, reason=None):
        """Start closing the serial port.
        
        Does nothing if the serial is already closed or failed.
        
        Inputs:
        - isOK: if True, mark state as Closed, else Failed
        - reason: a string explaining why, or None to leave unchanged;
            please specify if isOK is false.
        """
        #print "%s.close(isOK=%s, reason=%s)" % (self.__class__.__name__, isOK, reason)
        if self._state <= self.Closed:
            return

        if self._chanID:
            try:
                # close serial (this automatically deregisters any file events)
                self._tk.call('close', self._chanID)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception:
                pass
            self._chanID = None
        self._tk = None
        if isOK:
            self._setState(self.Closed, reason)
        else:
            self._setState(self.Failed, reason)
    
    def read(self, nChar=None):
        """Return up to nChar characters; if nChar is None then return
        all available characters.
        """
        try:
            if nChar == None:
                retVal = self._tk.call('read', self._chanID)
            else:
                retVal = self._tk.call('read', self._chanID, nChar)
        except Exception, e:
            self.close(isOK = False, reason = str(e))
            raise
        #print "read returning %r" % retVal
        return retVal

    def readLine(self, default=None):
        """Read one line of data.
        Do not return the trailing newline.
        If a full line is not available, return default.
        
        Inputs:
        - default   value to return if a full line is not available
                    (in which case no data is read)
        
        Raise RuntimeError if the serial is not open.
        """
        #print "%s.readLine(default=%s)" % (self.__class__.__name__, default)
        try:
            readStr = self._tk.call('gets', self._chanID)
        except Exception, e:
            self.close(isOK = False, reason = str(e))
            raise
        if not readStr:
            return default
        #print "readLine returning %r" % (readStr,)
        return readStr
    
    def setReadCallback(self, callFunc=None):
        """Specifies a read callback function
        (replacing the current one, if one exists).
        
        Inputs:
        - callFunc: the callback function, or None if none wanted.
                    The function is sent one argument: this TkSerial
        """
        self._readCallback = callFunc
    
    def write(self, data):
        """Write data to the serial port. Does not block.
        
        Raises UnicodeError if the data cannot be expressed as ascii.
        Raises RuntimeError if the serial connection is not open.
        If an error occurs while sending the data, the serial is closed,
        the state is set to Failed and _reason is set.
        """
        #print "write(%r)" % (data,)
        self._assertConn()
        try:
            self._tk.call('puts', '-nonewline', self._chanID, data)
        except Exception, e:
            self.close(isOK = False, reason=str(e))
            raise
        self._assertConn()
    
    def writeLine(self, data):
        """Write a line of data terminated by standard newline
        (which for the net is \r\n, but the serial's auto newline
        translation takes care of it).
        """
        #print "writeLine(%r)" % (data,)
        self._assertConn()
        try:
            self._tk.call('puts', self._chanID, data)
        except Exception, e:
            self.close(isOK = False, reason=str(e))
            raise
        self._assertConn()
    
    def _assertConn(self):
        """If not open, raise RuntimeError.
        """
        if self._state != self.Open:
            raise RuntimeError("%s not open" % (self,))
    
    def _clearCallbacks(self):
        """Clear any callbacks added by this class.
        Called just after the serial is closed.
        """
        TkBaseSerial._clearCallbacks()
        self._readCallback = None

    def _doRead(self):
        """Called when there is data to read"""
        #print "%s _doRead" % (self,)
        if self._readCallback:
            try:
                self._readCallback(self)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception, e:
                sys.stderr.write("%s read callback %s failed: %s\n" % (self, self._readCallback, e,))
                traceback.print_exc(file=sys.stderr)

    def _setSockCallback(self, callFunc=None, doWrite=False):
        """Set, replace or clear the read or write callback.

        Inputs:
        - callFunc  the new callback function, or None if none
        - doWrite   if True, a write callback, else a read callback
        """
        #print "%s._setSockCallback(callFunc=%s, doWrite=%s)" % (self.__class__.__name__, callFunc, doWrite)
        if doWrite:
            typeStr = 'writable'
        else:
            typeStr = 'readable'
        
        if callFunc:
            tclFunc = RO.TkUtil.TclFunc(callFunc)
            tkFuncName = tclFunc.tclFuncName
        else:
            tclFunc = None
            tkFuncName = ""
        
        try:
            self._tk.call('fileevent', self._chanID, typeStr, tkFuncName)
        except Tkinter.TclError, e:
            if tclFunc:
                tclFunc.deregister()
            raise RuntimeError(e)

        # deregister and dereference existing tclFunc, if any
        oldCallFunc = self._tkCallbackDict.pop(typeStr, None)
        if oldCallFunc:
            oldCallFunc.deregister()

        # Save a reference to the new tclFunc,, if any
        if tclFunc:
            self._tkCallbackDict[typeStr] = tclFunc
    
    def __del__(self):
        """At object deletion, make sure the serial is properly closed.
        """
        #print "TkSerial.__del__ called"
        self._readCallback = None
        self._stateCallback = None
        self.close()
    
    def __str__(self):
        return "%s %s %s" % (self.__class__.__name__, self._portName, self._chanID)


class NullSerial(TkBaseSerial):
    """Null connection.
    Forbids read, write and setting a new state callback.
    Close is OK and the state is always Closed.
    """
    def __init__ (self):
        TkBaseSerial.__init__(self,
            portName = "None",
            state = self.Closed,
        )
        self._reason = "This is an instance of NullSerial"

    def read(self, *args, **kargs):
        raise RuntimeError("Cannot read from null serial")
        
    def readLine(self, *args, **kargs):
        raise RuntimeError("Cannot readLine from null serial")

    def write(self, astr):
        raise RuntimeError("Cannot write %r to null serial" % astr)

    def writeLine(self, astr):
        raise RuntimeError("Cannot writeLine %r to null serial" % astr)
