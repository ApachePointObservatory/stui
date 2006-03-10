#!/usr/local/bin/python
"""Displays the axis position and various status.

To do: confirm that the axis ctrllr keeps running if the 1 Hz pulse is missing.

History:
2003-03-26 ROwen	Modified to use the tcc model.
2003-03-31 ROwen	Switched from RO.Wdg.LabelledWdg to RO.Wdg.Gridder
2003-06-09 Rowen	Removed dispatcher arg.
2003-06-12 ROwen	Added helpText entries.
2003-06-25 ROwen	Modified test case to handle message data as a dict.
2003-11-24 ROwen	Modified to play sounds when axis state changes.
2004-02-04 ROwen	Modified _HelpURL to match minor help reorg.
2004-08-11 ROwen	Modified for improved TCCModel.
					If axis controller status is None, displays "Not responding".
					Use modified RO.Wdg state constants with st_ prefix.
2004-09-03 ROwen	Modified for RO.Wdg.st_... -> RO.Constants.st_...
2005-01-05 ROwen	Modified for RO.Wdg.Label state->severity and RO.Constants.st_... -> sev...
2005-08-02 ROwen	Modified for TUI.Sounds->TUI.PlaySound.
2005-09-12 ROwen	Put "stop switch" near the end because it really means
					"axis controller shut itself down for some reason".
					Bug fix: used TUI.PlaySound without importing it.
2006-03-06 ROwen	Modified to use tccModel.axisCmdState and rotExists instead of tccStatus.
					Modified to play sounds in a particular order
					and with some time between them.
					Modified to hide rotator AxisErrCode when no rotator
					(and thus shown only one "NotAvailable").
					Reduced width of commanded state field by one.
"""
import Tkinter
import RO.Constants
import RO.Alg
import RO.BitDescr
import RO.StringUtil
import RO.Wdg
import TUI.PlaySound
import TUI.TCC.TCCModel
try:
	set
except NameError:
	from sets import Set as set

_SoundIntervalMS = 100 # time (ms) between the start of each sound (if more than one)

ErrorBits = (
	(11, 'Stop switch'),
	( 6, 'Hit min limit switch'),
	( 7, 'Hit max limit switch'),
	(18, 'Motor 2 current limit'),
	(19, 'Motor 1 current limit'),
	( 8, 'Low res encoder problem'),
	( 9, 'High res encoder problem'),
	(10, 'A/D converter problem'),
	(17, 'Limit switch connection problem'),
	(20, 'Servo amp 2 power loss'),
	(21, 'Servo amp 1 power loss'),
	(22, 'Motor 2 bad connection'),
	(23, 'Motor 1 bad connection'),
	( 2, 'Hit min soft pos limit'),
	( 3, 'Hit max soft pos limit'),
	(16, '1 Hz clock signal lost'),
)
WarningBits = (
	( 0, 'Motor control buffer empty'),
	( 1, 'Late position update'),
	(24, 'Pos error too large to correct'),
	( 4, 'Velocity limited'),
	( 5, 'Acceleration limited'),
)
# state dictionary:
# - keys are axis state characters,
# - values are the string to display and the severity of the axis state
_StateDict = {
	"t": ("Tracking", RO.Constants.sevNormal),
	"s": ("Slewing", RO.Constants.sevWarning),
	"h": ("Halted", RO.Constants.sevError),
	"x": ("Halted", RO.Constants.sevError),
	"-": ("Not Avail", RO.Constants.sevNormal),
}
# commanded state dictionary:
# - keys are axis commanded state keywords, cast to lowercase
# - values are the severity
_CmdStateDict = {
	"drifting": RO.Constants.sevWarning,
	"halted": RO.Constants.sevError,
	"halting": RO.Constants.sevError,
	"slewing": RO.Constants.sevWarning,
	"tracking": RO.Constants.sevNormal,
	"notavailable": RO.Constants.sevNormal,
}
		
def _getSoundData():
	"""Return a collection of sound data:
	- a dictionary of axis comanded state: (index, soundFunc)
	  where the sounds should be sorted by index before playing
	
	soundFunc is a function: call it to play the sound
	"""
	soundData = (
		(TUI.PlaySound.axisHalt, 'halted', 'halting'),
		(TUI.PlaySound.axisSlew, 'drifting', 'slewing'),
		(TUI.PlaySound.axisTrack, 'tracking'),
	)
	stateIndSoundDict = {}
	for ind in range(len(soundData)):
		item = soundData[ind]
		soundFunc = item[0]
		states = item[1:]
		for state in states:
			stateIndSoundDict[state] = (ind, soundFunc)
	return stateIndSoundDict

_StateIndSoundDict = _getSoundData()	

_HelpPrefix = "Telescope/StatusWin.html#"

def _computeBitInfo():
	"""Compute bitInfo array for RO.BitDescr module"""
	bitInfo = []
	for (bit, info) in ErrorBits:
		bitInfo.append((bit, (info, RO.Constants.sevError)))
	for (bit, info) in WarningBits:
		bitInfo.append((bit, (info, RO.Constants.sevWarning)))
	return bitInfo
_BitInfo = _computeBitInfo()

class AxisStatusWdg(Tkinter.Frame):
	def __init__ (self, master=None, **kargs):
		"""Displays information about the axes

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		self.tccModel = TUI.TCC.TCCModel.getModel()
		self.prevSounds = [None]*3 # sounds played last time we received AxisCmdState

		# magic numbers
		PosPrec = 1	# number of digits past decimal point
		PosWidth = 5 + PosPrec	# assumes -999.99... degrees is longest field
		AxisCmdStateWidth = 8
		AxisErrCodeWidth = 13
		CtrlStatusWidth = 25

		self.axisInd = range(len(self.tccModel.axisNames))
		
		# kludge to allow erasing ctrllr status if not set since last TCCStatus
		# states are:
		#  -1: ctrlStatus has been cleared
		#   0: ctrlStatus is stale
		#   1: ctrlStatus is current
		# when ctrlStatus is set, state = 1
		# when TCCStatus is set, state is checked;
		# if nonnegative then it is decremented, and if that pushes it negative
		# then ctrlStatus is cleared
		self.ctrlStatusState = -1
		
		# actual axis position widget set
		self.axePosWdgSet = [
			RO.Wdg.FloatLabel(self,
				precision = PosPrec,
				width = PosWidth,
				helpText = "Current axis position, as reported by the controller",
				helpURL = _HelpPrefix+"AxisPosition",
			)
			for ind in self.axisInd
		]
		self.tccModel.axePos.addROWdgSet(self.axePosWdgSet)
		
		# TCC status widget set (e.g. tracking or halted)
		self.axisCmdStateWdgSet = [
			RO.Wdg.StrLabel(self,
				width=AxisCmdStateWidth,
				helpText = "What the TCC is telling the axis to do",
				helpURL=_HelpPrefix+"AxisTCCStatus",
				anchor = "nw",
			)
			for ind in self.axisInd
		]
		self.tccModel.axisCmdState.addCallback(self.setAxisCmdState)
	
		self.tccModel.rotExists.addIndexedCallback(self.setRotExists)
		
		# axis error code widet set (why the TCC is not moving the axis)
		self.axisErrCodeWdgSet = [
			RO.Wdg.StrLabel(self,
				width=AxisErrCodeWidth,
				helpText = "Why the TCC halted the axis",
				helpURL=_HelpPrefix+"AxisTCCErrorCode",
				anchor = "nw",
			)
			for ind in self.axisInd
		]
		self.tccModel.axisErrCode.addROWdgSet(self.axisErrCodeWdgSet)		
	
		# controller status widget set (the status word)
		self.ctrlStatusWdgSet = [
			RO.Wdg.StrLabel(self,
				width=CtrlStatusWidth,
				helpText = "Status reported by the axis controller",
				helpURL=_HelpPrefix+"AxisCtrlStatus",
				anchor = "nw",
			)
			for ind in self.axisInd
		]
		for ind in self.axisInd:
			self.tccModel.ctrlStatusSet[ind].addIndexedCallback(
				RO.Alg.GenericCallback(self.setCtrlStatus, ind), 3)
		
				
		# grid the axis widgets
		gr = RO.Wdg.Gridder(self, sticky="w")
		for ind in self.axisInd:
			wdgSet = gr.gridWdg (
				label = self.tccModel.axisNames[ind],
				dataWdg = (
					self.axePosWdgSet[ind],
					Tkinter.Label(self, text=RO.StringUtil.DegStr),
					self.axisCmdStateWdgSet[ind],
					self.axisErrCodeWdgSet[ind],
					self.ctrlStatusWdgSet[ind],
				)
			)
			nextCol = wdgSet.nextCol
		
		# widen rotator commanded state widget
		# so there's room to display "NotAvailable"
		# (note that the error code widget will be hidden when this occurs
		# so the text will not overlap anything).
		self.axisCmdStateWdgSet[2].grid_configure(columnspan=2)


		# allow the last column to grow to fill the available space
		self.columnconfigure(nextCol, weight=1)
	
	def setAxisCmdState(self, axisCmdState, isCurrent, keyVar):
		if not isCurrent:
			for wdg in self.axisCmdStateWdgSet:
				wdg.setIsCurrent(False)
			return

		# set axis commanded state widgets
		for axis in self.axisInd:
			cmdState = axisCmdState[axis]
			severity = _CmdStateDict.get(cmdState.lower(), RO.Constants.sevError)
			self.axisCmdStateWdgSet[axis].set(cmdState, severity=severity)

		# clear ctrlStatus if needed
		if self.ctrlStatusState >= 0:
			self.ctrlStatusState -= 1
			if self.ctrlStatusState < 0:
				# print "clearing controller status"
				for wdg in self.tccModel.ctrlStatusSet:
					wdg.set((0.0, 0.0, 0.0, 0))
		
		# play sounds, if appropriate
		indSoundsToPlay = set() # add new sounds to play to a set to avoid duplicates
		for axis in self.axisInd:
			soundInd, soundFunc = _StateIndSoundDict.get(axisCmdState[axis].lower(), (0, None))
			if soundFunc and (soundFunc != self.prevSounds[axis]) and keyVar.isGenuine():
				indSoundsToPlay.add((soundInd, soundFunc))
			self.prevSounds[axis] = soundFunc
		
		if indSoundsToPlay:
			indSoundsToPlay = list(indSoundsToPlay)
			indSoundsToPlay.sort()
			soundsToPlay = list(zip(*indSoundsToPlay)[1])
			soundsToPlay.reverse() # since played from back to front
			self.playSounds(soundsToPlay)
		
	def setCtrlStatus(self, ind, statusWord, isCurrent=True, keyVar=None, *args):
		# print "setCtrlStatus called with ind, statusWord, isCurrent=", ind, statusWord, isCurrent
		if ind == 2 and not self.tccModel.rotExists[0]:
			# rotator does not exist; this is handled by setRotExists
			return

		ctrlStatusWdg = self.ctrlStatusWdgSet[ind]

		if statusWord != None:
			self.ctrlStatusState = 1
			infoList = RO.BitDescr.getDescr(_BitInfo, statusWord)
			
			# for now simply show the first status;
			# eventually provide a pop-up list showing all status bits
			if infoList:
				info, severity = infoList[0]
				ctrlStatusWdg.set(info, isCurrent, severity=severity)
			else:
				ctrlStatusWdg.set("", isCurrent, severity=RO.Constants.sevNormal)
		elif isCurrent:
			ctrlStatusWdg.set("Not responding", isCurrent, severity=RO.Constants.sevError)
		else:
			ctrlStatusWdg.setNotCurrent()
	
	def setRotExists(self, rotExists, isCurrent=True, **kargs):
		if not isCurrent:
			return
		if rotExists:
			self.axisErrCodeWdgSet[2].grid()
			self.ctrlStatusWdgSet[2].grid()
			self.ctrlStatusWdgSet[2].set("", severity=RO.Constants.sevNormal)
		else:
			self.axisErrCodeWdgSet[2].grid_remove()
			self.ctrlStatusWdgSet[2].grid_remove()
	
	def playSounds(self, sounds):
		"""Play one or more of a set of sounds,
		played in order from last to first.
		"""
		if not sounds:
			return
		soundFunc = sounds.pop(-1)
		soundFunc()
		if sounds:
			self.after(_SoundIntervalMS, self.playSounds, sounds)

			
if __name__ == "__main__":
	import time
	import TUI.TUIModel

	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher
		
	testFrame = AxisStatusWdg (root)
	testFrame.pack()

	dataSet = (
		{
			"TCCStatus": ("SSH","XXX"),
			"AxePos": (-350.999, 45, "NaN"),
		},
		{
			"AzStat": (45.0, 0.0, 4565, 0x801),
			"AltStat": (45.0, 0.0, 4565, 0x801),
		},
		{
			"TCCStatus": ("TTH","XXX"),
			"AxePos": (-350.999, 45, "NaN"),
		},
		{
			"TCCStatus": ("TTH","XXX"),
			"AxePos": (-350.999, 45, "NaN"),
		},
	)
	
	for dataDict in dataSet:
		msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
		print "dispatching data", msgDict["data"]
		kd.dispatch(msgDict)
		root.update()
		time.sleep(2.0)
	
	print "done with updates"

	root.mainloop()
		
