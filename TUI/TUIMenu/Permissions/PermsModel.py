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
2009-04-01 ROwen    Modified to use opscore.actor.model.
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = _Model()
    return _theModel

class _Model (actorModel.Model):
    def __init__(self):
        actorModel.Model.__init__(self, "perms")
