#!/usr/local/bin/python
"""Variant of Tkinter.Text that includes a few extra features, including:
- read-only support (can still copy data)
- contextual menu with cut/copy/paste and URL-based help
- help text (in conjunction with StatusBar)
  
History:
2004-08-11 ROwen
2004-09-14 ROwen	Added support for isCurrent and auto-colored state tags.
					Stopped importing unused modules os, re.
2005-01-05 ROwen	Changed _statePrefDict to _sevPrefDict.
"""
__all__ = ['Text']

import Tkinter
import RO.CnvUtil
import RO.StringUtil
import RO.MathUtil
import Bindings
import CtxMenu
import WdgPrefs

class Text (Tkinter.Text, CtxMenu.CtxMenuMixin):
	"""Text widget

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- helpText	a string that describes the widget
	- helpURL	URL for on-line help
	- readOnly	set True if you want to prevent the user from changing the text
				the user will still be able to copy the text
				and the widget can still be updated via set, etc.
				note that readOnly prevents any clear/default/etc menu items.
	- isCurrent	sets isCurrent and thus the background color
	- useStateTags	if True, tags for RO.Constant.sevNormal, etc. are set up with appropriate colors.
	- any additional keyword arguments are used to configure the widget;
				the default width is 8
				text and textvariable are silently ignored (use var instead of textvariable)
	"""
	def __init__ (self,
		master,
		helpText = None,
		helpURL = None,
		readOnly = False,
		isCurrent = True,
		useStateTags = False,
	**kargs):
		self.helpText = helpText
		self._readOnly = readOnly
		self._isCurrent = bool(isCurrent)
		
		Tkinter.Text.__init__(self, master, **kargs)

		CtxMenu.CtxMenuMixin.__init__(self, helpURL = helpURL)

		self._prefDict = WdgPrefs.getWdgPrefDict()
		self._sevPrefDict = WdgPrefs.getSevPrefDict()
		
		if self._readOnly:
			Bindings.makeReadOnly(self)
			self["takefocus"] = False

		# set up automatic update for bad background color pref
		self._prefDict["Bad Background"].addCallback(self._updateBGColor, callNow=False)
		
		if not self._isCurrent:
			self._updateBGColor()
		
		if useStateTags:
			for severity, pref in self._sevPrefDict.iteritems():
				if severity == RO.Constants.sevNormal:
					# normal foreground color is already automatically updated
					continue
				pref.addCallback(self._updateStateTagColors, callNow=False)

	def clear(self):
		if not self._readOnly:
			self.event_generate("<<Clear>>")

	def ctxConfigMenu(self, menu):
		"""Configure the contextual menu.
		Called just before the menu is posted.
		"""
		stateDict = {
			True:"normal",
			False:"disabled",
		}
		dataPresent = (self.get("1.0", "3.0") not in ("\n", ""))
		try:
			selPresent = (self.get("sel.first", "sel.last") != "")
		except Tkinter.TclError:
			selPresent = False
		if self._readOnly or not self.getEnable():
			menu.add_command(
				label = "Copy",
				command = self.copy,
				state = stateDict[selPresent],
			)
			return True

		try:
			clipPresent = (self.selection_get(selection="CLIPBOARD") != "")
		except Tkinter.TclError:
			clipPresent = False

		menu.add_command(
			label = "Clear",
			command = self.clear,
			state = stateDict[selPresent],
		)
		menu.add_command(
			label = "Cut",
			command = self.cut,
			state = stateDict[selPresent],
		)
		menu.add_command(
			label = "Copy",
			command = self.copy,
			state = stateDict[selPresent],
		)
		menu.add_command(
			label = "Paste",
			command = self.paste,
			state = stateDict[clipPresent],
		)
		menu.add_separator()
		menu.add_command(
			label = "Select All",
			command = self.selectAll,
			state = stateDict[dataPresent],
		)
				
		return True
	
	def cut(self):
		"""Cut the selection to the clipboard.
		"""
		if not self._readOnly:
			self.event_generate("<<Cut>>")
	
	def copy(self):
		"""Copy the selection to the clipboard.
		"""
		self.event_generate("<<Copy>>")
	
	def paste(self):
		"""Replace the selection with the contents of the clipboard.
		Works better than the default paste IMHO.
		"""
		if not self._readOnly:
			self.event_generate("<<Paste>>")
	
	def getEnable(self):
		"""Returns False if the state is disabled,
		True otherwise (state is normal or active)
		"""
		return self["state"] != Tkinter.DISABLED
	
	def getIsCurrent(self):
		"""Return True if value is current, False otherwise.
		"""
		return self._isCurrent

	def selectAll(self):
		"""Select all text in the Entry.
		Has no effect if there is no text.
		"""
		self.tag_add("sel", "0.0", "end")

	def setEnable(self, doEnable):
		"""Changes the enable state.
		"""
		if doEnable:
			self.configure(state="normal")
		else:
			self.configure(state="disabled")
	
	def setIsCurrent(self, isCurrent):
		"""Set isCurrent and thus the background color.
		"""
		isCurrent = bool(isCurrent)
		if self._isCurrent != isCurrent:
			self._isCurrent = isCurrent
			self._updateBGColor()

	def _updateBGColor(self, *args):
		"""Update the background color based on self._isCurrent.
		*args allows this to be used as a callback.
		"""
		if self._isCurrent:
			self.configure(background=self._prefDict["Background Color"].getValue())
		else:
			self.configure(background=self._prefDict["Bad Background"].getValue())

	def _updateStateTagColors(self, *args):
		"""Update the colors for tags RO.Constants.sevNormal, sevWarning and sevError.
		Ignored unless useStateTags True at instantiation.
		"""
		for state in (RO.Constants.sevWarning, RO.Constants.sevError):
			self.tag_configure(state, color = self._sevPrefDict[state].getValue())


if __name__ == "__main__":
	from RO.Wdg.PythonTk import PythonTk
	import StatusBar
	root = PythonTk()

	text1 = Text(root, "text widget", height=5, width=20)
	text2 = Text(root, readOnly=True, helpText = "read only text widget",  height=5, width=20)	
	statusBar = StatusBar.StatusBar(root)
	text1.grid(row=0, column=0, sticky="nsew")
	text2.grid(row=1, column=0, sticky="nsew")
	statusBar.grid(row=2, column=0, sticky="ew")
	root.grid_rowconfigure(0, weight=1)
	root.grid_rowconfigure(1, weight=1)
	root.grid_columnconfigure(0, weight=1)
	
	text1.insert("end", "this is an editable text widget\n")
	text2.insert("end", "this is a read-only text widget\n")

	root.mainloop()
