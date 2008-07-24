#!/usr/bin/env python
"""TripleSpec keywords that are common to TripleSpec and its guider.

The guider model is missing the following information; get them from TSpecModel instead:
- dspFiles, exposureModeInfo and the derived exposureModeInfoDict. They are only reported by TripleSpec.
- Environmental data. Both TripleSpec and its guider do report these keywords,
  but they report identical information so there's no point to listening to both sets.

2008-05-14 ROwen
2008-07-24 ROwen    Fixed PR PR 855: moved dspFiles, exposureModeInfo and exposureModeInfoDict to TSpecModel.
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
        
        self.exposureMode = keyVarFact(
            keyword = "exposureMode",
            converters = (str, RO.CnvUtil.asInt),
            description = "exposure mode",
        )

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
