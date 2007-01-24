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

class Tester(object):
    def __init__(self, dispatcher, dataSet=None, interval=2.0):
        self.dispatcher= dispatcher
        self.dataSet = None
        self.intervalMS = int(interval * 1000)
        self.wdg = Tkinter.Label()
        self.msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":{}}
    
        if dataSet:
            self.run(dataSet)
    
    def run(self, dataSet):
        self.dataSet = dataSet
        if self.dataSet:
            self.dispatchNext(iter(self.dataSet))
    
    def dispatchNext(self, dataIter):
        try:
            dataDict = dataIter.next()
        except StopIteration:
            print "Test finished"
            return
            
        self.msgDict["data"] = dataDict
        keys = dataDict.keys()
        keys.sort()
        print "Dispatching:"
        for key in keys:
            print "  %s = %r" % (key, dataDict[key])
        self.dispatcher.dispatch(self.msgDict)
        if self.dataSet:
            self.wdg.after(self.intervalMS, self.dispatchNext, dataIter)

def runTest(dispatcher):
    wdg = Tkinter.Label()
    
    dataSet = (
        {   # start with Echelle (no rotator) and stop buttons in
            "AxePos": (-340.009, 45, "NaN"),
            "AzStat": (-340.009, 0.0, 4565, 0x801),
            "AltStat": (45.0, 0.0, 4565, 0x801),
            "Inst": ("Echelle",),
            "AxisCmdState": ("Tracking","Tracking", "NotAvailable"),
            "AxisErrCode": ("","", "NotAvailable"),
            "SecFocus": (570,),
            "GCFocus": (-300,),
        },
        {   # enable stop buttons
            "AxePos": (-340.009, 45, "NaN"),
            "AzStat": (-340.009, 0.0, 4565, 0),
            "AltStat": (45.0, 0.0, 4565, 0),
        },
        {   # slew
            "ObjName": ("test object with a long name",),
            "ObjSys": ("FK5", 2000.0),
            "ObjNetPos": (120.123450, 0.000000, 4494436859.66000, -2.345670, 0.000000, 4494436859.66000),
            "RotType": ("None",),
            "AxePos": (-350.999, 45, "NAN"),
            "SlewDuration": (14.0,),
            "AxisCmdState": ("Slewing","Slewing", "NotAvailable"),
            "AxisErrCode": ("","", "NotAvailable"),
            "AxePos": (-340.009, 45, "NaN"),
            "SecFocus": (570,),
            "GCFocus": (-300,),
            "TCCPos": (-342.999, 38.623, "NaN"),
        },
        {
            "AxePos": (-348.121, 43.432, "NaN"),
            "TCCPos": (-342.999, 38.623, "NaN"),
        },
        {
            "AxePos": (-346.329, 41.765, "NaN"),
            "TCCPos": (-342.999, 38.623, "NaN"),
        },
        {
            "AxePos": (-344.325, 39.424, "NaN"),
            "TCCPos": (-342.999, 38.623, "NaN"),
        },
        {
            "AxePos": (-343.012, 38.532, "NaN"),
            "TCCPos": (-342.999, 38.623, "NaN"),
        },
        {
            "AxePos": (-342.999, 38.623, "NaN"),
            "TCCPos": (-342.999, 38.623, "NaN"),
        },
        {   # slew ends
            "SlewEnds": (),
            "AxisCmdState": ("Tracking","Tracking", "Halted"),
            "AxisErrCode": ("","", "NoRestart"),
            "AxePos": (-342.974, 38.645, 10.0),
            "TCCPos": (-342.974, 38.645, "NaN"),
        },
        {   # tracking
            "AxisCmdState": ("Tracking","Tracking", "Halted"),
            "AxisErrCode": ("","", "NoRestart"),
            "AxePos": (-342.964, 38.725, 10.0),
            "TCCPos": (-342.964, 38.725, "NaN"),
        },
        {   # change to dis, re-enabling the rotator
            "Inst": ("DIS",),
            "SlewDuration": (2.0,),
            "AxisCmdState": ("Slewing","Slewing", "Halting"),
            "AxisErrCode": ("","", "NoRestart"),
            "AzStat": (-342.953, -0.011, 4565, 0),
            "AltStat": (38.815, 0.10, 4565, 0),
            "RotStat": (10.0, 0.0, 4565, 0),
            "AxePos": (-342.563, 38.625, 10.0),
            "TCCPos": (-342.563, 38.625, "NaN"),
        },
        {
            "SlewEnds": (),
            "AxisCmdState": ("Tracking","Tracking", "Halted"),
            "AxisErrCode": ("","", "NoRestart"),
            "AxePos": (-342.563, 38.625, 10.0),
            "TCCPos": (-342.563, 38.625, "NaN"),
        },
        {   # slew rotator
            "SlewDuration": (6.0,),
            "AxisCmdState": ("Slewing","Slewing", "Slewing"),
            "AxisErrCode": ("","", ""),
            "RotType": ("Obj",),
            "RotPos": (3.456789, 0.000000, 4494436895.07921),
            "AxePos": (-342.563, 38.625, 9.4),
            "TCCPos": (-342.563, 38.625, 5.0),
        },
        {
            "AxePos": (-342.563, 38.625, 7.3),
            "TCCPos": (-342.563, 38.625, 5.0),
        },
        {
            "AxePos": (-342.563, 38.625, 6.1),
            "TCCPos": (-342.563, 38.625, 5.0),
        },
        {
            "AxePos": (-342.563, 38.625, 5.4),
            "TCCPos": (-342.563, 38.625, 5.0),
        },
        {
            "SlewEnds": (),
            "AxisCmdState": ("Tracking","Tracking", "Tracking"),
            "AxisErrCode": ("","", ""),
            "AxePos": (-342.563, 38.625, 5.0),
            "TCCPos": (-342.563, 38.625, 5.0),
        },
    )
    
    Tester(dispatcher, dataSet)
