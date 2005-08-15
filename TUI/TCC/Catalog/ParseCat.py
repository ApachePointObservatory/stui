#!/usr/local/bin/python
"""Parse an object catalog data, returning a list of data dictionaries, one per object.

History:
2003-11-04 ROwen
2003-11-18 ROwen	Modified to use SeqUtil instead of MathUtil.
2004-02-23 ROwen	Preference files are now read with universal newline support
					on Python 2.3 or later.
2004-03-05 ROwen	Modified parseCat to return a TelTarget instead of
					a list of value dictionaries and to parse new catalog options.
					Modified to use RO.OS.univOpen.
2004-05-18 ROwen	Stopped importing sys since it wasn't used.
					Eliminated a redundant import in the test code.
2004-10-12 ROwen	parseCat handles omitted object name better; they are now
					treated as any bad data line (skipped and reported in errList)
					instead of causing an abort.
2005-06-08 ROwen	Changed CatalogParser to a new-style class.
2005-08-15 ROwen	Modified the test code to run again.
"""
import os.path
import re
import Tkinter
import GetString
import RO.Alg
import RO.CnvUtil
import RO.OS
import RO.SeqUtil
import RO.ParseMsg.ParseData as ParseData
import TUI.TCC.UserModel
import TUI.TCC.TelTarget
import TUI.TCC.SlewWdg.InputWdg

def listGet(aList, ind, defValue=None):
	try:
		return aList[ind]
	except IndexError:
		return defValue


posOptionRE = re.compile(r'[ \t]*([0-9+-.:]+)[ \t]+([0-9+-.:]+)(?:[ \t]+(.*))?')
namePosOptionRE = re.compile(r'[ \t]*([^ \t,;]+)[ \t]+([0-9+-.:]+)[ \t]+([0-9+-.:]+)(?:[ \t]+(.*))?')

# these options are never used to create an object
# but are extracted and used when creating the final catalog
_CatOptionDict = {
	"doDisplay": True,
	"dispColor": "black",
}

class CatalogParser(object):
	"""Object that will read in object catalogs, expand abbreviations,
	correct case and check limits.
	
	Warning: uses a (hidden) Tkinter widget to perform value checking
	and abbreviation expansion. Thus:
	- Do not call from a background thread.
	- Before calling you should already	have created a root widget.
	"""
	def __init__(self):
		# get a local tcc user model and use to create a slew input widget
		# that I can safely set without affecting other widgets
		userModel = TUI.TCC.UserModel._Model()
		tl = Tkinter.Toplevel()
		tl.withdraw()
		self._slewInputWdg = TUI.TCC.SlewWdg.InputWdg.InputWdg(
			master = tl,
			userModel = userModel,
		)
		self._slewInputWdg.pack()

		defValueDict = self._slewInputWdg.getDefValueDict()
		defValueDict.update(_CatOptionDict)
		print defValueDict
		self._keyMatcher = RO.Alg.MatchList(
			valueList = defValueDict.keys(),
			abbrevOK = True,
			ignoreCase = True,
		)
		self._catOptions = _CatOptionDict
	
	def parseCat(self, filePath):
		"""Parse a catalog given its full file path.
		
		Returns two items:
		- objCat: the catalog as a TUI.TCC.TelTarget.Catalog
		- errList: a list of (line, errMsg) tuples, one per rejected line of object data
		
		Raises RuntimeError if the file cannot be read or a default is invalid.
		
		Uses universal newline support (new in Python 2.3) if possible.
		"""
#		print "parseCat(%r)" % (filePath,)
		fp = RO.OS.openUniv(filePath)
		catName = os.path.basename(filePath)

		defOptionDict = self._keyMatcher.matchKeys({
			"CSys": "FK5",
			"RotType": "Object",
		})
		errList = []
		objList = []
		
		# save checkWdg data, then use try/finally to restore no matter what
		ii = 0
		for line in fp:
			ii += 1
#			print "Parsing object %d" % ii
			isDefault = False
			line = line.strip()
			try:
				if not line:
					# blank line
					continue
				elif line[0] in ("#", "!"):
					# comment
					continue
				elif line[0] in ('"', "'"):
					# data with quoted object name
					(objName, nextInd) = GetString.getString(line)
					pos1, pos2, optionStr = posOptionRE.match(line[nextInd:]).groups()
				else:
					# data with unquoted object name or default option
					match = namePosOptionRE.match(line)
					if match:
						# data with unquoted object name
						objName, pos1, pos2, optionStr = match.groups()
					elif line[0].isdigit():
						raise ValueError("could not parse; is object name missing?")
					else:
						isDefault = True
						optionStr = line
		
				if optionStr:
					optDict = ParseData.parseKeyValueData(optionStr)
				else:
					optDict = {}
				
				if isDefault:
					# update existing defaults
					
					# merge new defaults into existing defaults
					# and check the result
					self._combineDicts(defOptionDict, optDict)
				else:
					# a line of data
					# the data dictionary starts with the current defaults
					dataDict = defOptionDict.copy()
					
					# add object name and position (non-dictionary items)
					dataDict.update({
						"Name": objName,
						"ObjPos": (pos1, pos2),
					})

					# merge new data with a copy of the defaults
					# and check the result
					self._combineDicts(dataDict, optDict)
					
					objList.append(TUI.TCC.TelTarget.TelTarget(dataDict))
			except (SystemExit, KeyboardInterrupt):
				raise
			except Exception, e:
				if isDefault:
					raise RuntimeError(str(e))
				else:
					errList.append((line, str(e)))
		
		# convert catalog options as appropriate
		self._catOptions["doDisplay"] = RO.CnvUtil.asBool(self._catOptions["doDisplay"])

		# create catalog
#		print "parseCat: catOptions =", self._catOptions
		objCat = TUI.TCC.TelTarget.Catalog (
			name = catName,
			objList = objList,
		**self._catOptions)
#		print "parseCat returning (%r, %r)" % (objCat, errList)
		return objCat, errList
	
	def _combineDicts(self, defDict, newDict):
		"""Combine a new dictionary into an existing default dictionary.
		The default dictionary is modified; newDict is not.
		
		It is assumed that defDict already has been key-matched
		(expanding abbreviations and correcting case).
		
		The process is as follows:
		- newDict is key-matched (creating a copy)
		- if the new dictionary has certain items (e.g. CSys, RotType)
		  then corresponding items are removed from the default dict (e.g. data, rotang).
		- newDict is added to defDict (overriding matching items)
	
		Raises ValueError if newDict cannot be key-matched
		or the resulting defDict has invalid values.
		"""
#		print "defDict = %r; newDict = %r" % (defDict, newDict)
		newDict = self._keyMatcher.matchKeys(newDict)
		# if newDict has csys, erase date in defDict, etc.
		for key1, key2 in (("CSys", "Date"), ("RotType", "RotAngle")):
			if newDict.has_key(key1):
				try:
					del defDict[key2]
				except KeyError:
					pass
		
		# convert scalar data to scalars
		for key in ("CSys", "Date", "RotAngle", "RotType", "Mag", "Px", "Rv", "Distance"):
			try:
				val = newDict[key]
				if RO.SeqUtil.isSequence(val):
					newDict[key] = val[0]
			except KeyError:
				pass

		# merge new dict into default dict
		defDict.update(newDict)
		
		# extract catalog options, if present
		for key in _CatOptionDict:
			if key in defDict:
				self._catOptions[key] = defDict.pop(key)[0]
		
		# check the new dictionary
		self._checkValueDict(defDict)
	
	def _checkValueDict(self, valueDict):
		"""Check valudDict.

		Raise ValueError if valueDict has unknown keys
		or a value would be out of bounds.
		"""
		self._entryErrMsg = None
		self._slewInputWdg.setValueDict(valueDict)
		if self._entryErrMsg:
			raise ValueError(self._entryErrMsg)
	
	def _handleEntryError(self, evt):
		"""Handle entry errors by recording the message."""
		msgStr = evt.widget.getEntryError()
		if msgStr:
			self._entryErrMsg = msgStr

if __name__ == "__main__":
	root = Tkinter.Tk()
	tuiModel = TUI.TUIModel.getModel(True)
	catParser = CatalogParser()
	
	fileName = 'testCat.txt'
	print "Reading file %r" % (fileName,)
	objCat, errList = catParser.parseCat(fileName)
	print "Catalog name = %r, doDisplay = %r, dispColor = %r" % \
		(objCat.name, objCat.getDoDisplay(), objCat.getDispColor())
	print "The catalog contains the following objects:"
	for item in objCat.objList:
		print item
	
	if errList:
		print "The following items could not be parsed:"
		for item in errList:
			print item
