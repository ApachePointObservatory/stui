#!/usr/bin/env python
"""Supplies test data for the Seeing Monitor

History:
2010-09-24
2010-09-29 ROwen    modified to use RO.Alg.RandomWalk
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
        
        self.randomValueDict = dict(
            azOff = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim),
            altOff = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim),
            rotOff = RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(mean, sigma, -lim, lim),
        )
    
    def update(self):
        """Randomly change values
        """
        for randomValue in self.randomValueDict.itervalues():
            randomValue.next()
    
    def getValueDict(self):
        """Get a dictionary of value name: value
        """
        return dict((name, randomValue.value) for name, randomValue in self.randomValueDict.iteritems())

    def getKeyVarStr(self):
        """Get the data as a keyword variable
        
        Fields are: az off (arcsec on sky), alt off (arcsec), rot off (arcsec)
        """
        return "axisChange=%(azOff)0.2f, %(altOff)0.2f, %(rotOff)0.2f, enabled" % self.getValueDict()

def runTest():
    _nextGuideOffset(GuideOffInfo(), 2)
    _nextSecFocus(RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(0, 10, -500, 500), 3)
    _nextSecPiston(RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(100, 50, -2000, 2000), 2)
    _nextScaleFac(RO.Alg.RandomWalk.ConstrainedGaussianRandomWalk(1.0, 0.001, 0.90, 1.1), 2)

def _nextGuideOffset(guideOffInfo, delaySec):
    guideOffInfo.update()
    keyVarStr = guideOffInfo.getKeyVarStr()
    testDispatcher.dispatch(keyVarStr, actor="guider")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextGuideOffset, guideOffInfo, delaySec)

def _nextSecFocus(secFocus, delaySec):
    keyVarStr = "SecFocus=%0.1f" % (secFocus.next(),)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextSecFocus, secFocus, delaySec)

def _nextSecPiston(secPiston, delaySec):
    keyVarStr = "SecOrient=%0.1f, 0, 0, 0, 0" % (secPiston.next(),)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextSecPiston, secPiston, delaySec)

def _nextScaleFac(scaleFac, delaySec):
    keyVarStr = "ScaleFac=%0.5f" % (scaleFac.next(),)
    testDispatcher.dispatch(keyVarStr, actor="tcc")
    tuiModel.tkRoot.after(int(delaySec * 1000), _nextScaleFac, scaleFac, delaySec)
