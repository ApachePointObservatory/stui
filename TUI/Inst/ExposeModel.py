#!/usr/local/bin/python
"""Model for exposures (data from the expose command).
A different model is required for each instrument,
but there are only a few minor differences.

Notes:
- At this time, nextPath is the only keyword reliably returned by keys for <inst>Expose.
  Thus it is the only keyword with a refresh command.
  Fix this when the expose command is fixed.

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
2004-08-27 ROwen	Added new <inst>NewFiles keyword.
2004-09-10 ROwen	Moved auto ftp code here from ExposeInputWdg.
					Added several ftp-related entries.
					Added formatExpCmd (to make scripting easier).
					Replaced model.dispatcher with model.tuiModel.
					Added __all__ to improve "from ExposeModel import *".
2004-09-28 ROwen	Added comment entry.
2004-10-19 ROwen	Added nicfps to _InstInfoDict.
2004-11-16 ROwen	Modified to explicitly ask for binary ftp
					(instead of relying on the ftp server to be smart).
"""
__all__ = ['getModel']

import os
import RO.CnvUtil
import RO.KeyVariable
import RO.StringUtil
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
	"nicfps": _ExpInfo(
		minExpTime = 3.25, 
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
		
		self.tuiModel = TUI.TUIModel.getModel()
		
		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = self.actor,
			dispatcher = self.tuiModel.dispatcher,
			converters = str,
			allowRefresh = False,
		)

		self.exposeTxt = keyVarFact(
			keyword="exposeTxt",
			description="progress report for current sequence",
			allowRefresh = False,
		)

		self.expState = keyVarFact(
			keyword = self.instName + "ExpState",
			converters = (str, str, str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asFloatOrNone),
			description = """current exposure info:
			- cmdr (progID.username)
			- exposure state (e.g. flushing, reading...)
			- start time (an ANSI-format UTC timestamp)
			- remaining time for this state (sec; 0 if short or unknown)
			- total time for this state (sec; 0 if short or unknown)
			""",
			allowRefresh = False, # change to True if/when <inst>Expose always outputs it with status
		)

		self.files = keyVarFact(
			keyword = self.instName + "Files",
			nval = 5 + self.instInfo.getNumCameras(),
			description = """file(s) just saved:
			- cmdr (progID.username)
			- host
			- common root directory
			- program and date subdirectory
			- user subdirectory
			- file name(s)
			
			This keyword is only output when a file is saved.
			It is not output as a result of status.
			
			The full path to a file is the concatenation of common root, program subdir, user subdir and file name.
			If a file in a multi-file instrument is not saved,
			the missing file name is omitted (but the comma remains).
			""",
			allowRefresh = False,
		)

		self.newFiles = keyVarFact(
			keyword = self.instName + "NewFiles",
			nval = 5 + self.instInfo.getNumCameras(),
			description = """file(s) that will be saved at the end of the current exposure:
			- cmdr (progID.username)
			- host
			- common root directory
			- program and date subdirectory
			- user subdirectory
			- file name(s)
			
			The full path to a file is the concatenation of common root, program subdir, user subdir and file name.
			If a file in a multi-file instrument is not saved,
			the missing file name is omitted (but the comma remains).
			""",
			allowRefresh = False, # change to True if/when <inst>Expose always outputs it with status
		)

		self.nextPath = keyVarFact(
			keyword = self.instName + "NextPath",
			nval = 5,
			description = """default file settings (used for the next exposure):
			- cmdr (progID.username)
			- user subdirectory
			- file name prefix
			- sequence number (with leading zeros)
			- file name suffix
			""",
			allowRefresh = True,
		)
		
		self.seqState = keyVarFact(
			keyword = self.instName + "SeqState",
			converters = (str, str, RO.CnvUtil.asFloatOrNone, RO.CnvUtil.asInt, RO.CnvUtil.asInt, str),
			description = """current sequence info:
			- cmdr (progID.username)
			- exposure type
			- exposure duration
			- exposure number
			- number of exposures requested
			- sequence status (a short string)
			""",
			allowRefresh = False, # change to True if/when <inst>Expose always outputs it with status
		)
		
		self.comment = keyVarFact(
			keyword = "comment",
			converters = str,
			description = "comment string",
			allowRefresh = False, # change to True if/when <inst>Expose always outputs it with status
		)
		
		keyVarFact.setKeysRefreshCmd(getAllKeys=True)
		
		# preferences and widget for sequencing and auto ftp
		
		self.seqByFilePref = self.tuiModel.prefs.getPrefVar("Seq By File")

		self.autoFTPPref = self.tuiModel.prefs.getPrefVar("Auto FTP")
		self.getCollabPref = self.tuiModel.prefs.getPrefVar("Get Collab")
		self.ftpSaveToPref = self.tuiModel.prefs.getPrefVar("Save To")
		
		ftpTL = self.tuiModel.tlSet.getToplevel("TUI.FTP Log")
		self.ftpLogWdg = ftpTL and ftpTL.getWdg()
		
		self.canAutoFTP =  None not in (self.autoFTPPref, self.getCollabPref, self.ftpSaveToPref, self.ftpLogWdg)
		if self.canAutoFTP:
			# set up automatic ftp; we have all the info we need
			self.files.addCallback(self._filesCallback)

	def _filesCallback(self, fileInfo, isCurrent, keyVar):
		"""Called whenever a file is written
		to start an ftp download (if appropriate).
		
		fileInfo consists of:
		- cmdr (progID.username)
		- host
		- common root directory
		- program and date subdirectory
		- user subdirectory
		- file name(s) for most recent exposure
		"""
		if not isCurrent:
			return
#		print "_filesCallback(%r, %r)" % (fileInfo, isCurrent)
		if not self.canAutoFTP:
			return
		if not self.autoFTPPref.getValue():
			return
		if not keyVar.isGenuine():
			# cached; avoid redownloading
			return
		
		cmdr, host, fromRootDir, progDir, userDir = fileInfo[0:5]
		progID, username = cmdr.split(".")
		fileNames = [fname for fname in fileInfo[5:] if fname != "None"]

		if progID != self.tuiModel.getProgID():
			# files are for a different program; ignore them
			return
		if not self.getCollabPref.getValue() and username != self.tuiModel.getUsername():
			# files are for a collaborator and we don't want those
			return
		
		toRootDir = self.ftpSaveToPref.getValue()

		# save in userDir subdirectory of ftp directory
		for fileName in fileNames:
			fromPath = "".join((host, fromRootDir, progDir, userDir, fileName))
			fromURL = "ftp://images:7nights.@%s;type=i" % (fromPath,)
			fromDisplayPath = "".join((progDir, userDir, fileName))
			
			toPath = os.path.join(toRootDir, progDir, userDir, fileName)
			
			self.ftpLogWdg.getFile(
				fromURL = fromURL,
				toPath = toPath,
				overwrite = False,
				createDir = True,
				dispURL = fromDisplayPath,
			)

	def formatExpCmd(self,
		expType = "object",
		expTime = None,
		cameras = None,
		fileName = "",
		numExp = 1,
		startNum = None,
		totNum = None,
		comment = None,
	):
		"""Format an exposure command.
		Raise ValueError or TypeError for invalid inputs.
		"""
		outStrList = []
		
		expType = expType.lower()
		if expType not in self.instInfo.expTypes:
			raise ValueError("unknown exposure type %r" % (expType,))
		outStrList.append(expType)
		
		if expType.lower() != "bias":
			if not expTime:
				raise ValueError("exposure time required")
			outStrList.append("time=%.2f" % (expTime))
		
		if cameras != None:
			camList = RO.SeqUtil.asSequence(cameras)
			for cam in camList:
				cam = cam.lower()
				if cam not in self.instInfo.camNames:
					raise ValueError("unknown camera %r" % (cam,))
				outStrList.append(cam)
	
		outStrList.append("n=%d" % (numExp,))

		if not fileName:
			raise ValueError("file name required")
		outStrList.append("name=%s" % (fileName,))
			
		if self.seqByFilePref.getValue():
			outStrList.append("seq=nextByFile")
		
		if startNum != None:
			outStrList.append("startNum=%d" % (startNum,))
		
		if totNum != None:
			outStrList.append("totNum=%d" % (totNum,))
		
		if comment != None:
			outStrList.append("comment=%s" % (RO.StringUtil.quoteStr(comment),))
	
		return " ".join(outStrList)


if __name__ == "__main__":
	getModel("DIS")
	getModel("Grim")
	getModel("Echelle")
