#!/usr/bin/env python
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("sop", delay=1.5)
tuiModel = testDispatcher.tuiModel

dataList = (
    "version=1.4",
    'bypassed=boss,False,ff_lamp,False,ffs,False,gcamera,False,hgcd_lamp,False,ne_lamp,False,uv_lamp,False,wht_lamp,False',
    'gotoFieldStages="slew","hartmann","calibs","guider"',
#    'gotoFieldState="done","off","done","done","done"',
)

dataSet = (
    (
    'gotoFieldState="starting","off","prepping","pending","pending"',
    ),
    (
    'gotoFieldState="running","off","running","prepping","pending"',
    ),
    (
    'gotoFieldState="running","off","done","running","prepping"',
    ),
    (
    'gotoFieldState="done","off","done","done","running"',
    ),
    (
    'gotoFieldState="done","off","done","done","failed"',
    ),
)

def start():
    testDispatcher.dispatch(dataList)

def animate():
    testDispatcher.runDataSet(dataSet)
