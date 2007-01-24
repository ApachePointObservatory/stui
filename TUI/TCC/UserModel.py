#!/usr/bin/env python
"""An object that models the user's target position.

2003-04-14 ROwen    Preliminary version.
2003-04-28 ROwen    Added rotType
2003-10-29 ROwen    Added potentialTarget, objCatalog;
                    added class _ObjVar;
                    modified class _TkVar to use RO.AddCallback.TkVarMixin.
2003-11-07 ROwen    Modified _TkVar to not create a StringVar unless it'll be used.
2004-03-03 ROwen    Changed userCat to userCatDict, a dictionary of catalogs.
2004-07-21 ROwen    Modified for updated RO.AddCallback.
"""
import Tkinter
import RO.AddCallback

_theModel = None

def getModel():
    global _theModel
    if _theModel ==  None:
        _theModel = _Model()
    return _theModel
        
class _Model (object):
    def __init__(self,
    **kargs):
        self.coordSysName = _TkVar()
        self.coordSysName.getVar().set("ICRS")
        
        self.coordSysDate = _TkVar()
        
        self.rotType = _TkVar()
        self.rotType.getVar().set("Object")
        
        # where the telescope will slew if the Slew button is pressed
        self.potentialTarget = _ObjVar()

        # a dictionary of user catalogs; each entry is
        # catalog name:TUI.TCC.TelTarget.Catalog
        self.userCatDict = _ObjVar({})

class _ObjVar(RO.AddCallback.BaseMixin):
    """A container for an arbitrary object.
    
    Inputs:
    - obj: the initial object, if any
    - callFunc: a function that is called when set is called;
        the function receives one argument: obj
    - callNow: if True, calls the function immediately
    """
    def __init__(self,
        obj = None,
        callFunc = None,
        callNow = False,
    ):
        RO.AddCallback.BaseMixin.__init__(self)
        self._obj = obj
        if callFunc:
            self.addCallback(callFunc, callNow)
    
    def _doCallbacks(self):
        self._basicDoCallbacks(self._obj)
    
    def get(self):
        return self._obj
    
    def set(self, newObj):
        self._obj = newObj
        self._doCallbacks()

class _TkVar(RO.AddCallback.TkVarMixin):
    """A container for a Tkinter Variable;
    basically provides a slightly nicer interface
    (since they already support callbacks).
    """
    def __init__(self,
        var=None,
        callFunc = None,
        callNow = False,
    ):
        if var == None:
            var = Tkinter.StringVar()       
        RO.AddCallback.TkVarMixin.__init__(self, var, callFunc, callNow)
    
    def _doCallbacks(self, *args):
        val = self._var.get()
        self._basicDoCallbacks(val)

    def getVar(self):
        return self._var

    def get(self):
        return self._var.get()
    
    def set(self, val):
        self._var.set(val)


if __name__ ==  "__main__":
    model = getModel()
