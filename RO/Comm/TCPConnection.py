#!/usr/local/bin/python -i
"""TCP specializations of TkSocket.

All permit disconnection and reconnection
and the base class offers support for
authorization and line-oriented output.

Requirements:
- Tkinter (due to the underlying TkSocket library)

History:
2002-11-22 R Owen: first version with history. Moved to RO.Comm
	and modified to use TkSocket sockets. This fixed a pitfall
	(it was not safe to close the socket if a read handler
	was present) and socket writes are done in a background thread
	and so no longer block.
2002-12-13 ROwen	Moved isConnected from VMSTelnet to TCPConnection.
2003-02-27 ROwen	Added setStateCallback; added connection state.
	Overhauled connection subroutine handling: you can now have multiple
	connection subroutines, they receive the new connection state variable
	and an explanatory message.
	Overhauled VMSTelnet to use this instead of printing negotation status directly.
2003-07-18 ROwen	Renamed subroutine to function, for consistency with other code;
	improved doc strings (including adding a doc string to NullConnection).
2003-10-13 ROwen	Major overhaul to match new TkSocket and simplify subclasses.
2003-11-19 ROwen	Bug fix: reason was not always a string; modified _setState
					to cast it to a string.
2003-12-04 ROwen	Modified to only call the state callback when the state
					or reason changes.
					Changed doCall to callNow in addStateCallback,
					for consistency with other addCallback functions.
2004-05-18 ROwen	Stopped importing string, Tkinter, RO.Alg and RO.Wdg; they weren't used.
2004-07-13 ROwen	Modified for overhauled TkSocket.
2004-09-14 ROwen	Importing socket module but not using it.
2004-10-12 ROwen	Corrected documentation for addReadCallback and addStateCallback.
2005-06-08 ROwen	Changed TCPConnection to a new-style class.
2005-08-10 ROwen	Modified for TkSocket state constants as class const, not module const.
2005-08-11 ROwen	Added isDone and getProgress methods.
"""
import sys
from TkSocket import TkSocket, NullSocket

# states
Connecting = 5
Authorizing = 4
Connected = 3
Disconnecting = 2
Failing = 1
Disconnected = 0
Failed = -1

# a dictionary that describes the various values for the connection state
_StateDict = {
	Connecting: "Connecting",
	Authorizing: "Authorizing",
	Connected: "Connected",
	Disconnecting: "Disconnecting",
	Failing: "Failing",
	Disconnected: "Disconnected",
	Failed: "Failed",
}

class TCPConnection(object):
	"""A TCP TkSocket with the ability to disconnect and reconnect.
	Optionally returns read data as lines
	and has hooks for authorization.

	Inputs:
	- host: initial host (can be changed when connecting)
	- port: initial port (can be changed when connecting);
	  defaults to 23, the standard telnet port
	- readCallback: function to call whenever data is read;
	  see addReadsubr for details.
	- readLines: if True, the read callbacks receive entire lines
		minus the terminator; otherwise the data is distributed as received
	- stateCallback: a function to call whenever the state or reason changes;
	  see addStateCallback for details.
	- authReadCallback: if specified, used as the initial read callback function;
		if auth succeeds, it must call self._authDone()
	- authReadLines: if True, the auth read callback receives entire lines
	"""
	def __init__ (self,
		host = None,
		port = 23,
		readCallback = None,
		readLines = False,
		stateCallback = None,
		authReadCallback = None,
		authReadLines = False,
	):
		self.host = host
		self.port = port
		self._readLines = readLines
		self._userReadCallbacks = []
		if readCallback:
			self.addReadCallback(readCallback)
		self._stateCallbacks = []
		if stateCallback:
			self.addStateCallback(stateCallback)
		self._authReadLines = authReadLines
		self._authReadCallback = authReadCallback

		self._state = 0
		self._reason = ""
		self._currReadCallbacks = []
		
		# translation table from TkSocket states to local states
		# note that the translation of Connected will depend
		# on whether there is authorization; this initial setup
		# assumes no authorization
		if self._authReadCallback:
			locConnected = Authorizing
		else:
			locConnected = Connected
		self._tkLocalStateDict = {
			TkSocket.Connecting: Connecting,
			TkSocket.Connected: locConnected,
			TkSocket.Closing: Disconnecting,
			TkSocket.Failing: Failing,
			TkSocket.Closed: Disconnected,
			TkSocket.Failed: Failed,
		}
		
		self._sock = NullSocket()
		
	def addReadCallback (self, readCallback):
		"""Add a read function, to be called whenever a line of data is read.
		
		Inputs:
		- readCallback: function to call whenever a line of data is read;
		  it is sent two arguments:
		  - the socket (a TkSocket object)
		  - the line of data read (without its terminating \r)
		"""
		assert callable(readCallback), "read callback not callable"
		self._userReadCallbacks.append(readCallback)
	
	def addStateCallback (self, stateCallback, callNow=False):
		"""Add a state function to call whenever the state or reason changes.
		
		Inputs:
		- stateCallback: the function; it is sent one argument: this TCPConnection
		- callNow: call the connection function immediately?
		"""
		assert callable(stateCallback)
		self._stateCallbacks.append(stateCallback)
		if callNow:
			stateCallback(self)
	
	def connect (self,
		host=None,
		port=None,
	):
		"""Open the connection.

		Inputs:
		- host: IP address (name or numeric) of host; if omitted, the default is used
		- port: port number; if omitted, the default is used
		"""
		if host:
			self.host = host
		if port:
			self.port = port
		if not self.host:
			self.disconnect(isOK = False, reason = "Cannot connect; no host specified")
			return
	
		# need a new socket; first disconnect the old one
		# and get rid of the old state callback
		self.disconnect(True, "new connection being made")
		self._sock.setStateCallback()

		self._sock = TkSocket(
			addr = self.host,
			port = self.port,
			stateCallback = self._sockStateCallback,
		)
		
		if self._authReadCallback:
			self._tkLocalStateDict[TkSocket.Connected] = Authorizing
			self._setRead(True)
		else:
			self._tkLocalStateDict[TkSocket.Connected] = Connected
			self._setRead(False)
	
	def disconnect(self, isOK=True, reason=None):
		"""Close the connection.

		Called disconnect instead of close (the usual counterpoint in the socket library)
		because you can reconnect at any time by calling connect.
		
		Inputs:
		- isOK: if True, final state is Disconnected, else Failed
		- reason: a string explaining why, or None to leave unchanged;
			please specify a reason if isOK is false!	
		"""
		self._sock.close(isOK=isOK, reason=reason)

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
			stateStr = "Unknown (%r)" % (state)
		return (state, stateStr, reason)

	def getProgress(self, wantConn):
		"""Describe the progress towards being connected or disconnected.
		
		Inputs:
		- wantConn	True if you want to be connected, False if disconnected
		
		Returns:
		- isDone	True if in a final state (connected, disconnected or failed)
		- isOK		True if in desired state or moving to it
		- state		current state code
		- stateStr	string description of state code
		- reason	the reason for the state ("" if none)
		"""
		state, stateStr, reason = self.getFullState()
		isDone = self.isDone()
		if wantConn:
			isOK = self._state in (Connecting, Connected)
		else:
			isOK = self._state in (Disconnecting, Disconnected)
		return isDone, isOK, state, stateStr, reason

	def getState(self):
		"""Returns the current state as a constant.
		"""
		return self._state
	
	def isConnected(self):
		"""Return True if connected, False otherwise.
		"""
		return self._state == Connected

	def isDone(self):
		"""Return True if connected, disconnected or failed.
		"""
		return self._state in (Connected, Disconnected, Failed)

	def removeReadCallback (self, readCallback):
		"""Attempt to remove the read callback function;

		Returns True if successful, False if the subr was not found in the list.
		"""
		try:
			self._userReadCallbacks.remove(readCallback)
			return True
		except ValueError:
			return False

	def removeStateCallback (self, stateCallback):
		"""Attempt to remove the state callback function;

		Returns True if successful, False if the subr was not found in the list.
		"""
		try:
			self._stateCallbacks.remove(stateCallback)
			return True
		except ValueError:
			return False
	
	def write(self, astr):
		"""Write data to the socket. Does not block.
		
		Safe to call as soon as you call connect, but of course
		no data is sent until the connection is made.
		
		Raises UnicodeError if the data cannot be expressed as ascii.
		Raises RuntimeError if the socket is not connecting or connected.
		If an error occurs while sending the data, the socket is closed,
		the state is set to Failed and _reason is set.
		"""
		self._sock.write(astr)

	def writeLine (self, astr):
		"""Send a line of data, appending newline.

		Raises UnicodeError if the data cannot be expressed as ascii.
		Raises RuntimeError if the socket is not connecting or connected.
		If an error occurs while sending the data, the socket is closed,
		the state is set to Failed and _reason is set.
		"""
		self._sock.writeLine(astr)
	
	def _authDone(self, msg=""):
		"""Call from your authorization callback function
		when authorization succeeds.
		Do not call unless you specified an authorization callback function.
		
		If authorization fails, call self.disconnect(False, error msg) instead.
		"""
		self._setRead(forAuth=False)
		self._setState(Connected, msg)
	
	def _setRead(self, forAuth=False):
		"""Set up reads.
		"""
		if (forAuth and self._authReadLines) or (not forAuth and self._readLines):
			self._sock.setReadCallback(self._sockReadLineCallback)
		else:
			self._sock.setReadCallback(self._sockReadCallback)
		if forAuth:
			self._currReadCallbacks = [self._authReadCallback,]
		else:
			self._currReadCallbacks = self._userReadCallbacks

	def _setState(self, newState, reason=None):
		"""Set the state and reason. If anything has changed, call the connection function.

		Inputs:
		- newState	one of the state constants defined at top of file
		- reason	the reason for the change (a string, or None to leave unchanged)
		"""
		oldStateReason = (self._state, self._reason)
		if not _StateDict.has_key(newState):
			raise RuntimeError, "unknown connection state: %s" % (newState,)
		self._state = newState
		if reason != None:
			self._reason = str(reason)
		
		# if the state or reason has changed, call state callbacks
		if oldStateReason != (self._state, self._reason):
			for stateCallback in self._stateCallbacks:
				stateCallback(self)
	
	def _sockReadCallback (self, sock):
		"""Read callback for the TkSocket.
				
		When data is received, read it and issues all callbacks.
		"""
		dataRead = sock.read()
		# print "TCPConnection._sockReadCallback called; data=%r" % (dataRead,)
		for subr in self._currReadCallbacks:
			subr(sock, dataRead)

	def _sockReadLineCallback (self, sock):
		"""Read callback for the TkSocket that returns whole lines.
				
		Whenever one or more lines is received, issues all callbacks;
		strips the line terminator(s).
		"""
		dataRead = sock.readLine()
		if not dataRead:
			# only a partial line was available
			return
		# print "TCPConnection._sockReadLineCallback called with data %r" % (dataRead,)
		for subr in self._currReadCallbacks:
			subr(sock, dataRead)
	
	def _sockStateCallback(self, sock):
		sockState, descr, reason = sock.getFullState()
		try:
			locState = self._tkLocalStateDict[sockState]
		except KeyError:
			sys.stderr.write("unknown TkSocket state %r\n" % sockState)
			return
		self._setState(locState, reason)
		

if __name__ == "__main__":
	import Tkinter
	
	root = Tkinter.Tk()
	
	def statePrt(sock):
		stateVal, stateStr, reason = sock.getFullState()
		if reason:
			print "socket %s: %s" % (stateStr, reason)
		else:
			print "socket %s" % (stateStr,)
		
	def readPrt(sock, outStr):
		print "read: %r" % (outStr,)

	ts = TCPConnection(
		readLines = True,
		host = "localhost",
		port = 7,
		stateCallback = statePrt,
		readCallback = readPrt,
	)
	ts.connect()
	
	root.mainloop()