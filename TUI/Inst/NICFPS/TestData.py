#!/usr/local/bin/python
import RO.Alg
import TUI.TUIModel

tuiModel = TUI.TUIModel.getModel(True)
dispatcher = tuiModel.dispatcher
cmdr = tuiModel.getCmdr()
actor = "nicfps"

MainDataSet = (
	('filter_names', ("Open", "MK_J", "MK_H", "MK_K", "MK_L", "MK_M", "Y", "Z",)),
	('filter_done', ("Open",)),
	('fp_opath', ("Out",)),
	('fp_mode', ("Operate",)),
	('fp_rtime', ("0.5",)),
	('fp_x', ("100",)),
	('fp_y', ("-200",)),
	('fp_z', ("321",)),
	('fp_zw', ("6.504",)),
	('fp_deszw', ("6.499",)),
	('fp_wavecal', ("0.874", "1.754e-02",)),
	('slit_opath', ("In",)),
	('slit_focus', ("120",)),
	('window', ("1", "1", "1024", "1024",)),
	('nfs', ("1",)),
	('nfs_names', ("0", "1", "2", "3", "4", "5", "6", "7", "8",)),
	('pressure_max', ("2.50e-04",)),
	('pressure', ("2.07e-05",)),
	('temp_names', ("FPA", "FWHEEL1", "CAMERA", "COLLIMATOR",)),
	('temp_min', ("75", "75", "75", "75",)),
	('temp_max', ("85", "90", "100", "110",)),
	('temp', ("80.2", "87.4", "85.7", "90.3",)),
)
MainDataSet = RO.Alg.OrderedDict(MainDataSet)
# each element of animDataSet is a full set of data to be dispatched,
# hence each element is a list of keyvar, value tuples
AnimDataSet = (
	{'filter_ttc': ('3',), 'temp': ("81.1", "87.9", "85.8", "90.4",),},
	{'temp': ("82.2", "88.3", "85.9", "90.3",), 'nfs': ("0",),},
	{'filter_done': ('MK_J',), 'temp': ("83.0", "88.7", "85.9", "90.5",),},	
	{'slit_ttc': ('3',),},
	{'fp_ttc': ('3',), 'temp': ("83.9", "89.2", "85.9", "90.5",),},
	{'slit_opath': ("Out",), 'temp': ("85.1", "89.9", "86.0", "90.6",),},
	{'fp_opath': ('In',), 'fp_mode': ('Balance',), 'temp': ("85.1", "90.1", "86.1", "90.7",),},
	{'fp_rtime': ('0.2',), 'fp_x': ("570",),},
	{'fp_rtime': ('0.5',), 'fp_y': ("-42",),},
	{'fp_mode': ("Operate",),},
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
