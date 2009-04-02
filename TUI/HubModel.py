#!/usr/bin/env python
"""An object that models the current state of the Hub.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

2004-07-22 ROwen
2004-08-25 ROwen    Added users (a new hub keyword) and commented out commanders.
2005-07-08 ROwen    Added httpRoot.
2006-03-30 ROwen    Added user.
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
        actorModel.Model.__init__(self, "hub")
