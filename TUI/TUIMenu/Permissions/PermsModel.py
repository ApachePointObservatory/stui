#!/usr/bin/env python
"""A model of the state of the perms actor.

It contains instance variables that are KeyVariables
or sets of KeyVariables. All are directly associated
with status keywords.

History:
2003-12-10 ROwen
2003-12-17 ROwen    Moved KeyVarFactory to RO.KeyVariable.
2004-05-18 ROwen    Eliminated unused testMode argument.
2004-07-22 ROwen    Stopped importing three unused modules.
"""
import RO.KeyVariable
import TUI.TUIModel

_theModel = None

def getModel():
    global _theModel
    if _theModel ==  None:
        _theModel = _Model()
    return _theModel

class _Model(object):
    def __init__(self):
        self.dispatcher = TUI.TUIModel.getModel().dispatcher

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = "perms",
            dispatcher = self.dispatcher,
            refreshCmd = "status",
            nval = (0, None),
            converters = str,
        )
        
    
        self.actors = keyVarFact(
            keyword = "actors",
            description = "Actors controlled by perms",
        )

        self.authList = keyVarFact(
            keyword = "authList",
            nval = (1,None),
            description = "Program and 0 or more authorized actors",
            refreshCmd = None, # no authLists if no programs yet registered
        )

        self.lockedActors = keyVarFact(
            keyword = "lockedActors",
            description = "Actors locked out by APO",
        )

        self.programs = keyVarFact(
            keyword = "programs",
            description = "Programs registered with perms",
        )
