#!/usr/bin/env python
"""Keywords returned by tcamera, the TripleSpec Guider.

Notes:
- Keywords used only by the tcam actor are omitted.
- The slit keywords are in TSpecModel even though they are controlled by the TCamera actor.
This is because logically I consider the slit part of the spectrograph, not the guider.

2008-05-14 ROwen
2008-05-15 ROwen    Modified import of TSpecCommonModel to make pychecker a bit happier.
"""
__all__ = ['getModel']

import RO.CnvUtil
import RO.KeyVariable
import TUI.TUIModel
from TUI.Inst.TSpec.TSpecCommonModel import TSpecCommonModel

_model = None

def getModel():
    global _model
    if _model == None:
        _model = Model()
    return _model

class Model (TSpecCommonModel):
    def __init__(self):
        TSpecCommonModel.__init__(self, "tcamera")

        keyVarFact = RO.KeyVariable.KeyVarFactory(
            actor = self.actor,
            dispatcher = self.dispatcher,
            converters = str,
            allowRefresh = True,
        )
        
        keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
    getModel()
