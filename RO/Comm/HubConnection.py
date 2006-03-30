#!/usr/local/bin/python
"""A version of RO.TCPConnection that can negotiate a connection with the APO Hub.
This is a good example of the sort of connection used by KeyDispatcher.

History:
2003-02-27 ROwen	First release; full username support awaits implementation in hub.
2003-03-05 ROwen	Finished username support.
2003-06-18 ROwen	Modified to exclude SystemExit and KeyboardInterrupt
					when testing for general exceptions.
2003-06-25 ROwen	Modified to handle message data as a dict.
2003-07-18 ROwen	Added getProgramName and NullConnection.
2003-10-06 ROwen	Added getCmdr; changed getProgramName to getProgID
					and made it return in the case used by the Hub.
2003-10-10 ROwen	Modified to use new TCPConnection; moved from TUI to RO package.
					Read and state callbacks now receive different args.
2003-10-14 ROwen	Bug fix: NullConnection used TCPConnection.Connected instead of Connected.
2003-10-15 ROwen	getProgID and getUsername were broken (usually returned cmdr).
2005-01-06 ROwen	Changed NullConnection program from myprog to TU01; a more realistic name.
2005-01-12 ROwen	Modified for new RO.Wdg.ModalDialogBase.
2006-04-29 ROwen	Added loginExtra arg.
"""
import sha
import sys
from TCPConnection import *
import RO.ParseMsg

class HubConnection(TCPConnection):
	def __init__ (self,
		host = None,
		port = 9877,
		readCallback = None,
		stateCallback = None,
		loginExtra = None,
	):
		"""
		Creates a hub connection but does not connect.

		Inputs:
		- host: default TCP address of host (can override when connecting)
		- port: default TCP port (can override when connecting);
			defaults to 9877, the standard hub port
		- readCallback: function to call whenever a line of data is read;
		  it will be sent two arguments: (self, readData);
		  the read data does not include the line terminator
		- stateCallback: function to call whenever the state of the connection changes;
		  it will be sent one argument: self
		- loginExtra: additional string to be sent with the login command.
		"""
		TCPConnection.__init__(self,
			host=host,
			port=port,
			readCallback = readCallback,
			readLines = True,
			stateCallback = stateCallback,
			authReadCallback = self._authRead,
			authReadLines = True,
		)
		self._initData()
		self._loginExtra = loginExtra
	
	def _initData(self):
		self.desProgID = None
		self.desUsername = None
		self.cmdr = None
		self._authState = 0
		self.__password = None
	
	def connect (self,
		progID,
		password,
		username,
		host = None,
		port = None,
	):
		"""Opens the connection and logs in.
		Inputs:
		- progID: the desired program ID; the actual program ID
			should be the same except case may differ
		- password: the password associated with the program ID
		- username: desired username; the actual username should match if unique,
			else the hub will modify it in some fashion
		- host: TCP address of host; overrides the default specified at instantiation
		- port: TCP port of host; overrides the default specified at instantiation
		"""
		# make the basic connection
		self._initData()
		self.desProgID = progID
		self.__password = password
		self.desUsername = username
		TCPConnection.connect(self, host, port)
		try:
			self.writeLine("1 auth knockKnock")
		except RuntimeError:
			pass
			
	def getCmdr(self):
		"""Returns the commander (in the form progID.username)
		last assigned by the Hub.
		"""
		return self.cmdr

	def getAuthState(self):
		"""Returns the authorization state.
		"""
		return self._authState

	def getProgID(self):
		"""Return the program ID assigned by the hub (which should
		match the requested program ID except case may differ),
		or None if not connected.
		"""
		cmdr = self.getCmdr()
		return cmdr and cmdr.split(".")[0]

	def getUsername(self):
		"""Return the username assigned by the Hub,
		or None if not connected.
		"""
		cmdr = self.getCmdr()
		return cmdr and cmdr.split(".")[1]
	
	def isConnected(self):
		return self._state == Connected

	def _authRead(self, sock, hubMsg):
		"""Read callback for authorization.
		"""
		try:
			if self._authState == 0:
				# record and null the password
				password = self.__password
				self.__password = None

				# expect the line ': nonce="..."'
				msgDict = RO.ParseMsg.parseHubMsg(hubMsg)
				msgType = msgDict["type"]
				dataDict = msgDict["data"]
				nonce = dataDict.get("nonce", (None,))[0]
				if (msgType != ":"):
					errMsg = dataDict.get("why", hubMsg)[0]
					raise RuntimeError, "knockKnock failed: %s" % (errMsg,)
				elif (nonce == None):
					raise RuntimeError, "nonce missing; got: %r" % (hubMsg,)
				
				# generate the combined password
				combPassword = sha.sha(nonce+password).hexdigest()

				self._setState(Authorizing, "nonce received")
				self._authState = 1
				
				# send the command auth login program=<user> password=<combPassword>
				loginCmd = '1 auth login program="%s" password="%s" username="%s"' \
					% (self.desProgID, combPassword, self.desUsername)
				if self._loginExtra:
					loginCmd = " ".join((loginCmd, self._loginExtra))
				self.writeLine(loginCmd)
			elif self._authState == 1:
				# expect the line ": loggedIn cmdrID=..."
				# print "read %r in response to login" % (hubMsg,)
				msgDict = RO.ParseMsg.parseHubMsg(hubMsg)
				msgType = msgDict["type"]
				dataDict = msgDict["data"]
				cmdr = dataDict.get("cmdrID", (None,))[0]
				if (msgType != ":"):
					errMsg = dataDict.get("why", hubMsg)[0]
					raise RuntimeError, "login failed: %s" % (errMsg,)
				elif cmdr == None:
					raise RuntimeError, "cmdr missing; got: %r" % (hubMsg,)
				
				self.cmdr = cmdr
					
				# authorization succeeded; start normal reads
				self._authState = 2
				self._authDone("you are %r" % (self.cmdr,))
			elif self._authState == 2:
				sys.stderr.write("warning: lost message: %r", hubMsg)
			else:
				raise RuntimeError, "bug: unknown auth state %r" % (_authState,)		
		except Exception, e:
			self._authState = -1
			self.disconnect(False, str(e))


class NullConnection(HubConnection):
	"""Null connection for test purposes.
	Always acts as if it is connected (so one can write data),
	but prohibits explicit connection (maybe not necessary,
	but done to make it clear to users that it is a fake).
	
	cmdr = "TU01.me"
	"""
	def __init__ (self, *args, **kargs):
		HubConnection.__init__(self, *args, **kargs)
	
		self.desUsername = "me"
		self.cmdr = "TU01.me"
		self._state = Connected

	def connect(self):
		raise RuntimeError("NullConnection is always connected")
	
	def disconnect(self):
		raise RuntimeError("NullConnection cannot disconnect")

	def writeLine(self, str):
		sys.stdout.write("Null connection asked to write: %s\n" % (str,))


if __name__ == "__main__":
	import Tkinter
	import RO.Wdg
	root = Tkinter.Tk()

	host = 'hub35m.apo.nmsu.edu'
	port = 9877

	def readCallback (sock, astr):
		print "read: %r" % (astr,)

	def stateCallback (sock):
		state, stateStr, reason = sock.getFullState()
		if reason:
			print "%s: %s" % (stateStr, reason)
		else:
			print stateStr

	myConn = HubConnection(
		readCallback = readCallback,
		stateCallback = stateCallback,
	)

	def doConnect(host, port):
		class PasswordDialog(RO.Wdg.ModalDialogBase):
			def body(self, master):
		
				Tkinter.Label(master, text="Program ID:").grid(row=0, column=0)
				Tkinter.Label(master, text="Password  :").grid(row=1, column=0)
		
				self.nameEntry = Tkinter.Entry(master)
				self.nameEntry.grid(row=0, column=1)
				self.pwdEntry = Tkinter.Entry(master, show="*")
				self.pwdEntry.grid(row=1, column=1)
				return self.nameEntry # return the item that gets initial focus
		
			def setResult(self):
				self.result = (self.nameEntry.get(), self.pwdEntry.get())

		pwdDialog = PasswordDialog(root, title="%s" % (host))
		namePwd = pwdDialog.result
		if namePwd:
			progID, password = namePwd
			myConn.connect (
				progID = progID,
				password = password,
				username = "test",
				host = host,
				port = port,
			)


	Tkinter.Label(text="Send:").pack(side="left")
	sendText = Tkinter.Entry(root)
	sendText.pack(fill="x", expand="yes", side="left")
	sendText.focus_set()

	def sendCmd (evt):
		try:
			astr = sendText.get()
			sendText.delete(0,Tkinter.END)
			myConn.writeLine(astr)
		except (SystemExit, KeyboardInterrupt):
			raise
		except Exception, e:
			sys.stderr.write ("Could not extract or send: %s\nError: %s\n" % (astr, e))

	sendText.bind('<KeyPress-Return>', sendCmd)

	doConnect(host, port)

	root.mainloop()
