#!/usr/bin/env python
"""Model for alerts actor

2009-07-21 ROwen
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
        actorModel.Model.__init__(self, "alerts")

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("alerts")
    Model()
