#!/usr/bin/env python
"""Get a model for an actor

Warnings:
- You must get the tui model before getting any other model.
- To obtain a tui model in debug mode, use TUI.Models.TUIModel.Model(True)
  instead of getModel("tui")

2010-03-11 ROwen
2010-05-21 ROwen    Minor tweak to the way opscore.actor.model is imported
"""
__all__ = ["getModel"]

import opscore.actor.model
import HubModel
import TCCModel
import TUIModel

_modelDict = dict()
_specialModelDict = {
    "hub": HubModel,
    "tcc": TCCModel,
    "tui": TUIModel,
}

def getModel(actor):
    global _modelDict
    actor = actor.lower()
    model = _modelDict.get(actor)
    if model:
        return model

    specialModule = _specialModelDict.get(actor)
    if specialModule:
        model = specialModule.Model()
    else:
        model = opscore.actor.model.Model(actor)
    _modelDict[actor] = model
    return _modelDict[actor]
