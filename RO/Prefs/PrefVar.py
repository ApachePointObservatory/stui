#!/usr/local/bin/python
"""Variables used for setting preferences.

One can assign callback functions. PrefVars are similar to KeyVariables, but
are optimized for preferences and are different in several important ways, including:
- they have a default value, instead of the possibility of being invalid
- they are set to a single value (or a list, but the input is treated atomically)

To Do:
- Consider if SoundPrefVar should return an object for getValue,
  in which case setValue and getValue and ??? need overhaul.
- Consider using RO.Wdg.Entry widgets; they are so similar to prefVars
  it's embarrassing, but they need a parent widget,
  and generating an editor widget could be confusing (unless I implement
  some way to copy an entry widget).

History:
2002-02-06 ROwen	Basics done, still need to finish color and implement fonts.
2002-02-07 ROwen	Added file I/O.
2002-02-08 ROwen	Added FontPrefVar; changed omitDefault to maskDefault in PrefSet.writeToFile.
2002-03-04 ROwen	Added BoolPrefVar; added asValue and asStr methods;
					fixed some bugs in value checking;
					made ColorPrefVar accept any valid Tk color.
2002-03-08 ROwen	Added WdgFontPrefVar; improved ColorPrefVar and FontPrefVar to auto-update widgets.
2002-12-20 ROwen	Removed defWdg argument from ColorPrefVar (it was being ignored);
					thanks to pychecker.
2003-02-28 ROwen	Fixed some bugs in StrPrefVar pattern matching.
2003-03-28 ROwen	Changed StrPrefVar to return a blank range string
					instead of a cryptic regular expression.
2003-04-11 ROwen	Changed BoolPrefVar to use RO.Wdg.Checkbutton;
					made all editors include helpText and helpURL.
2003-04-18 ROwen	Changed BoolPrefVar to use True and False as their string values;
					added methods asValue, asStr, asSummary.
2003-04-28 ROwen	Modified to use updated RO.KeyVariable cnv functions.
2003-04-29 ROwen	Fixes for Python 2.3:
					- modified to not use rexec (uses the less safe eval instead);
					- font summary explicitly converts all values to strings.
2003-05-08 ROwen	Changed FontPrefVar coerce values to int or bool as appropriate,
					fixing a problem introduced 2003-04-29 for Python 2.2;
					modified to use new RO.CnvUtil functions.
2003-06-18 ROwen	Modified to test for StandardError instead of Exception
2003-08-04 ROwen	Changed default callNow to False.
2003-08-07 ROwen	Added DirectoryPrefVar;
					modified getEditWdg to accept a 3rd argument:
					the contextual menu configuration function.
2003-08-11 ROwen	Modified getEditWdg so var is optional and edit value is pre-set.
2003-09-22 ROwen	Changed getDefaultValue to getDefValue, to match setDefValue and RO.Wdg.
2003-11-17 ROwen	Added FilePrefVar and SoundPrefVar; modified StrPrefVar such that
					its edit widget does its own value checking.
2003-11-24 ROwen	If defValue invalid, prints msg to stderr and uses None,
					instead of raising an exception.
2003-12-04 ROwen	Modified SoundPrefVar so right end of value is displayed
					in edit widget initially and after using Choose...
2004-02-02 ROwen	Bug fix: DirectoryPrefVar's edit widget's Choose... button
					was broken due to self_doChoose instead of self._doChoose.
2004-02-23 ROwen	Preference files are now read with universal newline support
					on Python 2.3 or later
2004-03-05 ROwen	Modified to use RO.OS.univOpen.
2004-05-18 ROwen	Removed checkPartialValue; it is the editor's responsibility.
					Removed **kargs from getEditWdg in a few places; it was ignored.
2004-08-06 ROwen	Bug fix in DirectoryPrefVar and FilePrefVar: if one typed
					an invalid directory or file name and then pressed Choose...
					to bring up a dialog box, the dialog box never got focus
					because the edit field kept taking it and beeping
					(but never coming to the front). Fixed by ditching the entry field.
2004-09-09 ROwen	Added oldPrefNames argument to PrefSet.
					Fixed SoundPrefVar in the same way as 2004-08-06 fixed FilePrefVar.
2004-09-20 ROwen	Modified dir, file and sound prefs to be auto-width,
					so the entire path is displayed.
2004-10-13 ROwen	Modified functions created by class methods to explicitly pre-bind variables.
2005-06-08 ROwen	Changed PrefVar, ColorUpdate and PrefSet to new-style classes.
2005-06-15 ROwen	Improved initial location of file dialog for FilePrefVar.
2005-07-14 ROwen	Changed help text for file, directory and sound editors to standard help text.
2005-09-15 ROwen	PrefSet: changed oldPrefNames argument to oldPrefInfo;
					one can now map old pref names to new pref names.
2006-03-07 ROwen	Modified Dir, File and SoundPrefVar to use new RO.Wdg.PathWdg.
2006-04-27 ROwen	Stopped importing unused tkFileDialog (thanks, pychecker!).
"""
import os.path
import re
import sys
import Tkinter
import tkFont
import RO.Alg
import RO.CnvUtil
import RO.MathUtil
import RO.OS
import RO.Wdg

class PrefVar(object):
	"""Base class for preference variables.
	
	Subclasses should override:
	- checkValue
	- and draw methods.
	"""

	def __init__(self,
		name,
		category = "",
		defValue = None,
		validValues = None,
		suggValues = None,
		units = "",
		helpText = "",
		helpURL = "",
		callFunc = None,
		callNow = False,
		formatStr = "%r",
		editWidth = 10,
		doPrint = 0,
		cnvFunc = None,
	):
		"""
		Inputs:
		- name: the name of this variable (a string)
		- category: category of preference
		- defValue: default value
		- validValues: an optional list of valid values, in internal representation
		- suggValues: an optional list of suggested values, in internal representation
		- units: the unit of measure
		- helpText: a short descriptive string
		- helpURL: url pointing to html help
		- callFunc: callback function; see addCallback for details
		- callNow: execute callFunc immediately? see addCallback for details
		- formatStr: format string used to display value
		- editWidth: default width for GUI edit widget
		- doPrint: a boolean flag controlling whether data is printed
			to stdout when it is set; simply for debugging.
		- cnvFunc: a conversion function for text values to internal values;
			it should also return values in the final format unchanged.
			Generally set by subclasses and so best left unspecified by users;
			no conversion if omitted.
		"""
		self.name = name
		self.category = category
		self.defValue = None
		self.units = units
		self.validValues = validValues
		self.suggValues = suggValues
		self.helpText = helpText
		self.helpURL = helpURL
		self.formatStr = formatStr
		self.editWidth = editWidth
		self.doPrint = doPrint
		self.cnvFunc = cnvFunc or RO.CnvUtil.nullCnv
		self._callbackList = []
		
		try:
			self.setDefValue(defValue)
		except (ValueError, TypeError), e:
			sys.stderr.write("Default rejected for %s %s: %s\n" % \
				(self.__class__.__name__, name, e))
	
		# check values
		if self.validValues != None:
			for val in self.validValues:
				self.checkValue(val)
		if self.suggValues != None:
			for val in self.suggValues:
				self.checkValue(val)

		self.restoreDefault()

		# if a callback function is specified, add a callback to it
		if callFunc:
			self.addCallback(callFunc, callNow)
	
	def addCallback(self, callFunc, callNow = True):
		"""Executes the given function whenever the variable is set or invalidated.

		Inputs:
		- callFunc: callback function with arguments (positional, not by name):
		  - value: the new value
		  - prefVar: this name variable
		- callNow: if true, execute callFunc immediately,
		  else wait until the variable is next set
		"""
		if callNow:
			callFunc(self.value, self)
		self._callbackList.append(callFunc)
	
	def checkValue(self, value):
		"""Override to provide different checks; if you just want to add checks
		then override locCheckValue instead.
		Raises a ValueError exception if the value is invalid.
		"""
		# check that value is in the list of valid values, if present
		if self.validValues:
			if value not in self.validValues:
				raise ValueError, "value %r not in %r" % (value, self.validValues)
		
		# apply local checks
		self.locCheckValue(value)
		
		# check that the value can be formatted for output
		try:
			self.asStr(value)
		except:
			raise ValueError, "value %r could not be formatted with string %r" % (value, self.formatStr)
	
	def getDefValue(self):
		"""Return the current default value"""
		return self.defValue
	
	def getDefValueStr(self):
		"""Return the default value as a string"""
		return self.asStr(self.defValue)
	
	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		editWdg = RO.Wdg.StrEntry(master,
			defValue = self.defValue,
			var = var,
			helpText = self.helpText,
			helpURL = self.helpURL,
			width = self.editWidth,
		)
		editWdg.set(self.getValue())
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg
		
	def getRangeStr(self):
		"""Return a brief description of the variable's range or other restrictions"""
		return ""
	
	def getValue(self):
		"""Return the current value"""
		return self.value
	
	def getValueStr(self):
		"""Return the current value as a string
		sufficient to reconstruct the value.
		"""
		return self.asStr(self.value)
	
	def locCheckValue(self, value):
		"""Override to provide additional checks here
		Raises a ValueError exception if the value is invalid.
		"""
		pass

	def restoreDefault(self):
		self.setValue(self.defValue)

	def setDefValue (self, rawValue):
		defValue = self.asValue(rawValue)
		self.checkValue(defValue)
		self.defValue = defValue
		
	def setValue (self, rawValue):
		"""Accepts values of the correct type or a string representation"""
		if isinstance(rawValue, str):
			value = self.asValue(rawValue)
		else:
			value = rawValue
		self.checkValue(value)
		self.value = value

		# print to stderr, if requested
		if self.doPrint:
			sys.stderr.write ("%s=%r\n" % (self.name, self.value))

		# apply callbacks, if any
		for callFunc in self._callbackList:
			callFunc(self.value, self)
	
	def asValue(self, rawValue):
		"""Converts a raw value (string or value) to the internal representation.
		"""
		return self.cnvFunc(rawValue)

	def asStr(self, rawValue):
		"""Converts a raw value (internal rep. or string);
		None is converted to "".
		"""
		if rawValue == None:
			return ""
		return self.formatStr % (self.asValue(rawValue),)
	
	def asSummary(self, rawValue):
		"""Converts a raw value (internal rep. or string) to a brief summary.
		"""
		return self.asStr(rawValue)
	
	def __str__(self):
		return ("%s " + self.formatStr) % (self.name, self.value)


class StrPrefVar(PrefVar):
	"""String preference variable with optional pattern matching.

	Inputs:
	- name: the name of this variable (a string)
	- category: category of preference
	- defValue: default value
	- partialPattern	a regular expression string which partial values must match
	- finalPattern	a regular expression string that the final value must match;
		if omitted, defaults to partialPattern
	- **kargs: keyword arguments for PrefVar
	 
	Note: formatStr and cnvFunc get sensible defaults and are best left unspecified
	unless you are sure what you are doing.
	"""
	def __init__(self,
		name,
		category = '',
		defValue = '',
		partialPattern = None,
		finalPattern = None,
		**kargs
	):
		kargs = kargs.copy()	# prevent modifying a passed-in dictionary

		self.finalPattern = finalPattern
		self.partialPattern = partialPattern
		
		# cache the valid pattern for local testing
		# (the edit widget handles the partial pattern itself)
		self.validRE = None
		if self.finalPattern:
			self.validRE = re.compile(self.finalPattern)

		kargs.setdefault("formatStr", "%s")
		kargs.setdefault("cnvFunc", str)

		PrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			**kargs
		)
	
	def locCheckValue(self, value):
		"""Test that the string matches the desired pattern, if any.
		Raise a ValueError exception if the value is invalid.
		"""
		if self.validRE:
			if self.validRE.match(value) == None:
				raise ValueError, "%r does not match pattern %r" % (value, self.finalPattern)
	
	def getRangeStr(self):
		"""Return a brief description of the variable's range or other restrictions.
		For strings there is nothing straightforward to return --
		regular expressions are pretty much unreadable.
		"""
		return ""

	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		editWdg = RO.Wdg.StrEntry(master,
			defValue = self.defValue,
			var = var,
			finalPattern = self.finalPattern,
			partialPattern = self.partialPattern,
			helpText = self.helpText,
			helpURL = self.helpURL,
			width = self.editWidth,
		)
		editWdg.set(self.getValue())
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg

class DirectoryPrefVar(StrPrefVar):
	"""Contains a path to an existing directory.

	Inputs:
	- name: the name of this variable (a string)
	- category: category of preference
	- defValue: default value
	- editWidth: width of text entry field (does not include the choose button)
	- **kargs: keyword arguments for StrPrefVar
	 
	Note: formatStr and cnvFunc get sensible defaults and are best left unspecified
	unless you are sure what you are doing.
	"""
	def __init__(self,
		name,
		category = '',
		defValue = '',
		editWidth=20,
		**kargs
	):
		StrPrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			editWidth = editWidth,
		**kargs)

	def locCheckValue(self, value):
		"""Check that the folder exists"""
		if not value:
			return
		if not os.path.isdir(value):
			if not os.path.exists(value):
				raise ValueError, "%r does not exist on this file system" % (value,)
			raise ValueError, "%r is not a directory" % (value,)
	
	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		if var == None:
			var = Tkinter.StringVar()

		def newPath(wdg, var=var):
			var.set(wdg.getPath())
		
		editWdg = RO.Wdg.DirWdg(master,
			defPath = var.get(),
			callFunc = newPath,
			helpText = self.helpText,
			helpURL = self.helpURL,
		)
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg

class FilePrefVar(StrPrefVar):
	"""Contains a path to an existing file.

	Inputs:
	- name: the name of this variable (a string)
	- category: category of preference
	- defValue: default value
	- editWidth: width of text entry field (does not include the choose button)
	- fileTypes: sequence of (label, pattern) tuples;
		use * as a pattern to allow all files of that labelled type;
		omit altogether to allow all files
	- fileDescr: very brief description; used for helpText
	- **kargs: keyword arguments for StrPrefVar
	 
	Note: formatStr and cnvFunc get sensible defaults and are best left unspecified
	unless you are sure what you are doing.
	"""
	def __init__(self,
		name,
		category = '',
		defValue = '',
		editWidth=20,
		fileTypes=None,
		fileDescr=None,
		**kargs
	):
		StrPrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			editWidth = editWidth,
		**kargs)
		self._fileTypes = fileTypes
		self._fileDescr = fileDescr

	def locCheckValue(self, value):
		"""Check that the file exists"""
		if not value:
			return
		if not os.path.isfile(value):
			if not os.path.exists(value):
				raise ValueError, "%r does not exist on this file system" % (value,)
			raise ValueError, "%r is not a file" % (value,)
	
	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		if var == None:
			var = Tkinter.StringVar()

		def newPath(wdg, var=var):
			var.set(wdg.getPath())
		
		editWdg = RO.Wdg.FileWdg(master,
			defPath = var.get(),
			callFunc = newPath,
			helpText = self.helpText,
			helpURL = self.helpURL,
		)
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg


class SoundPrefVar(FilePrefVar):
	"""Contains an RO.Wdg.SoundPlayer object, which plays a sound file.
	
	If sound file playing is not supported (snack not available),
	or no file is selected, plays a default bell sequence.

	Inputs:
	- name: the name of this variable (a string)
	- category: category of preference
	- defValue: default value
	- editWidth: width of text entry field (does not include the choose button)
	# these "bell" data are only used if the sound file
	# cannot be played for some reason, e.g. invalid file, no file
	# or the snack sound package not installed:
	- bellNum	number of times to ring the bell
	- bellDelay	delay (ms) between each ring
	- **kargs: keyword arguments for StrPrefVar
	 
	Note: formatStr and cnvFunc get sensible defaults and are best left unspecified
	unless you are sure what you are doing.
	"""
	def __init__(self,
		name,
		category = '',
		defValue = '',
		editWidth=20,
		bellNum=1,
		bellDelay=100,
		**kargs
	):
		# so many file types are supported that it may not make sense to filter
#		fileFormats = ("wav", "mp3", "au", "snd", "aiff", "sd", "smp", "nsp", "raw")
#		typeList = [(fmtName, "." + fmtName) for fmtName in fileFormats)
		self._snd = None
		self._bellNum = bellNum
		self._bellDelay = bellDelay
		FilePrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			editWidth = editWidth,
#			fileTypes = typeList,
			fileDescr = "sound",
		**kargs)
	
	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		if var == None:
			var = Tkinter.StringVar()

		def doPlay(btn=None, self=self, var=var):
			s = RO.Wdg.SoundPlayer(
				var.get(),
				bellNum = self._bellNum,
				bellDelay = self._bellDelay,
			)
			s.play()

		def newPath(wdg, var=var):
			newPath = wdg.getPath()
			var.set(newPath)
			if newPath:
				doPlay()
			
		wdgFrame = Tkinter.Frame(master)
		editWdg = RO.Wdg.FileWdg(wdgFrame,
			defPath = var.get(),
			callFunc = newPath,
			helpText = self.helpText,
			helpURL = self.helpURL,
		)
		editWdg.pack(side="left")
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		
		playButton = RO.Wdg.Button(wdgFrame,
			text = "Play",
			callFunc = doPlay,
			helpText = self.helpText,
			helpURL = self.helpURL,
		)
		playButton.pack(side="left")

		return wdgFrame

	def play(self):
		if self._snd:
			self._snd.play()
		
	def setValue (self, rawValue):
		FilePrefVar.setValue(self, rawValue)
		self._snd = RO.Wdg.SoundPlayer(
			fileName = rawValue,
			bellNum = self._bellNum,
			bellDelay = self._bellDelay,
		)


class BoolPrefVar(PrefVar):
	"""A boolean-valued PrefVar. Initialization arguments are the same as for PrefVar,
	except that suggestedValues and validValues are ignored.
	"""
	def __init__(self,
		name,
		category = "",
		defValue = None,
		**kargs
	):
		"""
		Inputs: same as PrefVar.
		
		Notes:
		- validValues and suggValues are ignored.
		- formatStr and cnvFunc get sensible defaults and are best left unspecified
		unless you are sure what you are doing.
		"""
		kargs = kargs.copy()	# prevent modifying a passed-in dictionary

		kargs.setdefault("formatStr", "%s")
		kargs.setdefault("cnvFunc", RO.CnvUtil.asBool)
		kargs["validValues"] = None
		kargs["suggValues"] = None
		
		PrefVar.__init__(self,
			name = name,
			category = category,
			defValue = bool(defValue),
			**kargs
		)

	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		# specify onvalue and offvalue because the pref editor
		# to avoid editor's variable from being set to '0' and '1'
		editWdg = RO.Wdg.Checkbutton(master,
			var = var,
			helpText = self.helpText,
			helpURL = self.helpURL,
			onvalue = "True",
			offvalue = "False",
		)
		editWdg.set(self.getValue())
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg

	def asStr(self, rawValue):
		"""Converts a raw value (internal rep. or string) to
		'True' or 'False' (the modern Python representation
		for boolean true or false).
		"""
		if self.asValue(rawValue):
			return 'True'
		else:
			return 'False'
	

class IntPrefVar(PrefVar):
	"""An integer-valued PrefVar. Initialization arguments
	are the same as for PrefVar.
	"""
	def __init__(self,
		name,
		category = "",
		defValue = None,
		minValue = None,
		maxValue = None,
		formatStr = "%d",
		**kargs
	):
		"""
		Inputs other than those for PrefVar:
		- minValue: minimum allowed value (None if no limit)
		- maxValue: maximum allowed value (None if no limit)
		
		Note: formatStr gets a sensible default and is best left unspecified
		unless you are sure what you are doing.
		"""
		kargs = kargs.copy()	# prevent modifying a passed-in dictionary

		self.minValue = minValue
		self.maxValue = maxValue
		
		kargs.setdefault("cnvFunc", RO.CnvUtil.asInt)
		
		PrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			formatStr = formatStr,
			**kargs
		)

	def locCheckValue(self, value):
		"""Raise a ValueError exception if the value is out of range.
		"""
		RO.MathUtil.checkRange(value, self.minValue, self.maxValue)

	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		editWdg = RO.Wdg.IntEntry(master,
			minValue = self.minValue,
			maxValue = self.maxValue,
			defValue = self.defValue,
			defFormat = self.formatStr,
			var = var,
			helpURL = self.helpURL,
			helpText = self.helpText,
			width = self.editWidth,
		)
		editWdg.set(self.getValue())		
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg

	def getRangeStr(self):
		"""Return a brief description of the variable's range or other restrictions"""
		if self.minValue == None and self.maxValue == None:
			return ""
		elif self.minValue == None:
			return ("<= " + self.formatStr) % (self.maxValue,)
		elif self.maxValue == None:
			return (">= " + self.formatStr) % (self.minValue,)
		else:
			return ("[" + self.formatStr + ", " + self.formatStr + "]") % (self.minValue, self.maxValue)
	

class FloatPrefVar(PrefVar):
	"""A float-valued PrefVar. 
	"""
	def __init__(self,
		name,
		category = "",
		defValue = None,
		minValue = None,
		maxValue = None,
		allowExp = 1,
		formatStr = "%.2f",
		**kargs
	):
		"""
		Inputs other than those for PrefVar:
		- minValue: minimum allowed value (None if no limit)
		- maxValue: maximum allowed value (None if no limit)
		- allowExp: allow exponential notation?

		Note: formatStr gets a sensible default and is best left unspecified
		unless you are sure what you are doing.
		"""
		kargs = kargs.copy()	# prevent modifying a passed-in dictionary

		self.minValue = minValue
		self.maxValue = maxValue
		self.allowExp = allowExp

		kargs.setdefault("cnvFunc", RO.CnvUtil.asFloat)
		
		PrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			formatStr = formatStr,
			**kargs
		)

	def locCheckValue(self, value):
		"""Raise a ValueError exception if the value is out of range.
		"""
		RO.MathUtil.checkRange(value, self.minValue, self.maxValue)

	def getEditWdg(self, master, var=None, ctxConfigFunc=None):
		"""Return a Tkinter widget that allows the user to edit the
		value of the preference variable.
		
		Inputs:
		- master: master for returned widget
		- var: a Tkinter variable to be used in the widget
		- ctxConfigFunc: a function that updates the contextual menu
		"""
		editWdg = RO.Wdg.FloatEntry(master,
			minValue = self.minValue,
			maxValue = self.maxValue,
			defValue = self.defValue,
			defFormat = self.formatStr,
			var = var,
			helpURL = self.helpURL,
			helpText = self.helpText,
			allowExp = self.allowExp,
			width = self.editWidth,
		)
		editWdg.set(self.getValue())
		if ctxConfigFunc:
			editWdg.ctxSetConfigFunc(ctxConfigFunc)
		return editWdg

	def getRangeStr(self):
		"""Return a brief description of the variable's range or other restrictions"""
		if self.minValue == None and self.maxValue == None:
			return ""
		elif self.minValue == None:
			return ("<= " + self.formatStr) % (self.maxValue,)
		elif self.maxValue == None:
			return (">= " + self.formatStr) % (self.minValue,)
		else:
			return ("[" + self.formatStr + ", " + self.formatStr + "]") % (self.minValue, self.maxValue)

class ColorUpdate(object):
	def __init__(self):
		self.varDict = {}
		
		# we'll need a Tkinter widget so we can call tk_setPalette
		# but don't get it yet -- Tk is probably not running!
		self.wdg = None

	def addVar(self, option, prefVar):
		self.varDict[option] = prefVar
		prefVar.addCallback(self.setColor)

	def setColor(self, *args):
		# if we haven't gotten a widget yet, now is the time
		if not self.wdg:
			self.wdg = Tkinter.Label()

		colorDict = {}
		for option, var in self.varDict.iteritems():
			colorDict[option] = var.getValue()

		# background is required; make sure we have it
		if not colorDict.has_key("background"):
			colorDict["background"] = self.wdg.cget("background")

		self.wdg.tk_setPalette(**colorDict)

theColorUpdater = ColorUpdate()

class ColorPrefVar(PrefVar):
	"""Tk color preference variable.
	"""

	def __init__(self,
		name,
		category = "",
		defValue = "black",
		wdgOption = None,
		**kargs
	):
		"""
		Inputs: same as PrefVar except:
		wdgOption: a widget option, such as "background", to automatically update.
		 
		Note: formatStr and cnvFunc are set internally; your values will be ignored.
		"""
		kargs = kargs.copy()	# prevent modifying a passed-in dictionary

		# create an arbitrary Tk widget we can query to convert colors
		self.colorCheckWdg = Tkinter.Label()

		kargs["formatStr"] = "%s"
		kargs["cnvFunc"] = str

		PrefVar.__init__(self,
			name = name,
			category = category,
			defValue = defValue,
			**kargs
		)
		if wdgOption:
			global theColorUpdater
			theColorUpdater.addVar(wdgOption, self)
	
	def locCheckValue(self, value):
		"""Test that the string matches the desired pattern, if any.
		Raise a ValueError exception if the value is invalid.
		"""
		try:
			self.colorCheckWdg.winfo_rgb(value)
		except Tkinter.TclError, e:
			raise ValueError, str(e)

class FontPrefVar(PrefVar):
	"""Tk Font preference variable.
	"""

	def __init__(self,
		name,
		category = "",
		font = None,
		defWdg = None,
		defValue = None,
		optionPatterns = (),
		**kargs
	):
		"""
		Inputs: same as PrefVar, plus:
		- font: a tkFont.Font object.
		- defWdg: a widget whose font is used for the default value.
		- defValue: defaults for one or more widget characteristics; see note on value below.
		- optionPatterns: entries to add to the option database.
		
		The default value is obtained by starting with a set of internal defaults
		and then applying inputs in the following order: font, defValue, defWdg
		
		The value of a prefFont is a dictionary containing one or more of the following keys:
			"family", "overstrike", "size", "slant", "underline", "weight"
		Warning: unlike many PrefVars, a string representation of a dictionary is NOT acceptable.
		It must actually be a dictionary.
		
		Option patterns:
		- Each listed entry is added to the option database using option_add(ptn, font).
		- This causes any widgets matching any of these patterns, so long as the widgets
		  are created after the entry is added and without specifying a font.
		- Example patterns:
			- fonts for all widgets: ("*font",)
			- fonts for menu widgets: ("*Menu.font", "*Menubutton.font", "*OptionMenu.font")
		- Always put the more general patterns into the database first. This applies both to
		  the order of creation of WdgFontPrefVars and to the order of entries in optionPatterns.
		
		Notes:
		- Allowing a string representation of a dictionary for setValue could be done
		by using r_eval from RExec. However, I see no point. r_eval is already used
		by PrefSet when reading from a file (i.e. the data is already converted),
		and a graphical preferences editor can easily supply the data in dictionary form.
		- Allowing the data to be expressed in modern Tkform (name, size, style-tuple)
		would be nice, but is too much of a pain. One can create a Font objects using this notation,
		but one cannot retrieve data in this form nor update a Font in this form.
		
		formatStr and cnvFunc are set internally; your values will be ignored.
		"""
		kargs = kargs.copy()	# prevent modifying a passed-in dictionary

		self.font = font or tkFont.Font()
		self.__internalDefaults = {"family":"helvetica", "size":"12",
			"weight":"normal", "slant":"roman", "underline":"0", "overstrike":"0"}
		kargs["formatStr"] = "%r"
		kargs["cnvFunc"] = dict # warning: no real point; it can't handle string a rep. of dict
		
		# apply defaults in the correct order
		netDefValue = self.__internalDefaults.copy()
		if font:
			netDefValue.update(font.configure())
		if defWdg:
			# the following is the only way I know to obtain a font dictionary from a widget
			wdgFontDict = tkFont.Font(font=defWdg.cget("font")).configure()
			netDefValue.update(wdgFontDict)
		if defValue:
			# defValue is the only one likely to have a bogus value; check it before applying it
			self.locCheckValue(defValue)
			netDefValue.update(defValue)

		self.value = {}
		PrefVar.__init__(self,
			name = name,
			category = category,
			defValue = netDefValue,
			**kargs
		)

		# if optionPatterns supplied, add font to option database
		for ptn in optionPatterns:
			Tkinter.Label().option_add(ptn, self.font)
	
	def getDefValue(self):
		"""Return the current default value"""
		return self.defValue.copy()

	def getValue(self):
		return self.value.copy()

	def locCheckValue(self, value):
		"""Test that the value is valid.
		"""
		badKeys = [key for key in value.iterkeys() if key not in self.__internalDefaults]
		if badKeys:
			raise ValueError, "Invalid key(s) %s in font dictionary %r" % (badKeys, value)

	def setValue (self, rawValue):
		"""Updates the internal font information from the font dictionary provided
		(as a dictionary or a string representation). Any unspecified fields are left unchanged.
		"""
		partialValue = self.cnvFunc(rawValue)
		self.checkValue(partialValue)
		self.font.configure(**partialValue)
		self.value = self.font.configure()
		
		# the following keep data in a standard format
		# between Python 2.2 (all values as strings) and 2.3
		for key, cnvFunc in (
			("size", RO.CnvUtil.asInt),
			("underline", RO.CnvUtil.asBool),
			("overstrike", RO.CnvUtil.asBool),
		):
			self.value[key] = cnvFunc(self.value[key])

		# print to stderr, if requested
		if self.doPrint:
			sys.stderr.write ("%s=%r\n" % (self.name, self.value))

		# apply callbacks, if any
		for callFunc in self._callbackList:
			callFunc(self.value, self)
	
	def asSummary(self, rawValue):
		value = self.asValue(rawValue)
		# list named characteristics and their default value (if any)
		namedCharDef = (("family", None), ("size", None), ("weight", "normal"), ("slant", "roman"))
		boolChars = ("underline", "overstrike")
		charList = []
		for charName, defVal in namedCharDef:
			charVal = value[charName]
			if charVal != defVal:
				charList.append(str(charVal))
		for charName in boolChars:
			if value[charName] == "1":
				charList.append(charName)
		return " ".join(charList)


class PrefSet(object):
	"""A set of PrefVars with methods to retrieve individual preference values
	and an ordered list of preferences by category"""
	def __init__(self,
		prefList = None,
		defFileName = None,
		defHeader = None,
		oldPrefInfo = None,
	):
		"""Inputs:
		- prefList: a list or tuple of prefVars or an iterator that returns prefVars
		- defFileName: the default file name for pref I/O
			The header may contain \n to produce multiple lines.
			If any line is missing a starting "#", it is preceded by "# ".
		- header: a default header string for writing the data to a file.
			The header may contain \n to produce multiple lines.
			If any non-blank line is missing a starting "#", one will be added for you.
		- oldPrefInfo: a dict of oldPrefName: newPrefName
			where newPrefName can be None if there is no match
			i.e. if the old preference is simply not used anymore
		"""
		self.defHeader = defHeader
		self.defFileName = defFileName
		self.prefDict = RO.Alg.OrderedDict()
		if prefList != None:
			for prefVar in prefList:
				self.addPrefVar(prefVar)
		self.oldPrefDict = {}
		if oldPrefInfo:
			for oldPrefName, newPrefName in oldPrefInfo.iteritems():
				if newPrefName:
					if newPrefName.lower() not in self.prefDict:
						raise RuntimeError("Invalid oldPrefInfo %s: %s; nonexistent new pref name" %
							(oldPrefName, newPrefName))
				self.oldPrefDict[oldPrefName.lower()] = newPrefName.lower()
				
	def addPrefVar(self, prefVar):
		"""Adds the preference variable, using as a key the variable's name converted to lowercase
		(so one can easily extract the name in a case-blind fashion).
		"""
		self.prefDict[prefVar.name.lower()] = prefVar
	
	def getPrefVar(self, name, default=None):
		"""Returns the preference variable, or default if not found"""
		return self.prefDict.get(name.lower(), default)
	
	def getValue(self, name):
		"""Returns the preference variable; raises an exception if not found"""
		return self.prefDict[name.lower()].value
	
	def getCategoryDict(self):
		"""Returns on RO.Alg.OrderedDict (a dictionary whose keys remain in the order added).
		Each key is a category and each value is a list of PrefVars in that category.
		"""
		catDict = RO.Alg.OrderedDict()
		
		for prefVar in self.prefDict.itervalues():
			catDict.setdefault(prefVar.category, []).append(prefVar)
		return catDict
	
	def restoreDefault(self):
		"""Restores all preferences to their default value.
		"""
		for pref in self.prefDict.itervalues():
			pref.restoreDefault()
	
	def readFromFile(self, fileName=None):
		"""Reads the preferences from a file, if the file exists.
		If there is an error in the file, prints a warning to stderr.
		
		Inputs:
		- fileName: path name of file, as a string; if omitted, the default filename is used
			(if available, else an exception is raised).
		
		Each line of data consists of:
		- one or more spaces
		- a preference name (without double quotes)
		- one or more spaces
		- the data for the preference (strings must include double quotes)
		- if you wish a comment, then follow that with 0 (ick) or more spaces, # and the comment
		Blank lines and lines starting with a # (in any column) are ignored.
		
		Example:
		# header line 1
		  # header line 2 followed by a blank line
		  
		pref1 'value of pref 1' # comment for pref 1
		  pref2      2          # comment
		  
		Details:
		It may help to know how data is recognized. The trick is removing the optional
		trailing comment (without getting confused on tricky data or comments).
		I decided to let the Python interpreter handle it, so I	feed the data (with
		the pref name removed) to eval. It ignores the leading white space and any
		trailing comment and returns the evaluated data (if it can understand the data;
		if not, it is ill-formed and the data is rejected with an error message).
		At that point the data is fed to the referenced preference variable.
		"""
		fileName = self.__getFileName(fileName)

		if not os.path.isfile(fileName):
			sys.stderr.write("No preference file %r; using default values\n" % (fileName,))
			return

		try:
			inFile = RO.OS.openUniv(fileName)
		except StandardError, e:
			sys.stderr.write("Could not open preference file %r; error: %s\n" % (fileName, e))
			return
			
		try:
			for line in inFile:
				# if line starts with #, it is a comment, skip it
				if line.startswith("#"):
					continue
				data = line.split("=", 1)
				if len(data) < 2:
					# no data on this line; skip it
					continue
				prefName = data[0].strip()
				prefValueStr = data[1]
				prefVar = self.getPrefVar(prefName)
				if not prefVar:
					try:
						newPrefName = self.oldPrefDict[prefName.lower()]
					except LookupError:
						sys.stderr.write("Unknown preference %r on line %r of file %r\n" % (prefName, line, fileName))
						continue
					if not newPrefName:
						continue
					prefVar = self.getPrefVar(newPrefName)

				# evaluate prefData -- report an error on failure to do so
				try:
					# parse prefValue; do not just feed it to prefVar.setValueStr
					# because it may include a comment
					prefValue = eval(prefValueStr)
					prefVar.setValue(prefValue)
				except StandardError, e:
					sys.stderr.write("Invalid data on line %r of file %r; error: %s\n" % (line, fileName, e))
					continue
		finally:
			inFile.close()
	
	def writeToFile(self, fileName=None, header=None, maskDefault=1):
		"""Writes the preferences to a file in a format that can be read by readFromFile.
		
		Inputs:
		- fileName: the file to receive the data; if omitted, the default file is used.
		- header: an optional header string; if omitted, the default is used (if specified).
			The header may contain \n to produce multiple lines.
			If any non-blank line is missing a starting "#", one will be added for you.
		- maskDefault: comment out preferences that have their default value?
		"""
		fileName = self.__getFileName(fileName)
		outFile = open(fileName, "w")
		try:
			headerText = header or self.defHeader
			if headerText:
				for headerLine in headerText.split('\n'):
					commentTest = headerLine
					commentTest.strip()
					if commentTest.startswith("#") or len(commentTest) == 0:
						# line already includes a starting comment or is blank; use as is
						outFile.write("%s\n" % headerLine)
					else:
						# line does not being with a comment; prepend "# "
						outFile.write("# %s\n" % headerLine)
			for prefVar in self.prefDict.itervalues():
				if maskDefault and prefVar.value == prefVar.defValue:
					outFile.write("# %s = %r\n" % (prefVar.name, prefVar.getValue()))
				else:
					outFile.write("%s = %r\n" % (prefVar.name, prefVar.getValue()))
		finally:
			outFile.close()
	
	def __getFileName(self, fileName=None):
		"""Returns the name of the file, which is fileName, if supplied,
		else the default fileName, if supplied, else a RuntimeError is rasied.
		"""
		trueName = fileName or self.defFileName
		if not trueName:
			raise RuntimeError, "No file specified and no default file"
		return trueName


if __name__ == "__main__":
	print "running PrefVar test"

	def callFunc(value, prefVar):
		print "callFunc called with value=%r, prefVar='%s'" % (value, prefVar)

	pv = PrefVar(
		name="basicPref",
		category="main",
		defValue=0,
		helpText="test PrefVar",
		callFunc=callFunc,
		callNow=True,
	)
	print "created a PrefVar with default value 0; value =", pv.getValue()
	
	pv.setValue("aString")
	print "set value to 'aString'; value =", pv.getValue()
		
	pv.restoreDefault()
	print "restored default; value =", pv.getValue()
