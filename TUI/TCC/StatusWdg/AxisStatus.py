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
"""
import Tkinter
import RO.Constants
import RO.Alg
import RO.BitDescr
import RO.StringUtil
import RO.Wdg
import TUI.PlaySound
import TUI.TCC.TCCModel

ErrorBits = (
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
	(11, 'Stop switch'),
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
# state change sound info for states: halt, track and slew;
# data is: (state chars, sound play function)
_StateCharsSound = (
	(('x','h'), TUI.PlaySound.axisHalt),
	(('t',), TUI.PlaySound.axisTrack),
	(('s',), TUI.PlaySound.axisSlew),
)

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
		self.oldStateStr = None

		# magic numbers
		PosPrec = 1	# number of digits past decimal point
		PosWidth = 5 + PosPrec	# assumes -999.99... degrees is longest field
		TCCStatusWidth = 9
		CtrlStatusWidth = 25
		AxisErrCodeWidth = 13

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
		
		# set this flag based on keyword TCCStatus;
		# if it goes false, set tccStatus and ctrlStatus rotator components null and valid
		self.rotExists = True  # assume it exists to start

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
		self.tccStatusWdgSet = [
			RO.Wdg.StrLabel(self,
				width=TCCStatusWidth,
				helpText = "What the TCC is telling the axis to do",
				helpURL=_HelpPrefix+"AxisTCCStatus",
				anchor = "nw",
			)
			for ind in self.axisInd
		]
		self.tccModel.tccStatus.addIndexedCallback(self.setTCCStateStr)
		
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
					self.tccStatusWdgSet[ind],
					self.axisErrCodeWdgSet[ind],
					self.ctrlStatusWdgSet[ind],
				)
			)
			nextCol = wdgSet.nextCol


		# allow the last column to grow to fill the available space
		self.columnconfigure(nextCol, weight=1)
	
	def setCtrlStatus(self, ind, statusWord, isCurrent=True, keyVar=None, *args):
		# print "setCtrlStatus called with ind, statusWord, isCurrent=", ind, statusWord, isCurrent
		ctrlStatusWdg = self.ctrlStatusWdgSet[ind]
		if ind == 2 and not self.rotExists:
			# rotator does not exist; this is handled by setTCCStateStr
			return

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
	

	def setTCCStateStr(self, stateStr, isCurrent, keyVar):
		# print "setTCCStateStr called with stateStr, isCurrent=", stateStr, isCurrent
		if stateStr:
			if len(stateStr) != len(self.axisInd):
				raise RuntimeError, "Invalid length for TCCStatus first string: ", stateStr

			stateStr = stateStr.lower()
	
			# if rotator does not exist, clear controller status
			self.rotExists = (stateStr[2] != "-")
			if not self.rotExists:
				self.rotExists = False
				self.ctrlStatusWdgSet[2].set("", severity=RO.Constants.sevNormal)
			
			# set displayed state strings
			for ind in self.axisInd:
				newChar = stateStr[ind]
				msg, severity = _StateDict.get(newChar, ("Unknown", RO.Constants.sevWarning))
				wdg = self.tccStatusWdgSet[ind]
				wdg.set(msg, severity=severity)
				
			# clear ctrlStatus if needed
			if self.ctrlStatusState >= 0:
				self.ctrlStatusState -= 1
				if self.ctrlStatusState < 0:
					# print "clearing status"
					for wdg in self.tccModel.ctrlStatusSet:
						wdg.set((0.0, 0.0, 0.0, 0))
			
			# if state has changed, play sounds appropriately
			if self.oldStateStr:
				# we know old state, so we know if state has changed
				for stateChars, soundFunc in _StateCharsSound:
					for axisInd in self.axisInd:
						newChar = stateStr[axisInd]
						oldChar = self.oldStateStr[axisInd]
						if newChar in stateChars \
							and oldChar not in stateChars:
							# state has changed; play the sound
							soundFunc()
							break
			
		# record new state (even if null)
		self.oldStateStr = stateStr

			
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
		
