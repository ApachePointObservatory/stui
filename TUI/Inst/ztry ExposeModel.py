#!/usr/local/bin/python
"""Model for exposures (data from the expose command).
A different model is required for each instrument,
but there are only a few minor differences.

Notes:
- At this time, nextPath is the only keyword reliably returned by keys for <inst>Expose. Thus it is the only keyword with a refresh command. Fix this when the expose command is fixed.

2003-07-16 ROwen
2003-07-25 ROwen	Added expState, seqState, nFiles
2003-07-30 ROwen	Added inst-specific info and getModel
2003-10-01 ROwen	Modified to use new versions of seqState and expState (for new hub).
2003-10-06 ROwen	Modified to use new versions of files and nextPath (for new hub).
2003-10-10 ROwen	Modified actor to match change in hub expose.
2003-10-16 ROwen	Bug fix: some refresh commands had not been updated for the new hub.
2003-10-22 ROwen	Bug fix: GRIM min exposure time is >1.21, not >=1.21 sec,
					so I set the lower limit to 1.22.
2003-12-17 ROwen	Modified to use KeyVariable.KeyVarFactory
					and to take advantage of key variables now
					auto-setting nval if a set of converters is supplied.
2004-01-06 ROwen	Modified to use KeyVarFactory.setKeysRefreshCmd.
"""
import RO.CnvUtil
import RO.KeyVariable
import TUI.TUIModel

class _ExpInfo:
	"""Exposure information for a camera
	
	Inputs:
	- min/maxExpTime: minimum and maximum exposure time (sec)
	- camNames: name of each camera (if more than one)
	- expTypes: types of exposures supported
	"""
	def __init__(self,
		minExpTime = 0.1,
		maxExpTime = 12 * 3600,
		camNames = None,
		expTypes = ("object", "flat", "dark", "bias"),
	):
		self.minExpTime = minExpTime
		self.maxExpTime = maxExpTime
		if camNames == None:
			camNames = ("",)
		self.camNames = camNames
		self.expTypes = expTypes
	
	def getNumCameras(self):
		return len(self.camNames)

# dictionary of instrument information
# instrument names should be lowercase
_InstInfoDict = {
	"dis": _ExpInfo(
		minExpTime = 1, 
		camNames = ("blue", "red"),
	),
	"grim": _ExpInfo(
		minExpTime = 1.22, 
		expTypes = ("object", "flat", "dark"),
	),
	"echelle": _ExpInfo(
	),
}

# cache of instrument exposure models
# each entry is instName: model
_modelDict = {}

def getModel(instName):
	global _modelDict
	instNameLow = instName.lower()
	model = _modelDict.get(instNameLow)
	if model == None:
		model = Model(instName)
		_modelDict[instNameLow] = model
	return model

class Model (object):
	def __init__(self, instName):
		self.instName = instName
		self.instNameLow = instName.lower()
		self.actor = "%sExpose" % self.instNameLow

		self.instInfo = _InstInfoDict[self.instNameLow]
		
		tuiModel = TUI.TUIModel.getModel()
		self.dispatcher = tuiModel.dispatcher
		
		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			dispatcher = self.dispatcher,
			converters = str,
		)

		self.exposeTxt = keyVarFact(
			keyword="exposeTxt",
			description="progress report for current sequence",
		)

		self.expState = keyVarFact(
			keyword = self.instNameLow + "ExpState",
			converters = (str, str, str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asFloatOrNone),
			description = """current exposure info:
			- cmdr (progID.username)
			- exposure state (e.g. flushing, reading...)
			- start time (an ANSI-format UTC timestamp)
			- remaining time for this state (sec; 0 if short or unknown)
			- total time for this state (sec; 0 if short or unknown)
			""",
		)

		self.files = keyVarFact(
			keyword = self.instNameLow + "Files",
			nval = 5 + self.instInfo.getNumCameras(),
			description = """file(s) just saved:
			- cmdr (progID.username)
			- host
			- common root directory
			- program subdirectory
			- user subdirectory
			- file name(s) for most recent exposure
			
			The full path to a file is the concatenation of common root, program subdir, user subdir and file name.
			If a file in a multi-file instrument is not saved,
			the missing file name is "None"
			""",
		)
		
		self.nextPath = keyVarFact(
			keyword = self.instNameLow + "NextPath",
			nval = 5,
			description = """default file settings (used for the next exposure):
			- cmdr (progID.username)
			- user subdirectory
			- file name prefix
			- sequence number (with leading zeros)
			- file name suffix
			""",
		)
		
		self.seqState = keyVarFact(
			keyword = self.instNameLow + "SeqState",
			converters = (str, str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asInt, RO.CnvUtil.asInt, str),
			description = """current sequence info:
			- cmdr (progID.username)
			- exposure type
			- exposure duration
			- exposure number
			- number of exposures requested
			- sequence status (a short string)
			""",
		)

		keyVarFact.setKeysRefreshCmd()


if __name__ == "__main__":
	getModel("DIS")
	getModel("Grim")
	getModel("Echelle")
