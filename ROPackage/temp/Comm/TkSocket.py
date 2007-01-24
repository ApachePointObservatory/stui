#!/usr/bin/env python
"""Sockets optimized for use with Tkinter GUIs.

TkSocket allows nonblocking event-driven operation:
- Connection and disconnection are done in the background.
- You may begin writing as soon as you start connecting.
- Written data is queued and sent as the connection permits.
- The read and readLine methods are nonblocking.
- You may specify a read callback, which is called when data is available,
  and a state callback, which is called when the connection state changed.

History:
2002-11-22 ROwen    First version
2003-02-25 ROwen    Bug fix: could hang on program exit; cured using atexit;
                    also added a __del__ method for the same reason.
2003-02-27 ROwen    _WriteThread.close was printing an error message
                    instead of terminating the write thread.
2003-04-04 ROwen    Bug fix: BasicSocket was being set to a function instead of a type;
                    this failed under Windows (hanks to Craig Loomis for report and fix).
2003-05-01 ROwen    Modified to work with Python 2.3b1 (which does not support
                    _tkinter.create/deletefilehandler); thanks to Martin v. Lowis for the fix.
2003-10-13 ROwen    Overhauled to more robust and to prevent delays while connecting.
                    Also added support for monitoring state.
2003-10-14 ROwen    Bug fix: close while NotConnected caused perpetual Closing state.
2003-11-19 ROwen    Bug fix: reason was not always a string; modified _setState
                    to cast it to a string.
2003-12-04 ROwen    Modified to only call the state callback when the state or reason changes.
2004-05-18 ROwen    Increased state polling delay from 100ms to 200ms.
                    Stopped importing sys since it was not being used.
2004-07-21 ROwen    Overhauled to add Windows compatibility, by eliminating the use
                    of createfilehandler. Modified to use tcl sockets,
                    eliminating all use of threads. Visible changes include:
                    - TCP/IP is the only type of socket.
                    - The socket is connected when it is created.
                    - The read callback no longer receives the data read;
                      call read or readLine as appropriate.
                    - The state Closing is gone; when a socket begins closing
                      the state is set to Closed and there is no way to tell
                      when the close finishes (due to limitations in tcl sockets)
                    - Any data queued for write is written before closing finishes.
2004-10-12 ROwen    Fixed documentation for setReadCallback.
                    Removed class attribute _tkWdg since it was not being used.
2005-06-08 ROwen    Changed TkSocket and NullSocket to new-style classes.
2005-06-14 ROwen    Modified to clear references to the following when the socket closes,
                    to aid garbage collection:
                    - read and state callback functions
                    - pointer to the tk socket
                    - pointer to a string var and its _tk
2005-06-16 ROwen    Removed an unused variable (caught by pychecker).
2005-08-05 ROwen    Modified to use _tk.call instead of _tk.eval for config (because I expect it to
                    handle quoting arguments better and I was able to cut down the number of calls).
2005-08-10 ROwen    Bug fix: was not sending binary data through correctly.
                    Fixed by using _tk.call instead of _tk.eval to write.
                    Modified to use call instead of eval in all cases.
                    Added TkServerSocket and TkBaseSocket.
                    Changed state constants from module constants to class constants.
2005-08-22 ROwen    TkSocket: bug fix: an exception could occur in the read
                    callback if the remote host closed the connection.
                    Formerly the internal socket read callback tried to check
                    the connection before calling the user's read callback,
                    but that test could fail due to timing issues.
                    Now the user's read callback is always called
                    and read and readLine always return "" (or default for readLine)
                    if the socket is closed -- they never raise an exception.
                    Bug fix: Bug fix: _TkCallback was creating a tk function name
                    that was not necessarily unique, which could lead to subtle bugs
                    (tk not being calling some callback functions).
                    Eliminated the unused self._tkVar.
2005-08-24 ROwen    Bug fix: leaked tcl functions.
                    Modified to use TkUtil.TclFunc instead of an local _TkCallback.
2006-07-10 ROwen    Modified BaseServer to be compatible with Python 2.3.
                    Added BaseServer to __all__.
                    Bug fix: invalid import in test code.
"""
__all__ = ["TkSocket", "TkServerSocket", "BaseServer", "NullSocket"]
import sys
import traceback
import Tkinter
import RO.TkUtil
try:
    set
except NameError:
    from sets import Set as set

class TkBaseSocket(object):
    """A basic TCP/IP socket.
    
    Inputs:
    - tkSock    the tk socket connection; if not None then sockArgs is ignored
    - sockArgs  argument list for tk socket; ignored if tkSock not None
    - state     the initial state
    """
    Connecting = 4
    Connected = 3
    Closing = 2
    Failing = 1
    Closed = 0
    Failed = -1
    
    _StateDict = {
        Connecting: "Connecting",
        Connected: "Connected",
        Closing: "Closing",
        Failing: "Failing",
        Closed: "Closed",
        Failed: "Failed",
    }
        
    StateStrMaxLen = 0
    for _stateStr in _StateDict.itervalues():
        StateStrMaxLen = max(StateStrMaxLen, len(_stateStr))
    del(_stateStr)
    
    def __init__(self,
        tkSock = None,
        sockArgs = None,
        state = Connected,
        addr = None,
        port = None,
        stateCallback = None,
    ):
        self._sock = None
        self._state = state
        self._reason = ""
        self._addr = addr
        self._port = port
        self._stateCallback = stateCallback
        self._tkCallbackDict = {}

        self._tk = Tkinter.StringVar()._tk
        
        if tkSock:
            self._sock = tkSock
        elif sockArgs:
            try:
                self._sock = self._tk.call('socket', *sockArgs)
            except Tkinter.TclError, e:
                raise RuntimeError(e)
        else:
            raise RuntimeError("Must specify tkSock or sockArgs")

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
            self._tk.call('fileevent', self._sock, typeStr, tkFuncName)
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

    def close(self, isOK=True, reason=None):
        """Start closing the socket.
        
        Does nothing if the socket is already closed or failed.
        
        Inputs:
        - isOK: if True, mark state as Closed, else Failed
        - reason: a string explaining why, or None to leave unchanged;
            please specify if isOK is false.
        """
        #print "%s.close(isOK=%s, reason=%s)" % (self.__class__.__name__, isOK, reason)
        if self._state <= self.Closed:
            return

        if self._sock:
            try:
                # close socket (this automatically deregisters any file events)
                self._tk.call('close', self._sock)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception:
                pass
            self._sock = None
        self._tk = None
        if isOK:
            self._setState(self.Closed, reason)
        else:
            self._setState(self.Failed, reason)
    
    def getFullState(self):
        """Returns the current state as a tuple:
        - state: a numeric value; named constants are available
        - stateStr: a short string describing the state
        - reason: the reason for the state ("" if none)
        """
        state, reason = self._state, self._reason
        return (state, self.getStateStr(state), reason)
    
    def getState(self):
        """Returns the current state as a constant.
        """
        return self._state

    def getStateStr(self, state=None):
        """Return the string description of a state.
        If state is omitted, return description of current state.
        """
        if state == None:
            state = self._state
        try:
            return self._StateDict[state]
        except KeyError:
            return "Unknown (%r)" % (state,)
        
    def isClosed(self):
        """Return True if socket no longer connected.
        Return False if connecting or connected.
        """
        return (self._state < self.Connected)
    
    def isConnected(self):
        return (self._state == self.Connected)
    
    def setStateCallback(self, callFunc=None):
        """Specifies a state callback function
        (replacing the current one, if one exists).
        
        Inputs:
        - callFunc: the callback function, or None if none wanted
                    The function is sent one argument: this TkSocket
        """
        self._stateCallback = callFunc
    
    def _assertConn(self):
        """If not connected and socket error-free, raise RuntimeError.
        """
        if not self._checkSocket():
            raise RuntimeError("%s not open" % (self,))

    def _checkSocket(self):
        """Check socket for errors.
        Return True if OK.
        Close socket and return False if errors found.
        """
        #print "%s._checkSocket()" % (self.__class__.__name__,)
        if self._state not in (self.Connected, self.Connecting):
            return False
        errStr = self._tk.call('fconfigure', self._sock, '-error')
        if errStr:
            self.close(isOK = False, reason = errStr)
            return False
        isEOFStr = self._tk.call('eof', self._sock)
        if int(isEOFStr):
            self.close(isOK = True, reason = "closed by remote host")
            return False
        return True
    
    def _clearCallbacks(self):
        """Clear any callbacks added by this class.
        Called just after the socket is closed.
        """
        #print "%s._clearCallbacks called" % (self.__class__.__name__,)
        for tclFunc in self._tkCallbackDict.itervalues():
            tclFunc.deregister()
        self._tkCallbackDict = None
        self._stateCallback = None

    def __del__(self):
        """At object deletion, make sure the socket is properly closed.
        """
        #print "TkSocket.__del__ called"
        self._stateCallback = None
        self.close()
    
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
        if self.isClosed():
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
        return "%s %s:%s" % (self.__class__.__name__, self._addr, self._port)


class TkSocket(TkBaseSocket):
    """A TCP/IP socket that reads and writes using Tk events.
    
    Inputs:
    - addr      IP address as dotted name or dotted numbers
    - port      IP port
    - binary    binary mode (disable newline translation)
    - readCallback: function to call when data read; receives: self
    - stateCallback: function to call when state or reason changes; receives: self
    - tkSock    existing tk socket (if missing, one is created and opened)
    """
    def __init__(self,
        addr,
        port,
        binary=False,
        readCallback = None,
        stateCallback = None,
        tkSock = None,
    ):
        self._binary = binary
        self._readCallback = readCallback
        
        if tkSock:
            state = self.Connected
            sockArgs = None
        else:
            state = self.Connecting
            sockArgs = ('-async', addr, port)
        
        TkBaseSocket.__init__(self,
            tkSock = tkSock,
            sockArgs = sockArgs,
            state = state,
            addr = addr,
            port = port,
            stateCallback = stateCallback,
        )

        try:
            # create and configure socket
            configArgs = (
                '-blocking', 0,
                '-buffering', 'none',
                '-encoding', 'binary',
            )
            if self._binary:
                configArgs += (
                    '-translation', 'binary',
                )
            self._tk.call('fconfigure', self._sock, *configArgs)
                
            # add callbacks; the write callback indicates the socket is open
            # and is just used to detect state
            self._setSockCallback(self._doRead)
            self._setSockCallback(self._doConnect, doWrite=True)
        except Tkinter.TclError, e:
            raise RuntimeError(e)
            
        self._setState(self.Connecting)
        self._checkSocket()
    
    def read(self, nChar=None):
        """Return up to nChar characters; if nChar is None then return
        all available characters.
        """
        if nChar == None:
            retVal = self._tk.call('read', self._sock)
        else:
            retVal = self._tk.call('read', self._sock, nChar)
        if not retVal:
            self._checkSocket()
        #print "read returning %r" % retVal
        return retVal

    def readLine(self, default=None):
        """Read one line of data.
        Do not return the trailing newline.
        If a full line is not available, return default.
        
        Inputs:
        - default   value to return if a full line is not available
                    (in which case no data is read)
        
        Raise RuntimeError if the socket is not open.
        """
        #print "%s.readLine(default=%s)" % (self.__class__.__name__, default)
        readStr = self._tk.call('gets', self._sock)
        if not readStr:
            self._checkSocket()
            return default
        #print "readLine returning %r" % (readStr,)
        self._prevLine = readStr
        return readStr
    
    def setReadCallback(self, callFunc=None):
        """Specifies a read callback function
        (replacing the current one, if one exists).
        
        Inputs:
        - callFunc: the callback function, or None if none wanted.
                    The function is sent one argument: this TkSocket
        """
        self._readCallback = callFunc
    
    def write(self, data):
        """Write data to the socket. Does not block.
        
        Safe to call as soon as you call connect, but of course
        no data is sent until the connection is made.
        
        Raises UnicodeError if the data cannot be expressed as ascii.
        Raises RuntimeError if the socket is not connecting or connected.
        If an error occurs while sending the data, the socket is closed,
        the state is set to Failed and _reason is set.
        
        An alternate technique (from Craig):
        turn } into \}; consider escaping null and all but
        the final \n in the same fashion
        (to do this it probably makes sense to supply a writeLine
        that escapes \n and \r and then appends \n).
        Then:
        self._tk.eval('puts -nonewline %s { %s }' % (self._sock, escData))
        """
        #print "writing %r" % (data,)
        self._tk.call('puts', '-nonewline', self._sock, data)
        self._assertConn()
    
    def writeLine(self, data):
        """Write a line of data terminated by standard newline
        (which for the net is \r\n, but the socket's auto newline
        translation takes care of it).
        """
        self.write(data + "\n")
    
    def _clearCallbacks(self):
        """Clear any callbacks added by this class.
        Called just after the socket is closed.
        """
        TkBaseSocket._clearCallbacks(self)
        self._readCallback = None
    
    def _doConnect(self):
        """Called when connection finishes or fails.
        
        Sets up read handler.
        """
        #print "%s: _doConnect" % (self,)
        # cancel write handler (it has done its job)
        self._setSockCallback(callFunc=None, doWrite=True)
        
        if self._checkSocket():
            self._setState(self.Connected)
    
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
    
    def __str__(self):
        return "%s %s" % (self.__class__.__name__, self._sock)


class TkServerSocket(TkBaseSocket):
    """A tcp server socket
    
    Inputs:
    - connCallback  function to call when a client connects;
                it recieves the following arguments:
                - sock, a TkBaseSocket
    - port      port number or name of supported service;
                if 0 then a port is automatically chosen
    - binary    should new connections be set to binary?
    """
    def __init__(self,
        connCallback,
        port = 0,
        binary = False,
    ):
        self._connCallback = connCallback
        self._binary = binary

        self._tkNewConn = RO.TkUtil.TclFunc(self._newConnection)
        sockArgs = (
            '-server', self._tkNewConn.tclFuncName,
            port,
        )
        TkBaseSocket.__init__(self,
            sockArgs = sockArgs,
            state = self.Connected,
            port = port,
        )
    
    def _clearCallbacks(self):
        """Clear any callbacks added by this class.
        Called just after the socket is closed.
        """
        TkBaseSocket._clearCallbacks(self)
        self._tkNewConn.deregister()
        self._tkNewConn = None
        self._connCallback = None
    
    def _newConnection(self, tkSock, clientAddr, clientPort):
        """A client has connected. Create a TkSocket
        and call the connection callback with it.
        """
        newSocket = TkSocket(
            tkSock = tkSock,
            addr = clientAddr,
            port = clientPort,
        )
        
        try:
            # configure socket
            configArgs = (
                '-blocking', 0,
                '-buffering', 'none',
                '-encoding', 'binary',
            )
            if self._binary:
                configArgs += ('-translation', 'binary')
            self._tk.call('fconfigure', self._sock, *configArgs)
        except Tkinter.TclError, e:
            raise RuntimeError('Could not configure new connection:', e)
        
        try:
            self._connCallback(newSocket)
        except (SystemExit, KeyboardInterrupt):
            raise
        except Exception, e:
            errMsg = "%s connection callback %s failed: %s" % (self.__class__.__name__, self._connCallback, e)
            sys.stderr.write(errMsg + "\n")
            traceback.print_exc(file=sys.stderr)
            

class BaseServer:
    """Simple tcp server class. Subclass to do real work
    """
    def __init__(self,
        port,
        binary = True,
        maxConn = None,
    ):
        self.servSock = TkServerSocket(
            connCallback = self.gotConn,
            port = port,
            binary = binary,
        )
        self.maxConn = maxConn
        self.sockSet = set()
    
    def gotConn(self, tkSock):
        if self.maxConn != None:
            if len(self.sockSet) >= self.maxConn:
                tkSock.write("No free connections")
                tkSock.close()
                return

        self.sockSet.add(tkSock)
        tkSock.setReadCallback(self.dataRead)
        tkSock.setStateCallback(self.stateChanged)
        
    def dataRead(self, tkSock):
        """Called when data is read on the socket.
        Subclass to do useful work.
        """
        pass
    
    def stateChanged(self, tkSock):
        if tkSock.isClosed():
            self.sockSet.remove(tkSock)

class NullSocket(TkBaseSocket):
    """Null connection.
    Forbids read, write and setting a new state callback.
    Close is OK and the state is always Closed.
    """
    def __init__ (self):
        TkBaseSocket.__init__(self,
            tkSock = "NullSocket",
            state = self.Closed,
        )
        self._reason = "This is an instance of NullSocket"

    def read(self, *args, **kargs):
        raise RuntimeError("Cannot read from null socket")
        
    def readLine(self, *args, **kargs):
        raise RuntimeError("Cannot readLine from null socket")

    def write(self, astr):
        raise RuntimeError("Cannot write %r to null socket" % astr)

    def writeLine(self, astr):
        raise RuntimeError("Cannot writeLine %r to null socket" % astr)


if __name__ == "__main__":
    import threading
    root = Tkinter.Tk()
    root.withdraw()
    
    port = 2150
    binary = False
    
    class TCPEcho(BaseServer):
        def __init__(self, port, binary=True):
            print "Starting echo server listener on port", port
            self.partialLastLine = ""
            BaseServer.__init__(self, port, binary=binary)

        def dataRead(self, tkSock):
            readData = tkSock.read()
            if not readData:
                print "TCPEcho Warning: got read callback, but no data available"
                return

            readLines = readData.split("\n")
            if self.partialLastLine:
                readLines[0] = self.partialLastLine + readLines[0]
            if readLines[-1] != "":
                self.partialLastLine = readLines.pop(-1)
            
            tkSock.write(readData)
            if "quit" in readLines:
                tkSock.close()
            

    # start single-user echo server as background thread
#   serverThread = threading.Thread(target=tcpEcho, args=(port,))
    echoObj = TCPEcho(port = port, binary = binary)
    
    if binary:
        testStrings = (
            "foo\nba",
            "r\nfuzzle\nqu",
            "it",
            "\n"
        )
    else:
        testStrings = (
            "foo",
            "string with 3 nulls: 1 \0 2 \0 3 \0 end",
            "string with 3 quoted nulls: 1 \\0 2 \\0 3 \\0 end",
            '"quoted string followed by carriage return"\r',
            "string with newline: \n end",
            "string with carriage return: \r end",
            "quit",
        )


    def statePrt(sock):
        stateVal, stateStr, reason = sock.getFullState()
        if reason:
            print "socket %s: %s" % (stateStr, reason)
        else:
            print "socket %s" % (stateStr,)
        if sock.isClosed():
            sys.exit(0)
        if sock.isConnected():
            runTest()
            
        
    def readPrt(sock):
        if binary:
            outStr = sock.read()
        else:
            outStr = sock.readLine()
        print "read   %r" % (outStr,)

    ts = TkSocket(
        addr = "localhost",
        port = port,
        binary = binary,
        stateCallback = statePrt,
        readCallback = readPrt,
    )
    
    strIter = iter(testStrings)

    def runTest():
        try:
            testStr = strIter.next()
            print "writing %r" % (testStr,)
            if binary:
                ts.write(testStr)
            else:
                ts.writeLine(testStr)
            root.after(500, runTest)
        except StopIteration:
            pass

    root.mainloop()
