"""
History:
2003-10-23 ROwen	Renamed from GetByPrefix and enhanced.
2005-06-08 ROwen	Changed MatchList to a new style class.
"""
class MatchList(object):
	"""Find matches for a string in a list of strings,
	optionally allowing abbreviations and ignoring case.
	
	Inputs:
	- valueList: a list of values; non-string entries are ignored
	- abbrevOK: allow abbreviations?
	- ignoreCase: ignore case?
	"""
	def __init__(self,
		valueList = (),
		abbrevOK = True,
		ignoreCase = True,
	):
		self.abbrevOK = bool(abbrevOK)
		self.ignoreCase = bool(ignoreCase)
		if self.abbrevOK:
			self.strMatchMethhod = str.startswith
		else:
			self.strMatchMethhod = str.__eq__
		
		self.setList(valueList)

	def getAllMatches(self, prefix):
		"""Return all matches
		"""
		if self.ignoreCase:
			prefix = prefix.lower()
		return [valItem[-1] for valItem in self.valueList
			if self.strMatchMethhod(valItem[0], prefix)
		]		

	def getUniqueMatch(self, prefix):
		"""If there is a unique match, return it, else raise ValueError.
		"""
		matchList = self.getAllMatches(prefix)
		if len(matchList) == 1:
			return matchList[0]
		else:
			errList = [val[-1] for val in self.valueList]
			if matchList:
				raise ValueError, "too many matches for %r in %r" % (prefix, errList)
			else:
				raise ValueError, "no matches for %r in %r" % (prefix, errList)
	
	def matchKeys(self, fromDict):
		"""Returns a copy of fromDict with keys replaced by their unique match.
		
		If any key does not have a unique match in the list, raises ValueError.
		If more than one key in fromDict has the same match, raises ValueError
		"""
		toDict = {}
		for fromKey, val in fromDict.iteritems():
			toKey = self.getUniqueMatch(fromKey)
			if toDict.has_key(toKey):
				raise ValueError, "%r contains multiple keys that match %s" % (fromDict, toKey,)
			toDict[toKey] = val
		return toDict
	
	def setList(self, valueList):
		"""Set the list of values to match.
		Non-string items are silently ignored.
		"""
		if self.ignoreCase:
			self.valueList = [
				(val.lower(), val) for val in valueList if hasattr(val, "lower")
			]
		else:
			self.valueList = [
				(val,) for val in valueList if hasattr(val, "lower")
			]
