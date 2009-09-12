#!/usr/bin/env python
"""Model for BOSS ICC

2009-09-11 ROwen
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = actorModel.Model("boss")
    return _theModel

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("boss")
    Model()
