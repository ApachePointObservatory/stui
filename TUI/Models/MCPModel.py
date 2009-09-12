#!/usr/bin/env python
"""Model for MCP non-axis-controller output

Includes calibration lamps and flat field screens

2009-04-02 ROwen
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = actorModel.Model("mcp")
    return _theModel

if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp")
    Model()
