#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassed=boss,False,ff_lamp,False,ffs,False,gcamera,False,hgcd_lamp,False,ne_lamp,False,uv_lamp,False,wht_lamp,False',
    'doCalibsStages="doCalibs"',
    'doScienceStages="doScience"',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
    'doCalibsState="done","done"',
    'doScienceState="done","done"',
    'gotoFieldState="done","off","done","done","done"',
    'doCalibs_nArc=2, 5, 6',
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
