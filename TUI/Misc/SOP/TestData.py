#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassed=boss,False,ff_lamp,False,ffs,False,gcamera,False,hgcd_lamp,False,ne_lamp,False,uv_lamp,False,wht_lamp,False',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
    'doCalibsStages="calibs"',
    'gotoFieldState="done","off","done","done","done"',
)

dataSet = (
    (
    'gotoFieldState="running","off","running","pending","pending"',
    ),
    (
    'gotoFieldState="running","off","running","running","pending"',
    ),
    (
    'gotoFieldState="running","off","running","done","running"',
    ),
    (
    'gotoFieldState="failed","off","done","done","failed"',
    ),
)

def start():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
