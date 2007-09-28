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
"""
import Tkinter
import TUI.TUIModel
import TUI.TCC.TCCModel

dispatcher = None
def setModel(tuiModel):
    global dispatcher
    dispatcher = tuiModel.dispatcher

def dispatchDataDict(dataDict):
    msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
    keys = dataDict.keys()
    keys.sort()
    print "Dispatching:"
    for key in keys:
        print "  %s = %r" % (key, dataDict[key])
    dispatcher.dispatch(msgDict)

def setDIS():
    dataDict = {
        "Inst": ("DIS",),
        "ObjSys": ("FK5", 2000.0),
        "RotType": ("Obj",),
        "RotAngle":("0.0",),
        "AxisCmdState": ("Tracking","Tracking", "Tracking"),
    }
    dispatchDataDict(dataDict)

def setEchelle():
    dataDict = {
        "Inst": ("Echelle",),
        "AxisCmdState": ("Tracking","Tracking", "NotAvailable"),
    }
    dispatchDataDict(dataDict)
