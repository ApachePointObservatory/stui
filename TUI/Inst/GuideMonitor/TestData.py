#!/usr/bin/env python
"""Supplies test data for the Seeing Monitor

History:
2010-09-24
2010-09-29 ROwen    modified to use RO.Alg.RandomWalk
2011-01-03 ROwen    Added lots of data.
"""
import math
import random
import RO.PhysConst
import RO.Alg.RandomWalk
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
tuiModel = testDispatcher.tuiModel

class GuideOffInfo(object):
    def __init__(self):
        lim = 10.0
        mean = 0.0
        sigma = 2.0
        
        self.azChange = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim)
        self.altChange = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim)
        self.rotChange = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim)
        self.focusChange = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(0, 50, -500, 500)
        self.scaleChange = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(0, 1e-5, -1e-4, 1e-4)
        self.seeing = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(1.5, 0.1, 0.3, 2.5)
        self.netAzOffset = 0
        self.netAltOffset = 0
        self.netRotOffset = 0
        self.netFocusOffset = 0
        self.netScale = 1.0
    
    def update(self):
        """Randomly change values
        """
        self.azChange.next()
        self.altChange.next()
        self.rotChange.next()
        self.focusChange.next()
        self.scaleChange.next()
        self.seeing.next()
        self.netAzOffset += self.azChange.value
        self.netAltOffset += self.altChange.value
        self.netRotOffset += self.rotChange.value
        self.netFocusOffset += self.focusChange.value
        self.netScale += self.scaleChange.value
    
    def getGuiderStr(self):
        """Get the data as a keyword variable
        
        Fields are: az off (arcsec on sky), alt off (arcsec), rot off (arcsec)
        """
        strList = [
            "axisError=%0.2f, %0.2f, %0.2f" % \
                (self.azChange.value * 1.4, self.altChange.value * 1.4, self.rotChange.value * 1.4),
            "axisChange=%0.2f, %0.2f, %0.2f, enabled" % \
                (self.azChange.value, self.altChange.value, self.rotChange.value),
            "focusError=%0.1f" % (self.focusChange.value * 1.4,),
            "focusChange=%0.1f, enabled" % (self.focusChange.value,),
            "scaleError=%0.6f" % (self.scaleChange.value * 1.4,),
            "scaleChange=%0.6f, enabled" % (self.scaleChange.value,),
            "seeing=%0.1f" % (self.seeing.value,),
        ]
        return "; ".join(strList)

    def getTCCStr(self):
        tccStrList = [
            "objArcOff=%0.5f, 0.0, 1000.0, %0.5f, 0.0, 1000.0" % \
                tuple(val / 3600.0 for val in (self.netAzOffset, self.netAltOffset)),
            "guideOff=0.0, 0.0, 1000.0, 0.0, 0.0, 1000.0, %0.5f, 0.0, 1000.0" % \
                (self.netRotOffset / 3600.0,),
            "secFocus=%0.7f" % (self.netFocusOffset,),
            "scaleFac=%0.7f" % (self.netScale,),
        ]
        return "; ".join(tccStrList)
    

def runTest():
    _nextGuideOffset(GuideOffInfo(), 2)
    _nextSecPiston(RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(100, 50, -2000, 2000), 2)

def _nextGuideOffset(guideOffInfo, delaySec):
    guideOffInfo.update()
    keyVarStr = guideOffInfo.getGuiderStr()
    testDispatcher.dispatch(keyVarStr, actor="guider")
    tccStr = guideOffInfo.getTCCStr()
    testDispatcher.dispatch(tccStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextGuideOffset, guideOffInfo, delaySec)

def _nextSecPiston(secPiston, delaySec):
    keyVarStr = "SecOrient=%0.1f, 0, 0, 0, 0" % (secPiston.next(),)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextSecPiston, secPiston, delaySec)
