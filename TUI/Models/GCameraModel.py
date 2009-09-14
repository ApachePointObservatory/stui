#!/usr/bin/env python
"""Model for gcamera actor

2009-09-14 ROwen
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = actorModel.Model("gcamera")
    return _theModel

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("gcamera")
    Model()
