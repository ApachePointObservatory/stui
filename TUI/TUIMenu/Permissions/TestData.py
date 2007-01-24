#!/usr/bin/env python
from __future__ import generators
"""Data for testing various DIS widgets"""
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = (
    {"actors": ("tcc", "nicfps", "dis", "echelle", "tlamps")},
    {"programs": ("UW01", "CL01", "TU01")},
    {"lockedActors": ("nicfps",)},
    {"authList": ("TU01", "tcc", "nicfps", "echelle", "perms")},
    {"authList": ("CL01", "tcc", "dis", "nicfps", "tlamps")},
    {"authList": ("UW01", "tcc", "echelle")},
)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
    (
        {"authList": ("CL01", "tcc", "dis", "echelle", "nicfps", "tlamps")},
        {"authList": ("UW02", "tcc", "nicfps", "tlamps")},
    ),
    (
        {"programs": ("TU01", "UW01")},
    ),
    (
        {"actors": ("tcc", "nicfps", "dis", "echelle", "tlamps", "apollo")},
    ),
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":"perms", "type":":"}

def dispatch(dataDict):
    """Dispatch a data dictionary"""
    print "Dispatching data:", dataDict
    msgDict = {"data":dataDict}
    msgDict.update(BaseMsgDict)
    dispatcher.dispatch(msgDict)

def start():
    for dataDict in MainDataSet:
        dispatch(dataDict)      
    
def animate(dataIter=None):
    if dataIter == None:
        dataIter = iter(AnimDataSet)
    try:
        dataList = dataIter.next()
    except StopIteration:
        return
    for dataDict in dataList:
        dispatch(dataDict)
    
    tuiModel.root.after(1500, animate, dataIter)
