#!/usr/local/bin/python
"""Display a slew countdown timer
(and, eventually, also trigger blink or some other indicator in certain
text fields such as net position).

Relevant keywords are:
SlewDuration: indicates a slew has begun
SlewEnd
SlewSuperseded

Warnings:
- It is possible for slewSuperceded to arrive after slewDuration for the next slew.
On the other hand, it doesn't appear necessary to use that keyword.
- It may also be possible for SlewEnd to appear before SlewBegin,
but I doubt that. If it proves so, check command IDs.
- Status may return TTT shortly after a slew has started. It is good to
look for T (as a safety measure) but be careful to ignore it if too close to slew start.

To do:
- Compute the bar length based on the available space this should be an option
to add to ProgressBar itself -- if length is None then compute it based on
the size of the containing frame).

History:
2002-03-15 R Owen: modified to reuse the existing progress bar.
2002-06-11 R Owen: bug fix: if one slew superseded another, the 2nd progress bar
	halted very early because SlewSuperceded (sic) for the old slew
	comes after SlewDuration for the new slow
2002-11-25 R Owen: changed actor from "TCC" to "tcc".
2003-03-05 ROwen	Modified to use simplified KeyVariables without isValid.
2003-03-26 ROwen	Modified to use the tcc model.
2003-04-28 ROwen	Added sound cue for end of slew.
2003-05-08 ROwen	Modified to use RO.CnvUtil.
2003-05-28 ROwen	Moved slew duration and slew end vars to TCCModel.
2003-06-09 ROwen	Removed dispatcher arg; made countdown more reliable by having
					a time limit before status=T ends the timer
					and printing a warning when it does.
2003-06-25 ROwen	Modified test case (rather crudely) to handle message data as a dict
2003-11-17 ROwen	Modified to use TUI.PlaySound.
2004-05-21 ROwen	Bug fix: do not start timer unless slewDuration is current.
2005-08-02 ROwen	Modified for TUI.Sounds->TUI.PlaySound.
2006-02-21 ROwen	Fix PR 358: stop timer when SlewSuperseded seen.
2006-03-06 ROwen	Modified to use tccModel.axisCmdState instead of tccStatus
					to make sure the timer is halted.
"""
import sys
import time
import Tkinter
import RO.CnvUtil
import RO.KeyVariable
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.PlaySound

class SlewStatusWdg(Tkinter.Frame):
	def __init__ (self,
		master = None,
	**kargs):
		"""Displays a slew progress bar

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		self.model = TUI.TCC.TCCModel.getModel()
		self.cmdID = None  # command ID of slew being counted down
		self.startTime = None
		
		self.progBar = RO.Wdg.TimeBar(
			   master = self,
			   valueFormat = "%3.0f sec",
			   barThick = 10,
			   isHorizontal = False,
			   label = "Slewing",
			   autoStop = True,
			   countUp = False,
			)
		self.progBarVisible = False
		
		self.model.slewDuration.addIndexedCallback(self.doSlewDuration, ind=0)
		
		self.model.slewEnd.addCallback(self.doSlewEnd)
		
		self.model.slewSuperseded.addCallback(self.doSlewEnd)
				
		self.model.axisCmdState.addCallback(self.setAxisCmdState)

	def doSlewDuration(self, slewDuration, isCurrent=True, **kargs):
		"""Call when keyword SlewDuration seen; starts the slew indicator"""
		# print "SlewStatus.doSlewDuration called with duration, isCurrent=", slewDuration, isCurrent
		if slewDuration:
			if isCurrent:
				self.startTime = time.time()
				self.progBar.start(newMax = slewDuration)
				self.progBar.pack(expand=True, fill="y")
				self.progBarVisible = True
		else:
			self.doSlewEnd(isCurrent = isCurrent)

	def doSlewEnd(self, junk=None, isCurrent=True, **kargs):
		"""Call to end the slew indicator"""
		# print "SlewStatus.doSlewEnd called"
		if self.progBarVisible:
			self.progBarVisible = False
			self.progBar.clear()  # halt time updates
			self.progBar.pack_forget()	# remove from display
			
#	def checkTCCStatus(self, statusStr, isCurrent=True, **kargs):
#		if self.progBarVisible and isCurrent:
#			statusStr = statusStr.lower()
#			if ('s' not in statusStr) and (time.time() > self.startTime + 5):
#				sys.stderr.write("Warning: halting countdown timer due to T in status, no SlewEnd keyword?\n")
#				self.doSlewEnd(isCurrent = isCurrent)

	def setAxisCmdState(self, axisCmdState, isCurrent=True, **kargs):
		"""Read axis commanded state.
		If drifting, start timer in unknown state.
		If tracking, halt timer.
		"""
		if not isCurrent:
			self.doSlewEnd()
			return
			
		isDrifting = False
		isSlewing = False
		for cmdState in axisCmdState:
			cmdState = cmdState.lower()
			if cmdState == "drifting":
				isDrifting = True
			elif cmdState == "slewing":
				isSlewing = True
			
		if isSlewing:
			return
		elif isDrifting:
			self.progBar.setUnknown()
			self.progBar.pack(expand=True, fill="y")
			self.progBarVisible = True
		elif self.progBarVisible == True:
			sys.stderr.write("Warning: halting countdown timer due to AxisCmdState\n")
			self.doSlewEnd()

if __name__ == "__main__":
	import TUI.TUIModel

	root = RO.Wdg.PythonTk()
	
	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = SlewStatusWdg (root)
	testFrame.pack()

	dtimeDataList = [
		(1,  (("SlewDuration", (10.0,)), )),
		(1,  (("TCCStatus", ("TTT", "NNN")), )),
		(2,  (("TCCStatus", ("SSS", "NNN")), )),
		(2,  (("TCCStatus", ("SSS", "NNN")), )),
		(3,  (("SlewDuration", (5.0,)), )),
		(2,  (("SlewDuration", (0.0,)), )),
		(6, (("SlewDuration", (4.0,)), )),
		(1,  (("TCCStatus", ("TTT", "NNN")), )),
		(6, (("SlewDuration", (4.0,)), )),
		(5,  (("SlewEnd", ()), )),
	]
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":None}

	def dispatchNext():
		global dtimeDataList
		dtime, dataList = dtimeDataList.pop(0)
		msgDict["data"] = dict(dataList)
		print "dispatching:", msgDict
		kd.dispatch(msgDict)
		if dtimeDataList:
			print "waiting", dtime, "seconds"
			root.after(int(dtime * 1000), dispatchNext)
		else:
			print "done"
	
	dispatchNext()

	root.mainloop()
		
