#!/usr/bin/env python
"""Model for guider actor

2009-09-11 ROwen
2010-03-11 ROwen    Deprecated.
2010-08-25 ROwen    Un-deprecated. Added fullGProbeBits field to combine gprobes with gprobeBits,
                    as a workaround until the guider does this itself and gprobes can be ignored.
"""
__all__ = ["Model"]

import re
import opscore.protocols.keys as protoKeys
import opscore.protocols.types as protoTypes
import opscore.actor.keyvar as actorKeyvar
import opscore.actor.model as actorModel

_theModel = None

def Model():
    global _theModel
    if not _theModel:
        _theModel = _Model()
    return _theModel

GProbesRE = re.compile(r"\((\d)+=(True|False)\)")
GProbeDisableBitVal = 4

class _Model (actorModel.Model):
    def __init__(self):
        actorModel.Model.__init__(self, "guider")
        
        # synthetic keywords
        self.fullGProbeBits = actorKeyvar.KeyVar(
            self.actor,
            protoKeys.Key("fullGProbeBits",
                protoTypes.Bits("broken", "unused", "disabled", help="Guide probe bits")*(0,),
                descr="Guide probe bits, including disabled")
        )

        self.gprobeBits.addCallback(self._updFullGProbeBits)
        self.gprobes.addCallback(self._updFullGProbeBits)
    
    def _updFullGProbeBits(self, dumKeyVar=None):
        if None in self.gprobes:
            return

        fullGProbeBits = list(self.gprobeBits.valueList)
        if None in fullGProbeBits:
            self.fullGProbeBits.set(
                fullGProbeBits,
                isCurrent = self.gprobeBits.isCurrent,
                isGenuine = self.gprobeBits.isGenuine,
            )
            return
        
        for val in self.gprobes:
            match = GProbesRE.match(val)
            if not match:
                continue
            probeNumStr, enabledStr = match.groups()
            probeInd = int(probeNumStr) - 1
            beforeValue = fullGProbeBits[probeInd]
            if enabledStr[0] == "F":
                fullGProbeBits[probeInd] |= GProbeDisableBitVal
        self.fullGProbeBits.set(
            fullGProbeBits,
            isCurrent = self.gprobeBits.isCurrent and self.gprobes.isCurrent,
            isGenuine = self.gprobeBits.isGenuine and self.gprobes.isGenuine,
        )


if __name__ == "__main__":
    import TUI.Base.TestDispatcher
    
    testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("guider")
    Model()
