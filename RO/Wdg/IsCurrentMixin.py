#!/usr/local/bin/python
"""Mixin classes that add an "isCurrent" flag
and adjust the widget background color based on that flag.

Warning: background color is ignored by Mac buttons and menubuttons.

See also: StateMixin.

History:
2004-12-29 ROwen
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
	- "Active Background Color"
	- "Active Bad Background"
	
	Adds these private attributes:
	- self.__isCurrent
	- self.__isCurrentPrefDict
	"""
	def __init__ (self, isCurrent = True):
		self._isCurrent = True
		self._isCurrentPrefDict = {} # set when first needed

		if isCurrent != True:
			self.setIsCurrent(isCurrent)

	def getIsCurrent(self):
		"""Return isCurrent flag (False or True)
		"""
		return self._isCurrent
		
	def setIsCurrent(self, isCurrent):
		"""Update isCurrent information.
		"""
		isCurrent = bool(isCurrent)
		if self._isCurrent != isCurrent:
			if not self._isCurrentPrefDict:
				self._isCurrentPrefDict[False] = WdgPrefs.getWdgPrefDict()["Bad Background"]
				self._isCurrentPrefDict[True] = WdgPrefs.getWdgPrefDict()["Background Color"]
				WdgPrefs.getWdgPrefDict()["Bad Background"].addCallback(self._updateIsCurrentColor, callNow=False)
				# normal background color is auto-updated within tcl; no callback needed
			self._isCurrent = isCurrent
			self._updateIsCurrentColor()
		
	def _updateIsCurrentColor(self, *args):
		"""Set the background to the current isCurrent color.

		Override if your widget wants other aspects updated.

		Called automatically. Do NOT call manually.
		"""
		color = self._isCurrentPrefDict[self._isCurrent].getValue()
		self.configure(background = color)


class IsCurrentActiveMixin(IsCurrentMixin):
	"""Version of IsCurrentMixin for widgets with activebackground:
	Button, Menu, Menubutton, Radiobutton, Scale, Scrollbar.
	For Checkbutton see IsCurrentCheckbuttonMixin.
	
	Adds these private attributes:
	- self.__isCurrent
	- self.__isCurrentPrefDict
	"""
	def setIsCurrent(self, isCurrent):
		"""Update isCurrent information.
		"""
		isCurrent = bool(isCurrent)
		if self._isCurrent != isCurrent:
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
				# unfortunately, a
			self._isCurrent = isCurrent
			self._updateIsCurrentColor()
		
	def _updateIsCurrentColor(self, *args):
		"""Set the background to the current isCurrent color
		(sets background, selectcolor and activebackground).

		Override if your widget wants other aspects updated.

		Called automatically. Do NOT call manually.
		"""
		normalColor, activeColor = [pref.getValue() for pref in self._isCurrentPrefDict[self._isCurrent]]
		self.configure(background = normalColor, activebackground = activeColor)

class IsCurrentCheckbuttonMixin(IsCurrentActiveMixin): 
	"""Version of IsCurrentMixin for Checkbutton widgets.
	
	Adds these private attributes:
	- self.__isCurrent
	- self.__isCurrentPrefDict
	"""
	def _updateIsCurrentColor(self, *args):
		"""Set the background to the current isCurrent color.

		Override if your widget wants other aspects updated.

		Called automatically. Do NOT call manually.
		"""
		normalColor, activeColor = [pref.getValue() for pref in self._isCurrentPrefDict[self._isCurrent]]
		self.configure(background = normalColor, selectcolor = normalColor, activebackground = activeColor)
	
	
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
