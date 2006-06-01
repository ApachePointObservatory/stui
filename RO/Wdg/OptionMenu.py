#!/usr/local/bin/python
"""A variant of Tkinter.OptionMenu that adds help, default handling,
the ability to change menu items and the ability to configure the menu.
OptionMenu is essentially an RO.Wdg.Entry widget (though I don't promise
that *all* methods are implemented).

Note: I had to go mucking with internals, so some of this code is based on
Tkinter's implementation of OptionMenu.

To do:
- Color menu items in autoIsCurrent mode.

Warning: as of Tk 8.4.8, MacOS X has poor visual support for background color
(isCurrent) and no support for foreground color (state) for OptionMenu
(and MenuButtons in general).

History:
2002-11-15 ROwen
2002-11-25 ROwen	Added helpURL support.
2003-03-10 ROwen	Overhauled to add support for changing the menu on the fly;
					added callFunc argument.
2003-03-12 ROwen	Added defIfDisabled
2003-03-14 ROwen	Added addCallback
2003-03-19 ROwen	Added doCheck input to setDefault
2003-03-31 ROwen	Changed 0 to False.
2003-04-03 ROwen	Added preliminary implementation of ConfigMenu;
					modified so default defValue is the first item.
2003-04-14 ROwen	Added defMenu input.
2003-04-15 ROwen	Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-04-17 ROwen	Modified to not set defValue = items[0];
					removed hack that set "" means restore default.
2003-04-24 ROwen	Modified to call callback functions
					when setDefault called.
2003-06-13 ROwen	Added support for multiple helpText items;
					bug fix: callFunc sometimes received an extra arg "caller".
2003-07-09 ROwen	Modified to call back with self instead of value;
					modified to use RO.AddCallback; added getEnable.
2003-08-05 ROwen	Modified so setDefault sets the current value if there is none;
					bug fix: getString returned None if no value and no default;
					now returns "" in that case.
2003-10-23 ROwen	Added label, abbrevOK and ignoreCase arguments;
					removed defIfDisabled since it wasn't being used and added clutter;
					removed ConfigMenu class since it didn't do much, wasn't being used
					and I didn't want to port the changes in ConfigMenu.
2003-11-07 ROwen	Modified to not create a StringVar unless it'll be used.
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2003-12-09 ROwen	Added argument item to getIndex.
					This required a different way of handling getIndex
					because if the item is the string representation
					of an integer, then tk's menu index returns that integer.
2003-12-17 ROwen	Bug fix: a value of None was being shown as "None"
					instead of a separator.
2004-03-05 ROwen	Added support for unicode entries.
2004-07-21 ROwen	Modified for updated RO.AddCallback.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-09-01 ROwen	Added checkDef argument to setItems; default is False (new behavior).
2004-09-14 ROwen	Removed unused *args from _doCallback to make pychecker happy.
					Improved the test code.
2004-11-29 ROwen	Reordered a few methods into alphabetical order.
2005-01-05 ROwen	Added autoIsCurrent, isCurrent and severity support.
					Modified expandValue method arguments and return value.
					Modified setDefault: the default for doCheck is now True.
2005-06-16 ROwen	Removed an unused variable (caught by pychecker).
2006-03-23 ROwen	Added isDefault method.
2006-05-24 ROwen	Bug fix: isDefault was broken.
2006-05-26 ROwen	Added trackDefault argument.
					Bug fix: added isCurrent argument to set.
					Bug fix: setItems properly preserves non-item-specific help.
"""
__all__ = ['OptionMenu']

import Tkinter
import RO.AddCallback
import RO.Alg
import RO.SeqUtil
from CtxMenu import CtxMenuMixin
from IsCurrentMixin import AutoIsCurrentMixin, IsCurrentActiveMixin
from SeverityMixin import SeverityActiveMixin

class _DoItem:
	def __init__(self, var, value):
		self.var = var
		self.value = value
	def __call__(self):
		self.var.set(self.value)

class OptionMenu (Tkinter.Menubutton, RO.AddCallback.TkVarMixin,
	AutoIsCurrentMixin, IsCurrentActiveMixin, SeverityActiveMixin, CtxMenuMixin):
	"""A Tkinter OptionMenu that adds many features.
	
	Inputs:
	- items		a list of items (strings) for the menu;
				if an item = None then a separator is inserted
	- var		a Tkinter.StringVar (or any object that has set and get methods);
				this is updated when a Menu item is selected or changed
				(and also during initialization if you specify defValue)
	- defValue	the default value; if specified, must match something in "items"
				(to skip checking, specify defValue = None initially,
				then call setDefault);
				if omitted then restoreDefault has no effect.
	- helpText	text for hot help; may be one string (applied to all items)
				or a list of help strings, one per item. At present
				help is only displayed for the currently chosen item;
				eventually I hope help can be shown for each item in turn
				as one scrolls through the menu.
	- helpURL	URL for longer help; many only be a single string (so far)
	- callFunc	callback function (not called when added);
				the callback receives one argument: this object
	- defMenu	name of "restore default" contextual menu item, or None for none
	- label		label for menu; if omitted then the label is automatically set to
				 the selected value.
	- abbrevOK	controls the behavior of set and setDefault;
				if True then unique abbreviations are allowed
	- ignoreCase controls the behavior of set and setDefault;
				if True then case is ignored
	- autoIsCurrent	controls automatic isCurrent mode
		- if false (manual mode), then is/isn't current if
		  set or setIsCurrent is called with isCurrent true/false
		- if true (auto mode), then is current only when all these are so:
			- set or setIsCurrent is called with isCurrent true
			- setDefValue is called with isCurrent true
			- current value == default value
	- trackDefault controls whether setDefault can modify the current value:
		- if True and isDefault() true then setDefault also changes the current value
		- if False then setDefault never changes the current value
		- if None then trackDefault = autoIsCurrent (because these normally go together)
	- isCurrent: is the value current?
	- severity: one of: RO.Constants.sevNormal (the default), sevWarning or sevError
	- all remaining keyword arguments are used to configure the Menu.
				text and textvariable are ignored.
	"""
	def __init__(self,
		master,
		items,
		var=None,
		defValue=None,
		helpText=None,
		helpURL=None,
		callFunc=None,
		defMenu = None,
		label = None,
		abbrevOK = False,
		ignoreCase = False,
		autoIsCurrent = False,
		trackDefault = None,
		isCurrent = True,
		severity = RO.Constants.sevNormal,
	**kargs):
		if var == None:
			var = Tkinter.StringVar()
		self._items = []
		self.defValue = None
		self._helpTextDict = {}
		self._fixedHelpText = None
		self.helpText = None
		self.defMenu = defMenu
		self._matchItem = RO.Alg.MatchList(abbrevOK = abbrevOK, ignoreCase = ignoreCase)
		if trackDefault == None:
			trackDefault = bool(autoIsCurrent)
		self.trackDefault = trackDefault

		# handle keyword arguments for the Menubutton
		# start with defaults, update with user-specified values, if any
		# then set text or textvariable
		wdgKArgs = {
			"borderwidth": 2,
			"indicatoron": True,
			"relief": "raised",
			"anchor": "c",
			"highlightthickness": 2,
		}
		wdgKArgs.update(kargs)
		for item in ("text", "textvariable"):
			if wdgKArgs.has_key(item):
				del(wdgKArgs[item])
		if label:
			wdgKArgs["text"] = label
		else:
			wdgKArgs["textvariable"] = var
		Tkinter.Menubutton.__init__(self, master, **wdgKArgs)
		self._menu = Tkinter.Menu(self, tearoff=False) # name="menu", tearoff=False)
		self["menu"] = self._menu
		# self.menuname = self._menu._w
		
		RO.AddCallback.TkVarMixin.__init__(self, var)
		
		# do after adding callback support
		# and before setting default (which triggers a callback)
		AutoIsCurrentMixin.__init__(self, autoIsCurrent)
		IsCurrentActiveMixin.__init__(self)
		SeverityActiveMixin.__init__(self, severity)

		CtxMenuMixin.__init__(self, helpURL = helpURL)
		
		self.setItems(items, helpText=helpText)
		
		self.setDefault(defValue, isCurrent = isCurrent, doCheck = True)
		self.restoreDefault()

		# add callback function after setting default
		# to avoid having the callback called right away
		if callFunc:
			self.addCallback(callFunc, False)

	def _doCallbacks(self):
		self._basicDoCallbacks(self)
		if self._helpTextDict:
			self.helpText = self._helpTextDict.get(self._var.get())

	def _addItems(self):
		"""Adds the list of items to the menu;
		must only be called when the menu is empty
		and self._items has been set
		"""
		for item in self._items:
			if item == None:
				self._menu.add_separator()
			else:
				self._menu.add_command(
					label=item,
					command=_DoItem(self._var, item),
				)

	def clear(self):
		self._var.set("")

	def ctxConfigMenu(self, menu):
		def addMenuItem(menu, descr, value):
			if descr and value != None:
				menuText = "%s (%s)" % (descr, value)
				def setValue():
					self.set(value)
				menu.add_command(label = menuText, command = setValue)

		addMenuItem(menu, self.defMenu, self.getDefault())
		return True

	def destroy(self):
		"""Destroy this widget and the associated menu.
		From Tkinter's OptionMenu"""
		Tkinter.Menubutton.destroy(self)
		self._menu = None
	
	def expandValue(self, value):
		"""Expand a value, unabbreviating and case correcting,
		as appropriate.
		
		Returns:
		- value: the expanded value, or the original value if None or invalid.
			Expansion of abbreviations and correction of case
			are controlled by the ignoreCase and abbrevOK flags
			supplied when creating this menu.
		- isOK	if False, the value was not valid and was not expanded.
			Note that None is always valid, but never expanded.
		"""
		if value == None:
			return None, True

		try:
			return self._matchItem.getUniqueMatch(value), True
		except ValueError:
			return value, False
	
	def getDefault(self):
		"""Returns the default value.
		"""
		return self.defValue

	def getEnable(self):
		"""Returns True if the button is enabled, False otherwise.
		
		Enabled is defined as the state not being 'disabled'.
		"""
		return self["state"] != "disabled"
	
	def getIndex(self, item=None):
		"""Returns the index of the specified item,
		or the currently selected item if item=None.
		
		Originally used self._menu.index,
		but that gives the wrong answer if the item
		is the string representation of an integer.

		Returns None if the specified item is not present
		or if item=None and no item is selected.
		"""
		if item == None:
			item = self._var.get()
		else:
			item = str(item)

		try:
			return self._items.index(item)
		except ValueError:
			return None
	
	def getMenu(self):
		"""Returns the Menu object from the OptionMenu;
		handy if you want to modify it in some way but use sparingly
		as you can easily manipulate it to foul up this widget
		"""
		return self._menu
	
	def getString(self):
		"""Returns the current value of the field, or the default if none selected.
		"""
		val = self._var.get()
		return val or self.defValue or ""
	
	def getVar(self):
		"""Returns the variable that is set to the currently selected item
		"""
		return self._var
	
	def insert_separator(self, indx, **kargs):
		"""Inserts a separator at the appropriate location.
		Note: the interal self._list is not modified,
		so if you choose to update the list of items later,
		your new list should not include the separators
		that you inserted.
		"""
		self._menu.insert_separator(indx, **kargs)
	
	def isDefault(self):
		"""Return True if current value matches the default value.
		"""
		return self._var.get() == (self.defValue or "")
	
	def restoreDefault(self):
		"""Restore the default value.
		Has no effect if the default was not specified.
		"""
#		print "restoreDefault(); currValue=%r, defValue=%r" % (self._var.get(), self.defValue,)
		if self.defValue != None:
			self._var.set(self.defValue)

	def set(self, newValue, isCurrent=True, doCheck=True, *args, **kargs):
		"""Changes the currently selected value.
		"""
		if newValue == None:
			return
		
		newValue, isOK = self.expandValue(newValue)
		if not isOK and doCheck:
			raise ValueError("Value %r invalid" % newValue)
	
		self.setIsCurrent(isCurrent)
		self._var.set(newValue)

	def setDefault(self, newDefValue, isCurrent=None, doCheck=True, *args, **kargs):
		"""Changes the default value. If the current value is None,
		also sets the current value.

		Inputs:
		- newDefValue: the new default value
		- isCurrent: if not None, set the _isCurrent flag accordingly.
			Typically this is only useful in autoIsCurrent mode.
		- doCheck: check that the new default value is in the menu
			(ignored if newDefValue is None)

		Error conditions:
		- Raises ValueError and leaves the default unchanged
		  if doCheck is True and if the new default value is neither in the list of values
		  nor is None.
		"""
#		print "setDefault(newDeffValue=%r, isCurrent=%r, doCheck=%r)" % (newDefValue, isCurrent, doCheck)
		newDefValue, isOK = self.expandValue(newDefValue)
		if not isOK and doCheck:
			raise ValueError("Default value %r invalid" % newDefValue)
		restoreDef = self.trackDefault and self.isDefault()
		self.defValue = newDefValue
		if isCurrent != None:
			self.setIsCurrent(isCurrent)

		if restoreDef:
			self.restoreDefault()
		else:
			self._doCallbacks()

	def setEnable(self, doEnable):
		"""Changes the enable state.
		"""
		if doEnable:
			self.configure(state="normal")
		else:
			self.configure(state="disabled")
	
	def setItems(self, items, isCurrent=None, helpText=None, checkDef=False, **kargs):
		"""Replaces the current set of items (but only if the new
		list is different than the old one). If the currently selected
		item is present in the new list, the current selection is retained;
		otherwise the default is restored.
		
		Inputs:
		- see init for most of them
		- isCurrent is ignored; it's purely for compatibility with key variable callbacks
		- checkDef	if True, set default to None if it is not in the new list of items
		- if helpText is None then the old helpText is left alone if it was a single string
		  (rather than a set of strings) and is nulled otherwise
		
		Warnings:
		- If the default is not present in the new list,
		then the default is silently nulled.
		"""
		#print "setItems(items=%s, isCurrent=%s, helpText=%s, checkDef=%s)" % (items, isCurrent, helpText, checkDef)
		# make sure items is a list (convert if necessary)
		items = list(items)

		# update help info
		self._helpTextDict = {}
		if helpText == None:
			# if existing help text is fixed, keep using it
			# otherwise there is no help (cannot reuse item-specific help)
			self.helpText = self._fixedHelpText
		elif RO.SeqUtil.isSequence(helpText):
			# new item-specific help
			nItems = len(items)
			self._fixedHelpText = None
			if len(helpText) != nItems:
				raise ValueError, "helpText list has %d entries but %d wanted" % \
					(len(helpText), nItems)
			for ii in range(nItems):
				self._helpTextDict[items[ii]] = helpText[ii]
		else:
			# new fixed help
			self.helpText = self._fixedHelpText = helpText
		
		# if no change (ignoring the difference between a list and a tuple)
		# then do nothing
		if items == self._items:
			return

		# update _matchItem
		self._matchItem.setList(items)
				
		# if the default value is not present, null the default value
		# don't bother with abbrev expansion; defValue should already be expanded
		if checkDef and self.defValue not in items:
			self.defValue = None
		
		# rebuild the menu
		self._items = items
		self._addItems()
		self._menu.delete(0, "end")
		self._addItems()
		
		currValue = self._var.get()
		if currValue not in self._items:
			self.restoreDefault()
		
		if self._helpTextDict:
			self.helpText = self._helpTextDict.get(self._var.get())


if __name__ == "__main__":
	import Label
	import PythonTk
	import StatusBar
	root = PythonTk.PythonTk()
	
	def callFunc(wdg):
		label.set(wdg.getString())

	items = ("Earlier", "Now", "Later", None, "Never")
	helpTexts = ("Help for Earlier", "Help for Now", "help for Later", "", "Help for Never")
	menu = OptionMenu(root,
		items = items,
		defValue = "Now",
		callFunc = callFunc,
		defMenu = "Default",
		helpText = helpTexts,
		autoIsCurrent = True,
	)
	menu.grid(row=0, column=0, sticky="w")

	label = Label.Label(root, width=20, anchor="w", helpText="current value")
	label.grid(row=1, column=0, sticky="w")
	
	statusBar = StatusBar.StatusBar(root, width=20)
	statusBar.grid(row=2, column=0, sticky="ew")

	root.mainloop()
