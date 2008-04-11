#!/usr/bin/env python
"""Data for testing various TSpec widgets

To do:
- set animated data set to reasonable values
"""
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

slitPosList = ["%s %s" % (a, b) for a in ("0.7", "1.1", "1.5", "1.7") for b in ("Slit", "Block")]
MainDataSet = dict(
     arrayPower = ("On",),
     exposureModeInfo = ("Fowler", 1, 16, "Sutr", 1, 4),
     exposureMode = ("Fowler", 3),
     slitPositions = slitPosList,
     slitPosition = slitPosList[2:3],
     slitState = ("Done", 0.0, 0.0),
     ttMode = ("ClosedLoop",),
     ttPosition = (15.4, 16.4, -17.2, -17.1),
     ttLimits = (-20.0, 20.0, -20.0, 20.0),
     tempNames = ("Array", "Window", "Misc", "ICC"),
     temps = (24.6, 43.2, 75.0, 222.2),
     tempAlarms = (0, 0, 0, 0),
     tempThresholds = (30.0, 70.0, None, -200.0), # neg values are lower limits
     vacuum = (1.5e-8,),
     vacuumAlarm = (0,),
     vacuumThreshold = (1e-7,),
)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a dict of keyvar, value tuples
AnimDataSet = (
    {"mirror": ("lamps",), "calFilter":("a",)},
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":"tspec", "type":":"}

def dispatch(dataSet=None):
    """Dispatch a set of data, i.e. a list of keyword, value tuples"""
    if dataSet == None:
        dataSet = MainDataSet
    
    # split dictionary between slit and non-slit data
    mainDict = {}
    slitDict = {}
    for key, value in dataSet.iteritems():
        if key.lower().startswith("slit"):
            slitDict[key] = value
        else:
            mainDict[key] = value
    if mainDict:
        print "dispatching:", mainDict
        msgDict = BaseMsgDict.copy()
        msgDict["data"] = mainDict
        dispatcher.dispatch(msgDict)
    if slitDict:
        print "dispatching from tcamera:", slitDict
        msgDict = BaseMsgDict.copy()
        msgDict["data"] = slitDict
        msgDict["actor"] = "tcamera"
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
