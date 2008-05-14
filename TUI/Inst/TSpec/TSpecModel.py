#!/usr/bin/env python
"""An object that models the current state TripleSpec.

Notes:
- ExposureModeInfo cannot be fully parsed due to limitations in KeyVariable
  so it is parsed locally and used to set exposureModeInfoDict.
- The slit keywords are in this model even though they are controlled by the TCamera actor.
  This is because logically I consider the slit part of the spectrograph, not the guider.


2008-02-22 ROwen    First cut based on 2008-02-21 command dictionary and 2008-02-22 feedback.
2008-02-22 ROwen    Added slit keywords.
2008-04-21 ROwen    Changed converter for arrayPower from asBool to asBoolOrNone
2008-04-24 ROwen    Removed unused exception object in except statement.
2008-05-14 ROwen    Moved keywords that are common between TSPec and its guider to TSpecCommonModel.
"""
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TSpecCommonModel

_theModel = None

def getModel():
    global _theModel
    if _theModel == None:
        _theModel = _Model()
    return _theModel


class _Model(TSpecCommonModel.TSpecCommonModel):
    def __init__(self,
    **kargs):
        TSpecCommonModel.TSpecCommonModel.__init__(self, "tspec")
        self.slitActor = "tcamera" # presently the guider actor

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            dispatcher = self.dispatcher,
        )
        
        # Slit keywords
        # Warning: the slit is controlled by tcamera (the TripleSpec guider), not tspec!
        
        self.slitPosition = keyVarFact(
            actor = self.slitActor,
            keyword = "slitPosition",
            description = "slit position (as a name)",
        )
        
        self.slitState = keyVarFact(
            actor = self.slitActor,
            keyword = "slitState",
            converters = (str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asFloatOrNone),
            description = """slit state; the fields are:
- state: one of: moving, done
- estTime: estimated total duration of this state (sec)
- remTime: estimated remaining time in this state (sec)
In the case of command failure the terminating command response will be followed by a slitPosition message
defined in setSlit, giving a best guess as to the current position of the slit substrate.
A slitPosition message following a normal command termination indicates the current slit position..""",
        )
        
        self.slitPositions = keyVarFact(
            actor = self.slitActor,
            nval = (0, None),
            keyword = "slitPositions",
            description = "list of allowed slit positions: Slit1, Block1, Slit2, Block2, Slit3, Block3, Slit4, Block4",
        )

        # Spectrograph Tip-Tilt
        
        self.ttMode = keyVarFact(
            keyword = "ttMode",
            description = "tip-tilt controller mode: one of offline, openLoop, closedLoop",
        )
        
        self.ttModeNamesConst = ("Offline", "OpenLoop", "ClosedLoop")
        
        self.ttPosition = keyVarFact(
            keyword = "ttPosition",
            nval = 4,
            converters = RO.CnvUtil.asFloatOrNone,
            description = "tip-tilt position: actual x, y; commanded x, y",
        )
        
        self.ttLimits = keyVarFact(
            keyword = "ttLimits",
            nval = 4,
            converters = RO.CnvUtil.asFloat,
            description = "tip-tilt limits: min x, y; max x, y",
        )

        # Temperature monitoring
        
        self.tempNames = keyVarFact(
            keyword = "tempNames",
            nval = (0, None),
            description = "temperature sensor names",
        )
        
        self.temps = keyVarFact(
            keyword = "temps",
            nval = (0, None),
            converters = RO.CnvUtil.asFloat,
            description = "temperatures",
        )
        
        self.tempMin = keyVarFact(
            keyword = "tempMin",
            nval = (0, None),
            converters = RO.CnvUtil.asFloat,
            description = "suggested minimum temperature for graphs",
        )
        
        self.tempMax = keyVarFact(
            keyword = "tempMax",
            nval = (0, None),
            converters = RO.CnvUtil.asFloatOrNone,
            description = "suggested maximum temperature for graphs",
        )
        
        self.tempAlarms = keyVarFact(
            keyword = "tempAlarms",
            nval = (0, None),
            converters = RO.CnvUtil.asBool,
            description = "is temperature bad?",
        )
        
        self.tempThresholds = keyVarFact(
            keyword = "tempThresholds",
            nval = (0, None),
            converters = RO.CnvUtil.asFloatOrNone,
            description = "temperature threshold; if pos/neg then temp >/< thresh is bad",
        )
        
        self.tempInterval = keyVarFact(
            keyword = "tempInterval",
            converters = RO.CnvUtil.asFloat,
            description = "reporting interval for temperatures (sec); 0.0 if none",
        )
        
        # Vacuum monitoring

        self.vacuum = keyVarFact(
            keyword = "vacuum",
            converters = RO.CnvUtil.asFloatOrNone,
            description = "vacuum, in torr",
        )
        
        self.vacuumAlarm = keyVarFact(
            keyword = "vacuumAlarm",
            converters = RO.CnvUtil.asBool,
            description = "is vacuum bad?",
        )
        
        self.vacuumThreshold = keyVarFact(
            keyword = "vacuumThreshold",
            converters = RO.CnvUtil.asFloat,
            description = "maximum good vacuum, in torr",
        )
        
        self.vacuumLimits = keyVarFact(
            keyword = "vacuumLimits",
            nval = 2,
            converters = RO.CnvUtil.asFloat,
            description = "suggested minimum and maximum vacuum for graphs, in torr",
        )
        
        self.vacuumInterval = keyVarFact(
            keyword = "vacuumInterval",
            converters = RO.CnvUtil.asFloat,
            description = "reporting interval for vacuum (sec); 0.0 if none",
        )

        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
