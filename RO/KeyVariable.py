#!/usr/local/bin/python
"""KeyVar and its cousins are used monitor data from the keyword dispatcher.
Keyword data may trigger callbacks or automatically update RO.Wdg widgets.

CmdVar is used to issue commands via the keyword dispatcher and monitor replies.

Error handling:
KeyVar.__init__ may raise an exception
KeyVar.set must not raise an exception; it should print warnings and errors to sys.stderr

History:
2001-01-10 R Owen: mod. FloatCnv to stop using nan (since python on Mac OS X doesn't support it);
	FloatCnv can now only detect the string version of "NaN".
2002-01-25 R Owen: Mod. to use the new RO.Wdg.getWdgBG function to determine
	background colors for good and bad vlues. Mod. to use SetWidgetText class,
	which reduces the complexity of the addWdgText, etc.
2002-02-05 R Owen: Mod. Intcnv to accept "NaN" for integers.
2002-03-04 R Owen: improved error messages from conversion classes.
2002-03-14 R Owen: major overhaul of callbacks:
	- addSetFunc renamed to addIndexedCallback; they now receive a 2nd positional argument isValid*
	- addCallback now receives a list of value, isValid duples*
	- added addValueListCallback, which is like the old addCallback
	The two callbacks that receive isValid may now get non-None values when isValid false
2002-05-02 R Owen: added an isRefresh field to KeyCmd. (It may be smarter to just
	let the RO.KeyDispatcher handle this knowledge by itself. We'll see.)
2002-05-29 R Owen: modified KeyCommand to accept timeLimKeyword and to compute self.maxEndTime
2002-06-11 R Owen: added a substitution dictionary to StringCnv.
2003-03-05 ROwen	Got rid of the whole idea of isValid; this simplifies get and callbacks;
	get now matches set (except for aggregate variables like PVTVar)
2003-04-10 ROwen	Modified FloatCnv and IntCnv to work with unicode strings.
2003-04-28 ROwen	Modified converter functions to use __call__ instead of cnv.
2003-05-08 ROwen	Corrected the test suite (was crashing on too few values);
					moved all conversion functions to RO.CnvUtil
					and removed use of typeName attribute in cnv functions.
2003-06-09 ROwen	Bug fix: inconsistent use of self.msgDict and self._msgDict.
2003-06-11 ROwen	Removed keyword argument from set.
2003-06-17 ROwen	Modified to call PVTVar callbacks 1/second if vel nonzero for any component;
					note that this means KeyVariable now relies on Tkinter;
					removed SetWidgetText class; it was not being used.
2003-06-25 ROwen	Modified to handle message data as a dict.
2003-07-16 ROwen	Added refreshTimeLim to KeyVar.
2003-08-04 ROwen	Changed default callNow to False.
2003-08-13 ROwen	Moved TypeDict and AllTypes from KeyDispatcher
					and added DoneTypes.
2003-09-23 ROwen	KeyCommand modified: added isDone and reply rejects attempts
					once the command has finished.
2003-10-22 ROwen	Bug fix: KeyCommand was looking for uppercase match strings;
					also modified KeyCommand to always lowercase callTypes
					to avoid this sort of problem in the future.
2003-11-21 ROwen	Overhauled handling of nval to permit varying-length KeyVars
					and to auto-computate nval by default.
					Modified to use SeqUtil instead of MathUtil.
2003-12-05 ROwen	Modified for RO.Wdg.Entry changes.
2003-12-17 ROwen	Added KeyVarFactory.
					Modified KeyVar to support the actor "keys", via new keyword refreshKeys
					and new attribute refreshInfo. Keys is used to refresh values from a cache,
					to save querying the original actor.
2003-12-26 ROwen	Added removeCallback method.
2004-01-06 ROwen	Removed refreshKeys arg from KeyVar (use KeyVarFactory.setKeysRefreshCmd instead);
					added hasRefreshCmd and getRefreshInfo to KeyVar;
					added setKeysRefreshCmd to KeyVarFactory.
2004-01-29 ROwen	Added isGenuine method to key variables.
2004-03-11 ROwen	KeyCommand timeLim documentation now states 0=no limit.
2004-04-19 ROwen	Speeded up handling of timeLimKeyword, based on the message's
					keyword data being a dictionary instead of (formerly) a list.
2004-07-21 ROwen	Renamed KeyCommand to CmdVar and modified as follows:
					- Added abortCmdStr argument
					- Added abort method
					- Added didFail method
					- changed callback named argument from keyCmd to cmdVar
					- changed cmdStarted to _setStartInfo (for clarity)
					  and added dispatcher and cmdID arguments.
					- callbacks are now protected (if a callback
					  fails a traceback is printed and the others are called).
					- initialized with type "i" (information) instead of None;
					  this assures CmdVars always have a character type.
					- added a dispatcher argument which immediately
					- added removeCallback method
					KeyVar changes:
					- setNotCurrent()-induced callbacks are now protected (if a callback
					  fails a traceback is printed and the others are called)
					- added __str__, which includes no type info
					- added removeCallback method (via inheriting from RO.AddCallback.BaseMixin)
					Added constant FailTypes.
2004-08-13 ROwen	Modified CmdVar.abort to make it only call the dispatcher
					if command not already done.
					KeyVarFactory: added refreshOptional argument.
2004-09-23 ROwen	Made callNow=True the default for callbacks
					script displays are current when first displayed.
2004-09-28 ROwen	Modified to allow removing callbacks while executing.
					Removed use of attribute _inCallbacks.
2005-02-01 ROwen	Bug fix: if an error occurred early in instantiation,
					formatting the exception string failed because no self.actor.
2005-06-08 ROwen	Changed CmdVar and KeyVarFactory to new style classes.
2005-06-14 ROwen	Modified CmdVar to clear all callbacks when command is done
					(to allow garbage collection).
"""
import sys
import time
import traceback
import Tkinter
import RO.AddCallback
import RO.Alg
import RO.CnvUtil
import RO.LangUtil
import RO.PVT
import RO.StringUtil
import RO.SeqUtil

# TypeDict translates message type characters to message categories
# entries are: (meaning, category), where:
# meaning is used for messages displaying what's going on
# category is coarser and is used for filtering by category
TypeDict = {
	"!":("fatal error", "Error"),	# a process dies
	"f":("failed", "Error"), # command failed
	"w":("warning", "Warning"),
	"i":("information", "Information"), # the initial state
	"s":("status", "Information"),
	">":("queued", "Information"),
	":":("finished", "Information"),
}
# all message types
AllTypes = "".join(TypeDict.keys())
# useful other message types
DoneTypes = ":f!"
FailTypes = "f!"

class KeyVar(RO.AddCallback.BaseMixin):
	"""Processes data associated with a keyword.
	
	Inputs:
	- keyword: the keyword associated with this variable (a string)
	- nval: the number of values:
		- if None, a fixed length KeyVar is assumed whose length is computed from converters
		- if a single integer, specifies the exact # of value required
		- if a pair of integers, specifies (min, max) # of values required;
			max = None means "no limit"
	- converters: one or a sequence of data converters (see below for more details);
		if there are more values than converters, the last converter is repeated;
		if there are more converters than allowed values, a ValueError is raised
	- actor: the name of the device which issued the keyword
	- description: a string describing the data, useful for help systems
	- refreshCmd: a command which can executed to refresh this item of data
	- refreshTimeLim: time limit for refresh command (sec)
	- dispatcher: keyword dispatcher; if supplied, the keyword subscribes itself to the dispatcher.
		Note that no record of that dispatcher is kept in the keyword (to reduce
		circular references, which as of this writing may not be garbage collected);
		so to unsubscribe this keyword you must talk to the dispatcher.
	- defValues: the value used initially and when data cannot be parsed;
		if one value, it is copied as many times as needed (max # of val, if finite, else min # of val)
		if a list of values, it is used "as is", after verifying the # of elements is in range
		Warning: default values are not converted and must be of the correct type; no checking is done
	- doPrint: a boolean flag controlling whether data is printed as set; for debugging

	Converters are functions that take one argument and return the converted data.
	The data supplied will usually be a string, but pre-converted data should
	also be acceptable. The converter should raise ValueError or TypeError for invalid data.
	
	There is an addCallback function that adds a callback function
	that is passed the following arguments whenever the KeyVar gets a reply
	or isCurrent goes false (as happens upon disconnection):
	- valueList: the new list of values,
	  (or the existing list if the variable is explicitly invalidated)
	- isCurrent (by name): false if value is not current
	- keyVar (by name): this keyword variable

	If a subclass sets self.cnvDescr before calling __init__
	then the original is retained.
	"""
	def __init__(self,
		keyword,
		nval = None,
		converters = RO.CnvUtil.nullCnv,
		actor = "",
		description = "",
		refreshCmd = None,
		refreshTimeLim  =  20,
		dispatcher = None,
		doPrint = False,
		defValues = None,
	):
		self.actor = actor
		self.keyword = keyword
		self.description = description
		if not hasattr(self, "cnvDescr"):
			self.cnvDescr = "" # temporary value for error messages

		# set and check self._converterList, self.minNVal and self.maxNVal
		self._converterList = RO.SeqUtil.asList(converters)
		if nval == None:
			# auto-compute
			self.minNVal = self.maxNVal = len(self._converterList)
		else:
			try:
				self.minNVal, self.maxNVal = RO.SeqUtil.oneOrNAsList(nval, 2, "nval")
				assert isinstance(self.minNVal, int)
				assert self.minNVal >= 0
				if self.maxNVal != None:
					assert isinstance(self.maxNVal, int)
					assert self.maxNVal >= self.minNVal
			except (ValueError, TypeError, AssertionError):
				raise ValueError("invalid nval = %r for %s" % (nval, self))
				
			if RO.SeqUtil.isSequence(converters) and self.maxNVal != None and len(converters) > self.maxNVal:
				raise ValueError("Too many converters (%d > max=%d) for %s" %
					(self.maxNVal, len(converters), self))
		
		#+
		# set self.cnvDescr (if necessary); this is used for __repr__ and error messages
		#-
		def nvalDescr():
			"""Returns a string describing the range of values:
			"""
			def asStr(numOrNone):
				if numOrNone == None:
					return "?"
				return "%r" % (numOrNone,)

			if self.minNVal == self.maxNVal:
				# fixed number of values; return it as a string
				return str(self.minNVal)
			else:
				# number of values varies; return the range as a string
				return "(%s-%s)" % (asStr(self.minNVal), asStr(self.maxNVal))
		
		if not self.cnvDescr:
			if self.maxNVal == 0:
				cnvDescr = "0"
			elif RO.SeqUtil.isSequence(converters):
				cnvNameList = [RO.LangUtil.funcName(cnv) for cnv in converters]
				cnvNameStr = ", ".join(cnvNameList)
				if not (self.minNVal == self.maxNVal == len(cnvNameList)):
					# not a fixed length keyVar or length != # of converters
					cnvNameStr += "..."
				cnvDescr = "%s, (%s)" % (nvalDescr(), cnvNameStr)
			else:
				cnvDescr = "%s, %s" % (nvalDescr(), RO.LangUtil.funcName(converters))
			self.cnvDescr = cnvDescr
		
		
		# handle refresh info; having a separate refreshActor
		# allows KeyVarFactory.setKeysRefreshCmd to set it to "keys"
		self.refreshActor = self.actor
		self.refreshCmd = refreshCmd
		self.refreshTimeLim = refreshTimeLim
		
		self.doPrint = doPrint
		self._msgDict = None	# message dictionary used to set KeyVar; can be None
		self._setTime = None
		self._refreshKeyCmd = None  # most recent command used to refresh
		self._valueList = []
		
		RO.AddCallback.BaseMixin.__init__(self, defCallNow = True)

		# handle defaults
		if RO.SeqUtil.isSequence(defValues):
			self._defValues = defValues
		else:
			if self.maxNVal != None:
				nval = self.maxNVal
			else:
				nval = self.minNVal
			self._defValues = (defValues,) * nval
		self._restoreDefault()

		self._isCurrent = False
		
		# if a keyword dispatcher is specified, add the keyword to it
		if dispatcher:
			dispatcher.add(self)
	
	def __repr__(self):
		return "%s(%r, %r, %s)" % \
			(self.__class__.__name__, self.actor, self.keyword, self.cnvDescr)
	
	def __str__(self):
		return "%s(%r, %r)" % \
			(self.__class__.__name__, self.actor, self.keyword)
	
	def _restoreDefault(self):
		"""Set self._valueList to initial values but does not call callbacks."""
		if self._defValues != None:
			self._valueList = self._defValues[:]

	def addDict (self, dict, item, fmtStr, ind=0):
		"""Adds a dictionary whose specified item is to be set"""
		def setFunc (value, isCurrent, keyVar, dict=dict, item=item, fmtStr=fmtStr):
			if value != None:
				dict[item] = fmtStr % value
			else:
				dict[item] = None
		self.addIndexedCallback (setFunc, ind)

	def addDictDMS (self, dict, item, nFields=3, precision=1, ind=0):
		"""Adds a dictionary whose specified item is to be set to the DMS representation of the data"""
		def setFunc (value, isCurrent, keyVar, dict=dict, item=item, precision=precision):
			if value != None:
				dict[item] = RO.StringUtil.dmsStrFromDeg(value, nFields, precision)
			else:
				dict[item] = None
		self.addIndexedCallback (setFunc, ind)

	def addIndexedCallback(self, callFunc, ind=0, callNow=True):
		"""Similar to addCallback, but the call function receives the value at one index.
		This simplifies callbacks a bit, especially for aggregate values (see PVTKeyVar).
	
		Note: if the keyvariable has a variable # of values	and the one specified
		by ind is not set, the callback is not called. In general, it is discouraged
		to use indexed callbacks for variable-length keyvariables.

		Inputs:
		- callFunc: callback function with arguments:
		  - value: new value at the specified index (or the existing value
				if the variable is explicitly invalidated)
		  - isCurrent (by name): false if value is not current
		  - keyVar (by name): this keyword variable
		- callNow: if true, execute callFunc immediately,
		  else wait until the keyword is seen
		"""
		if self.maxNVal == 0:
			raise ValueError("%s has 0 values; addIndexedCallback prohibited" % (self,))
		try:
			RO.MathUtil.checkRange(ind+1, 1, self.maxNVal)
		except ValueError:
			raise ValueError("invalid ind=%r for %s" % (ind, self,))
				
		def fullCallFunc(valueList, isCurrent, keyVar, ind=ind):
			try:
				val = valueList[ind]
			except IndexError:
				return
			callFunc(val, isCurrent=isCurrent, keyVar=keyVar)
		self.addCallback(fullCallFunc, callNow)

	def addROWdg (self, wdg, ind=0, setDefault=False):
		"""Adds an RO.Wdg; these format their own data via the set
		or setDefault function (depending on setDefault).
		Typically one uses set for a display widget
		and setDefault for an Entry widget
		"""
		if setDefault:
			self.addIndexedCallback (wdg.setDefault, ind)
		else:
			self.addIndexedCallback (wdg.set, ind)
	
	def addROWdgSet (self, wdgSet, setDefault=False):
		"""Adds a set of RO.Wdg wigets;
		should be more efficient than adding them one at a time with addROWdg
		"""
		if self.maxNVal != None and len(wdgSet) > self.maxNVal:
			raise IndexError("too many widgets (%d > max=%d) for %s" % (len(wdgSet), self.maxNVal, self,))
		if setDefault:
			class callWdgSet(object):
				def __init__(self, wdgSet):
					self.wdgSet = wdgSet
					self.wdgInd = range(len(wdgSet))
				def __call__(self, valueList, isCurrent, keyVar):
					for wdg, val in zip(self.wdgSet, valueList):
						wdg.setDefault(val, isCurrent=isCurrent, keyVar=keyVar)
		else:
			class callWdgSet(object):
				def __init__(self, wdgSet):
					self.wdgSet = wdgSet
					self.wdgInd = range(len(wdgSet))
				def __call__(self, valueList, isCurrent, keyVar):
					for wdg, val in zip(self.wdgSet, valueList):
						wdg.set(val, isCurrent=isCurrent, keyVar=keyVar)
		self.addCallback (callWdgSet(wdgSet))

	def get(self):
		"""Returns the data as a tuple:
		- valueList: a copy of the list of values
		- isCurrent
		"""
		return self._valueList[:], self._isCurrent
	
	def getInd(self, ind):
		"""Returns the data at index=ind as a tuple:
		- value: the value at index=ind
		- isCurrent
		"""
		return self._valueList[ind], self._isCurrent
	
	def hasRefreshCmd(self):
		"""Returns True if has a refresh command.
		"""
		return bool(self.refreshCmd)

	def getRefreshInfo(self):
		"""Returns the refresh actor, command (None if no command) and time limit
		or None if no refresh command.
		"""
		return (self.refreshActor, self.refreshCmd, self.refreshTimeLim)
	
	def getMsgDict(self):
		"""Returns the message dictionary from the most recent call to "set",
		or an empty dictionary if no dictionary supplied or "set" never called.
		"""
		return self._msgDict or {}
		
	def isCurrent(self):
		return self._isCurrent
	
	def isGenuine(self):
		"""Returns True if there is a message dict and it is from the actual actor.
		"""
		actor = self.getMsgDict().get("actor")
		return actor == self.actor
			
	def set(self, valueList, isCurrent=True, msgDict=None):
		"""Sets the variable's value,
		then updates the time stamp and executes the callbacks (if any)

		Inputs:
		- valueList: a tuple of new values; if None then all values are reset to default
		- msgDict: the full keyword dictionary, see KeywordDispatcher for details

		Errors:
		If valueList has the wrong number of elements then the data is rejected
		and an error message is printed to sys.stderr
		"""
		if valueList == None:
			self._restoreDefault()
		else: 
			nout = self._countValues(valueList)
	
			# set values
			self._valueList = [self._convertValueFromList(ind, valueList) for ind in range(nout)]

		# update remaining parameters
		self._isCurrent = isCurrent
		self._setTime = time.time()
		self._msgDict = msgDict

		# print to stderr, if requested
		if self.doPrint:
			sys.stderr.write ("%s = %r\n" % (self, self._valueList))

		# apply callbacks, if any
		self._doCallbacks()
	
	def setNotCurrent(self):
		"""Clears the isCurrent flag

		Does NOT update _setTime because that tells us when the value was last set;
		if we need a timestamp updated when the data was marked stale, add a new one.
		"""
		self._isCurrent = False

		# print to stderr, if requested
		if self.doPrint:
			sys.stderr.write ("%s=%r\n" % (self, self._valueList))
		
		self._doCallbacks()
	
	def _convertValueFromList(self, ind, valueList):
		"""A utility function for use on list of raw (unconverted) values.
		Returns cnvValue for valueList[ind], or None if value cannot be converted.
		
		Error handling:
		- If the value cannot be converted, complains and returns (valueList[ind], 0)
		- If the value does not exist in the list (or the converter does not exist),
		  silently returns (None, 0) (a message has already been printed)
		"""
		rawValue = valueList[ind]
		if rawValue == None:
			return None
		try:
			return self._getCnvFunc(ind)(rawValue)
		except (ValueError, TypeError), e:
			# value could not be converted
			sys.stderr.write("invalid value %r for ind %s of %s\n" % (rawValue, ind, self))
			return None
		except Exception, e:
			# unknown error; this should not happen
			sys.stderr.write("could not convert %r for ind %d of %s: %s\n" % (rawValue, ind, self, e))
			return None
	
	def _countValues(self, valueList):
		"""Check length of valueList and return the number of values there should be after conversion.
		"""
		nval = len(valueList)
		if nval < self.minNVal:
			raise ValueError("too few values in %r for %s (%s < %s)" % (valueList, self, nval, self.minNVal))
		if self.maxNVal != None and nval > self.maxNVal:
			raise ValueError("too many values in %r for %s (%s > %s)" % (valueList, self, nval, self.maxNVal))
		return nval

	def _doCallbacks(self):
		"""Call the callback functions.
		"""
		self._basicDoCallbacks(
			self._valueList,
			isCurrent = self._isCurrent,
			keyVar = self,
		)

	def _getCnvFunc(self, ind):
		"""Returns the appropriate converter function for index ind.
		If ind < 0, returns the last one
		"""
		try:
			return self._converterList[ind]
		except IndexError:
			return self._converterList[-1]


class PVTKeyVar(KeyVar):
	"""Position, velocity, time tuple for a given # of axes.

	Similar to KeyVar except:
	- The supplied keyword data is in the form:
		pos1, vel1, t1, pos2, vel2, t2..., pos<naxes>, vel<naxes>, t<naxes>
	- Values are PVTs
	"""
	_tkWdg = None
	def __init__(self,
		keyword,
		naxes=1,
		**kargs
	):
		if naxes < 1:
			raise ValueError("naxes = %d, but must be positive" % (naxes))
		self.cnvDescr = str(naxes)
		KeyVar.__init__(self,
			keyword = keyword,
			nval = naxes,
			converters = RO.CnvUtil.asFloat,
			defValues = RO.PVT.PVT(),
		**kargs)

		self._hasVel = False
		if PVTKeyVar._tkWdg == None:
			PVTKeyVar._tkWdg = Tkinter.Frame()
		self._afterID = None

	def addPosCallback(self, callFunc, ind=0, callNow=True):
		"""Similar to addIndexedCallback, but the call function
		receives the current position at one index.

		Inputs:
		- callFunc: callback function with arguments:
		  - value: new current position of the PVT at the specified index
		    (or of the existing PVT if the variable is explicitly invalidated)
		  - isCurrent (by name): false if value is not current
		  - keyVar (by name): this keyword variable
		- callNow: if true, execute callFunc immediately,
		  else wait until the keyword is seen
		"""
		def fullCallFunc(valueList, isCurrent, keyVar, ind=ind):
			return callFunc(valueList[ind].getPos(), isCurrent=isCurrent, keyVar=keyVar)
		self.addCallback(fullCallFunc, callNow)

	def addROWdg (self, wdg, ind=0):
		"""Adds an RO.Wdg; these format their own data via the set function"""
		self.addPosCallback (wdg.set, ind)
	
	def addROWdgSet (self, wdgSet):
		"""Adds a set of RO.Wdg wigets that are set to the current position;
		should be more efficient than adding them one at a time with addROWdg"""
		if self.maxNVal != None and len(wdgSet) > self.maxNVal:
			raise IndexError("too many widgets (%d > max=%d) for %s" % (len(wdgSet), self.maxNVal, self,))
		class callWdgSet(object):
			def __init__(self, wdgSet):
				self.wdgSet = wdgSet
				self.wdgInd = range(len(wdgSet))
			def __call__(self, valueList, isCurrent, keyVar):
				for ind in self.wdgInd:
					wdgSet[ind].set(valueList[ind].getPos(), isCurrent=isCurrent, keyVar=keyVar)
		self.addCallback (callWdgSet(wdgSet))
	
	def set(self, *args, **kargs):
		self._hasVel = False
		KeyVar.set(self, *args, **kargs)

	def _convertValueFromList(self, ind, valueList):
		"""Returns converted value at index ind, given valueList,
		or a null PVT if cannot convert. Should only be called by set.
		
		Error handling:
		- If the value cannot be converted, complains and returns a null PVT
		- If the value does not exist in the list (or the converter does not exist),
		  returns a null PVT after somebody prints a message
		"""
		try:
			startInd = ind * 3
			rawValue = valueList[startInd:startInd+3]
			pvt = RO.PVT.PVT(*rawValue)
			if pvt.vel not in (0.0, None):
				self._hasVel = True
			return pvt
		except (ValueError, TypeError):
			# value could not be converted
			sys.stderr.write("invalid value %r at index %d for %s\n" % (rawValue, ind, self))
			return RO.PVT.PVT()
		except IndexError:
			# value does not exist (or converter does not exist, but that's much less likely)
			# a message should already have been printed
			return RO.PVT.PVT()
		except Exception, e:
			# unknown error; this should not happen
			sys.stderr.write("could not convert %r at index %d for %s: %s\n" % (rawValue, ind, self, e))
			return RO.PVT.PVT()

	def _countValues(self, valueList):
		"""Check length of valueList and return the number of values there should be after conversion.
		"""
		nval = len(valueList)
		if nval < self.minNVal * 3:
			raise ValueError("too few values in %r for %s (%s < %s)" % (valueList, self, nval, self.minNVal * 3))
		if self.maxNVal != None and nval > self.maxNVal * 3:
			raise ValueError("too many values in %r for %s (%s > %s)" % (valueList, self, nval, self.maxNVal * 3))
		if nval % 3 != 0:
			raise ValueError("%s must contain a multiple of 3 elements for %s" % (valueList, self))
		return nval // 3

	def _doCallbacks(self):
		"""Call the callback functions.
		"""
		if self._afterID:
			PVTKeyVar._tkWdg.after_cancel(self._afterID)
		KeyVar._doCallbacks(self)
		if self._hasVel:
			self._afterID = PVTKeyVar._tkWdg.after(1000, self._doCallbacks)

class CmdVar(object):
	"""Issue a command via the dispatcher and receive callbacks
	as replies are received.
	"""
	def __init__(self,
		cmdStr = "",
		actor = "",
		timeLim = 0,
		description = "",
		callFunc = None,
		callTypes = DoneTypes,
		isRefresh = False,
		timeLimKeyword = None,
		abortCmdStr = None,
		dispatcher = None,
	):
		"""
		Inputs:
		- actor: the name of the device which issued the keyword
		- cmdStr: the command; no terminating \n wanted
		- timeLim: maximum time before command expires, in sec; 0 for no limit
		- description: a string describing the command, useful for help systems
		- callFunc: a function to call when the command changes state;
			see addCallback for details.
		- callTypes: the message types for which to call the callback;
			see addCallback for details.
		- isRefresh: the command was triggered by a refresh request, else is a user command
		- timeLimKeyword: a keyword specifying a delta-time by which the command must finish
		- abortCmdStr: a command string that will abort the command.
			Sent by abort if specified and if the command is executing.
		- dispatcher: command dispatcher; if specified, the command is automatically dispatched;
			otherwise you have to dispatch it yourself
		
		Note: timeLim and timeLimKeyword work together as follows:
		- The initial time limit for the command is timeLim
		- If timeLimKeyword is seen before timeLim seconds have passed
		  then self.maxEndTime is updated with the new value
		  
		Also the time limit is a lower limit. The command is guaranteed to
		expire no sooner than this 
		"""
		self.cmdStr = cmdStr
		self.actor = actor
		self.cmdID = None
		self.timeLim = timeLim
		self.description = description
		self.isRefresh = isRefresh
		self.timeLimKeyword = timeLimKeyword
		self.abortCmdStr = abortCmdStr

		self.dispatcher = None # dispatcher arg is handled later
		self.replies = []
		self.lastType = "i"
		self.startTime = None
		self.maxEndTime = None

		# the following is a list of (callTypes, callFunc)
		self.callTypesFuncList = []
		
		# if a timeLimKeyword specified
		# set up a callback, but only for non-final message types
		# (changing the time limit for the final message is a waste of time)
		if self.timeLimKeyword:
			self.addCallback(self._checkForTimeLimKeyword, callTypes = ">siw")

		if callFunc:
			self.addCallback(callFunc, callTypes)
		
		if dispatcher:
			dispatcher.executeCmd(self)
	
	def abort(self):
		"""Abort the command, including:
		- deregister the command from the dispatcher
		- send the abort command (if it exists)
		- set state to failed, calling the appropriate callbacks

		Has no effect if the command was never dispatched or has already ended.
		"""
		if self.dispatcher and not self.isDone():
			self.dispatcher.abortCmdByID(self.cmdID)

	def addCallback(self, callFunc, callTypes = DoneTypes):
		"""Executes the given function whenever a reply is seen
		for this user with a matching command number

		Inputs:
		- callFunc: a function to call when the command changes state
		- callTypes: the message types for which to call the callback;
			a string of one or more choices; see TypeDict for the choices;
			useful constants include DoneTypes (command finished or failed)
			and AllTypes (all message types, thus any reply).
			Not case sensitive (the string you supply will be lowercased).

		Callback arguments:
			msgType: the message type, a character (e.g. "i", "w" or ":");
				see TypeDict for the various types.
			msgDict: the entire message dictionary
			cmdVar (by name): this command variable
		"""
		self.callTypesFuncList.append((callTypes.lower(), callFunc))
	
	def didFail(self):
		"""Return True if the command failed, False otherwise.
		"""
		return self.lastType in FailTypes
	
	def isDone(self):
		"""Return True if the command is finished, False otherwise.
		"""
		return self.lastType in DoneTypes

	def removeCallback(self, callFunc, doRaise=True):
		"""Delete the callback function.
		Return True if successful, raise error or return False otherwise.

		Inputs:
		- callFunc	callback function to remove
		- doRaise	raise exception if unsuccessful? True by default.
		
		If doRaise true:
		- Raises ValueError if callback not found
		- Raises RuntimeError if executing callbacks when called
		Otherwise returns False in either case.
		"""
		for typesFunc in self.callTypesFuncList:
			if callFunc == typesFunc[1]:
				self.callTypesFuncList.remove(typesFunc)
				return True
		if doRaise:
			raise ValueError("Callback %r not found" % callFunc)
		return False
	
	def reply(self, msgDict):
		"""Add msgDict to self.replies and call the command callback
		(if the message type is appropriate).
		Warn and do nothing else if called after the command has finished.
		"""
		if self.lastType in DoneTypes:
			sys.stderr.write("Command %s already finished; no more replies allowed\n" % (self,))
			return
		self.replies.append(msgDict)
		msgType = msgDict["type"]
		self.lastType = msgType
		for callTypes, callFunc in self.callTypesFuncList[:]:
			if msgType in callTypes:
				try:
					callFunc(msgType, msgDict, cmdVar=self)
				except (SystemExit, KeyboardInterrupt):
					raise
				except:
					sys.stderr.write ("%s callback %s failed\n" % (self, callFunc))
					traceback.print_exc(file=sys.stderr)
		if self.lastType in DoneTypes:
			self.callTypesFuncList = []
					
	
	def _checkForTimeLimKeyword(self, msgType, msgDict, **kargs):
		"""Looks for self.timeLimKeyword in the message dictionary
		and updates self.maxEndTime if found.
		Adds self.timeLim as a margin (if self.timeLim was ever specified).
		Raises ValueError if the keyword exists but the value is invalid.
		"""
		valueTuple = msgDict["data"].get(self.timeLimKeyword)
		if valueTuple != None:
			if len(valueTuple) != 1:
				raise ValueError("Invalid value %r for timeout keyword %r for command %d: must be length 1"
					% (valueTuple, keywd, self.cmdID))
			try:
				newTimeLim = float(valueTuple[0])
			except:
				raise ValueError("Invalid value %r for timeout keyword %r for command %d: must be (number,)"
					% (valueTuple, keywd, self.cmdID))
			self.maxEndTime = time.time() + newTimeLim
			if self.timeLim:
				self.maxEndTime += self.timeLim

	def _setStartInfo(self, dispatcher, cmdID):
		"""Called by the dispatcher when dispatching the command.
		"""
		self.dispatcher = dispatcher
		self.cmdID = cmdID
		self.startTime = time.time()
		if self.timeLim:
			self.maxEndTime = self.startTime + self.timeLim
	
	def __repr__(self):
		return "%s %r: %r %r" % (self.__class__.__name__, self.cmdID, self.actor, self.cmdStr)
	
	def __str__(self):
		return "%s %r" % (self.actor, self.cmdStr)


class KeyVarFactory(object):
	"""Factory for contructing sets of similar KeyVars.

	It allows one to specify default values for parameters
	and override them as desired.
	
	Inputs are the default values for the key variable type plus:
	- keyVarType: the desired type (KeyVar by default)
	- allowRefresh: default for allowRefresh (see __call__)
	"""
	def __init__(self,
		keyVarType = KeyVar,
		allowRefresh = True,
	**defKeyArgs):
		"""Specify the default arguments for the key variable type;
		the usual choices are:
		- actor
		- dispatcher
		- refreshCmd
		and possibly:
		- nval
		- converters
		"""
		self._keyVarType = keyVarType
		self._allowRefresh = allowRefresh
		self._defKeyArgs = defKeyArgs
		# _actorKeyVarsRefreshDict is for use by setKeysRefreshCmd
		# entries are actor:list of keyVars that are not local
		# and don't have an explicit refresh command
		self._actorKeyVarsRefreshDict = RO.Alg.ListDict()
		self._actorOptKeywordsRefreshDict = RO.Alg.ListDict()
		
	def __call__(self,
		keyword,
		isLocal = False,
		allowRefresh = None,
		refreshOptional = False,
	**keyArgs):
		"""Create and return a new key variable.

		The arguments are the same as for the key variable class being constructed
		(with the defaults specified during __init__), plus:
		- isLocal	True means you only want to set the keyword yourself;
					it forces dispatcher and refreshCmd to None;
		- allowRefresh	is a refresh command allowed?
		- refreshOptional is a refresh command optional?
					this means it'll be requested from keys, but TUI will pay
					no attention if it fails to update the keyword.
					It is ignored if allowRefresh is False
					and requires at least one other keyword be updated for this actor.
		
		Raises RuntimeError if allowRefresh true and:
		- isLocal True
		- refreshCmd specified in this call (the default is irrelevant)
		"""
		if isLocal:
			keyArgs["dispatcher"] = None
			keyArgs["refreshCmd"] = None
		
		netKeyArgs = self._defKeyArgs.copy()
		netKeyArgs.update(keyArgs)
		keyVar = self._keyVarType(keyword, **netKeyArgs)

		if allowRefresh == None:
			allowRefresh = self._allowRefresh
		elif allowRefresh:
			# allowRefresh specified True in this call;
			# test for invalid combination of keyword args
			if keyArgs.get("refreshCmd", None):
				raise RuntimeError("%s: refreshCmd prohibited if allowRefresh false" % (keyVar,))
			if isLocal:
				raise RuntimeError("%s: isLocal prohibited if allowRefresh true" % (keyVar,))
			keyArgs["refreshCmd"] = None
		
		if allowRefresh and (not isLocal) and (not netKeyArgs.has_key("refreshCmd")):
			if refreshOptional:
				self._actorOptKeywordsRefreshDict[keyVar.actor] = keyword
			else:
				self._actorKeyVarsRefreshDict[keyVar.actor] = keyVar
		return keyVar

	def setKeysRefreshCmd(self, getAllKeys = False):
		"""Sets a refresh command of keys getFor=<actor> <key1> <key2>...
		for all key variables that meet these criteria:
		- are not local
		- do not have an explicit refresh command
		- produced since the last call to setKeysRefreshCmd
		
		Inputs:
		- getAllKeys: if True, gets all keys for this actor;
			the refresh command becomes: keys getFor=<actor>
			(without an explicit list of keywords)

		In case key variables with more than one actor have been produced,
		those for each actor get their own command.
		"""
		for actor, keyVars in self._actorKeyVarsRefreshDict.iteritems():
			if getAllKeys:
				refreshCmd = "getFor=%s" % (actor,)
			else:
				refreshKeys = [keyVar.keyword for keyVar in keyVars]
				extraKeys = self._actorOptKeywordsRefreshDict.get(actor, [])
				refreshKeys += extraKeys
				refreshCmd = "getFor=%s %s" % (actor, " ".join(refreshKeys))
#			print "setting refreshCmd=%r for keys %s" % (refreshCmd, refreshKeys)
			for keyVar in keyVars:
				keyVar.refreshActor = "keys"
				keyVar.refreshCmd = refreshCmd
				keyVar.refreshTimeLim = 20
		self._actorKeyVarsRefreshDict = RO.Alg.ListDict()
		self._actorOptKeywordsRefreshDict = RO.Alg.ListDict()


if __name__ == "__main__":
	doBasic = True
	doFmt = True
	import RO.KeyDispatcher
	import RO.Astro.Tm
	
	root = Tkinter.Tk()

	if doBasic:
		print "\nrunning basic variables test"
		varList = (
			KeyVar("Str0-?",       nval=(0,None), converters=str, doPrint=True),
			KeyVar("Empty",        nval=0, doPrint=True),
			KeyVar("Str",          converters=str, doPrint=True),
			KeyVar("Int",          converters=RO.CnvUtil.asInt, doPrint=True),
			KeyVar("Float",        converters=RO.CnvUtil.asFloat, doPrint=True),
			KeyVar("Bool",         converters=RO.CnvUtil.asBool, doPrint=True),
			KeyVar("IntStr",       converters=(RO.CnvUtil.asInt, str), doPrint=True),
			KeyVar("Str1-2",       nval=(1,2), converters=str, doPrint=True),
			KeyVar("Str2",         nval=2, converters=str, doPrint=True),
			PVTKeyVar("PVT1-2",    naxes=(1,2), doPrint=True),
			PVTKeyVar("PVT2",      naxes=2, doPrint=True),
		)
		dataList = (
			(),
			("hello",), ("t",), ("F",), (None,), ("",), ("NaN",), (0,), ("0",), (1,), ("1",), (2,), ("2",), (1.2,), ("1.2",),
			("hello",)*2, ("t",)*2, ("F",)*2, (None,)*2, ("",)*2, ("NaN",)*2, (0,)*2, ("0",)*2, (1,)*2, ("1",)*2, (2,)*2, ("2",)*2, (1.2,)*2, ("1.2",)*2,
			("hello",)*3, ("t",)*3, ("F",)*3, (None,)*3, ("",)*3, ("NaN",)*3, (0,)*3, ("0",)*3, (1,)*3, ("1",)*3, (2,)*3, ("2",)*3, (1.2,)*3, ("1.2",)*3,
			("lots", "of", "data", 1, 2, 3),
			(25, "hello",),
			(20, 0.1, 79842, 47, -0.2, 79842,),
			(20, 0.1, "NaN", 47, -0.2, 79842,),
			(20, 0.1, 79842, 47, -0.2, 79842, 88, 0.4, 79842,),
		)

		for data in dataList:
			print "\ndata: ", data
			for var in varList:
				try:
					var.set(data)
				except (ValueError, IndexError), e:
					print "failed with %s: %s" % (e.__class__.__name__, e)

	if doFmt:
		print "\nrunning format test"
		afl = KeyVar("FloatVar", 1, RO.CnvUtil.asFloat)
		fmtSet = ("%.2f", "%10.5f", "%.0f")
		dictList = []
		for fmtStr in fmtSet:
			dict = {"text":None}
			dictList.append(dict)
			afl.addDict (dict, "text", fmtStr)

		dict = {"text":None}
		dictList.append(dict)
		afl.addDictDMS (dict, "text", nFields=3, precision=1)


		# create a set of values and apply them one at a time, showing the results each time
		valSet = (0, 3.14159, -98.7654321)
		for val in valSet:
			print "\nval=", val
			try:
				afl.set((val,))
				for dict in dictList:
					print repr(dict["text"])
			except Exception, e:
					print e
	
	# test PVT callback
	print "\nrunning pvt callback test; hit ctrl-C to end"
	
	def pvtCallback(valList, isCurrent, keyVar):
		if valList == None:
			return
		pvt = valList[0]
		print "%s pos = %s" % (pvt, pvt.getPos())
	pvtVar = PVTKeyVar("PVT")
	pvtVar.addCallback(pvtCallback)
	currTAI = RO.Astro.Tm.TAI.taiFromPySec()
	pvtVar.set((1.0, 0.1, currTAI))

	root.mainloop()
