#!/usr/local/bin/python
"""Adjust widget foreground color as a function of state,
meaning one of the RO.Constant.st_ constants:
st_Normal
st_Warning
st_Error

Note: "state" is an unfortunate term since it's also used
to enable and disable tk widgets. But it's too deeply embedded
in the RO package to change the name.

Warning: foreground color is ignored by Mac buttons and menubuttons.

See also: IsCurrentMixin.

History:
2004-12-29 ROwen
"""
import RO.Constants
import WdgPrefs

class StateMixin:
	"""Mixin class that adds a state attribute
	and adjusts foreground color based on state.
	
	Valid states are:
	- RO.Constants.st_Normal
	- RO.Constants.st_Warning
	- RO.Constants.st_Error

	Uses these RO.Wdg.WdgPref preferences:
	- "Foreground Color"
	- "Warning Color"
	- "Error Color"
	
	Adds these attributes, all private:
	self._state
	self._statePrefDict
	"""
	def __init__ (self, state = RO.Constants.st_Normal):
		self._state = RO.Constants.st_Normal
		self._statePrefDict = {} # set when first needed

		if state != RO.Constants.st_Normal:
			self.setState(state)
		
	def getState(self):
		"""Return current state, one of: RO.Constants.st_Normal, st_Warning or st_Error.
		"""
		return self._state
		
	def setState(self, state):
		"""Update state information.
		
		Raise ValueError if state is not one of
		RO.Constants.st_Normal, st_Warning or st_Error.
		"""
		if self._state != state:
			if state not in self._statePrefDict:
				# either statePrefDict does not exist yet
				# or state is invalid or both
				if not self._statePrefDict:
					# set statePrefDict and subscribe to prefs;
					# then test state again
					self._statePrefDict = WdgPrefs.getWdgStatePrefDict()
					for iterstate, pref in self._statePrefDict.iteritems():
						if iterstate == RO.Constants.st_Normal:
							# normal foreground color is already automatically updated
							continue
						pref.addCallback(self._updateStateColor, callNow=False)
				if state not in self._statePrefDict:
					raise ValueError("Invalid state %r" % (state,))
			self._state = state
			self._updateStateColor()
	
	def _updateStateColor(self, *args):
		"""Apply the current color appropriate for the current state.
		
		Called automatically. Do NOT call manually.
		"""
		color = self._statePrefDict[self._state].getValue()
		self.configure(foreground = color)


class StateActiveMixin(StateMixin):
	"""Version of StateMixin for widgets with activeforegound:
	Button, Checkbutton, Menu, Menubutton, Radiobutton, Scale, Scrollbar.
	"""
	def _updateStateColor(self, *args):
		"""Apply the specified color."""
		color = self._statePrefDict[self._state].getValue()
		self.configure(foreground = color, activeforeground = color)


class StateSelectMixin(StateMixin):
	"""Version of StateMixin for widgets with selectforeground:
	Entry, Listbox, Text (also Canvas, but this class is not
	likely to be helpful for that).
	"""
	def _updateStateColor(self, *args):
		"""Apply the specified color."""
		color = self._statePrefDict[self._state].getValue()
		self.configure(foreground = color, selectforeground = color)


if __name__ == "__main__":
	import Tkinter
	import PythonTk
	root = PythonTk.PythonTk()
	
	class ColorButton(Tkinter.Button, StateActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Button.__init__(self, *args, **kargs)
			StateActiveMixin.__init__(self)

	class ColorCheckbutton(Tkinter.Checkbutton, StateActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Checkbutton.__init__(self, *args, **kargs)
			StateActiveMixin.__init__(self)

	class ColorEntry(Tkinter.Entry, StateSelectMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Entry.__init__(self, *args, **kargs)
			StateSelectMixin.__init__(self)

	class ColorLabel(Tkinter.Label, StateMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Label.__init__(self, *args, **kargs)
			StateMixin.__init__(self)

	class ColorOptionMenu(Tkinter.OptionMenu, StateActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.OptionMenu.__init__(self, *args, **kargs)
			StateActiveMixin.__init__(self)
		
	def setState(*args):
		stateStr = stateVar.get()
		state = {"Normal": RO.Constants.st_Normal,
			"Warning": RO.Constants.st_Warning,
			"Error": RO.Constants.st_Error,
		}.get(stateStr)
		print "Set state to %s = %r" % (stateStr, state)
		for wdg in wdgSet:
			wdg.setState(state)

	stateVar = Tkinter.StringVar()
	stateVar.set("Normal")
	stateVar.trace_variable("w", setState)
	
	entryVar = Tkinter.StringVar()
	entryVar.set("Entry")
	wdgSet = (
		ColorOptionMenu(root, stateVar, "Normal", "Warning", "Error",
		),
		ColorButton(root,
			text = "Button",
		),
		ColorCheckbutton(root,
			text = "Checkbutton",
		),
		ColorCheckbutton(root,
			text = "Checkbutton",
			indicatoron = False,
		),
		ColorEntry(root,
			textvariable = entryVar,
		),
		ColorLabel(root,
			text = "Label",
		),
	)
	for wdg in wdgSet:
		wdg.pack(fill=Tkinter.X)
			
	root.mainloop()
