#!/usr/bin/env python
"""Supplies test data for the tcc status window

To do:
- fix so order of data is preserved
  by specifying the data as a tuple of tuples
  and turning it into an ordered dict for each dispatched message

- convert all axis widgets to use this 
  or at least fix them to use AxisCmdState instead of TCCStatus
  as necessary

History:
2006-03-16 ROwen
2009-04-01 ROwen    Modified to use TUI.Base.TestDispatcher
"""
import TUI.Base.TestDispatcher

testDispatcher = TUI.Base.TestDispatcher.TestDispatcher("tcc")
tuiModel = testDispatcher.tuiModel

def setDIS():
    dataList = (
        "Inst=DIS",
        "IPConfig=TTF",
        "ObjSys=FK5, 2000.0",
        "RotType=Obj",
        "RotAngle=0.0",
    )
    testDispatcher.dispatch(dataList)

def setEchelle():
    dataList = (
        "Inst=Echelle",
        "IPConfig=FTF",
    )
    testDispatcher.dispatch(dataList)
