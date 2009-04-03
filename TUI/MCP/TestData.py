#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp")
tuiModel = testDispatcher.tuiModel

dataList = (
    "ffLeafStatus=01,01,01,01,01,01,01,01",
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
)

dataSet = (
    (
    ),
)

def init():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
