#!/usr/bin/env python
"""An object that models the current state of TripleSpec.

2008-02-22 ROwen    First cut based on 2008-02-21 command dictionary and 2008-02-22 feedback.
"""
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel


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
        self.actor = "tspec"
        self.dispatcher = tuiModel.dispatcher

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            nval = 1,
            dispatcher = self.dispatcher,
        )
        
        # Spectrograph State
        
        self.dspLoad = keyVarFact(
            keyword = "dspLoad",
            description = "name of the DSP timing file that is loaded",
        )
        
        self.dspFiles = keyVarFact(
            keyword = "dspFiles",
            nval = (0, None),
            description = "names of DSP timing files that may be loaded",
        )
        
        self.exposureMode = keyVarFact(
            keyword = "exposureMode",
            converters = (str, RO.CnvUtil.asInt),
            description = "exposure mode",
        )
        
        # likely to be renamed
        self.exposureModes = keyVarFact(
            keyword = "exposureModes",
            converters = (str, RO.CnvUtil.asInt, RO.CnvUtil.asInt),
            description = "exposure mode limits: exposure mode, min samples, max samples",
        )

        self.arrayPower = keyVarFact(
            keyword = "arrayPower",
            converters = RO.CnvUtil.asBool,
            description = "state of spectrograph array power",
        )

        # Spectrograph Exposures
        
        # perhaps a new state "failed" will be added
        self.exposureState = keyVarFact(
            keyword = "exposureState",
            converters = (str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asFloatOrNone),
            description = """exposure state; the fields are:
- state: one of: reading, integrating, processing, done or aborted
- estTime: estimated total duration of this state (sec)
- remTime: estimated remaining time in this state (sec)
if exposureState is returned as done, and the command failed, the response will be preceeded by
an informational response with the error message associated with the failure.""",
        )

        # Spectrograph Tip-Tilt
        
        self.ttMode = keyVarFact(
            keyword = "ttMode",
            description = "tip-tilt controller mode: one of offline, openLoop, closedLoop",
        )
        
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
        
        # I hope this will get changed to separate upper/lower limits
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
