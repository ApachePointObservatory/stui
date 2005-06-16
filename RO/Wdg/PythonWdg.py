#!/usr/local/bin/python
"""An interactive Python session and simple script file editor/runner
that may be used from Tkinter scripts. Before running a script,x=Tk() is replaced with x=Toplevel() and mainloop() is eliminated. Hence some Tk scripts
may be safely run. Presumably there are limitations. I suspect that mucking about
with menus might cause some problems, but we'll see.

Adapted from John Grayson's dgbwindow.py

To Do:
- Add status bar and help strings

History:
1-1 ROwen  Changed ScriptWindow to a subclass of Toplevel.
	First verision with history.
2002-04-29 ROwen	Renamed ScriptFrame to ScriptWdg for consistency with other code.
2002-12-20 ROwen	In ScriptWdg.__init__: removed callback, as it was ignored;
					changed bd to borderwidth, for clarity;
					fixed bug in save: filename not being handled properly;
					modified save to write entire script at once.
2003-04-05 ROwen	ScriptWindow fix: was mishandling keyword arguments.
					ScriptWdg changes:
					- Added universal newline support (Python 2.3 or later).
					- Changed arg filename to filePath.
					- Modified to convert values from tkFileDialog dialogs to strings,
					  in case they are modern Tkinter Tcl objects.
					- File handling put in try/finally block to assure file is closed.
2004-05-18 ROwen	Bug fix: ScriptWdg.run arguments globals and locals shadowed builtins.
					Stopped importing sys and string since they weren't used.
2004-06-22 ROwen	Renamed ScriptWdg->PythonWdg to avoid collisions with new
					RO.ScriptRunner and associated RO.ScriptWdg.
					Deleted ScriptWindow since it was not being used.
2004-08-10 ROwen	Added helpURL argument.
					Modified to use an RO.Wdg.Text widget.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-09-14 ROwen	Bug fix: output file close error (fd.close inst. of fd.close()).
2005-06-16 ROwen	Changed is None to == None to appease pychecker and myself.
"""
__all__ = ['PythonWdg']

import os
import re
import Text
import Tkinter
import tkFileDialog
import RO.CnvUtil
import RO.OS

class PythonWdg(Tkinter.Frame):
	"""A frame containing text window into which you may enter Python code.
	
	Inputs:
	- master	master Tk widget -- typically a frame or window
	- filePath	if specified, the widget starts out containing that file
	- helpURL	URL for on-line help
	"""
	def __init__ (self,
		master = None,
		filePath = None,
		helpURL = None,
	**kargs):
		Tkinter.Frame.__init__(self, master, **kargs)

		self.master=master
		self.filePath = filePath

		self.inputWdg = Text.Text(
			master = self,
			width = 60,
			height = 10,
			helpURL = helpURL
		)
		self.inputWdg.grid(row=0, column=0, sticky=Tkinter.NSEW)
		self.inputWdg.bind("<Key-Escape>", self.run)

		self.scroll = Tkinter.Scrollbar(self, command=self.inputWdg.yview)
		self.inputWdg.configure(yscrollcommand=self.scroll.set)
		self.scroll.grid(row=0, column=1, sticky=Tkinter.NS)

		if self.filePath:
			fd = RO.OS.openUniv(self.filePath)
			try:
				self.inputWdg.delete(1.0, Tkinter.END)
				for line in fd.readlines():
					self.inputWdg.insert(Tkinter.END, line)
			finally:
				fd.close()

		self.cmdbar = Tkinter.Frame(self, borderwidth=2, relief=Tkinter.SUNKEN)
		self.open = Tkinter.Button(self.cmdbar, text='Open...', command=self.open)
		self.open.pack(side=Tkinter.LEFT, expand=0, padx=3, pady=3)
		self.save = Tkinter.Button(self.cmdbar, text='Save...', command=self.save)
		self.save.pack(side=Tkinter.LEFT, expand=0, padx=3, pady=3)
		self.clr  = Tkinter.Button(self.cmdbar, text='Clear', command=self.clr)
		self.clr.pack(side=Tkinter.LEFT, expand=0, padx=3, pady=3)
		self.run  =Tkinter.Button(self.cmdbar, text='Run', command=self.run)
		self.run.pack(side=Tkinter.RIGHT, expand=0, padx=3, pady=3)
		self.cmdbar.grid(row=1, column=0, columnspan=2, sticky=Tkinter.EW)

		self.grid_rowconfigure(0, weight=1)
		self.grid_columnconfigure(0, weight=1)
		self.inputWdg.focus_set()

	def run(self, evt=None, globs=None, locs=None):
		script = self.inputWdg.get(1.0, Tkinter.END)

		# replace x = Tk() with x = Toplevel()
		tkPat = re.compile(r"^(.*=\s*)(:?ROStd)?Tk\(\)(.*)$", re.MULTILINE)
		script = tkPat.sub(r"\1Toplevel()\2", script)

		# strip mainloop()
		rootPat = re.compile(r"^.*mainloop\(\).*$", re.MULTILINE)
		script = rootPat.sub("", script)

		if globs == None:
			import __main__
			globs = __main__.__dict__
		if locs == None:
			locs = globs
		exec script in globs, locs

	def open(self):
		filePath = tkFileDialog.askopenfilename()
		if not filePath:
			return
		filePath = RO.CnvUtil.asStr(filePath)
		top = Tkinter.Toplevel(self.master, )
		top.title(os.path.basename(filePath))
		frame = PythonWdg(top, filePath=filePath)
		frame.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)

	def save(self, forPrt=None):
		script = self.inputWdg.get(1.0, Tkinter.END)
		if not script:
			return
		if forPrt:
			filePath = 'prt.tmp'
		else:
			filePath = tkFileDialog.asksaveasfilename(initialfile=self.filePath)
			if not filePath:
				return
			self.filePath = RO.CnvUtil.asStr(filePath)
		fd = open(filePath, 'w')
		try:
			fd.write(script)
		finally:
			fd.close()

	def clr(self):
		self.inputWdg.delete(1.0, "end")


if __name__ == '__main__':
	root = Tkinter.Tk()
	
	testFrame = PythonWdg(root)
	root.geometry("+0+450")
	testFrame.pack(expand=Tkinter.YES, fill=Tkinter.BOTH)

	root.mainloop()
