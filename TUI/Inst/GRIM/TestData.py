#!/usr/local/bin/python
from __future__ import generators
"""Data for testing various GRIM widgets"""
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()

MainDataSet = {
	'filter1': ('0',),
	'filter2': ('13',),
	'lens': ('0',),
	'grism': ('2',),
	'slit': ('7',),
	'grimmode': ('1',),
	'grimscale': ('1',),
	'grimfilter': ('13',),
}
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
	{'grimmode': ('0',), 'grimscale': ('1',), 'grimfilter': ('0',),},
	{'grimmode': ('0',), 'grimscale': ('1',), 'grimfilter': ('1',),},
	{'grimmode': ('0',), 'grimscale': ('1',), 'grimfilter': ('2',),},
	{'grimmode': ('0',), 'grimscale': ('1',), 'grimfilter': ('13',),},
	{'grimmode': ('0',), 'grimscale': ('1',), 'grimfilter': ('9',),},
	{'grimmode': ('1',), 'grimscale': ('1',), 'grimfilter': ('9',),},
	{'grimmode': ('1',), 'grimscale': ('1',), 'grimfilter': ('5',),},
	{'grimmode': ('3',), 'grimscale': ('1',), 'grimfilter': ('13',),},
	{'grimmode': ('3',), 'grimscale': ('3',), 'grimfilter': ('0',),},
	{'grimmode': ('3',), 'grimscale': ('5',), 'grimfilter': ('0',),},
	{'grimmode': ('3',), 'grimscale': ('13',), 'grimfilter': ('0',),},
	{'grimmode': ('3',), 'grimscale': ('21',), 'grimfilter': ('0',),},
	{'grimmode': ('4',), 'grimscale': ('0',), 'grimfilter': ('0',),},
	{'grimmode': ('5',), 'grimscale': ('0',), 'grimfilter': ('0',),},
	{'grimmode': ('6',), 'grimscale': ('0',), 'grimfilter': ('0',),},
	{'grimmode': ('7',), 'grimscale': ('0',), 'grimfilter': ('0',),},
)

BaseMsgDict = {"cmdr":cmdr, "cmdID":11, "actor":"grim", "type":":"}
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
