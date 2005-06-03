"""A ListPlus adds a few methods to a standard list
to make it more consistent with dict.

History:
2003-03-13 ROwen	First release
2005-06-03 ROwen	Fixed indentation quirks (needless spaces before tabs)
"""
from __future__ import generators

class ListPlus (list):
	def get(self, key, defValue = None):
		try:
			return self[key]
		except (LookupError, TypeError):
			return defValue
	
	def has_key(self, key):
		try:
			self[key]
			return True
		except (LookupError, TypeError):
			return False
	
	def iteritems(self):
		for key in self.iterkeys():
			yield (key, self[key])

	def iterkeys(self):
		return iter(xrange(len(self)))

	def itervalues(self):
		return iter(self)

	def keys(self):
		return range(len(self))
	
	def values(self):
		return self[:]
