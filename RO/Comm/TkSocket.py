#!/usr/local/bin/python
"""Enhanced sockets optimized for use with Tkinter GUIs.

TkSocket allows completely nonblocking operations:
- Connection and disconnection is done in the background.
- You may begin writing as soon as you start connecting.
- Written data is queued and sent as the connection permits.
- When data is available to be read. a read callback function is called.

Also, state changes can easily be monitored via a state callback function.

History:
2002-11-22 ROwen	First version
2003-02-25 ROwen	Bug fix: could hang on program exit; cured using atexit;
					also added a __del__ method for the same reason.
2003-02-27 ROwen	_WriteThread.close was printing an error message
					instead of terminating the write thread.
2003-04-04 ROwen	Bug fix: BasicSocket was being set to a function instead of a type;
					this failed under Windows (hanks to Craig Loomis for report and fix).
2003-05-01 ROwen	Modified to work with Python 2.3b1 (which does not support
					_tkinter.create/deletefilehandler); thanks to Martin v. Lowis for the fix.
2003-10-13 ROwen	Overhauled to more robust and to prevent delays while connecting.
					Also added support for monitoring state.
2003-10-14 ROwen	Bug fix: close while NotConnected caused perpetual Closing state.
2003-11-19 ROwen	Bug fix: reason was not always a string; modified _setState
					to cast it to a string.
2003-12-04 ROwen	Modified to only call the state callback when the state or reason changes.
2004-05-18 ROwen	Increased state polling delay from 100ms to 200ms.
					Stopped importing sys since it was not being used.
2004-07-21 ROwen	Overhauled to add Windows compatibility, by eliminating the use
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
2004-10-12 ROwen	Fixed documentation for setReadCallback.
					Removed class attribute _tkWdg since it was not being used.
2005-06-08 ROwen	Changed TkSocket and NullSocket to new-style classes.
2005-06-14 ROwen	Modified to clear references to the following when the socket closes,
					to aid garbage collection:
					- read and state callback functions
					- pointer to the tk socket
					- pointer to a string var and its _tk
2005-06-16 ROwen	Removed an unused variable (caught by pychecker).
"""
import sys
import traceback
import Tkinter

# states
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

class _TkCallback(object):
	"""Convenience class for Tk callbacks.
	"""
	def __init__(self, tk, func):
		# using the id of self rather than func
		# works around an oddity that an instance method
		# does not appear to have constant id
		self.name = "cb%d" % id(self)
		self.func = func
		tk.createcommand(self.name, func)

class TkSocket(object):
	"""A TCP/IP socket that reads and writes using Tk events.
	
	Inputs:
	- addr		IP address as dotted name or dotted numbers
	- port		IP port
	- binary	binary mode (disable newline translation)
	- readCallback: function to call when data read; receives: self, readData
	- stateCallback: function to call when state or reason changes; receives: self
	"""
	def __init__(self,
		addr,
		port,
		binary=False,
		readCallback = None,
		stateCallback = None,
	):
		self._addr = addr
		self._port = port
		self._binary = binary
		self._readCallback = readCallback
		self._stateCallback = stateCallback

		self._tkVar = Tkinter.StringVar()
		self._tk = self._tkVar._tk
		self._sock = None
		self._addr = ""
		self._port = ""
		self._binary = None
		
		self._state = Connecting
		self._reason = ""

#	the following is probably not needed with the new socket code
#		# make sure the socket is properly closed at exit;
#		# this avoids nasty infinite loops
#		atexit.register(self.close)

		try:
			# create and configure socket
			self._sock = self._tk.eval('socket -async %s %s' % (addr, port))
			self._tk.eval('fconfigure %s -blocking 0' % self._sock)
			self._tk.eval('fconfigure %s -buffering none' % self._sock)
			self._tk.eval('fconfigure %s -encoding binary' % self._sock)
			if self._binary:
				self._tk.eval('fconfigure %s -translation binary' % self._sock)
				
			# add callbacks; the write callback indicates the socket is open
			# and is just used to detect state
			doRead = _TkCallback(self._tk, self._doRead)
			doConnect = _TkCallback(self._tk, self._doConnect)
			self._tk.eval('fileevent %s readable %s' % (self._sock, doRead.name))
			self._tk.eval('fileevent %s writable %s' % (self._sock, doConnect.name))
		except Tkinter.TclError, e:
			raise RuntimeError(e)
			
		self._setState(Connecting)
		self._checkSocket()
	
	def close(self, isOK=True, reason=None):
		"""Start closing the socket.
		
		Does nothing if the socket is already closed or failed.
		
		Inputs:
		- isOK: if True, mark state as Closed, else Failed
		- reason: a string explaining why, or None to leave unchanged;
			please specify if isOK is false.
		"""
		if self._state <= Closed:
			return

		if isOK:
			self._setState(Closed, reason)
		else:
			self._setState(Failed, reason)
		if self._sock:
			try:
				# close socket (this automatically deregisters any file events)
				self._tk.eval('close %s' % self._sock)
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception:
				pass
			self._sock = None
		self._tkVar = None
		self._tk = None
		
	def isClosed(self):
		"""Return True if socket no longer connected.
		Return False if connecting or connected.
		"""
		return (self._state < Connected)
	
	def getState(self):
		"""Returns the current state as a constant.
		"""
		return self._state
	
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
	
	def read(self, nChar=None):
		"""Return up to nChar characters; if nChar is None then return
		all available characters.
		"""
		if nChar == None:
			retVal = self._tk.eval('read %s' % (self._sock,))
		else:
			retVal = self._tk.eval('read %s %i' % (self._sock, nChar))
		if not retVal:
			self._assertConn()
#		print "read returning %r" % retVal
		return retVal

	def readLine(self, default=None):
		"""Read one line of data.
		Do not return the trailing newline.
		If a full line is not available, return default.
		
		Inputs:
		- default	value to return if a full line is not available
					(in which case no data is read)
		
		Raise RuntimeError if the socket is not open.
		"""
		readStr = self._tk.eval('gets %s' % (self._sock,))
		if not readStr:
			self._assertConn()
			return default
#		print "readLine returning %r" % (readStr,)
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
	
	def setStateCallback(self, callFunc=None):
		"""Specifies a state callback function
		(replacing the current one, if one exists).
		
		Inputs:
		- callFunc: the callback function, or None if none wanted
					The function is sent one argument: this TkSocket
		"""
		self._stateCallback = callFunc
	
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
#		print "writing %r" % (data,)
		self._tkVar.set(data)
		self._tk.eval('puts -nonewline %s $%s' % (self._sock, self._tkVar))
		self._assertConn()
	
	def writeLine(self, data):
		"""Write a line of data terminated by standard newline
		(which for the net is \r\n, but the socket's auto newline
		translation takes care of it).
		"""
		self.write(data + "\n")
	
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
		if self._state not in (Connected, Connecting):
			return False
		errStr = self._tk.eval('fconfigure %s -error' % self._sock)
		if errStr:
			self.close(isOK = False, reason = errStr)
			return False
		isEOFStr = self._tk.eval("eof %s" % self._sock)
		if int(isEOFStr):
			self.close(isOK = True, reason = "closed by remote host")
			return False
		return True
					
	def __del__(self):
		"""At object deletion, make sure the socket is properly closed.
		"""
		# print "TkSocket.__del__ called"
		self._stateCallback = None
		self.close()
	
	def _doConnect(self):
		"""Called when connection finishes or fails.
		
		Sets up read handler.
		"""
		# cancel write handler (it has done its job)
		self._tk.eval('fileevent %s writable ""' % self._sock)
		
		if self._checkSocket():
			self._setState(Connected)
	
	def _doRead(self):
		"""Called when there is data to read"""
#		print "%s _doRead" % (self,)
		if not self._checkSocket():
			return

		if self._readCallback:
			try:
				self._readCallback(self)
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				sys.stderr.write("%s read callback %s failed: %s\n" % (self, self._readCallback, e,))
				traceback.print_exc(file=sys.stderr)
	
	def _setState(self, newState, reason=None):
		"""Change the state.
		
		Inputs:
		- newState: the new state
		- reason: an explanation (None to leave alone)
		"""
		# print "_setState(%r, %r)" % (newState, reason)
		self._state = newState
		if reason != None:
			self._reason = str(reason)

		if self._stateCallback:
			try:
				self._stateCallback(self)
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				sys.stderr.write("%s state callback %s failed: %s\n" % (self, self._stateCallback, e,))
				traceback.print_exc(file=sys.stderr)
		
		if self.isClosed():
			self._stateCallback = None
			self._readCallback = None
	
	def __str__(self):
		return "%s %s:%s" % (self.__class__.__name__, self._addr, self._port)


class NullSocket(object):
	"""Null connection.
	Forbids read, write and setting a new state callback.
	Close is OK and the state is always Closed.
	"""
	def __init__ (self):
		pass

	def close(self, isOK=True, reason=None):
		return
	
	def isClosed(self):
		return True
	
	def getState(self):
		return Closed
	
	def getFullState(self):
		return (Closed, _StateDict[Closed], "null socket")

	def read(self, *args, **kargs):
		raise RuntimeError("Cannot read from null socket")
		
	def readLine(self, *args, **kargs):
		raise RuntimeError("Cannot readLine from null socket")
	
	def setStateCallback(self, callFunc=None):
		if callFunc != None:
			raise RuntimeError("Cannot set state callback of null socket")

	def write(self, astr):
		raise RuntimeError("Cannot write %r to null socket" % astr)

	def writeLine(self, astr):
		raise RuntimeError("Cannot writeLine %r to null socket" % astr)


if __name__ == "__main__":
	import TCPEcho
	import threading
	root = Tkinter.Tk()
	root.withdraw()
	
	port = 2150
	
	# start single-user echo server as background thread
	serverThread = threading.Thread(target=TCPEcho.startServer, args=(port,))
	serverThread.setDaemon(True)
	serverThread.start()
	
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
		if sock.getState() == Connected:
			runTest()
			
		
	def readPrt(sock):
		outStr = sock.readLine()
		print "read: %r" % (outStr,)

	ts = TkSocket(
		addr = "localhost",
		port = port,
		binary = True,
		stateCallback = statePrt,
		readCallback = readPrt,
	)
	
	strIter = iter(testStrings)

	def runTest():
		try:
			testStr = strIter.next()
			ts.writeLine(testStr)
			root.after(500, runTest)
		except StopIteration:
			pass

	root.mainloop()
