#!/usr/local/bin/python
"""Mixin classes that add an "isCurrent" flag
and adjust the widget background color based on that flag.

Warning: background color is ignored by Mac buttons and menubuttons.

See also: StateMixin.

History:
2004-12-29 ROwen
2005-01-04 ROwen	Added AutoIsCurrentMixin.
					Modified IsCurrentCheckbuttonMixin to set selectcolor
					only if indicatoron is false.
"""
import WdgPrefs

class IsCurrentMixin:
	"""Mixin classes that add an "isCurrent" flag
	and adjust background color based on isCurrent.
	
	Use this version for widgets without the activebackground attribute,
	including Label and Entry.
	See also IsCurrentActiveMixin.
	
	Uses these RO.Wdg.WdgPref preferences:
	- "Background Color"
	- "Bad Background"
	
	Adds these private attributes:
	- self._isCurrent
	- self._isCurrentPrefDict
	"""
	def __init__ (self, isCurrent = True):
		self._isCurrent = True
		self._isCurrentPrefDict = {} # set when first needed

		if not isCurrent:
			self.setIsCurrent(False)

	def getIsCurrent(self):
		"""Return isCurrent flag (False or True)
		"""
		return self._isCurrent
		
	def setIsCurrent(self, isCurrent):
		"""Update isCurrent information.
		"""
		isCurrent = bool(isCurrent)
		if self._isCurrent != isCurrent:
			self._isCurrent = isCurrent
			self._updateIsCurrentColor()
		
	def _updateIsCurrentColor(self, *args):
		"""Set the background to the current isCurrent color.

		Override if your widget wants other aspects updated.

		Called automatically. Do NOT call manually.
		"""
		if not self._isCurrentPrefDict:
			self._isCurrentPrefDict[False] = WdgPrefs.getWdgPrefDict()["Bad Background"]
			self._isCurrentPrefDict[True] = WdgPrefs.getWdgPrefDict()["Background Color"]
			WdgPrefs.getWdgPrefDict()["Bad Background"].addCallback(self._updateIsCurrentColor, callNow=False)
			# normal background color is auto-updated within tcl; no callback needed

		isCurrent = self.getIsCurrent()
		color = self._isCurrentPrefDict[isCurrent].getValue()
		self.configure(background = color)


class IsCurrentActiveMixin(IsCurrentMixin):
	"""Version of IsCurrentMixin for widgets with activebackground:
	Button, Menu, Menubutton, Radiobutton, Scale, Scrollbar.
	For Checkbutton see IsCurrentCheckbuttonMixin.
	
	Uses these RO.Wdg.WdgPref preferences:
	- "Background Color"
	- "Bad Background"
	- "Active Background Color"
	- "Active Bad Background"

	Adds these private attributes:
	- self._isCurrent
	- self._isCurrentPrefDict
	"""
	def _updateIsCurrentColor(self, *args):
		"""Set the background to the current isCurrent color
		and activebackground to the current isCurrent active color.

		Override if your widget wants other aspects updated.

		Called automatically. Do NOT call manually.
		"""
		if not self._isCurrentPrefDict:
			self._isCurrentPrefDict[False] = (
				WdgPrefs.getWdgPrefDict()["Bad Background"],
				WdgPrefs.getWdgPrefDict()["Active Bad Background"],
			)
			self._isCurrentPrefDict[True] = (
				WdgPrefs.getWdgPrefDict()["Background Color"],
				WdgPrefs.getWdgPrefDict()["Active Background Color"],
			)
			WdgPrefs.getWdgPrefDict()["Background Color"].addCallback(self._updateIsCurrentColor, callNow=False)
			WdgPrefs.getWdgPrefDict()["Bad Background"].addCallback(self._updateIsCurrentColor, callNow=False)
			# active colors cannot be modified by the user, so no callback needed

		isCurrent = self.getIsCurrent()
		normalColor, activeColor = [pref.getValue() for pref in self._isCurrentPrefDict[isCurrent]]
		self.configure(background = normalColor, activebackground = activeColor)


class IsCurrentCheckbuttonMixin(IsCurrentMixin): 
	"""Version of IsCurrentMixin for Checkbutton widgets.
	
	Warning: selectbackground is forced equal to background
	if indicatoron false (since selectbackground is used
	as the text background in that case).
	
	Adds these private attributes:
	- self._isCurrent
	- self._isCurrentPrefDict
	"""
	def __init__ (self, isCurrent = True):
		"""In additon to the usual intialization,
		force selectcolor = background if indicatoron false
		"""
		IsCurrentMixin.__init__(self, isCurrent)
		if self.getIsCurrent() and not self["indicatoron"]:
			self["selectcolor"] = self["background"]

	def _updateIsCurrentColor(self, *args):
		"""Set the background to the current isCurrent color
		and activebackground to the current isCurrent active color.
		
		Also set selectbackground = background if indicatoron = false
		(because then the text background is selectbackground
		when the button is checked).
		
		Called automatically. Do NOT call manually.
		"""
		if not self._isCurrentPrefDict:
			self._isCurrentPrefDict[False] = (
				WdgPrefs.getWdgPrefDict()["Bad Background"],
				WdgPrefs.getWdgPrefDict()["Active Bad Background"],
			)
			self._isCurrentPrefDict[True] = (
				WdgPrefs.getWdgPrefDict()["Background Color"],
				WdgPrefs.getWdgPrefDict()["Active Background Color"],
			)
			WdgPrefs.getWdgPrefDict()["Background Color"].addCallback(self._updateIsCurrentColor, callNow=False)
			WdgPrefs.getWdgPrefDict()["Bad Background"].addCallback(self._updateIsCurrentColor, callNow=False)
			# active colors cannot be modified by the user, so no callback needed

		isCurrent = self.getIsCurrent()
		normalColor, activeColor = [pref.getValue() for pref in self._isCurrentPrefDict[isCurrent]]
		if self["indicatoron"]:
			# Checkbox visible. selectcolor is only used for checkbox color when checked;
			# it is not used for text background and so does not need to be set
			self.configure(background = normalColor, activebackground = activeColor)
		else:
			# No checkbox; selectcolor is used for text background and so must be set
			self.configure(background = normalColor, activebackground = activeColor, selectcolor = normalColor)


class AutoIsCurrentMixin:
	"""Add optional automatic control of isCurrent to input widgets.
	
	The widget must support:
	- a value with associated isCurrent flag
	- a default value with associated defIsCurrent flag
	- getString (returns the current value as a string)
	- getDefault (returns the default as a string)
	- addCallback (specifies a function to call
	  whenever the value or default is changed)

	autoIsCurrent sets the isCurrent mode to manual or automatic.
	- If false (manual mode), then the normal isCurrent behavior applies:
	  the widget is current if and only if self._isCurrent true.
	- If true (automatic mode), then the widget is current
	  only if all of the following are true:
		- current value = default value (self.getString() = self.getDefault())
		- self._isCurrent true
		- self._defIsCurrent true
		
	To use this class:
	- Inherit from this class AND THEN from one of the IsCurrent...Mixin classes.
	  AutoIsCurrentMixin must be listed BEFORE IsCurrent...Mixin,
	  so that the getIsCurrent in AutoIsCurrentMixin overrides the one in IsCurrent...Mixin.
	- Initialize AutoIsCurrentMixin before IsCurrent...Mixin.

	Adds these private attributes:
	- self._autoIsCurrent
	- self._defIsCurrent
	- self._isCurrent
	"""
	def __init__ (self,
		autoIsCurrent = False,
	):
		self._autoIsCurrent = bool(autoIsCurrent)
		self._defIsCurrent = True
		self._isCurrent = True
		
		self.addCallback(self._updateIsCurrentColor)
	
	def getIsCurrent(self):
		"""Get current isCurrent state.

		If self._autoIsCurrent true, then return True only if all of these are true:
		- self._isCurrent True
		- self._defIsCurrent True
		- self.getString() == self.getDefault()
		If self._autoIsCurrent false then returns self._isCurrent
		"""
		if self._autoIsCurrent:
#			print "_isCurrent=%r, _defIsCurrent=%r, getString=%r, getDefault=%r" % \
#				(self._isCurrent, self._defIsCurrent, self.getString(), self.getDefault())
			return self._isCurrent and self._defIsCurrent and \
				self.getString() == self.getDefault()
		return self._isCurrent
	
	
if __name__ == "__main__":
	import Tkinter
	import PythonTk
	root = PythonTk.PythonTk()
	
	class ColorButton(Tkinter.Button, IsCurrentActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Button.__init__(self, *args, **kargs)
			IsCurrentActiveMixin.__init__(self)

	class ColorCheckbutton(Tkinter.Checkbutton, IsCurrentActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Checkbutton.__init__(self, *args, **kargs)
			IsCurrentActiveMixin.__init__(self)

	class ColorEntry(Tkinter.Entry, IsCurrentMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Entry.__init__(self, *args, **kargs)
			IsCurrentMixin.__init__(self)

	class ColorLabel(Tkinter.Label, IsCurrentMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Label.__init__(self, *args, **kargs)
			IsCurrentMixin.__init__(self)

	class ColorOptionMenu(Tkinter.OptionMenu, IsCurrentActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.OptionMenu.__init__(self, *args, **kargs)
			IsCurrentActiveMixin.__init__(self)

	def setIsCurrent(*args):
		isCurrent = isCurrentVar.get()
		print "Set isCurrent %r" % (isCurrent,)
		for wdg in wdgSet:
			wdg.setIsCurrent(isCurrent)
	
	isCurrentVar = Tkinter.BooleanVar()
	isCurrentVar.set(True)
	isCurrentVar.trace_variable("w", setIsCurrent)

	stateVar = Tkinter.StringVar()
	stateVar.set("Normal")
	
	entryVar = Tkinter.StringVar()
	entryVar.set("Entry")
	wdgSet = (
		ColorCheckbutton(root,
			text = "Is Current",
			variable = isCurrentVar,
		),
		ColorOptionMenu(root, stateVar, "Normal", "Warning", "Error",
		),
		ColorButton(root,
			text = "Button",
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
