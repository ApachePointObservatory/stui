#!/usr/local/bin/python
from __future__ import generators
"""Data for testing various DIS widgets"""
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = {
	"IMAGETYP": ("",),
	"Mirror": (0,),
	"EFilter": (1,),
	"GCFilter": (3,),
	"Grating": (-1,),
	"SlitFcs": (3200,),
	"TipMtr": (7000,),
	"TiltMtr": (5000,),
	"CCDFcs": (-1000,),
	"LampT": (0,),
	"LampF": (0,),
	"LampW": (0,),
}
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
	{"Mirror": (1,), "EFilter":(3,)},
	{"LampT": (1,)},
	{"LampT": (0,), "LampW": (1,), "EFilter":(2,)},
	{"LampW": (1,), "EFilter":(1,)},
	{"LampW": (0,)},
	{"Mirror": (0,)},
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
