class IDGen:
	"""generates a sequence of integer ID numbers, wrapping around if desired.
	
	Warning: can be used as an iterator, but there is no stop condition!
	"""
	def __init__(self, startVal=1, wrapVal=None, incr=1):
		"""Inputs:
		- startVal: starting value
		- wrapVal: value at which output wraps around to startVal (not inclusive);
			if None then the ID will change into a long int
			(which has an arbitrary # of digits) when it exceeds sys.maxint
		- incr: increment
		"""
	
		self.startVal = startVal
		self.wrapVal = wrapVal
		self.incr = incr
		self.nextVal = self.startVal
	
	def next(self):
		"""Returns the next ID number."""
		newID = self.nextVal
		self.nextVal += self.incr
		if self.wrapVal != None:
			if  (self.incr > 0 and self.nextVal >= self.wrapVal) or \
				(self.incr < 0 and self.nextVal <= self.wrapVal):
				self.nextVal = self.startVal
		return newID
