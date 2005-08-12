#!/usr/local/bin/python
"""Containers (wrappers) for RO.Wdg input widgets, including Entry,
Checkbutton and OptionMenu.

Input containers support the following (and more):

* getString returns the data as a formatted string,
e.g. for generating commands from sets of input widgets.

This requires a formatting function for each container. Such functions are
quite simple to write. A few basic examples are provided, but if these do not
meet your needs then I strongly encourage you to write your own.

* getValueDict and setValueDict retrieve and restore the input values.
This can be useful for a command history (e.g. via RO.Wdg.HistoryMenu)
and for setting widgets based on data from files or programmatically generated data.

The make the latter easy, I have tried to keep the format of the value dictionary
as simple and straightforward as possible.
* clear clears all contained widgets
* restoreDefault sets all contained widgets to their default value.
* getWdgDict returns a dictionary of widgets; this makes it easy
  to access specific widgets from ContList, e.g. for formatting
* getWdgList returns all contained widgets as a flat list (in order).
  This makes it easy to pack a set of widgets.

History:
2001-08-13 ROwen
2001-11-01 ROwen	Added omitNone to getDefValueDict and getDefValueList,
					for symmetry with getValueDict and getValueList.
					Changed Set to have a keyword and use it for dictionary I/O,
					thus improving namespace separation and simplifying the Group class
					(since the new Set dictionary I/O methods work "as is" for Groups).
2001-11-05 ROwen	Added format functions, so each widget and widget set
					can provide specially formatted data.
					Added an optional namespace to Set (depending if keyword is blank).
					Removed Group, getQual, dictToQual and String.
2002-06-25 ROwen	Changed Set.__init__ to make keyword optional
					and documented Set.getDataDict to explain the implications of omitting keyword.
2002-07-29 ROwen	Added support for callback functions.
2002-08-23 ROwen	Changed defIfDisabled to defIfHidden since Entry
					widgets still show values even if disabled (returning the default
					when a different value was visible would be a big mistake).
					Added wdgSet parameter.
2002-11-15 ROwen	Moved InputCont.Frame to RO.Wdg.InputContFrame.
2003-03-11 ROwen	Fixed bugs: defaults in ROEntry widgets were miscomputed
2003-03-14 ROwen	Overhauled BasicContListFmt to include the keyword
					and to return "" if there are no elements in the list (after omitting blanks);
					added getStringList to Set;
					added blankIfHidden flag	(may want to ditch defIfHidden);
					converted boolean values to True/False
2003-04-03 ROwen	Added rejectBlanks to BasicContListFmt.
2003-04-16 ROwen	Added noneIfAllDef to class Set.
2003-05-28 ROwen	Modified ROEntry to let the widget handle callbacks.
2003-06-26 ROwen	Total rewrite (finally): now only handles RO.Wdg input widgets;
					handles lists of widgets; added a boolean container;
					format functions receive the input container and so have more power.
2003-07-24 ROwen	Further modification: if you specify a single widget for WdgCont
					then get<any>Dict returns a single value for that inputCont.
					Also, setValueDict can always take a singleton if there is one widget.
2003-08-04 ROwen	Bug fix in WdgCont.getWdgDict.
2003-08-08 ROwen	Added BoolOmitCont; changed BoolCont to BoolNegCont.
2003-10-20 ROwen	Bug fix: setValueList was broken.
2003-10-23 ROwen	Bug fix: getWdgByName was broken in BoolNegCont and BoolOmitCont;
					modified to use RO.Alg.MatchList instead of RO.Alg.GetByPrefix.
2003-11-04 ROwen	Modified WdgCont to not restore defaults while creating;
					RO.Wdg widgets are already set to their defaults
					and it caused problems by calling callbacks early.
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2004-05-18 ROwen	Stopped importing sys since it wasn't used.
2004-08-12 ROwen	Bug fix: BasicFmt ignored argument omitHidden (use blankIfDisabled instead).
2004-10-12 ROwen	ContList returns self instead of the changed container on callback.
					ContList restoreDefault and setValueDict now make just one callback,
					instead of one callback per input container.
2004-12-13 ROwen	Major overhaul:
					- ContList is now a subclass of WdgCont.
					- WdgCont modified to be like ContList in the following ways:
					  - restoreDefault and setValueDict now make just one callback,
					    instead of one callback per input container. 
					  - added removeCallback.
					- Renamed doEnable to setEnable to match RO.Wdg widgets.
					- Eliminated formatNow argument (it was not being used and was broken).
2005-05-10 ROwen	Removed up another omitHidden that was ignored
					(use blankIfDisabled or write your own format function instead).
2005-06-03 ROwen	Fixed test code (one class mis-named).
					Minor indentation tweaks.
2005-06-08 ROwen	Changed BasicFmt, BasicContListFmt and VMSQualFmt to new-style classes.
2005-08-12 ROwen	Removed unused import of string module.
"""
import types
import RO.AddCallback
import RO.SeqUtil

# formatting functions
def nullFmt(inputCont):
	return ""

class BasicFmt(object):
	"""A basic but somewhat flexible formatting function.

	Inputs:
	- begStr: prefix
	- omitName: if True, or if the name is None, the name and nameSep are omitted
	- nameSep: put between the name and the values; ignored if omitName True
	- valFmt: a function applied to each value; must take a string in and emit a string out
	- valSep: put between each value
	- endStr: suffix
	- blankIfDisabled: returns '' if any widget is disabled or hidden
	- rejectBlanks: raises a ValueError if any values non-blank (after applying valFmt)

	Note that rejectBlanks will not reject all blanks if
	the input container has omitDef set and the default is blank
	for each widget. This handles the common case where the user
	must either specify all values are no values.
	
	The following restrictions apply (write your own to override):
	- if the value list (inputCont.getValueList()) is blank, returns "";
	  this can only happen if the inputCont has omitDef set.
	- the value of each widget is used as formatted
	"""
	def __init__(self,
		begStr = "",
		omitName = False,
		nameSep = " ",
		valSep = " ",
		valFmt = None,
		endStr = "",
		blankIfDisabled = True,
		rejectBlanks = True,
	):
		self.begStr = begStr
		self.omitName = omitName
		self.nameSep = nameSep
		self.valFmt = valFmt
		self.valSep = valSep
		self.endStr = endStr
		self.blankIfDisabled = blankIfDisabled
		self.rejectBlanks = rejectBlanks

	def __call__(self, inputCont):
		name = inputCont.getName()
		valList = inputCont.getValueList()
		if not valList:
			return ''
		if self.blankIfDisabled and not inputCont.allEnabled():
			return ''
		if self.valFmt != None:
			valList = [self.valFmt(val) for val in valList]
		if self.rejectBlanks:
			if '' in valList:
				raise ValueError, 'must specify all values for %r' % (name,)
		
		if self.omitName or name == None:
			nameStr = ''
		else:
			nameStr = name + self.nameSep
		return self.begStr + nameStr + self.valSep.join(valList) + self.endStr

class VMSQualFmt(object):
	"""Format VMS qualifiers with one or more values.
	
	Inputs:
	- valFmt: a function applied to each value; must take a string in and emit a string out;
			by default blanks are converted to "" (as required by VMS in a list)
	- blankIfDisabled: returns '' if any widget is disabled or hidden
	- rejectBlanks: raises a ValueError if any values non-blank (after applying valFmt)
	"""
	def __init__(self,
		valFmt = None,
		blankIfDisabled = True,
		rejectBlanks = True,
	):
		if valFmt == None:
			def blankToQuotes(astr):
				if astr == '':
					return '""'
				return astr
			valFmt = blankToQuotes
		self.valFmt = valFmt
		self.blankIfDisabled = blankIfDisabled
		self.rejectBlanks = rejectBlanks

	def __call__(self, inputCont):
		name = inputCont.getName()
		valList = inputCont.getValueList()
		# print 'VMSQualFmt called; valList=%r' % (valList,)
		if not valList:
			return ''
		if self.blankIfDisabled and not inputCont.allEnabled():
			return ''
		if self.valFmt != None:
			valList = [self.valFmt(val) for val in valList]
		if self.rejectBlanks:
			if '' in valList:
				raise ValueError, 'must specify all values for %r' % (name,)

		if len(valList) > 1:
			return '/%s=(%s)' % (name, ', '.join(valList))
		else:
			return '/%s=%s' % (name, valList[0])


class BasicContListFmt(object):
	"""Use for ContList objects

	Inputs:
	- rejectBlanks: raises a ValueError if only some values non-blank
	- omitBlankValues: elides values that are "" or None
	- begStr: prefix
	- omitName: if True, or if the name is None, the name and nameSep are omitted
	- nameSep: put between the name and the values; omitted if omitName True
	- valSep: put between each value
	- endStr: suffix
	
	This approach relies on the contained containers formatting their own data.
	Usually this is easiest, but it is also possible to use the value list or
	value dictionary directly and thus bypass the contained format functions.
	"""
	def __init__(self,
		rejectBlanks = False,
		omitBlanks = True,
		begStr = '',
		omitName = False,
		nameSep = ' ',
		valSep = ' ',
		endStr = '',
	):
		self.rejectBlanks = rejectBlanks
		self.omitBlanks = omitBlanks
		self.begStr = begStr
		self.omitName = omitName
		self.nameSep = nameSep
		self.valSep = valSep
		self.endStr = endStr
		
	def __call__(self, contList):
		name = contList.getName()
		strList = contList.getStringList()
		if not strList:
			return ''

		if self.rejectBlanks:
			if '' in strList:
				raise ValueError, 'specify all values for %s' % (name,)

		if self.omitBlanks:
			strList = filter(lambda x: x != '', strList)
			if len(strList) == 0:
				return ''

		if self.omitName or name == None:
			nameStr = ''
		else:
			nameStr = name + self.nameSep
		try:
			return self.begStr + nameStr + self.valSep.join(strList) + self.endStr
		except Exception, e:
			raise ValueError, 'cannot format name %r with beg/sep/endStr=%r/%r/%r and data=%r; error=%s' % (
				name, self.begStr, self.valSep, self.endStr, strList, e)


# widget containers
class WdgCont(RO.AddCallback.BaseMixin):
	"""A container handling an ordered list of RO.Wdg input widgets with one associated name.
	
	Inputs:
	- name: unique name associated with this item (used for get/setValueDict...)
	- wdgs: one or more RO.Wdg input widgets
	- formatFunc: a function that takes one argument (this container)
			and returns a formatted string. Used for getString.
			The default is name value1 value2.... (BasicFmt with no arguments)
	- callFunc: a function to call whenever the value of any widget changes.
			It receives one argument: this input container.
	- callNow: if True, the callback function is tested during construction
	- omitDef: if True: getValueList returns [] and getValueDict returns {} if all values are default
	- setDefIfAbsent: if True: setValueDict sets all widgets to their default value if name is absent 
	"""
	def __init__ (self,
		name,
		wdgs = None,
		
		formatFunc = None,
		callFunc = None,
		callNow = False,
	
		omitDef = True,	
		setDefIfAbsent = True,
	):
		RO.AddCallback.BaseMixin.__init__(self)
		self._name = name
		self._isList = RO.SeqUtil.isSequence(wdgs)
		self._wdgList = RO.SeqUtil.asList(wdgs)
		self._didRegister = False
		
		self._omitDef = bool(omitDef)
		self._setDefIfAbsent = bool(setDefIfAbsent)
		
		if formatFunc == None:
			formatFunc = BasicFmt()
		self._formatFunc = formatFunc
		if not callable(self._formatFunc):
			raise ValueError, 'format function %r is not callable' % (self._formatFunc,)

		if callFunc:
			self.addCallback(callFunc, callNow)

	def addCallback(self, callFunc, callNow=False):
		"""Add a callback function which is called whenever
		the input value changes.
		
		Inputs:
		- callFunc	the function to call when any inputCont in the list changes.
			It receives one argument: this input container.
		"""
		# if never registered with the contained widgets, do it now
		if not self._didRegister:
			for wdg in self._wdgList:
				wdg.addCallback(self._doCallbacks)
			self._didRegister = True
		
		RO.AddCallback.BaseMixin.addCallback(self, callFunc, callNow)
	
	def allEnabled(self):
		"""Return true if all widgets are enabled and visible, False otherwise.
		"""
		for wdg in self._wdgList:
			if not wdg.winfo_ismapped() or not wdg.getEnable():
				return False
		return True
	
	def clear(self):
		"""Clear the contained widgets.
		"""
		for wdg in self._wdgList:
			wdg.clear()
	
	def setEnable(self, doEnable):
		"""Enable or disables the contained widgets.
		
		Inputs:
		- doEnable: enable (if True) or disable (if False) the contained widgets
		"""
		for wdg in self._wdgList:
			wdg.setEnable(doEnable)

	def getDefValueDict(self):
		"""Get the list of default values as a dictionary: {name:deflist}.
		"""
		return {self._name: self.getDefValueList()}
	
	def getDefValueList(self):
		"""Return a list of default values (as strings) for the widgets.
		"""
		return [wdg.getDefault() for wdg in self._wdgList]
	
	def getName(self):
		"""Return the name.
		"""
		return self._name
	
	def getString(self):
		"""Return the formatted string value for this input container.
		"""
		return self._formatFunc(self)
	
	def getStringList(self):
		"""Return [getString()]; a convenience function to make it act
		more like ContList.
		"""
		return [self.getString()]
	
	def getValueDict(self):
		"""Get the value as a dictionary: {name:value}
		where value is a list if wdgs was a list
		
		If omitDef true and all values are default, then returns {}.
		"""
		valList = self.getValueList()
		
		if self._omitDef and valList == []:
			return {}
		return {self._name: self._asOneOrList(valList)}
	
	def getValueList(self):
		"""Get the value as a list: [value1, value2, ...].
		"""
		valList = [wdg.getString() for wdg in self._wdgList]
		
		if self._omitDef and valList == self.getDefValueList():
			return []
		return valList
	
	def getWdgDict(self):
		"""Return {name: wdgList} where wdgList is a copy wdgs
		(thus a single widget if wdgs was, else a list of widgets).
		"""
		return {self._name: self._asOneOrList(self.getWdgList())}
		
	def getWdgList(self):
		"""Return a copy of the list of widgets.
		"""
		return self._wdgList[:]
	
	def restoreDefault(self):
		"""Restore all contained widgets to their default value.
		"""
		tempCallbacks, self._callbacks = self._callbacks, ()
		try:
			for wdg in self._wdgList:
				wdg.restoreDefault()
		finally:
			self._callbacks = tempCallbacks
			self._doCallbacks()
	
	def setValueDict(self, valDict):
		"""Set the widget from a dictionary: {name1:value1, ...}.
		Extra names in the dictionary are ignored.
		
		Inputs:
		- valDict: dictionary containing name:values pairs;
			values must be a sequence of the right length,
			or (if there is only one widget) it can be a singleton
		"""
		# note: entry may be a singleton or a sequence
		# convert to list before sending to setValueList and let it check length
		vals = valDict.get(self._name, None)
		if vals != None:
			self.setValueList(RO.SeqUtil.asSequence(vals))
		elif self._setDefIfAbsent:
			self.restoreDefault()

	def setValueList(self, valList):
		"""Set the value of each widget.
		"""
		if len(valList) != len(self._wdgList):
			raise ValueError, 'valList has %d elements; %d needed' % (len(valList), len(self._wdgList))
		
		tempCallbacks, self._callbacks = self._callbacks, ()
		try:
			for ind in range(len(valList)):
				self._wdgList[ind].set(valList[ind])
		finally:
			self._callbacks = tempCallbacks
			self._doCallbacks()

	def _asOneOrList(self, alist):
		"""Return alist[0] if the original wdgs was a single widget,
		else returns alist if wdgs was a sequence (even if it had length 1).
		"""
		if self._isList:
			return alist
		return alist[0]

	def _doCallbacks(self, dumArg=None):
		RO.AddCallback.BaseMixin._doCallbacks(self)


class BoolNegCont(WdgCont):
	"""A container handling a set of RO.Wdg.Checkbutton input widgets whose value is specified by
	name (if True) or negStr + name (if False). When setting values,
	case is irrelevant and names can be unique prefixes.
	
	See also BoolOmitCont, which is less flexible but has more standard default handling.
	
	Inputs:
	- name: unique name associated with this item (used for get/setValueDict...)
	- wdgs: one or more RO.Wdg.Checkbutton widgets
	- wdgNames: widget name(s); if omitted then the "text" property of each widget is used.
			if supplied then it must be the same length as wdgs.
			Names must not begin with negStr (case irrelevant).
	- negStr: prefix added if the checkbutton is unchecked
	- omitDef: if True: getValueDict returns {} if all values are default
			and getValueDict and getValueList omit individual values whose widgets are default
	- setDefIfAbsent: if True: setValueDict sets all widgets to their default value if name is absent
			and setValueDict and setValueList set individual widgets to their default value
			if they are missing from the value list.
	**kargs: keyword arguments for WdgCont.
	
	Notes:
	- setDefIfOmitted applies to each widget, as well as applying to the container as a whole
	  instead of to all widgets as a whole.
	- The checkbutton widgets are treated as strictly boolean;
	  their on value and off value are irrelevant.
	- For the most part, if you want a set of widgets that you can address by name
	  you should use a ContList, each element of which is a WdgCont. However,
	  boolean inputs lend themselves to this treatment, resulting in a simpler value dictionary.
	"""
	def __init__ (self,
		name,
		wdgs = None,
		wdgNames = None,
		negStr = 'No',
		omitDef = True,
	**kargs):
		WdgCont.__init__(self, name, wdgs, **kargs)
		self._negStr = negStr
		self._omitDef = omitDef
		
		if wdgNames == None:
			wdgNames = [wdg['text'] for wdg in self._wdgList]
		else:
			wdgNames = RO.SeqUtil.asList(wdgNames)
			if len(wdgNames) != len(self._wdgList):
				raise ValueError, 'wdgNames has %d elements; %d needed' % (len(wdgNames), len(self._wdgList))
		self._wdgNames = wdgNames

		# verify that the names are OK		
		lowerNegStr = self._negStr.lower()
		for name in self._wdgNames:
			if name.lower().startswith(lowerNegStr):
				raise ValueError, 'invalid widget name %r; cannot start with negStr=%r' % (name, self._negStr)
		
		# generate widget dict and widget name getter
		self._wdgDict = RO.Alg.OrderedDict(zip(self._wdgNames, self._wdgList))
		self._wdgNameGetter = RO.Alg.MatchList(wdgNames, abbrevOK=True, ignoreCase=True)
	
	def getDefValueList(self):
		"""Get the default value as a list: [name1, negStr + name2, ...].
		"""
		def fmtFunc(name, wdg):
			if wdg.getDefBool():
				return name
			else:
				return self._negStr + name
		return [fmtFunc(name, wdg) for name, wdg in self._wdgDict.iteritems()]

	def getValueList(self):
		"""Get the value as a list: [name1, negStr + name2, ...].

		If omitIfDef true then widgets with default value are omitted
		(the remaining values are in order).
		"""
		def fmtFunc(name, wdg):
			if wdg.getBool():
				return name
			else:
				return self._negStr + name
		if self._omitDef:
			return [fmtFunc(name, wdg) for name, wdg in self._wdgDict.iteritems() \
				if wdg.getDefault() != wdg.getString()]
		else:
			return [fmtFunc(name, wdg) for name, wdg in self._wdgDict.iteritems()]
	
	def getWdgByName(self, name):
		"""Return a widget given its name.
		
		The name need only be a unique prefix and case is ignored.
		"""
		fullName = self._wdgNameGetter.getUniqueMatch(name)
		return self._wdgDict[fullName]
	
	def setValueList(self, valList):
		"""Set the value of each widget.
		
		valList should contain one entry per widget to be set.
		The entry is the widget name to set it True (check the checkbox)
		or negStr + widget name to set it False (uncheck the checkbox).
		
				
		If setDefIfAbsent is true, then any widgets missing from valList
		are restored to their default value.
		"""
		wdgList = [] # list of widgets specified in valList
		lowerNegStr = self._negStr.lower()
		lenNegStr = len(self._negStr)
		for val in valList:
			if val.lower().startswith(lowerNegStr):
				boolVal = False
				name = val[lenNegStr:]
			else:
				boolVal = True
				name = val
			wdg = self.getWdgByName(name)
			wdgList.append(wdg)
			wdg.setBool(boolVal)
		
		if self._setDefIfAbsent:
			for wdg in wdgList:
				if wdg not in self._wdgList:
					wdg.restoreDefault()


class BoolOmitCont(WdgCont):
	"""A container handling a set of RO.Wdg.Checkbutton input widgets whose value is specified by
	name (if True) or omitted if false.
	
	Similar to BoolNegCont, but:
	- Less flexible. All widgets must be checked by default (because otherwise
	  there is no way to set the container from a value dictionary).
	- Default handling is much closer to standard WdgCont.
	
	When setting values, case is irrelevant and names can be unique prefixes.
	
	Inputs:
	- name: unique name associated with this item (used for get/setValueDict...)
	- wdgs: one or more RO.Wdg.Checkbutton widgets
	- wdgNames: widget name(s); if omitted then the "text" property of each widget is used.
			if supplied then it must be the same length as wdgs.
			Names must not begin with negStr (case irrelevant).
	- omitDef: if True: getValueDict returns {} if all values are default
	- setDefIfAbsent: if True: setValueDict sets all widgets to their default value if name is absent
	**kargs: keyword arguments for WdgCont.
	
	Notes:
	- The checkbutton widgets are treated as strictly boolean;
	  their on value and off value are irrelevant.
	- For the most part, if you want a set of widgets that you can address by name
	  you should use a ContList, each element of which is a WdgCont. However,
	  boolean inputs lend themselves to this treatment, resulting in a simpler value dictionary.
	"""
	def __init__ (self,
		name,
		wdgs = None,
		wdgNames = None,
		negStr = 'No',
		omitDef = True,
	**kargs):
		WdgCont.__init__(self, name, wdgs, **kargs)
		self._negStr = negStr
		self._omitDef = omitDef
		
		if wdgNames == None:
			wdgNames = [wdg['text'] for wdg in self._wdgList]
		else:
			wdgNames = RO.SeqUtil.asList(wdgNames)
			if len(wdgNames) != len(self._wdgList):
				raise ValueError, 'wdgNames has %d elements; %d needed' % (len(wdgNames), len(self._wdgList))
		self._wdgNames = wdgNames

		# generate widget dict and widget name getter
		self._wdgDict = RO.Alg.OrderedDict(zip(self._wdgNames, self._wdgList))
		self._wdgNameGetter = RO.Alg.MatchList(wdgNames, abbrevOK=True, ignoreCase=True)
		
		# verify that all widgets have default=checked
		for name, wdg in self._wdgDict.iteritems():
			if not wdg.getDefBool():
				raise ValueError, "widget %s does not have default=checked" % (name,)

	def getValueList(self):
		"""Get the value as a list: [name1, name3 ...] where only checked values
		are returned and the values are in order.

		If omitIfDef true then [] is returned if all widgets are default (checked).
		"""
		valList = [name for name, wdg in self._wdgDict.iteritems()
			if wdg.getBool()]
		if self._omitDef and len(valList) == len(self._wdgList):
			return []
		return valList
	
	def getWdgByName(self, name):
		"""Return a widget given its name.
		
		The name need only be a unique prefix and case is ignored.
		"""
		fullName = self._wdgNameGetter.getUniqueMatch(name)
		return self._wdgDict[fullName]
	
	def setValueList(self, valList):
		"""Check all widgets whose names appear in valList
		and uncheck all other widgets.
		"""
		trueWdgList = [] # list of widgets specified in valList
		for val in valList:
			wdg = self.getWdgByName(val)
			trueWdgList.append(wdg)
			wdg.setBool(True)
		
		for wdg in trueWdgList:
			if wdg not in self._wdgList:
				wdg.setBool(False)


# containers of widget containers
class ContList(WdgCont):
	"""A list of RO.InputCont container objects.
	
	Inputs:
	- conts: one or more RO.InputCont objects (including other containers)
	- name: optional name associated with this list; used for formatted output
			and as an optional namespace for the value dictionary.
			See the documentation for getValueDict for an explanation.
	- formatFunc: a function that takes one argument (this container)
			and returns a formatted string. Used for getString.
			The default is BasicContListFmt, which concatenates values
			from the contained input containers, separated by spaces.
	- callFunc	a function to call whenever the value of any widget changes;
			it receives one argument: this input container.
	- callNow: if True, the callback function is tested during construction
	
	See also the documentation for RO.InputCont.WdgCont.
	"""
	def __init__ (self,
		conts,
		name = None,
		formatFunc = None,
		callFunc = None,
		callNow = False,
	):
		if formatFunc == None:
			formatFunc = BasicContListFmt()

		WdgCont.__init__(self,
			name = name,
			wdgs = conts,
			formatFunc = formatFunc,
			callFunc = callFunc,
			callNow = callNow,
		)
		if len(RO.SeqUtil.asList(conts)) < 1:
			raise ValueError, 'must supply at least one input container'
		self._wdgList = self._wdgList

	def allEnabled(self):
		"""Return True if all contained widgets are enabled and visible, False otherwise"""
		for cont in self._wdgList:
			if not cont.allEnabled():
				return False
		return True
	
	def getDefValueDict(self):
		"""Get the default widget values as a value dictionary,
		such as that returned by getValueDict. The data is returned as:
		- {name:dataDict} if a non-blank name was specified
		- dataDict otherwise
		where dataDict is the combined data dictionary of all containers in the list.
		"""
		dataDict = {}
		for cont in self._wdgList:
			dataDict.update(cont.getDefValueDict())
		if self._name:
			return {self._name:dataDict}
		else:
			return dataDict
	
	def getDefValueList(self):
		"""Get the widget default values as a list: [value1, value2...].
		"""
		defValueList = []
		for cont in self._wdgList:
			defValueList.extend(cont.getDefValueList())
		return defValueList
	
	def getStringList(self):
		"""Return a list of strings, one per container.
		"""
		retList = []
		for cont in self._wdgList:
			str = cont.getString()
			if str:
				retList.append(str)
		return retList
	
	def getValueDict(self):
		"""Get the widget values as a value dictionary.
		The form of the dictionary depends if this list has a name.
		
		If this list has a name (self._name is not blank),
		then the data for the items in this list are put in their own dictionary:
		   {self._name:{name1:value1, name2:value2...}},
		where self._name is the name of this list,
		and name1, name2...are names of the RO.InputCont widgets in the list.
		
		If the list does not have a name (self._name is blank),
		then the data is put at the root level of the dictionary:
			{name1:value1, name2:value2...}
		
		Giving this list a name protects the items within this list from
		name collision with other containers by the same name. The issue
		is that the value dictionary grows as containers and sets of containers
		are combined into larger sets.

		Suppose this list contains two containers, with names "item1", "item2"
		and corresponding values "value1", "value2".
		If the list name is blank, getValueDict will return:
			{"item1":"value1", "item2:"value2"}
		and if this list is combined in a list with other input containers,
		the result will look something like:
			{"item1":"value1", "item2:"value2", "otherItem1":"otherValue1"...}
		You can see how namespace collision is fairly likely if there are many of widgets
		created in various places, and it can be an accident waiting to happen.
		
		If the list name is "set1", then getValueDict will return:
			("set1":{"item1":"value1", "item2:"value2"}}
		and if this list is combined in a list with other input containers,
		the result will look something like:
			("set1":{"item1":"value1", "item2:"value2"}, "otherItem1":"otherValue1"...}
		Now namespace collision is much less likely -- another widget has to have
		the same name as this list; any widgets within this list are protected.
		"""
		valDict = {}
		for cont in self._wdgList:
			valDict.update(cont.getValueDict())
		if self._name:
			valDict = {self._name:valDict}
		return valDict
	
	def getValueList(self):
		"""Get the widget values as a list: [value1, value2...].
		"""
		dataList = []
		for cont in self._wdgList:
			dataList.extend(cont.getValueList())
		return dataList
	
	def getWdgDict(self):
		"""Return {name: wdgList} where wdgList is a copy of the list of widgets.
		"""
		wdgDict = {}
		for cont in self._wdgList:
			wdgDict.update(cont.getWdgDict())
		if self._name:
			wdgDict = {self._name:wdgDict}
		return wdgDict

	def getWdgList(self):
		"""Return a flat list of all contained widgets.
		This is intended for packing or gridding but is not safe for all value access
		as elements of a group should probably be accessed as one entity
		"""
		wdgList = []
		for cont in self._wdgList:
			wdgList.extend(cont.getWdgList())
		return wdgList
	
	def setValueDict(self, valDict):
		"""Set the widget values from a value dictionary.
		Extra names in the dictionary are ignored.
		
		Inputs:
		- valDict: a dictionary of the form returned by getValueDict.
		"""
		# get dictionary associated with my name, or {} if no such entry
		if self._name:
			myDict = valDict.get(self._name, {})
		else:
			myDict = valDict

		# set my widgets from my dictionary
		# want one callback instead of one per container,
		# so disable callbacks until finished
		tempCallbacks, self._callbacks = self._callbacks, ()
		try:
			for cont in self._wdgList:
				cont.setValueDict(myDict)
		finally:
			self._callbacks = tempCallbacks
			self._doCallbacks()

	def setValueList(self, valList):
		"""Not implemented."""
		raise NotImplementedError("%s does not support setValueList" % self.__class__.__name__)

if __name__ == "__main__":
	import Tkinter
	import RO.Wdg
	root = RO.Wdg.PythonTk()
	
	def doHide(*args):
		if hideVar.get():
			wdgFrame.pack_forget()
		else:
			wdgFrame.pack()

	def printOptions():
		valDict = cList.getValueDict()
		print 'dict:', valDict
		try:
			fmtStr = cList.getString()
		except Exception, e:
			print 'no string, error=', e
		else:
			print 'string:', fmtStr
		
	def printCallback(modWdg):
		print 'modified container', modWdg.getName()
		try:
			valDict = cList.getValueDict()
			print 'new dict:', valDict
		except ValueError, e:
			print e
		
	def setEnable(*args):
		doEnable = enableVar.get()
		cList.setEnable(doEnable)
	
	hideVar = Tkinter.IntVar()
	hideVar.set(False)
	hideVar.trace_variable('w', doHide)
	hideButton = Tkinter.Checkbutton (root, variable=hideVar, text='hide')
	hideButton.pack()
	
	enableVar = Tkinter.IntVar()
	enableVar.set(1)
	enableVar.trace_variable('w', setEnable)
	enableButton = Tkinter.Checkbutton (root, variable=enableVar, text='Enable')
	enableButton.pack()
	
	getButton = Tkinter.Button (root, command=printOptions, text='Print Options')
	getButton.pack()
	
	wdgFrame = Tkinter.Frame(root)
	
	conts = (
		WdgCont (
			name = 'ASingle',
			wdgs=(
				RO.Wdg.StrEntry(wdgFrame, width=5),
			),
			formatFunc = VMSQualFmt(),
		),
		WdgCont (
			name = 'APair',
			wdgs=(
				RO.Wdg.StrEntry(wdgFrame, width=5),
				RO.Wdg.StrEntry(wdgFrame, width=5),
			),
			formatFunc = VMSQualFmt(),
		),
		BoolNegCont (
			name = 'Keep',
			wdgs=(
				RO.Wdg.Checkbutton(wdgFrame, text='Object'),
				RO.Wdg.Checkbutton(wdgFrame, text='Boresight'),
				RO.Wdg.Checkbutton(wdgFrame, text='Calib', defValue=True),
			),
			formatFunc = VMSQualFmt(),
		),
	)
	cList = ContList(
		conts,
		formatFunc = BasicContListFmt(valSep=''),
		callFunc = printCallback,
	)
	
	clearButton = Tkinter.Button (root, command=cList.clear, text='Clear')
	clearButton.pack()
	
	defButton = Tkinter.Button (root, command=cList.restoreDefault, text='Default')
	defButton.pack()
	
	flatWdgList = cList.getWdgList()
	for wdg in flatWdgList:
		wdg.pack()
	wdgFrame.pack()

	root.mainloop()
