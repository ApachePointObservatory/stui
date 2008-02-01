#!/usr/bin/env python
"""Model for gmech: the mechanical controller for the NA2 guider.

2008-01-25 ROwen
"""
__all__ = ['getModel']

import RO.CnvUtil
import RO.KeyVariable
import TUI.TUIModel

_model = None

def getModel():
    global _model
    if _model == None:
        _model = Model()
    return _model

class Model (object):
    def __init__(self):
        self.actor = "gmech"
        self.tuiModel = TUI.TUIModel.getModel()

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = "gmech",
            dispatcher = self.tuiModel.dispatcher,
            converters = str,
            allowRefresh = True,
        )

        # configuration parameters (these rarely change)
        
        self.filterNames = keyVarFact(
            keyword = "filterNames",
            nval = [1, None],
            description = "List of filter names, in order (filter number = index + 1)",
        )

        self.maxFilter = keyVarFact(
            keyword = "maxFilter",
            converters = RO.CnvUtil.asInt,
            description = "Maximum filter number (microns)",
        )

        self.maxPiston = keyVarFact(
            keyword = "maxPiston",
            converters = RO.CnvUtil.asInt,
            description = "Maximum piston (microns)",
        )

        self.minFilter = keyVarFact(
            keyword = "minFilter",
            converters = RO.CnvUtil.asInt,
            description = "Minimum filter number (microns)",
        )

        self.minPiston = keyVarFact(
            keyword = "minPiston",
            converters = RO.CnvUtil.asInt,
            description = "Minimum piston (microns)",
        )

        # state (these can change frequently)
                
        self.desFilter = keyVarFact(
            keyword = "desFilter",
            converters = RO.CnvUtil.asInt,
            description = "Desired filter number (microns)",
        )

        self.desFocus = keyVarFact(
            keyword = "desFocus",
            converters = RO.CnvUtil.asInt,
            description = "Desired focus (microns)",
        )

        self.desPiston = keyVarFact(
            keyword = "desPiston",
            converters = RO.CnvUtil.asInt,
            description = "Desired piston (microns)",
        )

        self.filter = keyVarFact(
            keyword = "filter",
            converters = RO.CnvUtil.asInt,
            description = "Filter number",
        )

        self.focus = keyVarFact(
            keyword = "focus",
            converters = RO.CnvUtil.asFloat,
            description = "Piston (microns)",
        )
    
        self.piston = keyVarFact(
            keyword = "piston",
            converters = RO.CnvUtil.asFloat,
            description = "Piston (microns)",
        )

        self.filterStatus = keyVarFact(
            keyword = "filterStatus",
            converters = RO.CnvUtil.asInt,
            description = "Filter status word",
        )
        
        self.pistonStatus = keyVarFact(
            keyword = "pistonStatus",
            converters = RO.CnvUtil.asInt,
            description = "Piston status word",
        )

        self.filterMoveTime = keyVarFact(
            keyword = "filterMoveTime",
            converters = (RO.CnvUtil.asFloat, RO.CnvUtil.asFloat),
            description = "Elapsed time and predicted total duration of filter move (sec)",
            allowRefresh=False,
        )

        self.pistonMoveTime = keyVarFact(
            keyword = "pistonMoveTime",
            converters = (RO.CnvUtil.asFloat, RO.CnvUtil.asFloat),
            description = "Elapsed time and predicted total duration of piston move (sec)",
            allowRefresh=False,
        )
        
        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
