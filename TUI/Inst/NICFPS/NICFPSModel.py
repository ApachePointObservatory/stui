#!/usr/local/bin/python
"""An object that models the current state of NICFPS.

It contains instance variables that are KeyVariables
or sets of KeyVariables. Most of these are directly associated
with status keywords and a few are ones that I generate.

Thus it is relatively easy to get the current value of a parameter
and it is trivial to register callbacks for when values change
or register ROWdg widgets to automatically display updating values.

To Do:
- add keywords needed for overall status (there may be a status word or string coming)

2004-09-08 ROwen	mostly complete; still need some status stuff
2004-09-23 ROwen	Modified to allow callNow as the default for keyVars.
2004-11-12 ROwen	Added (uncommented) fpZ and added pressure.
2004-11-15 ROwen	Fixed doc. of temperatures: units are K, not C.
2004-11-29 ROwen	Stopped looking for fp_rtime, fp_actzw, fp_deszw and
					commented out fpRTime, fpActZW, fpDesZW, fpZWLim.
					Bug fix: fpZ had allowRefresh=False.
"""
__all__ = ["getModel"]
import RO.CnvUtil
import RO.Wdg
import RO.KeyVariable
import TUI.TUIModel

# reasonable time for fairly fast commands
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
		self.actor = "nicfps"
		self.dispatcher = tuiModel.dispatcher
		self.timelim = _TimeLim
		
		# filter keywords

		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			converters = str,
			nval = 1,
			dispatcher = self.dispatcher,
		)
		
		self.filter = keyVarFact(
			keyword = "filter_done",
			description = "Name of current filter",
		)
		
		self.filterNames = keyVarFact(
			keyword = "filter_names",
			nval = [1,None],
			description = "Names of available filters",
		)
		
		self.filterTime  = keyVarFact(
			keyword = "filter_ttc",
			converters = RO.CnvUtil.asInt,
			description = "Expected time to completion of filter move (sec)",
			allowRefresh = False,
		)
		
#		self.filterMoving  = keyVarFact(
#			keyword = "filter_moving",
#			converters = RO.CnvUtil.asBool,
#			description = "True if filter change occurring, False otherwise",
#		)

#		self.filterPos = keyVarFact(
#			keyword = "filter_pos",
#			nval = 3,
#			converters = int,
#			description = "Position of each filter wheel",
#		)
		
		# Fabry-Perot etalon

		self.fpOPath = keyVarFact(
			keyword = "fp_opath",
			description = "Is the Fabry-Perot 'In' or 'Out' of the beam?",
		)
		
		self.fpTime = keyVarFact(
			keyword = "fp_ttc",
			converters = RO.CnvUtil.asInt,
			description = "Expected time to completion of Fabry-Perot move (sec)",
			allowRefresh = False,
		)
		
#		self.fpActZW = keyVarFact(
#			keyword = "fp_zw",
#			converters = RO.CnvUtil.asFloatOrNone,
#			description = "Actual Z spacing of Fabry-Perot Z, in um",
#		)
#		
#		self.fpDesZW = keyVarFact(
#			keyword = "fp_deszw",
#			converters = RO.CnvUtil.asFloatOrNone,
#			description = "Desired Z spacing of Fabry-Perot, in um",
#		)
		
		self.fpMode = keyVarFact(
			keyword = "fp_mode",
			description = "Mode of Fabry-Perot: operate or balance",
		)
		
#		self.fpWaveCal = keyVarFact(
#			keyword = "fp_wavecal",
#			nval = 2,
#			converters = RO.CnvUtil.asFloat,
#			description = "Fabry-Perot Z wavelength conversion coefficients Z (um) = coef0 + coef1 * Z (steps)",
#		)
	
#		self.fpZWLim = keyVarFact(
#			keyword = "fp_zwlim",
#			nval = 2,
#			converters = RO.CnvUtil.asFloat,
#			description = "Min and max ZW for Fabry-Perot (um)",
#			isLocal = True,
#		)
		
		self.fpZ = keyVarFact(
			keyword = "fp_z",
			converters = RO.CnvUtil.asIntOrNone,
			description = "Fabry-Perot Z spacing in steps",
		)

#		self.fpMoving = keyVarFact(
#			keyword = "fp_moving",
#			converters = RO.CnvUtil.asBool,
#			description = "True if Fabry-Perot moving, False otherwise",
#		)

#		self.fpRTime = keyVarFact(
#			keyword = "fp_rtime",
#			converters = RO.CnvUtil.asFloatOrNone,
#			description = "Response time of Fabry-Perot Z, in sec",
#		)
		
		# mimimum and maximum value for X and Y parellelism and Z spacing (steps)
		# warning: a constant, not a keyword variable
		self.fpXYZLimConst = [-2048, 2047]

		self.fpX = keyVarFact(
			keyword = "fp_x",
			converters = RO.CnvUtil.asIntOrNone,
			description = "X parallelism of Fabry-Perot Z, in steps",
		)

		self.fpY = keyVarFact(
			keyword = "fp_y",
			converters = RO.CnvUtil.asIntOrNone,
			description = "Y parallelism of Fabry-Perot Z, in steps",
		)
		
		# pressure sensor
		
		self.press = keyVarFact(
			keyword = "pressure",
			converters = RO.CnvUtil.asFloatOrNone,
			nval = [1,None],
			description = "Pressure (torr)",
		)
		
		self.pressMax = keyVarFact(
			keyword = "pressure_max",
			converters = RO.CnvUtil.asFloatOrNone,
			nval = [1,None],
			description = "Maximum allowed pressure (torr)",
		)

		# thermal sensors
		# make sure temp (current temperatures) are listed last
		# so the names and limits are fetched first
		
		self.tempNames = keyVarFact(
			keyword = "temp_names",
			nval = [1,None],
			description = "Names of thermal sensors",
		)
		
		self.tempMin = keyVarFact(
			keyword = "temp_min",
			converters = RO.CnvUtil.asFloatOrNone,
			nval = [1,None],
			description = "Minimum safe temperatures (K; same order as tempNames)",
		)
		
		self.tempMax = keyVarFact(
			keyword = "temp_max",
			converters = RO.CnvUtil.asFloatOrNone,
			nval = [1,None],
			description = "Maximum safe temperatures (K; same order as tempNames)",
		)
		
		self.temp = keyVarFact(
			keyword = "temp",
			converters = RO.CnvUtil.asFloatOrNone,
			nval = [1,None],
			description = "Temperatures (K; same order as tempNames)",
		)
		
		keyVarFact.setKeysRefreshCmd()
		
		# add callbacks that deal with multiple keyVars
#		self.fpWaveCal.addCallback(self._setFPZWLim)

	def _setFPZWLim(self, zeroAndScale, isCurrent, keyVar=None):
		"""Compute fpZWLim based on fwWaveCal"""
		if not isCurrent:
			self.fpZWLim.setNotCurrent()
			return
		
		zeroPoint, scale = zeroAndScale
		zwLim = [zeroPoint + (scale * limSteps) for limSteps in self.fpXYZLimConst]
		self.fpZWLim.set(zwLim)


if __name__ == "__main__":
	getModel()
