#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassNames=boss, ff_lamp, ffs, gcamera, hgcd_lamp, ne_lamp, uv_lamp, wht_lamp', 
    'bypassed=1, 0, 0, 0, 0, 1, 0, 1', 
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
