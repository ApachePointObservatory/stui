#!/usr/local/bin/python
"""

History:
2002-11-15 ROwen	Broken out of RO.InputCont to improve the architecture.
2003-03-12 ROwen	Added getStringList; changed 1/0 to True/False.
2003-07-10 ROwen	Uses self.inputCont instead of self.inputContSet.
2003-10-20 ROwen	Bug fixes: getDefValueDict and getValueDict both had
					extra args left over from an older InputCont.
2004-05-18 ROwen	Stopped importing string, sys and types since they weren't used.
2004-08-11 ROwen	Define __all__ to restrict import.
"""
__all__ = ['InputContFrame']

import Tkinter

class InputContFrame(Tkinter.Frame):
	"""A convenience class for widgets containing a set of RO.InputCont widgets, i.e. an RO.InputCont.Set.
	You must store the set in instance variable self.inputCont and all the
	important calls automatically work.
	
	Basically this is a cheesy form of multiple inheritance, as InputCont.Set has so many
	methods that I'm reluctant to just inherit them directly.
	"""
	def __init__(self, master, **kargs):
		Tkinter.Frame.__init__(self, master, **kargs)
	
	def addCallback(self, callFunc):
		return self.inputCont.addCallback(callFunc)
	
	def allEnabled(self):
		return self.inputCont.allEnabled()

	def clear(self):
		return self.inputCont.clear()
		
	def doEnable(self, doEnable):
		return self.inputCont.doEnable(doEnable)
	
	def getDefValueDict(self):
		return self.inputCont.getDefValueDict()
	
	def getValueDict(self):
		return self.inputCont.getValueDict()
	
	def getString(self):
		return self.inputCont.getString()

	def getStringList(self):
		return self.inputCont.getStringList()

	def restoreDefault(self):
		return self.inputCont.restoreDefault()
	
	def setValueDict(self, valDict):
		return self.inputCont.setValueDict(valDict)
