#!/usr/local/bin/python
"""Users window (display a list of users).

2003-12-06 ROwen
2003-12-17 ROwen	Added addWindow and renamed to UsersWindow.py.
2004-05-18 ROwen	Stopped obtaining TUI model in addWindow; it was ignored.
2004-07-22 ROwen	Modified to use TUI.HubModel.
2004-08-11 ROwen	Modified for updated RO.Wdg.CtxMenu.
2004-08-25 ROwen	Modified to use new hubModel.users keyvar.
2004-09-14 ROwen	Stopped importing TUI.TUIModel since it wasn't being used.
2004-11-15 ROwen	Added code to detect and report mal-formed usernames
					as a result of mystery errors appearing in the console.
"""
import time
import Tkinter
import RO.KeyVariable
import RO.StringUtil
import RO.Wdg
import TUI.HubModel

_HelpPage = "TUIMenu/UsersWin.html"

def addWindow(tlSet):
	tlSet.createToplevel(
		name = "TUI.Users",
		defGeom = "170x170+0+722",
		visible = False,
		resizable = True,
		wdgFunc = UsersWdg,
	)

class UsersWdg (Tkinter.Frame):
	"""Display the current users and those recently logged out.
	
	Inputs:
	- master	parent widget
	- retainSec	time to retain information about logged out users (sec)
	- height	default height of text widget
	- width	default width of text widget
	- other keyword arguments are used for the frame
	"""
	def __init__ (self,
		master=None,
		retainSec=300,
		height = 10,
		width = 20,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
		
		hubModel = TUI.HubModel.getModel()
		
		# entries are users
		self._userList = []
		# entries are (user, time deleted); time is from time.time()
		self._delUserTimeList = []
		# time to show deleted users
		self._retainSec = retainSec
		
		self.afterID = None
		
				
		self.yscroll = Tkinter.Scrollbar (
			master = self,
			orient = "vertical",
		)
		self.text = Tkinter.Text (
			master = self,
			yscrollcommand = self.yscroll.set,
			wrap = "word",
			height = height,
			width = width,
		)
		self.yscroll.configure(command=self.text.yview)
		self.text.grid(row=0, column=0, sticky="nsew")
		self.yscroll.grid(row=0, column=1, sticky="ns")
		RO.Wdg.Bindings.makeReadOnly(self.text)
		RO.Wdg.addCtxMenu(
			wdg = self.text,
			helpURL = _HelpPage,
		)

		
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		
		self.text.tag_configure("del", overstrike=True)

		hubModel.users.addCallback(self.updUsers)

	def updUsers(self, userList, isCurrent=True, keyVar=None):
		if not isCurrent:
			# set background to pink, then return
			return

		# remove users from deleted list if they appear in the new list
		self._delUserTimeList = [userTime for userTime in self._delUserTimeList
			if userTime[0] in self._userList]

		# add newly deleted users to deleted list
		for user in self._userList:
			if user not in userList:
				self._delUserTimeList.append((user, time.time()))
		
		# save commander list
		self._userList = userList

		self.updDisplay()
	
	def updDisplay(self):
		"""Display current data.
		"""
		if self.afterID:
			self.afterID = self.after_cancel(self.afterID)

		# remove users from deleted list if they've been around for too long
		maxDelTime = time.time() - self._retainSec
		self._delUserTimeList = [userTime for userTime in self._delUserTimeList
			if userTime[1] > maxDelTime]

		userTagList = [(user, "curr") for user in self._userList]
		if self._delUserTimeList:
			userTagList += [(userTime[0], "del") for userTime in self._delUserTimeList]
		userTagList.sort()
		self.text.delete("1.0", "end")
		for user, tag in userTagList:
			try:
				prog, user = user.split(".", 1)
			except ValueError:
				print "UsersWindow warning: no . in %r; userTagList=%r" % (user, userTagList)
				prog = user
				user = "???"
			userStr = "%s\t%s\n" % (prog, user)
			self.text.insert("end", userStr, tag)
		
		if self._delUserTimeList:
			self.afterID = self.after(1000, self.updDisplay)

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = UsersWdg (root, retainSec = 5)
	testFrame.pack(expand=True, fill="both")
	
	dataDicts = (
		{"Users": ("CL01.CPL","TU01.ROwen","TU01.ROwen-2")},
		{"Users": ("CL01.CPL","TU01.ROwen")},
		{"Users": ("CL01.CPL","TU01.ROwen","TU01.ROwen-2")},
		{"Users": ("CL01.CPL","TU01.ROwen-2")},
	)

	delayMS = 1000
	dataIter = iter(dataDicts)
	def dispatchNext():
		try:
			newDataDict = dataIter.next()
		except StopIteration:
			return
		
		msgDict = {"cmdr":".hub", "cmdID":11, "actor":"hub", "type":"i", "data":newDataDict}
		kd.dispatch(msgDict)
		root.after(delayMS, dispatchNext)
	dispatchNext() 

	root.mainloop()
