#!/usr/bin/env python
"""TripleSpec keywords that are common to TripleSpec and its guider.

Notes:
- Both tspec and tcamera report environmental data, but they are reporting the identical data,
  so it's redundant to pay attention to those keywords from both ICCs. Thus those keywords are in TSpecModel.


2008-05-14 ROwen
"""
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

class TSpecCommonModel(object):
    def __init__(self, actor):
        tuiModel = TUI.TUIModel.getModel()
        self.actor = actor
        self.slitActor = "tcamera" # presently the guider actor
        self.dispatcher = tuiModel.dispatcher
        self.exposureModeInfoDict = {}

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            converters = str,
            dispatcher = self.dispatcher,
        )
        
        # Detector-Related State
        
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
        
        self.exposureModeInfo = keyVarFact(
            keyword = "exposureModeInfo",
            nval = (3, None),
            description = """Information for one or more exposure modes; for each mode provide:
- name, min samples 1, max samples
Warning: the data is all strings because keywords cannot replicate a set of converters an arbitrary # of times
""",
        )
        self.exposureModeInfo.addCallback(self._updExposureModeInfo, callNow=False)

        self.arrayPower = keyVarFact(
            keyword = "arrayPower",
            converters = RO.CnvUtil.asBoolOrNone,
            description = "state of spectrograph array power",
        )

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

        self.isBSub = keyVarFact(
            keyword = "isBSub",
            converters = RO.CnvUtil.asBool,
            description = "Is background subtraction on or off?",
        )

        self.bsubBase = keyVarFact(
            keyword = "bsubBase",
            nval = (1, None),
            description = "Base filename of image used for background subtraction, possible additional info",
        )

        keyVarFact.setKeysRefreshCmd()
    
    def _updExposureModeInfo(self, expModeInfo, isCurrent, keyVar):
        if None in expModeInfo:
            return
        newExpModeInfoDict = {}
        if len(expModeInfo) % 3 != 0:
            raise RuntimeError("tspec exposureModeInfo not a multiple of 3 values")
        for ii in range(0, len(expModeInfo), 3):
            expModeName = expModeInfo[ii]
            try:
                minNum = int(expModeInfo[ii + 1])
                maxNum = int(expModeInfo[ii + 2])
            except Exception:
                raise RuntimeError("tspec exposureModeInfo=%s invalid; non-numeric range for mode=%s" % (expModeInfo, expModeName))
            newExpModeInfoDict[expModeName] = (minNum, maxNum)
        self.exposureModeInfoDict = newExpModeInfoDict
