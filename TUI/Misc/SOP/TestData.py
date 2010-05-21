#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassed=boss,False,ff_lamp,False,ffs,False,gcamera,False,hgcd_lamp,False,ne_lamp,False,uv_lamp,False,wht_lamp,False',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
    'gotoFieldStates="done","off","done","done","done"',
)

dataSet = (
    (
    'gotoFieldStates="starting","off","prepping","pending","pending"',
    ),
    (
    'gotoFieldStates="running","off","running","prepping","pending"',
    ),
    (
    'gotoFieldStates="running","off","done","running","prepping"',
    ),
    (
    'gotoFieldStates="done","off","done","done","running"',
    ),
    (
    'gotoFieldStates="done","off","done","done","failed"',
    ),
)

def start():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
