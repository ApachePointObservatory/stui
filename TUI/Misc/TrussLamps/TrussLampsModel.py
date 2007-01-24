#!/usr/bin/env python
"""An object that models the current state of the truss lamps.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

2004-10-01 ROwen
"""
__all__ = ["getModel"]
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for fairly fast commands;
_TimeLim = 60

_theModel = None

def getModel():
    global _theModel
    if _theModel == None:
        _theModel = _Model()
    return _theModel
        
class _Model (object):
    def __init__(self,
    **kargs):
        tuiModel = TUI.TUIModel.getModel()
        self.actor = "tlamps"
        self.dispatcher = tuiModel.dispatcher
        self.timelim = _TimeLim

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = 1,
            dispatcher = self.dispatcher,
        )
        
        self.lampNames = keyVarFact(
            keyword = "lampNames",
            nval = [0, None],
            description = "Lamp names",
        )
        
        self.lampStates = keyVarFact(
            keyword = "lampStates",
            nval = [0,None],
            description = "State of each lamp; one of On, Off, Unknown or Rebooting",
        )

        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
