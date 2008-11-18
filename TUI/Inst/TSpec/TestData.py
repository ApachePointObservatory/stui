#!/usr/bin/env python
"""Data for testing various TSpec widgets
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
     tempNames = ("BoilOff","TempBrd","PrismBox","SpecCam","AuxTank","H1","BH4","BH3","BH2","Shield"),
     temps = (85.404,284.601,78.508,77.363,76.405,78.069,78.392,77.749,77.503,79.244),
     tempAlarms = (0,0,0,0,0,0,0,0,0,0),
     tempThresholds = (115,400,400,400,80,400,400,None,400,400), # neg for lower limit; None for no limit
     vacuum = (1.5e-8,),
     vacuumAlarm = (0,),
     vacuumThreshold = (1e-7,),
)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a dict of keyvar, value tuples
AnimDataSet = (
    {"mirror": ("lamps",), "calFilter":("a",)},
    dict(
        temps = (159.404,284.601,78.508,77.363,76.405,78.069,78.392,77.749,77.503,79.244),
        tempAlarms = (1,0,0,0,0,0,0,0,0,0),
    ),
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
