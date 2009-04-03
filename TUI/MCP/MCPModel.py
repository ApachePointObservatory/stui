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
        _theModel = _Model()
    return _theModel

class _Model (actorModel.Model):
    def __init__(self):
        actorModel.Model.__init__(self, "mcp")
