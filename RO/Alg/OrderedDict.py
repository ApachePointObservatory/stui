"""An OrderedDict is a dictionary in which the order of adding items is preserved.
Replacing an existing item replaces it at its current location.

Works by maintaining a list of keys in order, in addition to a regular dictionary.
Hence retrieval should occur at full speed, but an OrderedDict uses more memory
than a regular dictionary and insertion and deletion are a bit slower,

Requires Python 2.2 or later.

For an alternative implementation of an ordered dictionary,
see RBTree <http://newcenturycomputers.net/projects/rbtree.html>
(thanks to Laura Creighton for the reference).

History:
2002-02-01 ROwen	First release.
2002-02-04 ROwen	Added code for iterkeys, itervalues and iteritems 
	(as I feared I would have to do, but my limited tests suggested otherwise).
	Thanks to Jason Orendorff for insisting and for supplying the nice code
	for itervalues and iteritems. Also added __str__ and copy methods,
	allowed the constructor to make copies and improved the self tests.
2002-02-05 ROwen	Keys now returns a copy of the keys instead of the internal list.
	Added the remaining missing methods: popitem, setdefault and update.
	Made all iterators explicitly depend on self.iterkeys(), reducing dependency
	on internals and so making it easier to subclass OrderedDict.
2003-08-05 ROwen	Modified to accept a sequence as an initializer (like normal dict).
2004-03-25 ROwen	Added sort method to OrderedDict.
"""
from __future__ import generators
import string

class OrderedDict (dict):
	"""A dictionary in which the order of adding items is preserved.
	Replacing an existing item replaces it at its current location.

	Inputs:
	- seqOrDict: a sequence of (key, value) tuples or a dictionary
	Warning: if the supplied dictionary is not an OrderedDict
	then the resulting keys will not be in order
	"""
	def __init__(self, seqOrDict=None):
		dict.__init__(self)
		self.__keyList = []
		if seqOrDict == None:
			return
		elif hasattr(seqOrDict, "iteritems"):
			for key, val in seqOrDict.iteritems():
				self[key] = val
		else:
			for key, val in seqOrDict:
				self[key] = val
	
 	def __delitem__(self, key):
 		dict.__delitem__(self, key)
 		self.__keyList.remove(key)
 	
	def __iter__(self):
 		return self.iterkeys()
 	
 	def __repr__(self):
 		return '{'+ string.join(["%r: %r" % item for item in self.iteritems()], ', ')+'}'
 	
	def __setitem__(self, key, value):
		if not self.has_key(key):
			self.__keyList.append(key)
		dict.__setitem__(self, key, value)
	
 	def clear(self):
 		self.__keyList = []
 		dict.clear(self)
 		
 	def copy(self):
 		return OrderedDict(self)
 		
 	def iterkeys(self):
 		return iter(self.__keyList)
 	
 	def itervalues(self):
 		for key in self.iterkeys():
 			yield self[key]
 	
 	def iteritems(self):
 		for key in self.iterkeys():
 			yield (key, self[key])
 	
  	def keys(self):
 		return self.__keyList[:]
 	
 	def popitem(self, i=-1):
 		"""Remove the ith item from the dictionary (the last item if i is omitted)
 		and returns (key, value). This emulates list.pop() instead of dict.popitem(),
 		since ordered dictionaries have a defined order.
 		"""
 		key = self.__keyList[i]
 		item = (key, self[key])
 		self.__delitem__(key)
 		return item
 	
 	def setdefault(self, key, value):
 		if key not in self:
 			self[key] = value
 		return self[key]
 	
 	def sort(self, cmpFunc=None):
 		"""Sort the keys.
 		"""
 		self.__keyList.sort(cmpFunc)
 	
 	def update(self, aDict):
 		"""Add all items from dictionary aDict to self (in order if aDict is an ordered dictionary).
 		"""
 		for key, value in aDict.iteritems():
 			self[key] = value
 
 	def values(self):
  		return [self[key] for key in self.iterkeys()]
 	
 	def checkIntegrity(self):
 		"""Perform an internal consistency check and raise an AssertionError if anything is wrong.
 		
 		In principal a bug could lead to the system getting out of synch, hence this method.
		"""
 		assert len(self) == len(self.__keyList), \
			"length of dict %r != length of key list %r" % (len(self), len(self.__keyList))
 		for key in self.iterkeys():
 			assert self.has_key(key), \
 				"key %r in key list missing from dictionary" % (key,)

if __name__ == "__main__":
	print "testing OrderedDict"
	import copy
	import random
	
	# basic setup
	showOutput = 0	# display results or just complain if failure?
	nItems = 10	# length of dictionary to test
	nToDelete = 2	# number of items to delete
	nToReplace = 5	# number of items to replace
	
	assert (nToDelete > 0)
	assert (nToReplace > 0)
	assert (nItems >= nToDelete + nToReplace)

	def testDict(desKeys, desValues, theDict):
		"""Test an ordered dictionary, given the expected keys and values (in order)"""
		actKeys = theDict.keys()
		assert desKeys == actKeys, "keys() failed; keys %r != %r" % (desKeys, actKeys)
		
		actValues = theDict.values()
		assert desValues == actValues, "values() failed; values %r != %r" % (desValues, actValues)
		
		assert len(theDict) == len(desKeys), "len() failed: %r != %r" % (len(desKeys), len(theDict))
	
		# verify that iteration works:
		actKeys = [key for key in theDict]
		assert desKeys == actKeys, "__iter__() failed; keys %r != %r" % (desKeys, actKeys)
	
		actValues = [v for v in theDict.itervalues()]
		assert desValues == actValues, "itervalues() failed; values %r != %r" % (desValues, actValues)
		
		desKeyValues = map(lambda key, v: (key, v), desKeys, desValues)
		actKeyValues = [kv for kv in theDict.iteritems()]
		assert desKeyValues == actKeyValues, "iteritems() failed; values %r != %r" % (desKeyValues, actKeyValues)
	
		theDict.checkIntegrity()	

	
	def keyToValue(key):
		return "val[%r]" % (key,)
		
	def altKeyToValue(key):
		return "alt[%r]" % (key,)

	oDict = OrderedDict()

	# start with a simple dictionary with no repeating keys
	inKeys = [x for x in range(0, nItems)]
	random.shuffle(inKeys)
	inValues = [keyToValue(key) for key in inKeys]
	for key in inKeys:
		oDict[key] = keyToValue(key)
	if showOutput:
		print "initial dictionary: %r" % (oDict)
	testDict(inKeys, inValues, oDict)

	# now delete some items
	for ii in range(nToDelete):
		delKey = random.choice(inKeys)
		inKeys.remove(delKey)
		del(oDict[delKey])
	inValues = [keyToValue(key) for key in inKeys]
	if showOutput:
		print "after %r items removed: %r" % (nToDelete, oDict)
	testDict(inKeys, inValues, oDict)

	# now replace some items; use new values so you can tell the difference
	replaceKeys = copy.deepcopy(inKeys)
	random.shuffle(replaceKeys)
	replaceKeys = replaceKeys[0:nToReplace]
	for key in replaceKeys:
		ind = inKeys.index(key)
		inValues[ind] = altKeyToValue(key)
		oDict[key] = altKeyToValue(key)
	testDict(inKeys, inValues, oDict)
	if showOutput:
		print "after replacing %r items: %r" % (nToReplace, oDict)
	
	# test copying
	dictCopy = oDict.copy()
	assert dictCopy.keys() == oDict.keys(), "copy failed; keys %r != %r" % (dictCopy.keys(), testDict.keys())
	
	testKey = dictCopy.keys()[0]
	dictCopy[testKey] = "changed value"
	assert dictCopy.values() != oDict.values(), "copy failed; changing a value in one affected the other"
	
	# add a new item to dictCopy and make sure the integrity of both are preserved
	# (verifies that the __keyList lists in each dictionary are separate entities)
	dictCopy[()] = "value for ()"
	dictCopy.checkIntegrity()
	oDict.checkIntegrity()
