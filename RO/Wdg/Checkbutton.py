#!/usr/local/bin/python
"""A variant on Checkbutton that add help, default handling and other niceties
including a command callback that is called in more cases.

History:
2002-11-15 ROwen
2002-12-04 ROwen	Added support for helpURL.
2003-03-13 ROwen	Renamed from ROCheckbutton to Checkbutton;
					added defIfDisabled, setEnable and class EnableCheckbutton.
2003-04-15 ROwen	Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-05-29 ROwen	Removed EnableCheckbutton (it's obsolete).
2003-07-09 ROwen	Added addCallback, clear, getEnable and setBool;
					modified to use RO.AddCallback.
2003-08-04 ROwen	Improved callbacks to fire when command fires (a bit later in the process;
					prevents display bugs in some applications).
2003-08-11 ROwen	Added set, asBool; changed isSelected to getBool.
2003-11-03 ROwen	Modified so callbacks are called for set, setBool, select, etc.
					or when the variable is set. These are all cases in which
					standard Tk Checkbutton command callbacks are NOT called.
2003-12-02 ROwen	Bug fix: getBool would always return False if a BooleanVar was used.
					Modified asBool to return False in the case of a string that does not match onvalue,
					instead of raising an exception if the string didn't match onvalue or offvalue.
					Added some doc strings.
2003-12-05 ROwen	Changed setDefValue to setDefault for consistency.
2003-12-19 ROwen	Added showValue arg to __init__.
					Improved documentation and checking of **kargs for __init__.
					Added *args, **kargs to set and setDefault
					so they can be called by KeyVariable addROWdg.
2004-05-18 ROwen	Modified so indicatoron tested for logical false when tweaking
					selectcolor. This still doesn't handle "f" and other tk-ish
					logical values, but is clearer for python-ish logical values
					and makes pychecker happier.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-09-14 ROwen	Tweaked the imports.
2004-11-15 ROwen	Improved defaults: if showValue True then defaults to indicatoron = False;
					if indicatoron = False then defaults to padx=5, pady=2.
"""
__all__ = ['Checkbutton']

import Tkinter
import RO.AddCallback
import RO.MathUtil
import CtxMenu

class Checkbutton (Tkinter.Checkbutton, RO.AddCallback.TkVarMixin, CtxMenu.CtxMenuMixin):
	def __init__(self,
		master,
		var = None,
		defValue = False,
		helpText = None,
		helpURL = None,
		callFunc = None,
		defIfDisabled = False,
		showValue = False,
	**kargs):
		"""Creates a new Checkbutton.
		
		Inputs:
		- var		a Tkinter variable; this is updated when Checkbutton state changes
					(and also during initialization if you specify defValue)
		- defValue	the default state: either a string (which must match on or off value)
					or a bool (selected if True, unselected if False)
		- helpText	text for hot help
		- helpURL	URL for longer help
		- callFunc	callback function; the function receives one argument: self.
					It is called whenever the value changes (manually or via
					the associated variable being set) and when setDefault is called
					(unlike command, which is only called for user action and invoke()).
		- defIfDisabled	show the default value if disabled (via doEnable)?
		- showValue	Display text = current value;
					overrides text and textvariable
		- all remaining keyword arguments are used to configure the Tkinter Checkbutton;
		  - command is supported, but see also the callFunc argument
		  - variable is forbidden (use var)
		  - text and textvariable are forbidden if showValue is true
		
		Note: if indicatoron false, then default selectcolor
		is the background color. This avoids really ugly
		display when the widget is checked.
		"""
		if var == None:
			var = Tkinter.StringVar()
		self._var = var
		self._defIfDisabled = defIfDisabled
		self.helpText = helpText
		
		# if a command is supplied in kargs, remove it now and set it later
		# so it is not called during init
		cmd = kargs.get("command")
		if cmd:
			del(kargs["command"])
		if "variable" in kargs:
			raise ValueError("Specify var instead of variable")
		if showValue:
			if "text" in kargs:
				raise ValueError("Do not specify text if showValue True")
			if "textvariable" in kargs:
				raise ValueError("Do not specify textvariable if showValue True (specify var instead)")
			kargs.setdefault("indicatoron", False)
			kargs["textvariable"] = self._var
		
		if not bool(kargs.get("indicatoron", True)):
			kargs.setdefault("padx", 5)
			kargs.setdefault("pady", 2)

		Tkinter.Checkbutton.__init__(self,
			master = master,
			variable = self._var,
		**kargs)

		RO.AddCallback.TkVarMixin.__init__(self, self._var)
		
		CtxMenu.CtxMenuMixin.__init__(self,
			helpURL = helpURL,
		)

		# deal with fixing selectcolor after creating the widget
		# so we can query the resultant background color
		if not kargs.get("indicatoron", True) \
			and not kargs.has_key("selectcolor"):
			self["selectcolor"] = self["bg"]

		self.setDefault(defValue)
		self.restoreDefault()
		
		# add the callbacks last, to avoid calling them while setting default
		self.addCallback(callFunc, False)
		if cmd:
			self["command"] = cmd
		
	def asBool(self, val):
		"""Returns a value as a bool.
		
		The input value can be any of:
		- a string: returns True if matches onvalue (case sensitive), else False*
		- True, False: returns val
		- anything else: returns bool(val)
		
		*This matches the behavior of checkbuttons (based on observation on one platform,
		so this may not always be true): they are checked if the value matches onvalue,
		else unchecked.
		"""
		if hasattr(val, "lower"):
			if val == self["onvalue"]:
				return True
			else:
				return False

		return bool(val)
	
	def clear(self):
		"""Convenience function, makes it work more like an RO.Wdg.Entry widget.
		"""
		self.deselect()
	
	def getBool(self):
		"""Returns True if the checkbox is selected (checked), False otherwise.
		"""
		return self.asBool(self._var.get())
	
	def getDefBool(self):
		"""Returns True if the checkbox is selected (checked) by default, False otherwise.
		"""
		return self._defBool

	def getDefault(self):
		"""Returns onvalue if the default is selected (checked) by default, offvalue otherwise.
		Onvalue and offvalue are strings.
		"""
		if self._defBool:
			return self["onvalue"]
		else:
			return self["offvalue"]

	def getEnable(self):
		"""Returns True if the button is enabled, False otherwise.
		
		Enabled is defined as the state not being 'disabled'.
		"""
		return self["state"] != "disabled"
	
	def getVar(self):
		return self._var
	
	def getString(self):
		return str(self._var.get())

	def set(self, newValue, *args, **kargs):
		"""Sets the value (toggled or not) and triggers the callback functions.
		
		Valid values are:
		- a string that matches self["onvalue"] or self["offvalue"]
		  (case matters!)
		- True or False (anything else will be coerced)
		
		Raises ValueError if newDefValue is a string and does not match
		the on or off value.
		"""
		self.setBool(self.asBool(newValue))
	
	def setBool(self, doCheck):
		"""Checks or unchecks the checkbox.
		"""
		if doCheck:
			self.select()
		else:
			self.deselect()

	def setDefault(self, newDefValue, *args, **kargs):
		"""Changes the default value, triggers the callback functions
		and (if widget disabled and defIfDisabled true) updates the displayed value.
		
		Valid values are:
		- a string that matches self["onvalue"] or self["offvalue"]
		  (case matters!)
		- True or False (anything else will be coerced)
		
		Raises ValueError if newDefValue is a string and does not match
		the on or off value.
		"""
		self._defBool = self.asBool(newDefValue)
		
		# if disabled and defIfDisabled, update display
		# (which also triggers a callback)
		# otherwise leave the display alone and explicitly trigger a callback
		if self._defIfDisabled and self["state"] == "disabled":
			self.restoreDefault()
		else:
			self._doCallbacks()

	def setEnable(self, doEnable):
		"""Changes the enable state and (if the widget is being disabled
		and defIfDisabled true) displays the default value
		"""
		if doEnable:
			self.configure(state="normal")
		else:
			self.configure(state="disabled")
			if self._defIfDisabled:
				self.restoreDefault()
	
	def restoreDefault(self):
		"""Restores the default value. Calls callbacks (if any).
		"""
		if self._defBool:
			self.select()
		else:
			self.deselect()

if __name__ == "__main__":
	import PythonTk
	root = PythonTk.PythonTk()
	
	def btnCallback(btn):
		print "%s state=%s" % (btn["text"], btn.getBool())

	Checkbutton(root,
		text = "Item one",
		defValue = False,
		callFunc = btnCallback,
		helpText = "Help for checkbox 'Item one', default off",
	).pack()
	Checkbutton(root,
		text = "Item two",
		defValue = True,
		callFunc = btnCallback,
		helpText = "Help for checkbox 'Item two', default on",
	).pack()
	var = Tkinter.StringVar()
	Checkbutton(root,
		text = "Item three",
		defValue = True,
		callFunc = btnCallback,
		helpText = "Help for checkbox 'Item three', default on",
		var = var,
		indicatoron = False,
		padx = 5,
		pady = 2,
	).pack()

	root.mainloop()
