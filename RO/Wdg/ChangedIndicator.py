#!/usr/local/bin/python
"""An indicator that shows if one or more ROEntry widgets
have been set to nondefault values.

History:
2003-04-14 ROwen
2003-04-15 ROwen	Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-04-24 ROwen	Modified to use addCallback if available.
2003-07-07 ROwen	Modified to use RO.MathUtil.asList.
2003-11-07 ROwen	Modified to not create a StringVar unless it'll be used.
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-09-14 ROwen	Tweaked the imports.
"""
__all__ = ['ChangedIndicator']

import Tkinter
import RO.SeqUtil
import CtxMenu

class ChangedIndicator (Tkinter.Label, CtxMenu.CtxMenuMixin):
	def __init__(self,
		master,
		wdgOrSet,
		var = None,
		helpText = None,
		helpURL = None,
		clearMenu = "Clear",
		defMenu = "Default",
	**kargs):
		"""Creates a new ChangedIndicator.
		
		Inputs:
		- wdgOrSet	one or more ROEntry widgets
		- var		variable to contain current value ("" or "!")
		- helpText	text for hot help
		- helpURL	URL for longer help
		- all remaining keyword arguments are used to configure the Menu
		"""
		if var == None:
			var = Tkinter.StringVar()		
		self.__var = var
		self.__inputCont = None
		self.wdgSet = []
		self.helpText = helpText
		self.clearMenu = clearMenu
		self.defMenu = defMenu
		
		kargs.setdefault("width", 1)

		Tkinter.Label.__init__(self,
			master = master,
			textvariable = self.__var,
		**kargs)
		CtxMenu.CtxMenuMixin.__init__(self,
			helpURL = helpURL,
		)
		
		if wdgOrSet:
			self.addWdg(wdgOrSet)

	def addWdg(self, wdgOrSet):
		"""Adds a single ROEntry widget or set of widgets to control.
		Then sets the enabled state appropriately for all widgets.
		"""
		if wdgOrSet == None:
			return

		wdgSet = RO.SeqUtil.asList(wdgOrSet)
		
		self.wdgSet += wdgSet

		for wdg in wdgSet:
			try:
				wdg.addCallback(self._wdgChanged)
			except AttributeError:
				var = wdg.getVar()
				var.trace_variable('w', self._wdgChanged)
		
	def ctxConfigMenu(self, menu):
		if self.clearMenu:
			menu.add_command(label = self.clearMenu, command = self.clear)
		if self.defMenu:
			menu.add_command(label = self.defMenu, command = self.restoreDefault)
		return True
	
	def getVar(self):
		return self.__var
	
	def getString(self):
		return str(self.__var.get())
	
	def isChanged(self):
		return bool(self.__var.get())
	
	def setEnable(self, doEnable):
		"""Changes the enable state
		"""
		if doEnable:
			self.configure(state="normal")
		else:
			self.configure(state="disabled")
	
	def restoreDefault(self):
		"""Restores all controlled widgets to their default values.
		"""
		for wdg in self.wdgSet:
			wdg.restoreDefault()
		
	def clear(self):
		"""Restores all controlled widgets to their default values.
		"""
		for wdg in self.wdgSet:
			wdg.clear()
		
	def _wdgChanged(self, *args, **kargs):
		"""Called when any widget is changed"""
		isChanged = False
		for wdg in self.wdgSet:
			if wdg.getDefault() != wdg.getString():
				isChanged = True
		if isChanged:
			self.__var.set("!")
		else:
			self.__var.set("")
