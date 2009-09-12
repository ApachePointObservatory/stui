#!/usr/bin/env python
"""Model for alerts actor

2009-07-21 ROwen
2009-09-11 ROwen    Modified to not use a subclass of actorModel.Model.
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = actorModel.Model("alerts")
    return _theModel

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("alerts")
    Model()
