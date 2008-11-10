#!/usr/bin/env python
"""An object that models the current state of Agile.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

2008-11-10 ROwen    preliminary; does not include support for the filterwheel
"""
__all__ = ["getModel"]
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for fairly fast commands
_TimeLim = 80

_theModel = None

def getModel():
    global _theModel
    if _theModel == None:
        _theModel = _Model()
    return _theModel
        
class _Model (object):
    def __init__(self,
    **kargs):
        tuiModel = TUI.TUIModel.getModel()
        self.actor = "agile"
        self.dispatcher = tuiModel.dispatcher
        self.timelim = _TimeLim
        self.arcsecPerPixel = 0.273

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = 1,
            dispatcher = self.dispatcher,
        )
        
        # Filter
        
#         self.filterNames = keyVarFact(
#             keyword = "filter_names",
#             nval = [1,None],
#             description = "Names of available filters",
#         )
# 
#         self.filter = keyVarFact(
#             keyword = "filter_done",
#             description = "Name of current filter",
#         )
# 
#         self.filterTime  = keyVarFact(
#             keyword = "filter_ttc",
#             converters = RO.CnvUtil.asInt,
#             description = "Expected time to completion of filter move (sec)",
#             allowRefresh = False,
#         )
#         
#         self.filterMoving  = keyVarFact(
#             keyword = "filter_moving",
#             converters = RO.CnvUtil.asBool,
#             description = "True if filter change occurring, False otherwise",
#         )
#         
#         self.filterPos = keyVarFact(
#             keyword = "filter_pos",
#             nval = 3,
#             converters = int,
#             description = "Position of each filter wheel",
#         )

        # Detector
        
        self.detSizeConst = (1024, 1024)
        
        self.bin = keyVarFact(
            keyword="bin",
            nval = 1,
            converters=RO.CnvUtil.asIntOrNone,
            description="bin factor (x=y)",
        )
        
        self.window = keyVarFact(
            keyword="window",
            nval = 4,
            converters=RO.CnvUtil.asIntOrNone,
            description="window (subframe): minX, minY, maxX, maxY (binned pixels; inclusive)",
        )

        self.overscan = keyVarFact(
            keyword="overscan",
            nval = 2,
            converters=RO.CnvUtil.asIntOrNone,
            description="overscan: x, y (binned pixels)",
        )

        self.ccdTemp = keyVarFact(
            keyword = "ccdTemp",
            nval = 2,
            converters = (RO.CnvUtil.asFloatOrNone, str),
            description = "CCD temperature (C) and state summary",
        )
        
        self.ccdSetTemp = keyVarFact(
            keyword = "ccdSetTemp",
            nval = 2,
            converters = (RO.CnvUtil.asFloatOrNone, str),
            description = "CCD temperature setpoint (C) and state summary",
        )
        
        self.ccdTempLimits = keyVarFact(
            keyword = "ccdTempLimits",
            nval = 4,
            converters = RO.CnvUtil.asFloatOrNone,
            description = "CCD temperature error limit: low, high, veryLow, veryHigh",
        )
        
        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()

