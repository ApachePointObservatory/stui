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
    'doCalibsState="done","OK","done"',
    'doScienceState="done","OK","done"',
    'gotoFieldState="done","OK","off","done","done","done"',
    'doCalibs_nArc=2, 5',
    'doCalibs_arcTime=5.0, 6.0',
    'gotoField_guiderTime=5, 10',
    'gotoGangChange_alt=30.0, 45.0',
    'doApogeeScience_comment="test comment", ""',
)

dataSet = (
    (
    'surveyCommands=gotoField, doCalibs, gotoInstrumentChange',
    'gotoFieldStages="hartmann","guider"',
    'gotoFieldState="done","OK","done","done"',
    ),
    (
    'surveyCommands=gotoStow, gotoField, doScience, doCalibs, gotoInstrumentChange',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
    'gotoFieldState="running","OK","off","running","pending","pending"',
    ),
    (
    'gotoFieldState="running","OK","off","running","running","pending"',
    ),
    (
    'gotoFieldState="running","OK","off","running","done","running"',
    ),
    (
    'gotoFieldState="failed","OK","off","done","done","failed"',
    ),
)

def start():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
