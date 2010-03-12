#!/usr/bin/env python
"""Model for BOSS ICC

2009-09-11 ROwen
2010-03-11 ROwen    Deprecated
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel
import warnings

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        warnings.warn("Use TUI.Models.getModel(\"boss\") instead", DeprecationWarning)
        _theModel = actorModel.Model("boss")
    return _theModel

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("boss")
    Model()
