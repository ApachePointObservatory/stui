#!/usr/local/bin/python
from __future__ import generators
"""Data for testing various DIS widgets"""
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = (
	{"actors": ("tcc", "grim", "dis", "echelle", "tlamps")},
	{"programs": ("UW01", "CL01", "TU02", "myprog")},
	{"lockedActors": ("grim",)},
	{"authList": ("TU02", "tcc", "grim", "echelle", "perms")},
	{"authList": ("myprog", "tcc", "grim", "echelle", "perms")},
	{"authList": ("CL01", "tcc", "dis", "grim", "tlamps")},
	{"authList": ("UW01", "tcc", "echelle")},
)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
	{"authList": ("CL01", "tcc", "dis", "echelle", "grim", "tlamps")},
	{"authList": ("UW02", "tcc", "grim", "tlamps")},
	{"programs": ("UW01", "UW02", "CL01")},
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
		dataDict = dataIter.next()
	except StopIteration:
		return
	dispatch(dataDict)
	
	tuiModel.root.after(1500, animate, dataIter)
