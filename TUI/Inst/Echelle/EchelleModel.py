#!/usr/local/bin/python
"""An object that models the current state of the Echelle.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

Note: LampF is not used.

2003-12-09 ROwen
2003-12-17 ROwen	Modified to refresh using refreshKeys and to use KeyVarFact.
2004-01-06 ROwen	Modified to use KeyVarFactory.setKeysRefreshCmd.
2004-05-18 ROwen	Stopped importing math and Tkinter; they weren't used.
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
	
# Guide camera and "e" (calib) filter names
# Warning: filter IDs are 1-based
_GCFiltNames = ("None", "ND1", "ND2", "ND3", "Red", "Blue", )
_CalFiltNames = ("None", "Blue", "3", "4", "5", "6",)
		
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

		self.filterID = keyVarFact(
			keyword = "eFilter",
			converters = RO.CnvUtil.asInt,
			description = "ID of filter in front of slit",
		)

		self.filterName = keyVarFact(
			keyword = "loc_filterName",
			description = "Name of filter in front of slit",
			isLocal = True,
		)
		self.filterID.addIndexedCallback(self.updCalFilterName)
		
		self.filterNames = keyVarFact(
			keyword = "loc_filterNames",
			nval = 6,
			description = "Names of filters in front of slit; ID is name index + 1",
			isLocal = True,
		)
		self.filterNames.set(_CalFiltNames, isCurrent = True)

		self.gcFilterID = keyVarFact(
			keyword = "gcFilter",
			converters = RO.CnvUtil.asInt,
			description = "Guide camera filter position number",
		)

		self.gcFilterName = keyVarFact(
			keyword="gcFilter",
			description="Guide camera filter name",
			isLocal = True,
		)
		self.gcFilterID.addIndexedCallback(self.updGCFilterName)
		
		self.gcFilterNames = keyVarFact(
			keyword = "loc_gcFilterNames",
			nval = 6,
			description="Names of guide camera filters; ID is name index + 1",
			isLocal = True,
		)
		self.gcFilterNames.set(_GCFiltNames, isCurrent = True)

		self.lampT = keyVarFact(
			keyword = "lampT",
			converters = RO.CnvUtil.asBool,
			description = "Th/Ar calibration lamp on?",
		)

		self.lampW = keyVarFact(
			keyword = "lampW",
			converters = RO.CnvUtil.asBool,
			description = "White (quartz) calibration lamp on?",
		)

		self.calMirror = keyVarFact(
			keyword = "Mirror",
			converters = RO.CnvUtil.asBool,
			nval = 1,
			description = "Calib mirror in place?",
		)
		
		# the following items are for experts only
		
		self.ccdFocus = keyVarFact(
			keyword = "CCDFcs",
			converters = RO.CnvUtil.asInt,
			description = "CCD focus (experts only)",
		)
		
		self.slitFocus = keyVarFact(
			keyword = "SlitFcs",
			converters = RO.CnvUtil.asInt,
			description = "Slit focus (experts only)",
		)
		
		self.tipMotor = keyVarFact(
			keyword = "TipMtr",
			converters = RO.CnvUtil.asInt,
			description = "Tip motor position (experts only)",
		)
		
		self.tiltMotor = keyVarFact(
			keyword = "TiltMtr",
			converters = RO.CnvUtil.asInt,
			description = "Tilt motor position (experts only)",
		)
		
		keyVarFact.setKeysRefreshCmd()
		

	def updCalFilterName(self, filtID, isCurrent, **kargs):
		"""Update filterName based on filterID.
		"""
		if filtID != None:
			listInd = filtID - 1
			try:
				filtName = _CalFiltNames[listInd]
			except IndexError:
				filtName = "Unknown"
			self.filterName.set((filtName,), isCurrent)
		elif not isCurrent:
			self.filterName.setNotCurrent()
	
	def updGCFilterName(self, filtID, isCurrent, **kargs):
		"""Update gcFilterName based on gcFilterID.
		"""
		if filtID != None:
			listInd = filtID - 1
			try:
				filtName = _GCFiltNames[listInd]
			except IndexError:
				filtName = "Unknown"
			self.gcFilterName.set((filtName,), isCurrent)
		elif not isCurrent:
			self.gcFilterName.setNotCurrent()


if __name__ == "__main__":
	getModel()
