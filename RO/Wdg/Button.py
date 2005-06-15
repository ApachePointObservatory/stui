#!/usr/local/bin/python
"""Variants on buttons that add help.

History:
2003-04-24 ROwen
2003-06-12 ROwen	Added Radiobutton.
2003-08-04 ROwen	Added addCallback; modified to use RO.AddCallback.
2004-08-11 ROwen	Define __all__ to restrict import.
2004-09-14 ROwen	Tweaked the imports.
2005-06-15 ROwen	Added severity support. Unfortunately, for Button
					it has no visible effect on MacOS X Aqua.
"""
__all__ = ['Button', 'Radiobutton']

import Tkinter
import RO.AddCallback
import RO.Constants
import CtxMenu
from SeverityMixin import SeverityActiveMixin

class Button (Tkinter.Button, RO.AddCallback.TkButtonMixin, CtxMenu.CtxMenuMixin,
	SeverityActiveMixin):
	def __init__(self,
		master,
		helpText = None,
		helpURL = None,
		callFunc = None,
		severity = RO.Constants.sevNormal,
	**kargs):
		"""Creates a new Button.
		
		Inputs:
		- helpText	text for hot help
		- helpURL	URL for longer help
		- callFunc	callback function; the function receives one argument: self.
					It is called whenever the value changes (manually or via
					the associated variable being set).
		- severity	initial severity; one of RO.Constants.sevNormal, sevWarning or sevError
		- all remaining keyword arguments are used to configure the Tkinter Button;
		  command is supported, for the sake of conformity, but callFunc is preferred.
		"""
		self.helpText = helpText

		Tkinter.Button.__init__(self,
			master = master,
		**kargs)
		
		RO.AddCallback.TkButtonMixin.__init__(self, callFunc, False, **kargs)
		
		CtxMenu.CtxMenuMixin.__init__(self,
			helpURL = helpURL,
		)
		SeverityActiveMixin.__init__(self, severity)
	
	def setEnable(self, doEnable):
		if doEnable:
			self["state"] = "normal"
		else:
			self["state"] = "disabled"
	
	def getEnable(self):
		return self["state"] == "normal"


class Radiobutton (Tkinter.Radiobutton, CtxMenu.CtxMenuMixin, SeverityActiveMixin):
	def __init__(self,
		master,
		helpText = None,
		helpURL = None,
		severity=RO.Constants.sevNormal,
	**kargs):
		"""Creates a new Button.
		
		Inputs:
		- helpText	text for hot help
		- helpURL	URL for longer help
		- severity	initial severity; one of RO.Constants.sevNormal, sevWarning or sevError
		- all remaining keyword arguments are used to configure the Tkinter Button
		"""
		self.helpText = helpText

		Tkinter.Radiobutton.__init__(self,
			master = master,
		**kargs)
		CtxMenu.CtxMenuMixin.__init__(self,
			helpURL = helpURL,
		)
		SeverityActiveMixin.__init__(self, severity)
