#!/usr/local/bin/python
"""An object that models the current state of the Echelle.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

2003-12-09 ROwen
2003-12-17 ROwen	Modified to refresh using refreshKeys and to use KeyVarFact.
2004-01-06 ROwen	Modified to use KeyVarFactory.setKeysRefreshCmd.
2004-05-18 ROwen	Stopped importing math and Tkinter; they weren't used.
2005-05-12 ROwen	Modified for new Echelle ICC.
2005-06-06 ROwen	Bug fix: curr filter keywords came before filter name list keywords
					so the data was requested in the wrong order.
2005-06-10 ROwen	Added shutter keyword.
"""
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for fairly fast commands;
# how long does Echelle take to read out?
_TimeLim = 80

_theModel = None

def getModel():
	global _theModel
	if _theModel == None:
		_theModel = _Model()
	return _theModel


class _Model (object):
	def __init__(self,
	**kargs):
		tuiModel = TUI.TUIModel.getModel()
		self.actor = "echelle"
		self.dispatcher = tuiModel.dispatcher
		self.timelim = _TimeLim

		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			converters = str,
			nval = 1,
			dispatcher = self.dispatcher,
		)
		
		self.calFilterNames = keyVarFact(
			keyword = "calFilterNames",
			nval = (1, None),
			description = "Names of calibration lamp filters (ignore blanks)",
		)

		self.calFilter = keyVarFact(
			keyword = "calFilter",
			description = "Name of current calibration lamp filter",
		)
	
		self.svFilterNames = keyVarFact(
			keyword = "svFilterNames",
			nval = (1, None),
			description = "Names of slit viewer filters (ignore blanks)",
		)
	
		self.svFilter = keyVarFact(
			keyword = "svFilter",
			description = "Name of current slit viewer filter",
		)
	
		self.numLamps = 3

		self.lampNames = keyVarFact(
			keyword = "lampNames",
			nval = (1, self.numLamps),
			description = "Names of calibration lamps (ignore blanks)",
		)

		self.lampStates = keyVarFact(
			keyword = "lampStates",
			converters = RO.CnvUtil.asBool,
			nval = self.numLamps,
			description = "States of calibration lamps (1=on, 0=off)",
		)
		
		# obsolete dict -- use mirStatesConst instead
		# dict of ICC mirror state names: TUI mirror state names
		self.mirStatesConst = ("sky", "lamps")
		
		self.mirror = keyVarFact(
			keyword = "mirror",
			nval = 1,
			description = "Calibration mirror position: sky or calibration",
		)
	
		self.shutter = keyVarFact(
			keyword = "shutter",
			nval = 1,
			description = "Current shutter state",
		)
		
		keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
	getModel()
