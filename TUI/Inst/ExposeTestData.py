#!/usr/local/bin/python
from __future__ import generators
"""Data for testing various DIS exposure widgets

To do:
- change timestamps to valid values

History:
2003-10-22 ROwen	Modified data to match new hub.
"""
import TUI.TUIModel
import ExposeModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
progID = tuiModel.getProgID()
expModel = ExposeModel.getModel("DIS")
cmdr = tuiModel.getCmdr()

MainDataSet = {
	"disFiles": (cmdr, "holecard.apo.nmsu.edu","/export/images/",progID.upper() + "/","","test0005b.fits","test0005r.fits"),
	"disNextPath": (cmdr, "","test","0006",".fits"),
}

# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
	{
		"disSeqState": (cmdr, "object", "6.0", "1", "1", "running"),
		"disExpState": (cmdr, "flushing", "2003...", "0", "0"),
	},
	{
		"disExpState": (cmdr, "integrating", "2003...", "6.0", "6.0"),
	},
	{},
	{
		"disExpState": (cmdr, "paused", "2003...", "3.0", "6.0"),
		"disSeqState": (cmdr, "object", "6.0", "1", "1", "paused"),
	},
	{},
	{},
	{
		"disExpState": (cmdr, "resume", "2003...", "3.0", "6.0"),
		"disSeqState": (cmdr, "object", "6.0", "1", "1", "running"),
	},
	{},
	{
		"disExpState": (cmdr, "reading", "2003...", "3", "3"),
	},
	{},
	{
		"disFiles": (cmdr, "holecard.apo.nmsu.edu","/export/images/",progID.upper() + "/","","test0006b.fits","test0006r.fits"),
		"disNextPath": (cmdr, "","test","0007",".fits"),
		"disExpState": (cmdr, "done", "2003...", "0", "0"),
		"disSeqState": (cmdr, "object", "6.0", "1", "1", "done"),
	},
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":expModel.actor, "type":":"}
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
		print "Done"
		return
	dispatch(data)
	
	tuiModel.root.after(1500, animate, dataIter)
