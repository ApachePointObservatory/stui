#!/usr/local/bin/python
"""Widgets for selecting files and directories.

History:
2006-03-07 ROwen
"""
import os
import tkFileDialog
import Tkinter
import RO.AddCallback
import RO.Constants
import CtxMenu
from SeverityMixin import SeverityActiveMixin

__all__ = ["DirWdg", "FileWdg"]

class BasePathWdg (Tkinter.Button, RO.AddCallback.BaseMixin, CtxMenu.CtxMenuMixin,
	SeverityActiveMixin):
	def __init__(self,
		master,
		helpText = None,
		helpURL = None,
		maxChar=30,
		callFunc = None,
		severity = RO.Constants.sevNormal,
	**kargs):
		"""Creates a new Button.
		
		Inputs:
		- helpText	text for hot help
		- helpURL	URL for longer help
		- maxChar: maximum # of characters of file path to display
		- callFunc	callback function; the function receives one argument: self.
					It is called whenever the value changes (manually or via
					the associated variable being set).
		- severity	initial severity; one of RO.Constants.sevNormal, sevWarning or sevError
		- all remaining keyword arguments are used to configure the Tkinter Button;
		  command is supported, for the sake of conformity, but callFunc is preferred.
		"""
		self.helpText = helpText
		self.defPath = None
		self.path = None
		
		self.maxChar = max(3, int(maxChar))
		self.leftChar = 0
		self.rightChar = (self.maxChar - self.leftChar) - 1

		Tkinter.Button.__init__(self,
			master = master,
		**kargs)
		
		RO.AddCallback.BaseMixin.__init__(self, callFunc, False)
		
		CtxMenu.CtxMenuMixin.__init__(self,
			helpURL = helpURL,
		)
		SeverityActiveMixin.__init__(self, severity)
	
	def setEnable(self, doEnable):
		if doEnable:
			self["state"] = "normal"
		else:
			self["state"] = "disabled"
	
	def getEnable(self):
		return self["state"] == "normal"
		
	def setPath(self, path):
		if path == None:
			dispStr = ""
		else:
			path = os.path.abspath(path)
			if len(path) > self.maxChar:
				dispStr = "".join((
					path[0:self.leftChar],
					u"\N{HORIZONTAL ELLIPSIS}",
					path[-self.rightChar:],
				))
			else:
				dispStr = path
		self.path = path
		self["text"] = dispStr
		self._doCallbacks()
	
	def getPath(self):
		return self.path

	def ctxConfigMenu(self, menu):
		"""Configure the contextual menu.
		Called just before the menu is posted.
		"""
		if not self.getEnable():
			return True
		
		if self.path == None:
			state = "disabled"
		else:
			state = "normal"
		
		if self.path:
			copyLabel = " ".join(("Copy", self.path))
		else:
			copyLabel = "Copy"
		menu.add_command(
			label = copyLabel,
			command = self._copyToClip,
			state = state,
		)
		return True
	
	def _copyToClip(self):
		"""Copy the current path to the clipboard
		"""
		if self.path != None:
			self.clipboard_clear()
			self.clipboard_append(self.path)

class DirWdg(BasePathWdg):
	"""A widget showing a directory; push to pick another directory.
	
	Inputs:
	- callFunc: function to call when a file is chosen
	- fileTypes: sequence of (label, pattern) tuples;
		use * as a pattern to allow all files of that labelled type;
		omit altogether to allow all files
	- defPath: initial path
	"""
	def __init__(self,
		master,
		callFunc=None,
		maxChar=30,
		fileTypes=None,
		defPath=None,
	**kargs):
		kargs["command"] = self._doChoose
		BasePathWdg.__init__(self, master, **kargs)
		
		self.fileTypes = fileTypes

		if defPath and not os.path.exists(defPath):
			defPath = None
		self.defPath = defPath
		self.setPath(defPath)
		
		if callFunc:
			self.addCallback(callFunc, False)

	def _doChoose(self):
		"""Put up a dialog to choose a new file.
		"""
		if self.path != None:
			startDir = self.path
		else:
			startDir = self.defPath
			
		kargs = {}
		if self.fileTypes:
			kargs["filetypes"] = self.fileTypes
		newPath = tkFileDialog.askdirectory(
			initialdir = startDir,
			mustexist = True,
			title = self.helpText,
		**kargs)
		if newPath:
			# handle case of newPath being a weird Tcl object
			newPath = RO.CnvUtil.asStr(newPath)
			self.setPath(newPath)
	
			
class FileWdg(BasePathWdg):
	"""A widget showing a file; push to pick another file.
	
	Inputs:
	- callFunc: function to call when a file is chosen
	- fileTypes: sequence of (label, pattern) tuples;
		use * as a pattern to allow all files of that labelled type;
		omit altogether to allow all files
	- defPath: initial path; if a file, it is displayed,
		if a dir, used for starting location for file picker dialog box
	"""
	def __init__(self,
		master,
		callFunc=None,
		maxChar=30,
		fileTypes=None,
		defPath=None,
	**kargs):
		kargs["command"] = self._doChoose
		BasePathWdg.__init__(self, master, **kargs)
		
		self.fileTypes = fileTypes

		if defPath and not os.path.exists(defPath):
			defPath = None
		self.defPath = defPath
		self.path = None

		if defPath and os.path.isfile(defPath):
			self.setPath(defPath)
		
		if callFunc:
			self.addCallback(callFunc, False)

	def _doChoose(self):
		"""Put up a dialog to choose a new file.
		"""
		if self.path != None:
			startPath = self.path
		else:
			startPath = self.defPath

		startDir = startFile = None
		if startPath:
			if os.path.isfile(self.defPath):
				startDir, startFile = os.path.split(self.path)
			elif os.path.isdir(self.defPath):
				startDir = self.defPath

		if startDir != None:
			startDir = os.path.abspath(startDir)
			
		kargs = {}
		if self.fileTypes:
			kargs["filetypes"] = self.fileTypes
		newPath = tkFileDialog.askopenfilename(
			initialdir = startDir,
			initialfile = startFile,
			title = self.helpText,
		**kargs)
		if newPath:
			# handle case of newPath being a weird Tcl object
			newPath = RO.CnvUtil.asStr(newPath)
			self.setPath(newPath)


if __name__ == "__main__":
	from RO.Wdg.PythonTk import PythonTk
	root = PythonTk()
	
	modFile = __file__
	modDir = os.path.split(__file__)[0]
	
	def wdgFunc(wdg):
		print "%s set to %s" % (wdg.__class__.__name__, wdg.getPath())

	f1 = FileWdg(root, callFunc=wdgFunc)
	f1.pack()
	
	f2 = FileWdg(root, callFunc=wdgFunc, defPath=modDir)
	f2.pack()
	
	f3 = FileWdg(root, callFunc=wdgFunc, defPath=modFile)
	f3.pack()

	d1 = DirWdg(root, callFunc=wdgFunc)
	d1.pack()
	
	d2 = DirWdg(root, callFunc=wdgFunc, defPath=modDir)
	d2.pack()
	
	root.mainloop()
