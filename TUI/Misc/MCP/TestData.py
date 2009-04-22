#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "ffsStatus=01,01,01,01,01,01,01,01",
    "ffsCommandedOn=false",
    "ffsSelected=11",
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
    "ffsCommandedOn=true",
    ),
    (
    "ffLampCommandedOn=true",
    "ffsStatus=00,00,00,00,00,00,00,00",
    ),
    (
    "ffLamp=1,0,0,1",
    "ffsStatus=01,00,10,10,10,11,10,10",
    ),
    (
    "ffLamp=1,1,1,1",
    "ffsStatus=10,10,10,10,10,10,10,10",
    ),
)

def init():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
