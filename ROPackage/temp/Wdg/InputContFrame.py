#!/usr/bin/env python
"""

History:
2002-11-15 ROwen    Broken out of RO.InputCont to improve the architecture.
2003-03-12 ROwen    Added getStringList; changed 1/0 to True/False.
2003-07-10 ROwen    Uses self.inputCont instead of self.inputContSet.
2003-10-20 ROwen    Bug fixes: getDefValueDict and getValueDict both had
                    extra args left over from an older InputCont.
2004-05-18 ROwen    Stopped importing string, sys and types since they weren't used.
2004-08-11 ROwen    Define __all__ to restrict import.
2004-12-13 ROwen    Added removeCallback; added addCallback arg. callNow.
"""
__all__ = ['InputContFrame']

import Tkinter

class InputContFrame(Tkinter.Frame):
    """A convenience class for widgets containing an RO.InputCont container class.
    You must store the container list in instance variable self.inputCont and all the
    important calls automatically work.
    
    This is a substitute for inheritance; it is less robust with regards to
    changes in InputCont, but avoids cluttering up your class with attributes.
    """
    def __init__(self, master, **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)
    
    def addCallback(self, callFunc, callNow=False):
        return self.inputCont.addCallback(callFunc, callNow = callNow)
    
    def allEnabled(self):
        return self.inputCont.allEnabled()

    def clear(self):
        return self.inputCont.clear()
    
    def getDefValueDict(self):
        return self.inputCont.getDefValueDict()
    
    def getValueDict(self):
        return self.inputCont.getValueDict()
    
    def getString(self):
        return self.inputCont.getString()

    def getStringList(self):
        return self.inputCont.getStringList()
    
    def removeCallback(self, callFunc, doRaise=True):
        return self.inputCont.removeCallback(callFunc, doRaise = doRaise)

    def restoreDefault(self):
        return self.inputCont.restoreDefault()
    
    def setEnable(self, doEnable):
        return self.inputCont.setEnable(doEnable)
    
    def setValueDict(self, valDict):
        return self.inputCont.setValueDict(valDict)
