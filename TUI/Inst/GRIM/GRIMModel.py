#!/usr/local/bin/python
"""An object that models the current state of GRIM.

For the most part its instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Some instance variables are dictionaries. These are only used for
constant data and all have names that end in Dict. (If it turns out
that this data can change, those instance variables will have to be changed
since KeyVariables cannot at present be dictionaries.)

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register RO.Wdg widgets to automatically display updating values.

2003-08-05 ROwen
2003-12-17 ROwen	Modified to refresh using refreshKeys and to use KeyVarFact.
2004-01-06 ROwen	Modified to use KeyVarFactory.setKeysRefreshCmd.
2004-05-18 ROwen	Stopped importing Tkinter; it wasn't used.
"""
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for status commands
_TimeLim = 80

_ModeInfo = (
	(0, "Image"),
	(4, "Image+ND  3% "),
	(5, "Image+ND 13%"),
	(6, "Image+ND 25%"),
	(1, "Spectra"),
	(2, "View slit"),
	(3, "Object grism"),
	(7, "Polarimetry"),
	(-1, "Dark"),
)
_ModeIDNameDict = RO.Alg.OrderedDict(_ModeInfo)

_ScaleInfo = (
	(1, "f/5"),
	(3, "f/10"),
	(5, "f/20"),
	(13, "f/20 short"),
	(21, "f/20 long"),
)
_ScaleIDNameDict = RO.Alg.OrderedDict(_ScaleInfo)

_FilterInfo = (
	(1, "J"),
	(2, "H"),
	(3, "K"),
	(4, "K prime"),
	(5, "K short"),
	(6, "K continuum"),
	(7, "K dark"),
	(8, "1.580 BP 0.010"),
	(9, "1.700 BP 0.050"),
	(15, "1.083um"),
	(16, "1.094um"),
	(17, "1.237um"),
	(18, "1.282um"),
	(19, "1.644um"),
	(20, "1.99um"),
	(21, "2.122um"),
	(22, "2.166um"),
	(23, "2.22um"),
	(24, "2.248um"),
	(25, "2.295um"),
	(26, "2.36um"),
	(13, "Open"),
	(0, "Blank Off"),
)
_FilterIDNameDict = RO.Alg.OrderedDict(_FilterInfo)

# for the following modes f/20 short and f/20 long are disallowed
# (they are treated as f/20)
_RestrictedModeIDs = (0, 3, 4, 5, 6)
_RestrictedModeNames = [_ModeIDNameDict[modeID] for modeID in _RestrictedModeIDs]

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
		self.actor = "grim"
		self.dispatcher = tuiModel.dispatcher
		self.timelim = _TimeLim
		
		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			converters = str,
			nval = 1,
			dispatcher = self.dispatcher,
		)			

		self.modeIDNameDict = _ModeIDNameDict
		# dict of mode id: name entries

		self.modeName = keyVarFact(
			keyword="modeName",
			description="current mode",
			isLocal = True,
		)
		
		self.modeID = keyVarFact(
			keyword="grimmode",
			converters=RO.CnvUtil.asInt,
			description="ID of current mode",
		)
		self.modeID.addIndexedCallback(self.__updmode)


		self.scaleIDNameDict = _ScaleIDNameDict
		# dict of scale id: name entries

		self.scaleName = keyVarFact(
			keyword="scaleName",
			description="current scale",
			isLocal = True,
		)
		
		self.scaleID = keyVarFact(
			keyword="grimscale",
			converters=RO.CnvUtil.asInt,
			description="ID of current scale",
		)
		self.scaleID.addIndexedCallback(self.__updscale)


		self.filterIDNameDict = _FilterIDNameDict
		# dict of filter id: name entries

		self.filterName = keyVarFact(
			keyword="filterName",
			description="current filter",
			isLocal = True,
		)
		
		self.filterID = keyVarFact(
			keyword="grimfilter",
			converters=RO.CnvUtil.asInt,
			description="ID of current filter",
		)
		self.filterID.addIndexedCallback(self.__updfilter)
		
		keyVarFact.setKeysRefreshCmd()
	
	def isRestrictedMode(self, modeName):
		"""Returns True if the scale f/20 short or f/20 long are not allowed
		for this mode.
		"""
		return modeName in _RestrictedModeNames

	def __updmode(self, modeID, isCurrent, **kargs):
		"""modeID has changed; update modeName;
		"""
		if modeID == None and not isCurrent:
			self.modeName.setNotCurrent()
			return

		modeName = self.modeIDNameDict.get(modeID, "unknown")
		self.modeName.set((modeName,), isCurrent)
	
	def __updscale(self, scaleID, isCurrent, **kargs):
		"""scaleID has changed; update scaleName;
		"""
		if scaleID == None and not isCurrent:
			self.scaleName.setNotCurrent()
			return

		scaleName = self.scaleIDNameDict.get(scaleID, "unknown")
		self.scaleName.set((scaleName,), isCurrent)
	
	def __updfilter(self, filterID, isCurrent, **kargs):
		"""filterID has changed; update filterName;
		"""
		if filterID == None and not isCurrent:
			self.filterName.setNotCurrent()
			return

		filterName = self.filterIDNameDict.get(filterID, "unknown")
		self.filterName.set((filterName,), isCurrent)


if __name__ == "__main__":
	# confirm compilation
	model = getModel()
