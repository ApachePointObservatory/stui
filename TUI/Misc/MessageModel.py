#!/usr/bin/env python
"""Model for instant messaging actor

History:
2009-04-01 ROwen
"""
__all__ = ["Model"]

import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = actorModel.Model("msg")
    return _theModel
