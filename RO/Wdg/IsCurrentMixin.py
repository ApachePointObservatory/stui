#!/usr/local/bin/python
"""Mixin classes that add an "isCurrent" flag
and adjust the widget background color based on that flag.

Warning: background color is ignored by Mac buttons and menubuttons.

See also: StateMixin.

To Do:
- Support autoIsCurrent Entry widgets.
  I fear what is needed is a supplementary set of mixin classes -- 
  one set for isCurrent support, another set for Auto support.
  This is because the problems seem orthogonal -- i.e. what
  items to change depend on the widget, but whether to use autoIsCurrent
  or not is a more general question.
  Another option is to make a variant module AutoIsCurrentMixin.
  But again I rather hate the resulting clutter.
  Yet another option is to force all widgets to support autoIsCurrent mode,
  but that makes no sense for Label, Button, etc.

History:
2004-12-29 ROwen
2005-01-03 ROwen	Added support for autoIsCurrent.
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


class IsCurrentAutoMixin(IsCurrentActiveMixin):
	"""Version of IsCurrentActiveMixin that can automatically set isCurrent
	based on whether the current value of the widget equals the default value.

	see getIsCurrent for more information.

	Adds these private attributes:
	- self._autoIsCurrent
	- self._defIsCurrent
	- self._isCurrent
	- self._isCurrentPrefDict
	
	Warning: if getString and getDefault methods are not available
	then you must override getIsCurrent.
	"""
	def __init__ (self,
		autoIsCurrent = False,
		isCurrent = True,
		defIsCurrent = True,
	):
		self._autoIsCurrent = autoIsCurrent
		self._defIsCurrent = defIsCurrent
		# use default isCurrent so _updateIsCurrentColor not called yet
		# then set _isCurrent and decide if _update... needs to be called
		IsCurrentActiveMixin.__init__(self)
		self._isCurrent = isCurrent
		
		if autoIsCurrent:
			self.addCallback(self._updateIsCurrentColor)
		
		if not self.getIsCurrent():
			self._updateIsCurrentColor()

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

	def setDefIsCurrent(self, isCurrent):
		isCurrent = bool(isCurrent)
		if self._defIsCurrent != isCurrent:
			self._defIsCurrent = isCurrent
			self._updateIsCurrentColor()


class IsCurrentCheckbuttonMixin(IsCurrentAutoMixin): 
	"""Version of IsCurrentAutoMixin for Checkbutton widgets.
	
	Warning: selectbackground is forced equal to background
	if indicatoron false (since selectbackground is used
	as the text background in that case).
	
	Adds these private attributes:
	- self._isCurrent
	- self._isCurrentPrefDict
	- self._indicatorOn
	"""
	def __init__ (self,
		autoIsCurrent = False,
		isCurrent = True,
		defIsCurrent = True,
	):
		"""In additon to the usual intialization,
		force selectcolor = background if indicatoron false
		"""
		IsCurrentAutoMixin.__init__(self,
			autoIsCurrent = autoIsCurrent,
			isCurrent = isCurrent,
			defIsCurrent = defIsCurrent,
		)
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
