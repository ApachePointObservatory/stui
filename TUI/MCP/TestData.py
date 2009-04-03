#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("mcp", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "petalsStatus=01,01,01,01,01,01,01,01",
    "petalsCommandedOn=false",
    "petalsSelected=11",
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
    "petalsCommandedOn=true",
    ),
    (
    "ffLampCommandedOn=true",
    "petalsStatus=00,00,00,00,00,00,00,00",
    ),
    (
    "ffLamp=1,0,0,1",
    "petalsStatus=01,00,10,10,10,11,10,10",
    ),
    (
    "ffLamp=1,1,1,1",
    "petalsStatus=10,10,10,10,10,10,10,10",
    ),
)

def init():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
