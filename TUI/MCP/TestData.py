#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp")
tuiModel = testDispatcher.tuiModel

dataSet = (
    (
        "ffLeafStatus=00,00,00,00,00,00,00,00",
        "ffLeafCommandedOn=false",
        "ffLeafSelected=11",
        "ffLamp=0,0,0,0",
        "ffLampCommandedOn=false",
        "neLamp=0,0,0,0",
        "neLampCommandedOn=false",
        "hgCdLamp=0,0,0,0",
        "hgCdLampCommandedOn=false",
        "whtLampCommandedOn=false",
        "needIack=true",
    ),
)

def runTest():
    testDispatcher.runDataSet(dataSet)
