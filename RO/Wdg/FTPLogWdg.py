#!/usr/local/bin/python
"""FTP download with Tkinter-based progress reporting

Downloads files given the url and destination path.
Reports progress and allows cancellation.

Known problems:
- The bottom state display label sometimes overlaps the details panel. I've not found a solution. Using the setgrid option would help, but only if the grid could be made an exact multiple if the line height (tricky when the font size can change). Gridding the displaly panel first does not help. I've considered using tags to insert the state information, but there doesn't seem to be any way to set a tab stop in ens, ems or "avarage width characters", just inches and other such units. What's really wanted is a multi-column list widget. Saving that, I think it best to live with the current cosmetic problem.
  
History:
2003-09-22 ROwen
2003-09-30 ROwen	Added helpURL; bug fix: index error if select and no entries.
2003-10-30 ROwen	Added auto-scrolling.
2004-05-03 ROwen	Bug fixes:
					- Abort button not shown while connecting.
					- Aborting connections were counted as running
					  and thus blocked new connections from starting.
2004-05-04 ROwen	Improved the test code.
2004-08-11 ROwen	Use modified RO.Wdg state constants with st_ prefix.
					Define __all__ to restrict import.
2004-09-03 ROwen	Modified for RO.Wdg.st_... -> RO.Constants.st_...
"""
__all__ = ['FTPLogWdg']

import os
import urllib
import Bindings
import Tkinter
import RO.AddCallback
import RO.Constants
import RO.MathUtil
import RO.Comm.GetFile as GetFile
import RO.Wdg
import CtxMenu

class FTPLogWdg(Tkinter.Frame):
	"""A widget to initiate file get via ftp, to display the status
	of the transfer and to allow users to abort the transfer.
	
	Inputs:
	- master: master widget
	- maxTrransfers: maximum number of simultaneous transfers; additional transfers are queued
	- maxLines: the maximum number of lines to display in the log window. Extra lines are removed (unless a queued or running transfer would be removed).
	- helpURL: the URL of a help page; it may include anchors for:
	  - "LogDisplay" for the log display area
	  - "From" for the From field of the details display
	  - "To" for the To field of the details display
	  - "State" for the State field of the details display
	  - "Abort" for the abort button in the details display
	"""
	def __init__(self,
		master,
		maxTransfers = 1,
		maxLines = 500,
		helpURL = None,
	**kargs):
		Tkinter.Frame.__init__(self, master = master, **kargs)
		
		self.maxLines = maxLines
		self.maxTransfers = maxTransfers
		self.selFTPGet = None # selected getter, for displaying details; None if none
		
		self.dispList = []	# list of displayed ftpGets
		self.getQueue = []	# list of unfinished (ftpGet, stateLabel) pairs
		
		self.yscroll = Tkinter.Scrollbar (
			master = self,
			orient = "vertical",
		)
		self.text = Tkinter.Text (
			master = self,
			yscrollcommand = self.yscroll.set,
			wrap = "none",
			tabs = (8,),
			height = 4,
			width = 50,
		)
		self.yscroll.configure(command=self.text.yview)
		self.text.grid(row=0, column=0, sticky="nsew")
		self.yscroll.grid(row=0, column=1, sticky="ns")
		Bindings.makeReadOnly(self.text)
		if helpURL:
			CtxMenu.addCtxMenu(
				wdg = self.text,
				helpURL = helpURL + "#LogDisplay",
			)
		
		self.rowconfigure(0, weight=1)
		self.columnconfigure(0, weight=1)
		
		detFrame = Tkinter.Frame(self)
			
		gr = RO.Wdg.Gridder(detFrame, sticky="ew")
		
		self.fromWdg = RO.Wdg.StrEntry(
			master = detFrame,
			readOnly = True,
			helpURL = helpURL and helpURL + "#From",
			borderwidth = 0,
		)
		gr.gridWdg("From", self.fromWdg, colSpan=3)

		self.toWdg = RO.Wdg.StrEntry(
			master = detFrame,
			readOnly = True,
			helpURL = helpURL and helpURL + "#To",
			borderwidth = 0,
		)
		gr.gridWdg("To", self.toWdg, colSpan=2)
		
		self.stateWdg = RO.Wdg.StrEntry(
			master = detFrame,
			readOnly = True,
			helpURL = helpURL and helpURL + "#State",
			borderwidth = 0,
		)
		self.abortWdg = RO.Wdg.Button(
			master = detFrame,
			text = "Abort",
			command = self._abort,
			helpURL = helpURL and helpURL + "#Abort",
		)
		gr.gridWdg("State", self.stateWdg, colSpan=2)
		
		self.abortWdg.grid(row=1, column=2, rowspan=2, sticky="s")
		
		detFrame.columnconfigure(1, weight=1)
		
		detFrame.grid(row=1, column=0, columnspan=2, sticky="ew")
		
		self.text.bind("<Button-1>", self._selectEvt)
		self.text.bind("<B1-Motion>", self._selectEvt)
		
		self._updAllStatus()
	
	def getFile(self,
		fromURL,
		toPath,
		overwrite = False,
		createDir = True,
		dispURL = None,
	):
		"""Get a file
	
		Inputs:
		- fromURL: source URL
		- toPath: full path of destination file
		- overwrite: if True, overwrites the destination file if it exists;
			otherwise raises ValueError
		- createDir: if True, creates any required directories;
			otherwise raises ValueError
		- dispURL: url to display; if omitted, defaults to fromURL
		"""
#		print "getFile(%r, %r, %r, %r, %r)" % (fromURL, toPath, overwrite, createDir, dispURL)
		stateLabel = RO.Wdg.StrLabel(self, anchor="w", width=GetFile.StateStrMaxLen)
		
		ftpGet = GetFile.GetFile(
			fromURL = fromURL,
			toPath = toPath,
			overwrite = overwrite,
			createDir = createDir,
			startNow = False,
			dispURL = dispURL,
		)

		# if scrolled to the end, set doAutoScroll true
		scrollPos = self.yscroll.get()
		doAutoScroll = scrollPos[1] == 1.0 or scrollPos[0] == scrollPos[1]

		# display item and append to list
		# (in that order so we can test for an empty list before displaying)
		if self.dispList:
			# at least one item is shown
			self.text.insert("end", "\n")
		self.text.window_create("end", window=stateLabel)
		self.text.insert("end", ftpGet.dispURL)
		self.dispList.append(ftpGet)
		
		# append ftpGet to the queue
		self.getQueue.append((ftpGet, stateLabel))
		
		if not self.selFTPGet:
			self._selectInd(-1)
		
		# purge old display items if necessary
		while self.maxLines < len(self.dispList):
			if self.dispList[0].isDone():
				if self.selFTPGet == self.dispList[0]:
					self._selectInd(-1)
				del(self.dispList[0])
				self.text.delete("1.0", "1.0 lineend")
			else:
				break

		# auto scroll
		if doAutoScroll:
			self.text.see("end")
	
	def _abort(self):
		"""Abort the currently selected transaction (if any).
		"""
		if self.selFTPGet:
			self.selFTPGet.abort()
	
	def _selectEvt(self, evt):
		"""Determine the line currently pointed to by the mouse
		and show details for that transaction.
		Intended to handle the mouseDown event.
		"""
		self.text.tag_remove("sel", "1.0", "end")
		x, y = evt.x, evt.y
		mousePosStr = "@%d,%d" % (x, y)
		indStr = self.text.index(mousePosStr)
		ind = int(indStr.split(".")[0]) - 1
		self._selectInd(ind)
		return "break"
	
	def _selectInd(self, ind):
		"""Display details for the ftpGet at self.dispList[ind]
		and selects the associated line in the displayed list.
		If ind == None then displays no info and deselects all.
		"""
		try:
			self.selFTPGet = self.dispList[ind]
			if ind < 0:
				lineNum = len(self.dispList) + 1 + ind
			else:
				lineNum = ind + 1
			self.text.tag_add('sel', '%s.0' % lineNum, '%s.0 lineend' % lineNum)
		except IndexError:
			self.selFTPGet = None
			self.text.tag_remove('sel', '1.0', 'end')
		self._updDetailStatus()
	
	def _updAllStatus(self):
		"""Update status for running transfers
		and start new transfers if there is room
		"""
		newGetQueue = list()
		nRunning = 0
		for ftpGet, stateLabel in self.getQueue:
			if not ftpGet.isDone():
				newGetQueue.append((ftpGet, stateLabel))
				state = ftpGet.getState()
				if state == GetFile.Queued:
					if nRunning < self.maxTransfers:
						ftpGet.start()
						nRunning += 1
				elif state in (GetFile.Running, GetFile.Connecting):
					nRunning += 1
			self._updOneStatus(ftpGet, stateLabel)
		self.getQueue = newGetQueue
	
		self._updDetailStatus()
		 
		self.after(200, self._updAllStatus)
		
	def _updOneStatus(self, ftpGet, stateLabel):
		"""Update the status of one transfer"""
		state = ftpGet.getState()
		if state == GetFile.Running:
			if ftpGet.getTotBytes():
				pctDone = 100 * ftpGet.getReadBytes() / ftpGet.getTotBytes()
				stateLabel["text"] = "%3d %%" % pctDone
			else:
				kbRead = ftpGet.getReadBytes() / 1024
				stateLabel["text"] = "%d kB" % kbRead
		else:
			# display text description of state
			stateStr = ftpGet.getStateStr(state)
			if state == GetFile.Failed:
				dispState = RO.Constants.st_Error
			else:
				dispState = RO.Constants.st_Normal
			stateLabel.set(stateStr, state=dispState)
	
	def _updDetailStatus(self):
		"""Update the detail status for self.selFTPGet"""
		if not self.selFTPGet:
			self.fromWdg.set("")
			self.toWdg.set("")
			self.stateWdg.set("")
			if self.abortWdg.winfo_ismapped():
				self.abortWdg.grid_remove()
			return

		ftpGet = self.selFTPGet
		currState = ftpGet.getState()
		
		# show or hide abort button, appropriately
		if currState >= GetFile.Running:
			if not self.abortWdg.winfo_ismapped():
				self.abortWdg.grid()
		else:
			if self.abortWdg.winfo_ismapped():
				self.abortWdg.grid_remove()

		if currState == GetFile.Running:
			readBytes = ftpGet.getReadBytes()
			totBytes = ftpGet.getTotBytes()
			if totBytes:
				stateStr = "read %s of %s bytes" % (readBytes, totBytes)
			else:
				stateStr = "read %s bytes" % (readBytes,)
		else:
			if currState == GetFile.Failed:
				stateStr = "Failed: %s" % (ftpGet.getException())
			else:
				stateStr = ftpGet.getStateStr()

		self.stateWdg.set(stateStr)
		self.fromWdg.set(ftpGet.dispURL)
		self.toWdg.set(ftpGet.toPath)


if __name__ == "__main__":
	from PythonTk import *
	root = PythonTk()

	row = 0
	
	testFrame = FTPLogWdg (
		master=root,
	)
	testFrame.grid(row=row, column=0, columnspan=2, sticky="nsew")
	row += 1

	overwriteVar = Tkinter.BooleanVar()
	overwriteVar.set(True)
	overwriteWdg = Tkinter.Checkbutton(
		master=root,
		text="Overwrite",
		variable=overwriteVar,
	)
	overwriteWdg.grid(row=row, column=1, sticky="w")
	row += 1

	Tkinter.Label(root, text="ToPath:").grid(row=row, column=0, sticky="e")
	toPathWdg = Tkinter.Entry(root)
	toPathWdg.insert(0, "tempfile")
	toPathWdg.grid(row=row, column=1, sticky="ew")
	row += 1
	
	Tkinter.Label(root, text="FromURL:").grid(row=row, column=0, sticky="e")
	fromURLWdg = Tkinter.Entry(root)
	fromURLWdg.grid(row=row, column=1, sticky="ew")
	row += 1

	
	def getFile(evt):
		overwrite = overwriteVar.get()
		toPath = toPathWdg.get()
		fromURL = fromURLWdg.get()
		testFrame.getFile(fromURL=fromURL, toPath=toPath, overwrite=overwrite)
		
	fromURLWdg.bind("<Return>", getFile)
	
	root.rowconfigure(0, weight=1)
	root.columnconfigure(1, weight=1)

	root.mainloop()
