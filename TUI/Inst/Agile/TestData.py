#!/usr/bin/env python
import RO.Alg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()
actor = "agile"

MainDataSet = (
    ('filter_names', ("Open", "MK_J", "MK_H", "MK_K", "MK_L", "MK_M",)),
    ('filter_done', ("Open",)),
    ('window', ("1", "1", "1024", "1024",)),
    ('ccdTempLimits', ("", "1.5", "", "10",)),
    ('ccdTemp', ("-40", "normal")),
    ('ccdSetTemp', ("-40", "normal")),
)
MainDataSet = RO.Alg.OrderedDict(MainDataSet)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
    {'filter_ttc': ('3',), 'temp': ("81.1", "87.9", "85.8", "90.4",),},
    {'ccdTemp': ("-5", "veryHigh"),},
    {'ccdTemp': ("-35", "high"),},
    {'ccdTemp': ("-45", "low"),},
    {'ccdTemp': ("-65", "veryLow"),},
    {'ccdTemp': ("-40", "normal"),},
    {'ccdTempLimits': ("1.5", "1.5", "10", "10",),},
    {'filter_done': ('MK_J',), 'temp': ("83.0", "88.7", "85.9", "90.5",),}, 
    {'window': ("4", "5", "1001", "1002",),},
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":actor, "type":":"}
MainMsgDict = {"data":MainDataSet}.update(BaseMsgDict)

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
