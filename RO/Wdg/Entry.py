#!/usr/local/bin/python
"""Widgets for floating point, integer and sexagesimal input using Tkinter.
These widgets have many useful features, including:
- default values
- contextual help
- entry validation

Numeric input fields also offer:
- getNum to return a value in numeric form
- the various set methods accept numbers or strings
- range checking
- configurable formatting

Validation error handling:
- The event <<EntryError>> is generated
- The receiver should use wdg.getEntryError to read the error text

To Do:
- Allow setting isCurrent and state via the "set" method;
  modify KeyVariable as needed so callbacks still work.
- Add an automatic isCurrent mode, whereby isCurrent is false
  if the current value is not the default value
  or the default is not current.
  
History:
2002-02-06 ROwen 	bug fix: IntEntry allowed floating point notation.
2002-03-08 ROwen 	bug fix: FloatEntry. setDefValue broken; used checkRange without namespace.
2002-07-29 ROwen 	DMSEntry neatenValue now only sets the Tk variable if it will change.
					This avoids triggering needless callbacks.
2002-08-01 ROwen 	Removed scaling option; widgets cannot return numerical values in different
					units than those displayed. It was just too messy (though some of that mess
					made its way into DMSEntry to handle setIsHours).
					Modified many methods to accept values as numbers or formatted strings;
					thus you can now specify defaults exactly as you wish them to appear.
					Added methods asStr and asNum.
					IntEntry now can only contain true integers; with scale gone
					there was no need for the mess of rounding floats.
					If the lower limit is 0 then minus signs may not be entered.
2002-11-15 ROwen 	Added _BaseEntry and StringEntry. Added support for CtxMenuMixin.
2002-11-26 ROwen 	Added support for helpURL.
2002-12-04 ROwen	Swapped helpText and helpURL args.
2002-12-20 ROwen	Fixed typo in DMSEntry: restoreDefault->resetDefault;
					fixed SEL_FIRST/LAST -> Tkinter.SEL_FIRST/LAST in DMSEntry;
					removed getHelp and hasHelp (both obsolete) from DMSEntry;
					minor cleanups. All thanks to pychecker.
2003-02-26 ROwen	Readonly widgets no longer take focus (though you can still
					click to leave the insertion cursor in them, alas).
2003-03-07 ROwen	Renamed StringEntry to StrEntry to match the Python standard abbreviation.
2003-03-12 ROwen	Added defIfDisabled
2003-03-20 ROwen	Bug fix in DMSEntry: initially specified min and max values could be munged
2003-03-24 ROwen	Improved the units display (but units now can be 6 characters wide)
2003-04-03 ROwen	Modified to not change blank to default on focus out.
2003-04-11 ROwen	Overhauled value checking:
					- removed leading _ from checkValue
					- added checkPartialValue
					- issue event <<EntryError>> on entry error instead of printing to stderr
					Added numeric base class _NumEntry, which includes checkPartialValue
					to handle ranges that do not include 0.
					Ditched "Default" menu item; it's rarely wanted,
					and when it is wanted it often wants another name.
2003-04-15 ROwen	Overhauled to use CtxMenu 2003-04-15;
					Added clearMenu and defMenu to all items;
					and minMenu and maxMenu to numerical items.
2003-04-21 ROwen	Modified numeric entry widgets to compute default width to fit.
2003-04-24 ROwen	Added addCallback; modified to call callbacks when setDefValue called.
2003-04-28 ROwen	Added getEnable; removed __setEnable and getEnableVar;
					modified to only show help in the ctx menu if disabled.
2003-05-28 ROwen	Implemented callbacks properly (in particular,
					callers never receive invalid values).
2003-05-29 ROwen	Fixed getEnable to return True if the state is "active".
2003-06-13 ROwen	Fixed StrEntry to accept unicode strings.
2003-07-09 ROwen	Modified to call back with self instead of value;
					modified to use RO.AddCallback;
					added omitExtraFields to DMSEntry.
2003-07-16 ROwen	Added UnicodeEntry; made StrEntry reject non-ascii.
2003-07-24 ROwen	Added default of None (no limit) for minValue and maxValue;
					Entry widgets now start out by displaying their default value.
2003-10-14 ROwen	Changed defIfDisabled to defIfBlank.
2003-10-22 ROwen	Modified to retain focus if final check fails;
					moved entry error beep to <<EntryError> handler in StatusBar
					so others can catch <<EntryError>> and handle it differently;
					changed entry error message to quote the invalid value.
2003-10-27 ROwen	Bug fix: set did not raise ValueError for invalid values
					(though it did issue an <<EntryError>> event),
					and it only called checkPartialValue instead of checkValue,
					thus letting some invalid values slip through.
2003-11-04 ROwen	Improved error message for setRange;
					bug fix: if default = "" then setRange would fail if it did not include 0.
2003-11-07 ROwen	Modified to not create a StringVar unless it'll be used.
2003-11-17 ROwen	Added DirectoryEntry, FileEntry.
					Changed _BaseEntry.checkPartialValue to do nothing,
					instead of calling checkValue; existing subclasses overrode it anyway
					and it was illogical and messed up DirectoryEntry and FileEntry.
					Changed StrEntry: renamed validPattern to finalPattern and made
					finalPattern = partialPattern by default (instead of visa versa);
					this matches StrPrefVar and seemed more logical to me.
				
2003-12-05 ROwen	Changed setDefValue to setDefault for consistency.
2003-12-12 ROwen	Added isOK and renamed _setEntryError to setEntryError
					to make it a public method.
2004-03-04 ROwen	Changed UnicodeEntry->StrEntry, StrEntry->ASCIIEntry;
					this better matches how Python works.
2004-07-20 ROwen	Added Cut/Copy/Paste to the contextual menu.
2004-08-10 ROwen	Added Select All to the contextual menu.
2004-08-11 ROwen	Removed DirectoryEntry and FileEntry (since prefs no longer use them).
					Define __all__ to restrict import.
2004-09-14 ROwen	Bug fix to test code (used two obsolete classes).
					Minor changes to make pychecker happy.
2004-09-24 ROwen	Added unitsSuffix to DMSEntry.
2004-10-01 ROwen	Bug fix: HTML help was broken for numeric entry widgets.
2004-10-11 ROwen	Fixed units for relative DMS fields (' and " swapped)
2004-12-29 ROwen	Preliminary isCurrent and state support (see To Do list above).
"""
__all__ = ['StrEntry', 'ASCIIEntry', 'FloatEntry', 'IntEntry', 'DMSEntry']

#import os
import re
import Tkinter
import RO.AddCallback
import RO.CnvUtil
import RO.StringUtil
import RO.MathUtil
import Bindings
import CtxMenu
from IsCurrentMixin import IsCurrentActiveMixin
from StateMixin import StateSelectMixin

class _BaseEntry (Tkinter.Entry, RO.AddCallback.BaseMixin,
	IsCurrentActiveMixin, StateSelectMixin, CtxMenu.CtxMenuMixin):
	"""Base class for RO.Wdg entry widgets.
	
	Subclasses may wish to override:
	- asStr
	- checkValue
	- checkPartialValue
	- neatenDisplay

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- defValue	default value;
				"" or None mean a blank field
	- var		a StringVar to use as the widget's Tk variable
	- helpText	a string that describes the widget
	- helpURL	URL for on-line help
	- readOnly	set True if you want to prevent the user from changing the text
				the user will still be able to copy the text
				and the widget can still be updated via set, etc.
				note that readOnly prevents any clear/default/etc menu items.
	- callFunc	callback function; the function receives one argument: self.
				It is called whenever the value changes (manually or via
				the associated variable being set) and when setDefault is called.
	- clearMenu	name of "clear" contextual menu item, or None for none
	- defMenu	name of "restore default" contextual menu item, or None for none
	- defIfBlank	setDefault also sets the value if value is blank.
	- any additional keyword arguments are used to configure the widget;
				the default width is 8
				text and textvariable are silently ignored (use var instead of textvariable)
	"""
	def __init__ (self,
		master,
		defValue = None,
		var = None,
		helpText = None,
		helpURL = None,
		readOnly = False,
		callFunc=None,
		clearMenu = "Clear",
		defMenu = None,
		defIfBlank = True,
		isCurrent = True,
		state = RO.Constants.st_Normal,
	**kargs):
		self.defValueStr = ""
		if var == None:
			var = Tkinter.StringVar()	
		self.var = var
		self.helpText = helpText
		self._readOnly = readOnly
		self.clearMenu = clearMenu
		self.defMenu = defMenu
		self._defIfBlank = defIfBlank

		self._entryError = None

		IsCurrentActiveMixin.__init__(self, isCurrent)
		StateSelectMixin.__init__(self, state)
		
		# status widget stuff
		self.errMsgID = None	# ID for validation error messages
		self.helpMsgID = None	# ID for help messages
		
		# set default widget configuration
		kargs.setdefault("width", 8)
		if kargs.has_key("text"):
			del(kargs["text"])
		kargs["textvariable"] = self.var  # overrides user attempt to set
		
		Tkinter.Entry.__init__(self, master, **kargs)
		
		self.currStrVal = ""
		self.var.trace_variable("w", self._checkVar)

		# use BaseMixin and trigger callbacks manually instead of using TkVarMixin
		# because the value checking may modify the variable,
		# which would cause TkVarMixin to issue multiple callbacks.
		RO.AddCallback.BaseMixin.__init__(self)
		
		# set default -- do after binding check function
		# and setting range and etc, so we are sure the default value
		# can be represented in the default format
		self.setDefault(defValue)

		CtxMenu.CtxMenuMixin.__init__(self, helpURL = helpURL)

		self.bind("<FocusOut>", self._focusOut)
		
		if self._readOnly:
			Bindings.makeReadOnly(self)
			self["takefocus"] = False

		# add callback function after setting default
		# to avoid having the callback called right away
		if callFunc:
			self.addCallback(callFunc, False)
	
	def asStr(self,
		val,
	):
		"""Returns any valid value as a string or unicode.
		Useful if numbers or other non-strings are valid values,
		but doesn't do much in the base class.
		If val is "" or None, returns "".
		"""
		if val == None:
			return ""
		return RO.CnvUtil.asStr(val)

	def clear(self):
		self.var.set("")

	def _ctxAddSetItem(self, menu, descr, value):
		"""Add a set value item to the contextual menu.
		"""
		if descr and value != None:
			menuText = "%s (%s)" % (descr, value)
			def setValue():
				self.set(value)
			menu.add_command(label = menuText, command = setValue)
	
	def ctxConfigMenu(self, menu):
		"""Configure the contextual menu.
		Called just before the menu is posted.
		"""
		if not self.getEnable():
			return True

		stateDict = {
			True:"normal",
			False:"disabled",
		}
		selPresent = self.selection_present()
		dataPresent = self.getString() != ""
		if self._readOnly:
			menu.add_command(
				label = "Copy",
				command = self.copy,
				state = stateDict[selPresent],
			)
			return True

		try:
			clipPresent = (self.selection_get(selection="CLIPBOARD") != "")
		except Tkinter.TclError:
			clipPresent = False

		if self.clearMenu:
			menu.add_command(
				label = self.clearMenu,
				command = self.clear,
				state = stateDict[dataPresent],
			)
			menu.add_command(
				label = "Cut",
				command = self.cut,
				state = stateDict[selPresent],
			)
		menu.add_command(
			label = "Copy",
			command = self.copy,
			state = stateDict[selPresent],
		)
		menu.add_command(
			label = "Paste",
			command = self.paste,
			state = stateDict[clipPresent],
		)
		menu.add_separator()
		menu.add_command(
			label = "Select All",
			command = self.selectAll,
			state = stateDict[dataPresent],
		)
				
		self._ctxAddSetItem(menu, self.defMenu, self.defValueStr)
		return True
	
	def cut(self):
		"""Cut the selection to the clipboard.
		"""
		if not self._readOnly:
			self.event_generate("<<Cut>>")
	
	def copy(self):
		"""Copy the selection to the clipboard.
		"""
		self.event_generate("<<Copy>>")
	
	def paste(self):
		"""Replace the selection with the contents of the clipboard.
		Works better than the default paste IMHO.
		"""
		if not self._readOnly:
			self.event_generate("<<Paste>>")
	
	def getDefault(self):
		"""Returns the default value as a string"""
		return self.defValueStr
	
	
	def getEnable(self):
		"""Returns False if the state is disabled,
		True otherwise (state is normal or active)
		"""
		return self["state"] != Tkinter.DISABLED

	def getEntryError(self):
		"""Returns the current validation error.
		For use by <<EntryError>> handlers.
		"""
		return self._entryError
	
	def getString(self):
		"""Returns the text of the field; returns "" if empty.
		"""
		return self.var.get()
		
	def getStringOrDefault(self):
		"""Returns the current value of the field, or the default if blank
		"""
		val = self.var.get()
		return val or self.defValueStr
	
	def getVar(self):
		return self.var
	
	def isOK(self):
		"""Checks the value and neatens it.
		Returns True if value OK, False otherwise.
		
		Call before using the value.
		"""
		try:
			self.checkValue(self.var.get())
			self.neatenDisplay()
		except (ValueError, TypeError), e:
			self.setEntryError(str(e))
			self.focus_set()
			return False

		if self._entryError:
			self.setEntryError(None)
		return True		

	def neatenDisplay(self):
		"""Neatens the display.
		
		Does nothing in the base class.
		"""
		pass
	
	def restoreDefault(self):
		"""Sets the default value, after checking it"""
		self.set(self.defValueStr)
	
	def selectAll(self):
		"""Select all text in the Entry.
		Has no effect if there is no text.
		"""
		self.selection_range(0, "end")

	def set(self, newVal, *args, **kargs):
		"""Set the field from a native value or formatted string.
		If the value is None, sets the field blank.

		Error conditions:
		- Raises ValueError and leaves the widget unchanged
		  if newVal is is invalid (including out of range for numeric entry widgets).
		"""
		if newVal != None:
			self.checkValue(newVal)
		self.var.set(self.asStr(newVal))
	
	def setDefault(self, newDefValue, *args, **kargs):
		"""Changes the default value.
		
		Also, if the wiget was never set then updates the displayed value.

		Error conditions:
		- Raises ValueError and leaves the default unchanged
		  if the new default value is invalid.
		"""
		self.checkValue(newDefValue, "new default value")
		self.defValueStr = self.asStr(newDefValue)
		if self._defIfBlank and self.getString() == "":
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
	
	def setEntryError(self, errMsg):
		"""Call to report or clear the entry error.
		
		Inputs:
		- errMsg	a string or None (to clear the error)
		"""
		self._entryError = errMsg
		self.event_generate("<<EntryError>>")
	
	def checkValue(self, val, descr=None):
		"""Raise an exception if the final value "val" is invalid.
		The exception should include the string "descr".
		
		Warning: checkValue must catch all the errors caught by
		checkPartialValue, else values given to set will not be
		properly verified.
		
		Does nothing in the base class.
		
		The exception raised should be one of ValueError or TypeError.
		"""
		return
		
	def checkPartialValue(self, val, descr=None):	
		"""Raise an exception if partial value "val" is invalid.
		The exception should include the string "descr".

		Example: for a number one should check that the value
		contains valid characters, but one should not check the range
		since the number has not yet been fully entered.
		
		Does nothing in the base class.
		
		The exception raised should be one of ValueError or TypeError.
		"""
		return
	
	def _checkVar(self, *args, **kargs):
		"""This method is called whenever the variable changes.
		It checks the value using checkPartialValue
		and restores it if the value is invalid.
		If the value is valid, it calls the callback functions.
		"""
		try:
			newStrVal = self.getString()
			self.checkPartialValue(newStrVal)
			self.currStrVal = newStrVal
			if self._entryError:
				self.setEntryError(None)
		except (ValueError, TypeError), e:
			self.setEntryError(str(e))
			self.var.set(self.currStrVal)
	
		if self._callbacks:
			self._doCallbacks()

	def _focusOut(self, evt=None):
		"""Checks the final value and neatens the display.
		"""
		currVal = self.var.get()
		try:
			self.checkValue(currVal)
			self.neatenDisplay()
			if self._entryError:
				self.setEntryError(None)
		except (ValueError, TypeError), e:
			self.setEntryError(str(e))
			self.focus_set()
			return "break"
		self.icursor("end")
		return None


class StrEntry (_BaseEntry):
	"""A widget for entering and validating strings
	(which may contain unicode characters).

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- partialPattern	a regular expression string which partial values must match
	- finalPattern	a regular expression string that the final value must match;
		if omitted, defaults to partialPattern
	- all other inputs for _BaseEntry.__init__
	
	Note for regular expression patterns:
	- your pattern must end with $ to match the entire string;
	  otherwise an entry will be accepted if any initial part matches
	"""
	def __init__ (self,
		master,
		partialPattern = None,
		finalPattern = None,
	**kargs):
		self.partialPatternStr = partialPattern
		if finalPattern == None:
			finalPattern = partialPattern
		self.finalPatternStr = finalPattern

		class NullRE:
			"""This class emulates a compiled regular expression
			just enough to make StrEntry think the value always matches.
			"""
			def match(self, str):
				return True

		if self.finalPatternStr:
			self.finalPatternCompiled = re.compile(self.finalPatternStr)
		else:
			self.finalPatternCompiled = NullRE()
		if self.partialPatternStr:
			self.partialPatternCompiled = re.compile(self.partialPatternStr)
		else:
			self.partialPatternCompiled = NullRE()
		
		_BaseEntry.__init__(self, master=master, **kargs)

	def checkValue(self, val, descr=None):
		"""Raise ValueError if the final value "val" is invalid.
		"""
		# print "StrEntry checkValue(%r, %r)" % (val, descr)
		if val in (None, ""):
			return
		if not self.finalPatternCompiled.match(val):
			errStr = "%r invalid" % (val,)
			if descr:
				errStr += " for %s" % (descr,)
			raise ValueError, errStr
	
	def checkPartialValue(self, val, descr=None):
		"""Raise ValueError if val is invalid.
		"""
		# print "StrEntry checkPartialValue(%r, %r)" % (val, descr)
		if val in (None, ""):
			return
		if not self.partialPatternCompiled.match(val):
			errStr = "%r invalid" % (val,)
			if descr:
				errStr += " for %s" % (descr,)
			raise ValueError, errStr

class ASCIIEntry (StrEntry):
	"""A widget for entering and validating ASCII strings..

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- partialPattern	a regular expression string which partial values must match
	- finalPattern	a regular expression string that the final value must match;
		if omitted, defaults to partialPattern
	- all other inputs for _BaseEntry.__init__
	
	Note for regular expression patterns:
	- your pattern must end with $ to match the entire string;
	  otherwise an entry will be accepted if any initial part matches
	"""
	def asStr(self,
		val,
	):
		"""Return any valid value as an ASCII string;
		raise UnicodeDecodeError otherwise.
		"""
		if val == None:
			return ""
		return RO.CnvUtil.asASCII(val)

	def checkValue(self, val, descr=None):
		"""Raise UnicodeDecodeError if the final value "val" is invalid.
		"""
		# print "ASCIIEntry checkValue(%r, %r)" % (val, descr)
		if val in (None, ""):
			return
		
		# verify data is ASCII
		RO.CnvUtil.asASCII(val)
		
		# standard Str checks
		StrEntry.checkValue(self, val, descr)

	def checkPartialValue(self, val, descr=None):
		"""Raise UnicodeDecodeError if the partial value "val" is invalid.
		"""
		# print "ASCIIEntry checkPartialValue(%r, %r)" % (val, descr)
		if val in (None, ""):
			return
		
		# verify data is ASCII
		RO.CnvUtil.asASCII(val)

		# standard Str checks
		StrEntry.checkPartialValue(self, val, descr)


#class DirectoryEntry(_BaseEntry):
#	"""Edit a path to an existing directory.
#
#	Inputs are identical to _BaseEntry
#	"""
#	def checkValue(self, val, descr=None):
#		"""Check that the folder exists"""
#		if val in (None, ""):
#			return
#		if not os.path.isdir(val):
#			if not os.path.exists(val):
#				errStr = "directory %r does not exist" % (val,)
#			else:
#				errStr = "%r is not a directory" % (val,)
#			if descr:
#				errStr += " for %s" % (descr,)
#			raise ValueError, errStr
#		
#
#class FileEntry(_BaseEntry):
#	"""Edit a path to an existing file.
#
#	Inputs are identical to _BaseEntry
#	"""
#	def checkValue(self, val, descr=None):
#		"""Check that the folder exists"""
#		if val in (None, ""):
#			return
#		if not os.path.isfile(val):
#			if not os.path.exists(val):
#				errStr = "file %r does not exist" % (val,)
#			else:
#				errStr = "%r is not a file" % (val,)
#			if descr:
#				errStr += " for %s" % (descr,)
#			raise ValueError, errStr


class _NumEntry (_BaseEntry):
	"""Base class for numerical entry widgets.
	Simply adds range checking.
	
	Subclasses must define numFromStr and may wish to redefine strFromNum

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- minValue	minimum acceptable value, as a numer or formatted string
	- maxValue	maximum acceptable value, as a numer or formatted string
	- all other inputs for _BaseEntry.__init__
	  (note that defValue can be a number or a formatted string)
	- any additional keyword arguments are used to configure the widget;
		the default width is just enough to fit the smallest and largets number
		using the default format, or 8 if that cannot be computed
		(min value, max value or default format not specified);
		the default justify is "right";
		text and textvariable are silently ignored (use var instead of textvariable)
	"""
	def __init__ (self,
		master,
		minValue = None,
		maxValue = None,
		defValue = None,
		defFormat = None,
		minMenu = None,
		maxMenu = None,
	**kargs):
		self.defFormat = defFormat
		self.minMenu = minMenu
		self.maxMenu = maxMenu
		
		minNum = self.asNum(minValue)
		maxNum = self.asNum(maxValue)
		self._basicSetRange(minNum, maxNum)
		
		if not kargs.has_key("width"):
			if None in (minNum, maxNum, defFormat):
				kargs["width"] = 8
			else:
				kargs["width"] = max(len(defFormat % (minNum,)), len(defFormat % (maxNum,)))
	
		kargs.setdefault("justify", "right")
		
		# initialize the base class last, so the default value is properly checked
		_BaseEntry.__init__(self,
			master = master,
			defValue = defValue,
		**kargs)

	def numFromStr(self, strVal):
		"""Converts a formatted string to a number.
		Raises ValueError if the string is invalid.
		Does no range checking or default handling!
		
		Subclasses must override
		"""
		raise RuntimeError, "subclass must define numFromStr"

	def strFromNum(self,
		numVal,
		format=None,
	):
		"""Returns the value appropriately formatted.
		If numVal is None, returns ""
		If format is omitted, the default format is used.
		Performs no range checking.
		"""
		if numVal == None:
			return ""

		if format == None:
			format = self.defFormat
		try:
			return format % (numVal,)
		except:
			raise ValueError, "Cannot format data %r with format %r" % (numVal, format)

	def asNum(self, val):
		"""Returns any valid value -- formatted string or number -- as a number.
		If val is "" or None, returns None
		Performs no range checking.
		"""
		if isinstance(val, str):
			return self.numFromStr(val)
		return val
	
	def asStr(self,
		val,
		format=None,
	):
		"""Returns any valid value -- formatted string or number -- as a string.
		If val is "" or None, returns "".
		If format is omitted, the default format is used.
		Performs no range checking.
		"""
		if isinstance(val, str):
			return val
		return self.strFromNum(val, format)

	def getNum(self):
		"""Return the numerical value of the field.
		Returns the default value if empty or invalid (and None if the default value is "" or None)
		Does no range checking (that should be done elsewhere).
		"""
		strVal = self.getStringOrDefault()
		try:
			return self.numFromStr(strVal)
		except:
			return self.numFromStr(self.defValueStr)

	def ctxConfigMenu(self, menu):
		"""Add contextual menu items after cut/copy/paste and before help.
		"""
		_BaseEntry.ctxConfigMenu(self, menu)
		self._ctxAddSetItem(menu, self.maxMenu, self.strFromNum(self.maxNum))
		self._ctxAddSetItem(menu, self.minMenu, self.strFromNum(self.minNum))
		return True

	def _basicSetRange(self, minNum, maxNum):
		"""Changes the allowed range of values. Does no checking.
		"""
		self.minNum = minNum
		self.maxNum = maxNum

		if minNum > 0:
			self.minPartialNum = None
		else:
			self.minPartialNum = minNum
		if maxNum < 0:
			self.maxPartialNum = None
		else:
			self.maxPartialNum = maxNum
	

	def setRange(self, minValue, maxValue):
		"""Changes the allowed range of values.
		If the current value is out of range, the default value is restored.
		
		Raises ValueError if the new range does not include the default value
		"""
		# check new range to be sure it includes the default value
		minNum = self.asNum(minValue)
		maxNum = self.asNum(maxValue)
		if self.defValueStr != "":
			# test that default is included in range
			try:
				RO.MathUtil.checkRange(self.asNum(self.defValueStr), minNum, maxNum)
			except ValueError:
				raise ValueError("range [%r, %r] does not include default %r" % (minNum, maxNum, self.defValueStr))
		elif minNum > maxNum:
			# ignore the default but sanity-check the range
			raise ValueError("range [%r, %r] has min>max" % (minValue, maxValue))
		
		self._basicSetRange(minNum, maxNum)

		# if the current value is out of range, restore the field to its default
		try:
			self.checkValue(self.getNum())
		except ValueError:
			self.restoreDefault()

	def checkValue(self, val, descr=""):
		"""Checks that a value (number or string) is well formed and in range"""
		if val in (None, ""):
			return
		if self.minNum >= 0 and isinstance(val, str) and "-" in val:
			raise ValueError, "%s cannot be negative" % (descr,)

		RO.MathUtil.checkRange(self.asNum(val), self.minNum, self.maxNum, descr)

	def checkPartialValue(self, val, descr=""):
		"""Checks that a partial value (number or string) is well formed and in range.
		If minVal > 0 then minimum cannot be checked.
		If maxVal < 0 then maximum cannot be properly checked.
		"""
		if val in (None, ""):
			return
		if self.minNum >= 0 and isinstance(val, str) and "-" in val:
			raise ValueError, "%s cannot be negative" % (descr,)
		
		RO.MathUtil.checkRange(self.asNum(val), self.minPartialNum, self.maxPartialNum, descr)


class FloatEntry (_NumEntry):
	"""A widget for entering floating point numbers with validity and range checking.

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- minValue	minimum acceptable value, as a numer or formatted string
	- maxValue	maximum acceptable value, as a numer or formatted string
	- defFormat	default format used when converting numbers to strings
	- allowExp	true to allow exponential notation; false by default
	- all other inputs for _BaseEntry.__init__
	  (note that defValue can be a number or a formatted string)
	- any additional keyword arguments are used to configure the widget;
		the default width is just enough to fit the smallest and largets number
		using the default format, or 8 if that cannot be computed
		(min value, max value or default format not specified);
		the default justify is "right";
		text and textvariable are silently ignored (use var instead of textvariable)
	"""
	def __init__ (self,
		master,
		minValue = None,
		maxValue = None,
		defValue = None,
		defFormat = "%.2f",
		allowExp = 0,
	**kargs):
		self.allowExp = allowExp
		
		kargs.setdefault("justify", "right")
		
		# initialize the base class
		_NumEntry.__init__(self,
			master = master, 
			minValue = minValue,
			maxValue = maxValue,
			defValue = defValue,
			defFormat = defFormat,
		**kargs)

	def numFromStr(self, strVal):
		"""Converts a formatted string to a number.
		Raises ValueError if the string is invalid.
		Does no range checking or default handling!
		"""
		return RO.StringUtil.floatFromStr(strVal, allowExp=self.allowExp)


class IntEntry(_NumEntry):
	"""A widget for entering decimal integer numbers
	with validity and range checking.

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- minValue	minimum acceptable value, as a numer or formatted string
	- maxValue	maximum acceptable value, as a numer or formatted string
	- all other inputs for _BaseEntry.__init__
	  (note that defValue can be a number or a formatted string)
	- any additional keyword arguments are used to configure the widget;
		the default width is just enough to fit the smallest and largets number
		using the default format, or 8 if that cannot be computed
		(min value, max value or default format not specified);
		the default justify is "right";
		text and textvariable are silently ignored (use var instead of textvariable)
	"""
	def __init__ (self,
		master,
		minValue = None,
		maxValue = None,
		defValue = None,
	**kargs):
		kargs.setdefault("defFormat", "%d")
		_NumEntry.__init__(self,
			master = master,
			minValue = minValue,
			maxValue = maxValue,
			defValue = defValue,
		**kargs)
	
	def numFromStr(self, strVal):
		"""Converts a string to a number.
		Raises ValueError if the string is invalid.
		Does no range checking or default handling!
		"""
		return RO.StringUtil.intFromStr(strVal)


class DMSEntry (_NumEntry):
	"""A widget for entering sexagesimal numbers (e.g. ddd:mm:ss.ss)
	with validity and range checking.

	Inputs:
	- master	master Tk widget -- typically a frame or window
	- minValue	minimum acceptable value; a string or number is acceptable
	- maxValue	maximum acceptable value; a string or number is acceptable
	- defValue	default value; a string or number is acceptable;
				if specified, it must be in range
				"" and None are acceptable to mean a blank field
	- defFormat a tuple consisting of (# of fields, precision of right-most field)
	- omitExtraFields	don't show unnecessary fields when defFormat is used
				(counting from the left if isRelative is True, from the right otherwise);
				typically you'll want this True if isRelative True and False otherwise.
	- isRelative	controls units of numerical value and meaning of omitted fields:
				if false: numerical values are in deg; strings are d.d, d:m.m or d:m:s.s
				if true:  numerical values are in seconds; strings are s.s, m:s.s or d:m:s.s
				where d means degrees or hours, depending on isHours
				Set True for intervals of time or changes in position,
				False for absolute positions or times.
	- var		a StringVar to use as the widget's Tk variable
	- unitsVar	if supplied, this variable is updated with the units
				as the number of fields entered changes, e.g.:
				1 field: "h(m:s)", 2 fields: "h:m(s)", 3 fields: h:m:s
	- unitsSuffix	text to append to the units; ignored if unitsVar not supplied
	- isHours	units are h:m:s, not deg:':"; see also isRelative
	- any additional keyword arguments are used to configure the widget;
		the default width is 13 (just enough to display -ddd:mm:ss.ss);
		the default justify is "left";
		text and textvariable are silently ignored (use var instead of textvariable).
	"""
	
	def __init__ (self,
		master,
		minValue = None,
		maxValue = None,
		defValue = None,
		defFormat = (3, 1),
		omitExtraFields = False,
		isRelative = False,
		var = None,
		unitsVar = None,
		unitsSuffix = "",
		isHours = False,
	**kargs):
		self.isRelative = bool(isRelative)
		self.unitsVar = unitsVar
		self.unitsSuffix = unitsSuffix
		self.isHours = bool(isHours)
		self.omitExtraFields = omitExtraFields
		
		kargs.setdefault("width", 13)
		_NumEntry.__init__(self,
			master = master,
			minValue = minValue,
			maxValue = maxValue,
			defValue = defValue,
			defFormat = defFormat,
			var = var,
		**kargs)

		# set units variable
		self._setUnitsVar()
	
		self.bind("<KeyPress>", self._keyPress)
		self.bind("<Option-KeyPress>", self._optionKeyPress)
		
	def getIsHours(self):
		return self.isHours

	def numFromStr(self, strVal):
		"""Converts a formatted string to a number.
		Raises ValueError if the string is invalid.
		Does no range checking or default handling!
		"""
		if self.isRelative:
			return RO.StringUtil.secFromDMSStr(strVal)
		else:
			return RO.StringUtil.degFromDMSStr(strVal)

#	def set(self, stringValue):
#		"""Set the field from a string; neaten the data and reject bad data.
#
#		error conditions:
#			raises ValueError if the string cannot be parsed
#		"""
#		self.var.set(neatenDMSStr(stringValue))
	
	def setIsHours(self, isHours, resetCurrent=0):
		"""Specifies whether or not the units are hours.
		
		Inputs:
		- isHours		is the representation in hours? (else in degrees)
		- resetCurrent	how to handle the current value *if* the representation changes:
						- if true: reset the field to the default
						- if false: rescale the current value
		
		If the representation changes (e.g. was in hours but now is not) then:
		- The default format's precision is increased by 1 if going from degrees to hours
		  and decreased by 1 if going the other way
		- The minimum and maximum values are rescaled
		- The default value is rescaled, altering the precision
		- The current value is reset to the default if resetCurrent is true
		  else it is scaled as for the default value
		"""
		# figure out what to do
		if isHours and not self.isHours:
			scale = 1.0 / 15.0
			deltaPrec = 1
		elif self.isHours and not isHours:
			scale = 15.0
			deltaPrec = -1
		else:
			# the representation does not change, do nothing
			return
		
		# adjust the precision
		nFields, precision = self.defFormat
		precision += deltaPrec
		self.defFormat = (nFields, precision)

		# scale the limits		
		if self.minNum:
			self.minNum *= scale
		if self.maxNum:
			self.maxNum *= scale
		if self.minPartialNum:
			self.minPartialNum *= scale
		if self.maxPartialNum:
			self.maxPartialNum *= scale
		
		# scale the default value; preserve the number of fields and adjust the precision
		if self.defValueStr:
			nFields, precision = RO.StringUtil.dmsStrFieldsPrec(self.defValueStr)
			precision += deltaPrec
			newNumVal = self.numFromStr(self.defValueStr) * scale
			self.set(self.strFromNum(newNumVal, (nFields, precision)))
		
		# handle current value
		if resetCurrent:
			# reset the current value to the default
			self.restoreDefault()
		else:
			# scale the current value; preserve the number of fields and adjust the precision
			oldValueStr = self.var.get()
			if oldValueStr:
				nFields, precision = RO.StringUtil.dmsStrFieldsPrec(oldValueStr)
				precision += deltaPrec
				newNumVal = self.numFromStr(oldValueStr) * scale
				self.set(self.strFromNum(newNumVal, (nFields, precision)))
		
		# final cleanup
		self.isHours = isHours
		self._setUnitsVar()

	def strFromNum(self,
		numVal,
		format=None,
	):
		"""Returns the value appropriately formatted.
		If numVal is None, returns ""
		If format is omitted, the default format is used.
		Performs no range checking.
		"""
		if numVal == None:
			return ""

		if format == None:
			format = self.defFormat
		try:
			nFields, precision = format
		except:
			raise ValueError, "invalid format %r" % (format,)

		try:
			if self.isRelative:
				return RO.StringUtil.dmsStrFromSec(
					numVal,
					nFields = nFields,
					precision = precision,
					omitExtraFields = self.omitExtraFields,
				)
			else:
				return RO.StringUtil.dmsStrFromDeg(
					numVal,
					nFields = nFields,
					precision = precision,
					omitExtraFields = self.omitExtraFields,
				)
		except ValueError:
			raise ValueError, "Cannot format data %r with format %r" % (numVal, format)
	
	def neatenDisplay(self):
		"""Neaten up the display -- preserve the final field as is
		(rather than trying to guess the # of digits to display),
		but format the others.
		"""
		currVal = self.var.get()
		neatValue = RO.StringUtil.neatenDMSStr(currVal)
		if currVal != neatValue:
			self.var.set(neatValue)

	def _checkVar(self, *args, **kargs):
		_NumEntry._checkVar(self, *args, **kargs)
		self._setUnitsVar()
	
	def _setUnitsVar(self):
		"""Sets the units variable appropriately.
		"""
		if not self.unitsVar:
			return
			
		nFields, precision = RO.StringUtil.dmsStrFieldsPrec(self.var.get())
		if nFields not in (1,2,3):
			# if data is blank or wierd, show for 1 field
			nFields = 1
		
		# keys are (isRelative, nFields)
		unitsSepDict = {
			(False, 1):("",  "(", ":", ")"),
			(False, 2):("",  ":", "(", ")"),
			(False, 3):("",  ":", ":", ""),
			
			(True, 1):("(", ":", ")", ""),
			(True, 2):("(", ")", ":", ""),
			(True, 3):("",  ":", ":", ""),
		}
		unitsSepTuple = unitsSepDict[(self.isRelative, nFields)] + (self.unitsSuffix,)
		if self.isHours:
			unitsStr = "%sh%sm%ss%s%s" % unitsSepTuple
		else:
			unitsStr = u"%s\N{DEGREE SIGN}%s\'%s\"%s%s" % unitsSepTuple
		self.unitsVar.set(unitsStr)

		# index = nFields*2-1  # use if there is a separator between characters, e.g. h:m:s
#		index = nFields
#		if self.isHours:
#			if self.isRelative:
#				self.unitsVar.set("hms"[-index:])
#			else:
#				self.unitsVar.set("hms"[:index])
#		else:
#			if self.isRelative:
#				self.unitsVar.set(RO.StringUtil.DMSStr[-index:])
#			else:
#				self.unitsVar.set(RO.StringUtil.DMSStr[:index])
	
	def _keyPress(self, evt):
		keysym = evt.keysym
		if keysym in ("space", "semicolon", "equal", "slash", "KP_Equal", "KP_Divide"):
			# space is convenient for the main keyboard
			# semicolon is colon unshifted
			# equals is convenient for the keypad and is reminiscent of a colon
			# KP_Divide: pcs don't have = on the keypad, so keypad / is second best
			self.insert("insert", ":")
			return "break"
		elif keysym in ("Return", "Enter"):
			self._focusOut()
		return None

	def _optionKeyPress(self, evt):
		keysym = evt.keysym
		if keysym == "Left":
			currVal = self.var.get()
			# try to select the previous field
			if self.selection_present():
				ind = self.index(Tkinter.SEL_FIRST) - 1
			else:
				ind = self.index("insert") - 1
			(leftInd, rightInd) = RO.StringUtil.findLeftNumber(currVal, ind)
			if (leftInd, rightInd) == (None, None):
				return
			self.selection_range(leftInd, rightInd+1)
			self.icursor(rightInd+1)
			return "break"
		elif keysym == "Right":
			# try to select the next digit
			currVal = self.var.get()
			if self.selection_present():
				ind = self.index(Tkinter.SEL_LAST)
			else:
				ind = self.index("insert")
			(leftInd, rightInd) = RO.StringUtil.findRightNumber(currVal, ind)
			if (leftInd, rightInd) == (None, None):
				return
			self.selection_range(leftInd, rightInd+1)
			self.icursor(rightInd+1)
			return "break"
		return None


if __name__ == "__main__":
	from RO.Wdg.PythonTk import PythonTk
	import StatusBar
	root = PythonTk()
	
	entryList = []

	def addEntry(descr, entry, unitsLabel=None):
		newFrame = Tkinter.Frame(root)
		newFrame.lower()
		if descr:
			Tkinter.Label(newFrame, text=descr).pack(side="left")
		entry.pack(in_=newFrame, side="left")
		if unitsLabel:
			unitsLabel.pack(in_=newFrame, side="left")
		newFrame.pack(side="top", anchor="w")
		entryList.append((descr, entry))
	
	def doPrint(*args):
		for (descr, entry) in entryList:
			try:
				print "%s = %r" % (descr, entry.getNum())
			except AttributeError:
				print "%s = %r" % (descr, entry.getString())
	
	def doDefault(*args):
		for (descr, entry) in entryList:
			entry.restoreDefault()

	def setHours(*args):
		for (descr, entry) in entryList:
			if isinstance(entry, DMSEntry):
				entry.setIsHours(True)
		
	def setDeg(*args):
		for (descr, entry) in entryList:
			if isinstance(entry, DMSEntry):
				entry.setIsHours(False)

	getButton = Tkinter.Button (root, command=doPrint, text="Print Values")
	getButton.pack()
	
	defButton = Tkinter.Button (root, command=doDefault, text="Default")
	defButton.pack()
	
	hrsButton = Tkinter.Button (root, command=setHours, text="DMS in hrs")
	hrsButton.pack()
	
	degButton = Tkinter.Button (root, command=setDeg, text="DMS in deg")
	degButton.pack()
	
	statusBar = StatusBar.StatusBar(root)
		
	addEntry (
		"StrEntry",
		StrEntry(root,
			helpText = "Any string"
		),
	)
	
	addEntry (
		"StrEntry alphabetic",
		StrEntry(root,
			partialPattern = r'[a-zA-Z]*$',
			helpText = "Letters only",
		),
	)
	
	addEntry (
		"IntEntry 0-90",
		IntEntry(root,
			0,
			90,
			helpText = "An integer in the range 0-90",
		),
	)
	
	addEntry (
		"FloatEntry, no exp 0-90",
		FloatEntry(root,
			0,
			90,
			helpText = "A float in the range 0-90",
		),
	)	

	addEntry (
		"FloatEntry, exp OK 0-90",
		FloatEntry(root,
			0.0,
			90.0,
			defValue="0.0",
			allowExp=True,
			helpText = "A float in the range 0-90; exponent OK",
		),
	)
	
	
	absUnitsVar = Tkinter.StringVar()
	addEntry (
		"Abs DMSEntry -90-90 deg",
		DMSEntry(root,
			-90.0,
			90.0,
			unitsVar=absUnitsVar,
			helpText = "d:m:s in the range -90-90",
		),
		Tkinter.Label(root, textvar=absUnitsVar, width=5),
	)
	
	abs2UnitsVar = Tkinter.StringVar()
	addEntry (
		"Abs DMSEntry 0-180 deg",
		DMSEntry(root,
			0.0,
			180.0,
			unitsVar=abs2UnitsVar,
			helpText = "d:m:s in the range 0-180",
			clearMenu = None,
		),
		Tkinter.Label(root, textvar=abs2UnitsVar, width=5),
	)
	
	relUnitsVar = Tkinter.StringVar()
	addEntry (
		"Rel DMSEntry -90-90 sec",
		DMSEntry(root,
			-90.0,
			90.0,
			defFormat=(1,0),
			unitsVar=relUnitsVar,
			isRelative=True,
			helpText = "relative d:m:s in the range -90-90",
			minMenu = "Minimum",
			maxMenu = "Maximum",
		),
		Tkinter.Label(root, textvar=relUnitsVar, width=5),
	)
	
	rel2UnitsVar = Tkinter.StringVar()
	addEntry (
		"Rel DMSEntry 0-180 sec",
		DMSEntry(root,
			0.0,
			180.0,
			defFormat=(1,0),
			unitsVar=rel2UnitsVar,
			isRelative=True,
			# helpText = "relative d:m:s in the range 0-180",
			minMenu = "Minimum",
			maxMenu = "Maximum",
		),
		Tkinter.Label(root, textvar=rel2UnitsVar, width=5),
	)
	
	statusBar.pack(side="top", expand="yes", fill="x")

	root.mainloop()
