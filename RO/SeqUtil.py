#!/usr/local/bin/python
"""Sequence utilities by Russell Owen

History:
2003-11-18 ROwen	Extracted from MathUtil and added oneOrNAsSeq
2004-05-18 ROwen	Bug fix: flatten was called flattenList in a few places.
2005-06-07 ROwen	Added isString.
"""
import UserString
import RO.MathUtil

def asList(item):
	"""Converts one or more items to a list, returning a copy.
	If item is a non-string-like sequence, returns list(item),
	else returns [item].
	Note: the returned value is a copy, even if item is already a list.
	"""
	if isSequence(item):
		return list(item)
	else:
		return [item]

def asSequence(item):
	"""Converts one or more items to a sequence,
	If item is already a non-string-like sequence, returns it unchanged,
	else returns [item].
	"""
	if isSequence(item):
		return item
	else:
		return [item]

def flatten(a):
	"""Flattens a sequence of sequences.
	"""
	ret = []
	for ai in a:
		if isSequence(ai):
			ret += flatten(ai)
		else:
			ret.append(ai)
	return ret

def isSequence(item):
	"""Return True if the input is a non-string sequence,
	False otherwise. See isString for a definition of string.
	"""
	try:
		item[0:0]
	except (AttributeError, TypeError):
		return False
	return not isString(item)

def isString(item):
	"""Return True if the input is a string-like sequence.
	Strings include str, unicode and UserString objects.
	
	From Python Cookbook, 2nd ed.
	"""
	return isinstance(item, (basestring, UserString.UserString))

def oneOrNAsList (
	oneOrNVal,
	n,
	valDescr = None,
):
	"""Converts a variable that may be a single item
	or a non-string sequence of n items to a list of n items,
	returning a copy.

	Raises ValueError if the input is a sequence of the wrong length.
	
	Inputs:
	- oneOrNVal one value or sequence of values
	- n	desired number of values
	- valDescr	string briefly describing the values
		(used to report length error)
	"""
	if isSequence(oneOrNVal):
		if len(oneOrNVal) != n:
			valDescr = valDescr or "oneOrNVal"
			raise ValueError("%s has length %d but should be length %d" % (valDescr, len(oneOrNVal), n))
		return list(oneOrNVal)
	else:
		return [oneOrNVal]*n

def removeDups(aSeq):
	"""Remove duplicate entries from a sequence,
	returning the results as a list.
	Preserves the ordering of retained elements.
	"""
	tempDict = {}
	def isUnique(val):
		if val in tempDict:
			return False
		tempDict[val] = None
		return True
	
	return [val  for val in aSeq if isUnique(val)]

def matchSequences(a, b, rtol=1.0e-5, atol=RO.SysConst.FAccuracy):
	"""Compares sequences a and b element by element,
	returning a list of indices for non-matching value pairs.
	The test for matching is compareFloats
	
	This is essentially the same as Numeric.allclose,
	but returns a bit more information.
	"""
	return [ind for ind in range(len(a))
		if RO.MathUtil.compareFloats(a[ind], b[ind], rtol, atol) != 0]


if __name__ == '__main__':
	print "testing isSequence"
	u = u'unicode string'
	assert(not isSequence(u))
	s = 'regular string'
	assert(not isSequence(s))
	l = []
	assert(isSequence(l))
	t = ()
	assert(isSequence(t))

	print "testing flatten"
	f = (((),("abc",)), u"abc", ["a", "b", "c"])
	assert(flatten(f) == ["abc", u"abc", "a", "b", "c"])

	print "OK"
