#!/usr/local/bin/python
"""RO.Wdg.Label widgets are display widgets that store data in its most basic form,
yet know how to format it for display. These widgets consider their data to be bad
(and display it with a bad background color) if the value is None or the value is not current.

Background color is handled as follows:
- Good (normal) background color is copied from a widget whose background is never directly
  modified; hence it tracks changes to the global application background color
- Bad background color cannot be handled in this fashion, so a preference variable is used
  and a callback is registered (that's going to be a painfully slow callback if there
  are a lot of widgets to update).

History:
2002-01-25 ROwen	Fixed handling of default background color;
					now it is read from the widget when that widget is first created,
					so all the standard techniques work for setting that color.
2002-01-30 ROwen	Improved background color handling again;
					it is always read from the option database when the state changes.
2002-03-14 ROwen	Modified to handle isValid argument;
					modified get to return isValid in the tuple; fixed get to return a value instead of None.
2002-03-18 ROwen	Repackaged as part of larger RO.Wdg package.
2002-11-15 ROwen	Added use of CtxMenuMixin.
2002-11-26 ROwen	Added support for helpURL.
2002-12-04 ROwen	Swapped helpURL and helpText args.
2002-12-20 ROwen	Bug fixes: _subscribeStatePrefs was specifying a callback to a nonexistent function;
					setNotCurrent called _setIsCurrent with an extraneous "self";
					corrected typo in error message (pint for point); thanks to pychecker.
2003-03-05 ROwen	Removed all isValid handling; invalid values have value None
2003-03-06 ROwen	Fixed default precision for FloatLabel (was None, which caused errors).
2003-03-17 ROwen	Fixed StrLabels to handle unicode.
2003-04-15 ROwen	Modified to use RO.Wdg.CtxMenu 2003-04-15.
2003-06-17 ROwen	Modified to be in current state by default (so can be used as a general label);
					overhauled setting of state and improved lazy subscription to state colors.
2003-06-18 ROwen	Modified to pass SystemExit and KeyboardInterrupt when
					testing for general errors.
2003-07-25 ROwen	Modified to allow a format string.
2003-12-19 ROwen	Added BoolLabel. Added tests for disallowed keywords.
2004-08-11 ROwen	Modified to use Constants and WdgPrefs.
					Use modified state constants with st_ prefix.
					Define __all__ to restrict import.
2004-09-03 ROwen	Modified for RO.Wdg.st_... -> RO.Constants.st_...
2004-09-14 ROwen	Bug fix: isCurrent was ignored for most classes.
"""
__all__ = ['Label', 'BoolLabel', 'StrLabel', 'IntLabel', 'FloatLabel', 'DMSLabel']

import sys
import Tkinter
import RO.Constants
import RO.MathUtil
import RO.StringUtil
import CtxMenu
import WdgPrefs

class Label(Tkinter.Label, CtxMenu.CtxMenuMixin):
	"""Base class for labels (display ROWdgs); do not use directly.
	
	Inputs:
	- formatStr: formatting string; if omitted, formatFunc is used.
		Displayed value is formatStr % value.
	- formatFunc: formatting function; ignored if formatStr specified.
		Displayed value is formatFunc(value).
	- helpText	short text for hot help
	- helpURL	URL for on-line help
	- isCurrent	sets isCurrent and uses standard background colors
	- **kargs: all other keyword arguments go to Tkinter.Label;
		the defaults are anchor="e", justify="r"
		
	Note: if display formatting fails (raises an exception)
	then "?%r?" % value is displayed.
	"""

	def __init__ (self,
		master,
		formatStr = None,
		formatFunc = unicode,		
		helpText = None,
		helpURL = None,
		isCurrent = True,
	**kargs):
		kargs.setdefault("anchor", "e")
		kargs.setdefault("justify", "r")
		
		Tkinter.Label.__init__(self, master, **kargs)
		
		CtxMenu.CtxMenuMixin.__init__(self, helpURL=helpURL)
		
		self._prefDict = WdgPrefs.getWdgPrefDict()
		self._statePrefDict = WdgPrefs.getWdgStatePrefDict()

		self._formatStr = formatStr
		if formatStr != None:
			formatFunc = self._formatFromStr
		self._formatFunc = formatFunc
		self.helpText = helpText
		self._isCurrent = bool(isCurrent)

		self._value = None
		self._state = RO.Constants.st_Normal
		self._isSubscrStatePrefs = False

		# set up automatic update for bad background color pref
		# (don't do this lazily because there'd be a huge number
		# of subscriptions the first time isCurrent changed --
		# because it usually changes for all labels at once)
		self._prefDict["Bad Background"].addCallback(self._updateBGColor, callNow=False)
		
		if not self._isCurrent:
			self._updateBGColor()

	def get(self):
		"""Return a tuple consisting of (set value, isCurrent).
		
		If the value is None then it is invalid or unknown.
		If isCurrent is false then the value is suspect
		Otherwise the value is valid and current.
		"""
		return (self._value, self._isCurrent)
	
	def getFormatted(self):
		"""Return a tuple consisting of the (displayed value, isCurrent).
		
		If the value is None then it is invalid.
		If isCurrent is false then the value is suspect
		Otherwise the value is valid and current.
		"""
		if self._value == None:
			return (None, self._isCurrent)
		else:
			return (self["text"], self._isCurrent)
	
	def getIsCurrent(self):
		"""Return True if value is current, False otherwise.
		"""
		return self._isCurrent
	
	def getState(self):
		"""Return current state, one of: RO.Constants.st_Normal, st_Warning or st_Error.
		"""
		return self._state
	
	def clear(self, isCurrent=1):
		"""Clear the display; leave state unchanged.
		"""
		self.set(value="", isCurrent=isCurrent)
	
	def set(self,
		value,
		isCurrent=True,
		state = None,
	**kargs):
		"""Set the value

		Inputs:
		- value: the new value
		- isCurrent: is value current (if not, display with bad background color)
		- state: the new state, one of: RO.Constants.st_Normal, st_Warning or st_Error;
		  	if omitted, the state is left unchanged		  
		kargs is ignored; it is only present for compatibility with KeyVariable callbacks.
		
		Raises an exception if the value cannot be coerced.
		"""
		# print "RO.Wdg.Label.set called: value=%r, isCurrent=%r, **kargs=%r" % (value, isCurrent, kargs)
		self._value = value
		self._setIsCurrent(isCurrent)
		if state != None:
			self._setState(state)
		self._updateText()
	
	def setNotCurrent(self):
		"""Mark the data as not current.
		
		To mark the value as current again, set a new value.
		"""
		self._setIsCurrent(False)
	
	def _formatFromStr(self, value):
		"""Format function based on formatStr.
		"""
		return self._formatStr % value

	def _setIsCurrent(self, isCurrent):
		"""Update isCurrent information.
		"""
		isCurrent = bool(isCurrent)
		if self._isCurrent != isCurrent:
			self._isCurrent = isCurrent
			self._updateBGColor()
	
	def _setState(self, state):
		"""Update state information.
		"""
		assert state in self._statePrefDict, "invalid state %r" % (state,)
		if self._state != state:
			self._state = state
			self._updateFGColor()
	
	def _subscribeStatePrefs(self):
		"""Subscribe this widget to state color changes.
		Called automatically if a variable is set with state specified
		as something other than normal.
		(Using lazy evaluation saves needless callbacks).
		"""
		if not self._isSubscrStatePrefs:
			for state, pref in self._statePrefDict.iteritems():
				if state == RO.Constants.st_Normal:
					# normal foreground color is already automatically updated
					continue
				pref.addCallback(self._updateFGColor, callNow=False)
			self._isSubscrStatePrefs = True

	def _updateBGColor(self, *args):
		"""Update the background color based on self._isCurrent.
		*args allows this to be used as a callback.
		"""
		if self._isCurrent:
			self.configure(background=self._prefDict["Background Color"].getValue())
		else:
			self.configure(background=self._prefDict["Bad Background"].getValue())
	
	def _updateFGColor(self, *args):
		"""Update the foreground color based on self._state.
		"""
		try:
			pref = self._statePrefDict[self._state]
		except KeyError:
			sys.stderr.write ("RO.Wdg.Label with value %r is in unknown state %r\n" % (self._value, self._state))
			pref = self._statePrefDict[RO.Constants.st_Error]
		
		self.configure(foreground=pref.getValue())
		if not self._isSubscrStatePrefs and self._state != RO.Constants.st_Normal:
			self._subscribeStatePrefs()
	
	def _updateText(self):
		"""Updates the displayed value. Ignores self._isCurrent and self._state.
		"""
		if self._value == None:
			self["text"] = ""
		else:
			try:
				self["text"] = self._formatFunc(self._value)
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				sys.stderr.write("format of value %r failed with error: %s\n" % (self._value, e))
				self["text"] = "?%r?" % (self._value,)


class BoolLabel(Label):
	"""Label to display string data.
	Inputs are those for Label, but formatStr and formatFunc are forbidden.
	"""
	def __init__ (self,
		master,
		helpText = None,
		helpURL = None,
		trueValue = "True",
		falseValue = "False",
		isCurrent = True,
		**kargs
	):
		assert not kargs.has_key("formatStr"), "formatStr not allowed for %s" % self.__class__.__name__
		assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__

		def formatFnct(val):
			if val:
				return trueValue
			else:
				return falseValue

		Label.__init__(self,
			master,
			formatFunc = formatFnct,
			helpText = helpText,
			helpURL = helpURL,
			isCurrent = isCurrent,
		**kargs)


class StrLabel(Label):
	"""Label to display string data.
	Inputs are those for Label but the default formatFunc is str.
	"""
	def __init__ (self,
		master,
		helpText = None,
		helpURL = None,
		isCurrent = True,
		**kargs
	):
		kargs.setdefault("formatFunc", str)
		
		Label.__init__(self,
			master,
			helpText = helpText,
			helpURL = helpURL,
			isCurrent = isCurrent,
		**kargs)


class IntLabel(Label):
	"""Label to display integer data; truncates floating point data
	Inputs are those for Label, but the default formatStr is "%s" and formatFunc is forbidden.
	"""
	def __init__ (self,
		master,
		helpText = None,
		helpURL = None,
		isCurrent = True,
		**kargs
	):
		kargs.setdefault("formatStr", "%d")
		assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__
		
		Label.__init__(self,
			master,
			helpText = helpText,
			helpURL = helpURL,
			isCurrent = isCurrent,
		**kargs)


class FloatLabel(Label):
	"""Label to display floating point data.
	
	If you specify a format string, that is used and the specified is ignored
	else you must specify a precision, in which case the data is displayed
	as without an exponent and with "precision" digits past the decimal.
	The default precision is 2 digits.
	
	Inputs:
	- precision: number of digits past the decimal point; ignored if formatStr specified
	The other inputs are those for Label but formatFunc is forbidden.
	"""
	def __init__ (self,
		master,
		formatStr=None,
		precision=2,
		helpText = None,
		helpURL = None,
		isCurrent = True,
	**kargs):
		assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__

		# handle default format string
		if formatStr == None:
			formatStr = "%." + str(precision) + "f"
			
		# test and set format string
		try:
			formatStr % (1.1,)
		except:
			raise ValueError, "Invalid floating point format string %s" % (formatStr,)

		Label.__init__(self,
			master,
			formatStr = formatStr,
			helpText = helpText,
			helpURL = helpURL,
			isCurrent = isCurrent,
		**kargs)


class DMSLabel(Label):
	"""Label to display floating point data as dd:mm:ss.ss.
	Has the option to store data in degrees but display in hh:mm:ss.ss;
	this option can be changed at any time and the display updates correctly.
	
	Inputs:
	- precision: number of digits past the decimal point
	- nFields: number of sexagesimal fields to display
	- cnvDegToHrs: if True, data is in degrees but display is in hours
	The other inputs are those for Label, but formatStr and formatFunc are forbidden.
	"""
	def __init__ (self,
		master,
		precision,
		nFields = 3,
		cvtDegToHrs = False,
		helpText = None,
		helpURL = None,
		isCurrent = True,
	**kargs):
		assert not kargs.has_key("formatStr"), "formatStr not allowed for %s" % self.__class__.__name__
		assert not kargs.has_key("formatFunc"), "formatFunc not allowed for %s" % self.__class__.__name__
		
		self.precision = precision
		self.nFields = nFields
		self.cvtDegToHrs = cvtDegToHrs

		Label.__init__(self,
			master,
			formatFunc = self.formatFunc,
			helpText = helpText,
			helpURL = helpURL,
			isCurrent = isCurrent,
		**kargs)
	
	def formatFunc(self, value):
		if self.cvtDegToHrs and value != None:
			value = value / 15.0
		return RO.StringUtil.dmsStrFromDeg (
			value,
			precision = self.precision,
			nFields = self.nFields,
		)
	
	def setCvtDegToHrs(self, cvtDegToHrs):
		if RO.MathUtil.logNE(self.cvtDegToHrs, cvtDegToHrs):
			self.cvtDegToHrs = cvtDegToHrs
			self._updateText()


if __name__ == "__main__":
	import PythonTk
	root = PythonTk.PythonTk()

	wdgSet = (
		BoolLabel(root,
			helpText = "Bool label",
		),
		StrLabel(root,
			helpText = "String label",
		),
		IntLabel(root,
			width=5,
			helpText = "Int label; width=5",
		),
		FloatLabel(root,
			precision=2,
			width=5,
			helpText = "Float label; precision = 2, width=5",
		),
		FloatLabel(root,
			formatStr="%.5g",
			width=8,
			helpText = "Float label; format = '\%.5g', width = 8",
		),
		DMSLabel(root,
			precision=2,
			width=10,
			helpText = "DMS label; precision = 2, width = 10",
		),
		DMSLabel(root,
			precision=2,
			cvtDegToHrs=1,
			width=10,
			helpText = "DMS label; precision = 2, width = 10, convert degrees to hours",
		),
	)
	for wdg in wdgSet:
		wdg.pack(fill=Tkinter.X)
	
	# a list of (value, isCurrent) pairs
	testData = [
		("some text", True),
		("invalid text", False),
		(0, True),
		("", True),
		(False, True),
		(1, True),
		(1234567890, True),
		(1234567890, False),
		(1.1, True),
		(1.9, True),
		(-1.1, True),
		(-1.9, True),
		(-0.001, True),
		(-1.9, False),
	]
	
	ind = 0
	def displayNext():
		global ind, testData
		val = testData[ind]
		print "\nvalue = %r, isCurrent = %s" % tuple(val)
		for wdg in wdgSet:
			wdg.set(*val)
		ind += 1
		if ind < len(testData):
			root.after(1200, displayNext)
	root.after(1200, displayNext)
			
	root.mainloop()
