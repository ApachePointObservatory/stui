#!/usr/local/bin/python
"""VMS telnet connection. May work with other operating systems.

Note: not very well tested, since I no longer use it.

Requirements:
- Threads
- Tkinter (though if you don't wish to use read callbacks you can easily
  rewrite the underlying socket library TkSocket to remove this restriction)

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
2003-10-10 ROwen	Modified to use new TCPConnection.
2005-01-12 ROwen	Modified for new RO.Wdg.ModalDialogBase.
"""
import sys
import RO.Wdg
from TCPConnection import *

class VMSTelnet (TCPConnection):
	"""A telnet connection that negotiates the telnet protocol
	and handles password login. The only thing specific to VMS
	is the details of the username/password negotiation; presumably
	this could trivially be modified for other platforms.
	"""
	_IAC  = chr(255)	# Interpret as command
	_DONT = chr(254)
	_DO   = chr(253)
	_WONT = chr(252)
	_WILL = chr(251)

	def __init__ (self,
		host = None,
		port = 23,
		readCallback = None,
		stateCallback = None,
	):
		"""Create a telnet connection.

		Inputs:
			readCallback: function to call whenever a line of data is read;
				it will be sent one argument: the line of data
			stateCallback: function to call whenever the socket
				connects or disconnected; it will be sent two arguments:
					is connected flag (true if connected, false if not)
					this connection object		
		"""
		TCPConnection.__init__(self,
			host=host,
			port=port,
			readCallback=readCallback,
			stateCallback=stateCallback,
			readLines = True,
			authReadCallback = self._authRead,
			authReadLines = False,
		)
		
		self._initData()
	
	def _initData(self):
		"""Initialize extra fields."""
		self._iac = 0
		self._opt = ''
		self._password = None
		self._username = None
		self._authState = 0
		self._partialData = ""

	def connect (self,
		username,
		password,
		host = None,
		port = None,
	):
		"""Open the connection and log in.

		Inputs:
			host: IP address (name or numeric) of host
			username: username for login
			password: password for login
		"""
		self._initData()
		self._password = password
		self._username = username

		TCPConnection.connect(self, host, port)
	
	def connectDialog (self, master, username, host=None):
		"""Prompt for a password and then connect.
		"""
		if host:
			self.host = host
	
		class PasswordDialog(RO.Wdg.ModalDialogBase):
			def body(self, master):
		
				RO.Wdg.StrLabel(master, text="Password:").grid(row=0, column=0)
		
				self.pwdEntry = RO.Wdg.StrEntry(master, show="*")
				self.pwdEntry.grid(row=0, column=1)
				return self.pwdEntry # initial focus
		
			def setResult(self):
				self.result = self.pwdEntry.get()

		pwdDialog = PasswordDialog(master, title="%s@%s" % (username, self.host))
		passwd = pwdDialog.result
		if passwd:
			print "calling connect"
			self.connect (
				username = username,
				password = passwd,
			)
		
	def _authRead (self, sock, readData):
		"""Handle username/password authentication and telnet negotiation.
		
		- Handles telnet negotiation by denying all requests.
		- If negotation fails, closes the connection (and so calls the
		  connection state callback function).
		
		Intended to be the read callback function while negotiation the connection.
		"""
		for c in readData:
			if self._opt:
				self.write(self._opt + c)
				self._opt = ''
			elif self._iac:
				self._iac = 0
				if c == self._iac:
					self._partialData = self._partialData + c
				elif c in (VMSTelnet._DO, VMSTelnet._DONT):
					self._opt = VMSTelnet._IAC + VMSTelnet._WONT
				elif c in (VMSTelnet._WILL, VMSTelnet._WONT):
					self._opt = VMSTelnet._IAC + VMSTelnet._DONT
			elif c == VMSTelnet._IAC:
				self._iac = 1
			elif c == '\0':
				pass
			elif c == '\n':
				pass
			elif c == " ":
				self._partialData += c
				if self._authState == 0 and self._partialData.find("Username:") >= 0:
					self._setState(Authorizing, "Sending username")
					self._partialData = ""
					self._authState = 1
					self.writeLine (self._username)
				elif self._authState == 1 and self._partialData.find("Password:") >= 0:
					self._setState(Authorizing, "Sending password")
					self._partialData = ""
					self._authState = 2
					self.writeLine (self._password)
			elif c == '\r':
				if self._partialData.find("rror") >= 0:
					self.disconnect(False, "Connection negotiation failed; probably timed out\n")
				elif self._partialData.find("authorization failure") >= 0:
					self.disconnect(False, "Invalid password\n")
				elif self._authState == 2 and self._partialData.find("login") >= 0:
					self._partialData = ""
					self._authDone()
				else:
					print self._partialData
					self._partialData = ""
			else:
				self._partialData += c

class NullConnection(TCPConnection):
	"""Null connection for test purposes.
	Always acts as if it is connected (so one can write data),
	but prohibits explicit connection (maybe not necessary,
	but done to make it clear to users that it is a fake).
	"""
	def connect(self):
		raise RuntimeError, "NullConnection cannot connect"

	def isConnected(self):
		return True

	def writeLine(self, str):
		sys.stdout.write("Null connection asked to write: %s\n" % (str,))


if __name__ == "__main__":
	import Tkinter
	root = Tkinter.Tk()

	host = "tccdev"
	username = "TCC"

	def readCallback (sock, astr):
		print "read: %r" % (astr,)

	def stateCallback (sock):
		state, stateStr, reason = sock.getFullState()
		if reason:
			print "%s: %s" % (stateStr, reason)
		else:
			print stateStr

	myConn = VMSTelnet(
		host = host, 
		readCallback = readCallback,
		stateCallback = stateCallback,
	)

	sendText = Tkinter.Entry(root)
	sendText.pack(fill=Tkinter.X, expand=Tkinter.YES)
	sendText.focus_set()

	Tkinter.Button(root, text="Disconnect", command=myConn.disconnect).pack()	

	def sendCmd (evt):
		try:
			astr = sendText.get()
			sendText.delete(0,Tkinter.END)
			myConn.writeLine(astr)
		except Exception, e:
			sys.stderr.write ("Could not extract or send: %s\n" % (astr))
			sys.stderr.write ("Error: %s\n" % (e))

	sendText.bind('<KeyPress-Return>', sendCmd)

	myConn.connectDialog(root, username=username)

	root.mainloop()
