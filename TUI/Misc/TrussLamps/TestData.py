#!/usr/local/bin/python
import RO.Alg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()
actor = "tlamps"

MainDataSet = (
	('lampNames', ("He", "Ne", "Ar", "Bright Quartz", "Dim Quartz",)),
	('lampStates', ("Off", "On", "Off", "On", "Off",)),
)
MainDataSet = RO.Alg.OrderedDict(MainDataSet)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a dict of keyvar: valueList items
AnimDataSet = (
	{'lampStates': ("On", "On", "Off", "On", "Off",)},
	{'lampStates': ("Off", "Off", "Off", "Unknown", "Rebooting",)},
	{
		'lampNames': ("He", "Ne", "Ar", "Bright Quartz", "Dim Quartz", "Extra",),
		'lampStates': ("Off", "On", "Off", "On", "Off", "On",),
	},
	{'lampStates': ("Off", "Off", "Off", "Off", "Off",)},
	{
		'lampNames': ("He", "Ne", "Ar", "Bright Quartz",),
		'lampStates': ("Off", "On", "Off", "Unknown",),
	},
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
