#!/usr/bin/env python
"""An object that models the current state of the MCP.

2013-08-23 ROwen    Added apogeeGangLabelDict in lieu of figure out how to access labelHelp from an opscore Key
2014-12-18 ROwen    Reemoved unused import.
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
       actorModel.Model.__init__(self, "mcp")
       self.apogeeGangLabelDict = {
            "0": "Unknown",
            "1": "Disconnected",
            "2": "At Cart",
            "4": "Podium: ?",
           "12": "Podium: Dense",
           "17": "Disconnected w FPI",
           "18": "FPS w FPI",
           "20": "Podium: Sparse",
           "28": "Podium: Dense FPI",
           "36": "Podium: 1M",
           "52": "Podium: 1M FPI",
       }
