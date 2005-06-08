#!/usr/local/bin/python
"""Adjust widget foreground color as a function of severity,
meaning one of the RO.Constant.sev constants:
sevNormal
sevWarning
sevError

Note: "severity" is an unfortunate term since it's also used
to enable and disable tk widgets. But it's too deeply embedded
in the RO package to change the name.

Warning: foreground color is ignored by Mac buttons and menubuttons.

See also: IsCurrentMixin.

History:
2005-01-05 ROwen
2005-06-08 ROwen	Changed SeverityMixin to a new-style class.
"""
import RO.Constants
import WdgPrefs

class SeverityMixin(object):
	"""Mixin class that adds a severity attribute
	and adjusts foreground color based on severity.
	
	Valid severitys are:
	- RO.Constants.sevNormal
	- RO.Constants.sevWarning
	- RO.Constants.sevError

	Uses these RO.Wdg.WdgPref preferences:
	- "Foreground Color"
	- "Warning Color"
	- "Error Color"
	
	Adds these attributes, all private:
	self._severity
	self._severityPrefDict
	"""
	def __init__ (self, severity = RO.Constants.sevNormal):
		self._severity = RO.Constants.sevNormal
		self._severityPrefDict = {} # set when first needed

		if severity != RO.Constants.sevNormal:
			self.setSeverity(severity)
		
	def getSeverity(self):
		"""Return current severity, one of: RO.Constants.sevNormal, sevWarning or sevError.
		"""
		return self._severity
		
	def setSeverity(self, severity):
		"""Update severity information.
		
		Raise ValueError if severity is not one of
		RO.Constants.sevNormal, sevWarning or sevError.
		"""
		if self._severity != severity:
			if severity not in self._severityPrefDict:
				# either severityPrefDict does not exist yet
				# or severity is invalid or both
				if not self._severityPrefDict:
					# set severityPrefDict and subscribe to prefs;
					# then test severity again
					self._severityPrefDict = WdgPrefs.getSevPrefDict()
					for iterseverity, pref in self._severityPrefDict.iteritems():
						if iterseverity == RO.Constants.sevNormal:
							# normal foreground color is already automatically updated
							continue
						pref.addCallback(self._updateSeverityColor, callNow=False)
				if severity not in self._severityPrefDict:
					raise ValueError("Invalid severity %r" % (severity,))
			self._severity = severity
			self._updateSeverityColor()
	
	def _updateSeverityColor(self, *args):
		"""Apply the current color appropriate for the current severity.
		
		Called automatically. Do NOT call manually.
		"""
		color = self._severityPrefDict[self._severity].getValue()
		self.configure(foreground = color)


class SeverityActiveMixin(SeverityMixin):
	"""Version of SeverityMixin for widgets with activeforegound:
	Button, Checkbutton, Menu, Menubutton, Radiobutton, Scale, Scrollbar.
	"""
	def _updateSeverityColor(self, *args):
		"""Apply the specified color."""
		color = self._severityPrefDict[self._severity].getValue()
		self.configure(foreground = color, activeforeground = color)


class SeveritySelectMixin(SeverityMixin):
	"""Version of SeverityMixin for widgets with selectforeground:
	Entry, Listbox, Text (also Canvas, but this class is not
	likely to be helpful for that).
	"""
	def _updateSeverityColor(self, *args):
		"""Apply the specified color."""
		color = self._severityPrefDict[self._severity].getValue()
		self.configure(foreground = color, selectforeground = color)


if __name__ == "__main__":
	import Tkinter
	import PythonTk
	root = PythonTk.PythonTk()
	
	class ColorButton(Tkinter.Button, SeverityActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Button.__init__(self, *args, **kargs)
			SeverityActiveMixin.__init__(self)

	class ColorCheckbutton(Tkinter.Checkbutton, SeverityActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Checkbutton.__init__(self, *args, **kargs)
			SeverityActiveMixin.__init__(self)

	class ColorEntry(Tkinter.Entry, SeveritySelectMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Entry.__init__(self, *args, **kargs)
			SeveritySelectMixin.__init__(self)

	class ColorLabel(Tkinter.Label, SeverityMixin):
		def __init__(self, *args, **kargs):
			Tkinter.Label.__init__(self, *args, **kargs)
			SeverityMixin.__init__(self)

	class ColorOptionMenu(Tkinter.OptionMenu, SeverityActiveMixin):
		def __init__(self, *args, **kargs):
			Tkinter.OptionMenu.__init__(self, *args, **kargs)
			SeverityActiveMixin.__init__(self)
		
	def setSeverity(*args):
		severityStr = severityVar.get()
		severity = {"Normal": RO.Constants.sevNormal,
			"Warning": RO.Constants.sevWarning,
			"Error": RO.Constants.sevError,
		}.get(severityStr)
		print "Set severity to %s = %r" % (severityStr, severity)
		for wdg in wdgSet:
			wdg.setSeverity(severity)

	severityVar = Tkinter.StringVar()
	severityVar.set("Normal")
	severityVar.trace_variable("w", setSeverity)
	
	entryVar = Tkinter.StringVar()
	entryVar.set("Entry")
	wdgSet = (
		ColorOptionMenu(root, severityVar, "Normal", "Warning", "Error",
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
