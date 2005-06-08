"""Generate a series of ID numbers.

Note: this would be a bit simpler as a generator instead of a class,
but then the input values would not be validity-tested
until the first call to next().

History:
2005-06-08 ROwen	Added error checking for inconsistent inputs.
					Added method __repr__.
					Changed to a new style class.
					
"""
class IDGen(object):
	"""generate a sequence of integer ID numbers, wrapping around if desired.
	
	Warning: can be used as an iterator, but there is no stop condition!
	"""
	def __init__(self, startVal=1, wrapVal=None, incr=1):
		"""Inputs:
		- startVal: starting value
		- wrapVal: value at which output wraps around to startVal; exclusive
			(meaning next() will never return wrapVal).
			if None then the ID will change into a long int
			(which has an arbitrary # of digits) when it exceeds sys.maxint
		- incr: increment
		"""
		self.startVal = startVal
		self.wrapVal = wrapVal
		self.incr = incr
		self.ind = 0
		if wrapVal != None:
			self.nSteps = (wrapVal - startVal) // incr
			if self.nSteps < 1:
				raise ValueError("no id numbers in range %s:%s:%s" % (startVal, wrapVal, incr))
	
	def next(self):
		"""Return the next ID number."""
		newID = self.startVal + (self.ind * self.incr)
		self.ind += 1
		if self.wrapVal != None:
			self.ind %= self.nSteps
		return newID
	
	def __repr__(self):
		return "IDGen(startVal=%s, wrapVal=%s, incr=%s)" % (self.startVal, self.wrapVal, self.incr)
