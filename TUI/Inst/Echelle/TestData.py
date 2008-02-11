#!/usr/bin/env python
"""Data for testing various DIS widgets"""
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = {
    "shutter": ("closed",),
    "calFilterNames": ("a", "b", "open", "", "", ""),
    "svFilterNames": ("x", "y", "z", "open", "", ""),
    "mirrorNames": ("sky", "calibration"),
    "mirror": ("sky",),
    "calFilter": ("open",),
    "svFilter": ("open",),
    "lampNames": ("ThAr", "Quartz", ""),
    "lampStates": (0, 0, 0),
}
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a dict of keyvar, value tuples
AnimDataSet = (
    {"mirror": ("lamps",), "calFilter":("a",)},
    {"lampStates": (1,0,0), "shutter": ("open",)},
    {"lampStates": (0,1,0), "calFilter":("b",)},
    {"lampNames": ("ThAr", "Quartz", "Other")},
    {"lampStates": (0,0,1), "calFilter":("a",)},
    {"lampNames": ("ThAr", "Quartz", "")},
    {"mirror": ("sky",), "lamps": (0,0,0), "shutter": ("closed",)},
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":"echelle", "type":":"}

def dispatch(dataSet=None):
    """Dispatch a set of data, i.e. a list of keyword, value tuples"""
    if dataSet == None:
        dataSet = MainDataSet
    print "Dispatching data:", dataSet
    msgDict = {"data":dataSet}
    msgDict.update(BaseMsgDict)
    dispatcher.dispatch(msgDict)
    
def animate(dataIter=None):
    if dataIter == None:
        dataIter = iter(AnimDataSet)
    try:
        data = dataIter.next()
    except StopIteration:
        return
    dispatch(data)
    
    tuiModel.root.after(1500, animate, dataIter)
