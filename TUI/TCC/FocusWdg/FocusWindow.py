#!/usr/local/bin/python
"""Secondary mirror focus control.

History:
2004-01-09 ROwen	first draft
2004-02-23 ROwen	Modified to play cmdDone/cmdFailed for commands.
2004-03-11 ROwen	Bug fix: assumed the secondary mirror would start moving
					within 10 seconds (a poor assumption if others are moving
					the mirror). Fixed by removing the time limit.
2004-05-18 ROwen	Eliminated redundant import in test code.
2004-06-22 ROwen	Modified for RO.Keyvariable.KeyCommand->CmdVar
2005-01-05 ROwen	Changed level to severity for RO.Wdg.StatusBar.
"""
import Tkinter
import tkSimpleDialog
import RO.Wdg
import TUI.TUIModel
import RO.StringUtil
import TUI.TCC.TCCModel

_HelpURL = "Telescope/FocusWin.html"
_MaxFocus = 9999 # microns; this is a bit larger than the current total range of the secondary, hence a bit more than twice what it needs to be

def addWindow(tlSet):
	"""Create the window for TUI.
	"""
	tlSet.createToplevel(
		name = "TCC.Secondary Focus",
		defGeom = "+240+507",
		resizable = False,
		visible = False,
		wdgFunc = SecFocusWdg,
	)

class SecFocusWdg(Tkinter.Frame):
	def __init__ (self,
		master = None,
	 **kargs):
		"""creates a new widget for specifying secondary focus

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		Tkinter.Frame.__init__(self, master, **kargs)

		self.tccModel = TUI.TCC.TCCModel.getModel()
		
		tuiModel = TUI.TUIModel.getModel()

		# current focus display
		RO.Wdg.Label(self, text="Sec Focus").grid(row=0, column=0)
		self.currFocus = RO.Wdg.FloatLabel(
			master = self,
			formatStr = "%.1f",
			width = len(str(_MaxFocus)) + 3, # 3 is for "-.x"
			helpText = "Current secondary focus",
			helpURL = _HelpURL,
		)
		self.tccModel.secFocus.addROWdg(self.currFocus)
		self.currFocus.grid(row=0, column=1)
		RO.Wdg.Label(self, text=RO.StringUtil.MuStr + "m").grid(row=0, column=2)

		self.timerWdg = RO.Wdg.TimeBar(
			master = self,
			autoStop = True,
			helpText = "Estimated move time",
			helpURL = _HelpURL,
		)
		self.timerWdg.grid(row=0, column=3, sticky="ew")
		self.timerWdg.grid_remove()
		self.grid_columnconfigure(3, weight=1)

		# set up the command monitor
		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			dispatcher = tuiModel.dispatcher,
			prefs = tuiModel.prefs,
			playCmdSounds = True,
			helpURL = _HelpURL,
		)
		self.statusBar.grid(row=2, column=0, columnspan=4, sticky="ew")
		
		# command buttons
		buttonFrame = Tkinter.Frame(self)
				
		self.setButton = RO.Wdg.Button(
			master = buttonFrame,
			text = "Set...",
			callFunc = self.doSet,
			helpText = "Set an absolute focus",
		)
		self.setButton.pack(side="left")	

		self.decreaseButton = RO.Wdg.Button(
			master=buttonFrame,
			text = "-50",
			width = 4,
			callFunc = self.doDelta,
			helpText = "Decrease focus",
			helpURL = _HelpURL,
		)
		self.decreaseButton.pack(side="left")

		self.increaseButton = RO.Wdg.Button(
			master=buttonFrame,
			text = "+50",
			width = 4,
			callFunc = self.doDelta,
			helpText = "Increase focus",
			helpURL = _HelpURL,
		)
		self.increaseButton.pack(side="left")

		self.deltaMenu = RO.Wdg.OptionMenu(
			master = buttonFrame,
			items = ("25", "50", "100"),
			defValue = "50",
			callFunc = self.doAdjIncr,
			width = 4,
			helpText = "Set focus increment",
		)
		self.deltaMenu.pack(side="left")

		buttonFrame.grid(row=4, column=0, columnspan=5)
		
		# monitor some keywords for putting up a timer	
		keyVarFact = RO.KeyVariable.KeyVarFactory(
			actor = "tcc",
			nval = 1,
			converters = RO.CnvUtil.asFloatOrNone,
			dispatcher = self.tccModel.dispatcher,
		)
		self.cmdDTimeVar = keyVarFact(
			keyword = "CmdDTime",
		)
		self.cmdDTimeVar.addIndexedCallback(self._doCmdDTime)
		self.secActMountVar = keyVarFact(
			keyword = "SecActMount",
			nval = (3, None),
		)
		self.secActMountVar.addCallback(self._doSecActMount)
	
	def doAdjIncr(self, mnu):
		incr = mnu.getString()
		self.decreaseButton["text"] = "-" + incr
		self.increaseButton["text"] = "+" + incr
		
	def doDelta(self, btn):
		"""Adjust the focus.
		"""
		deltaFocus = int(btn["text"])
		cmdStr = "set focus=%s/incr" % deltaFocus

		cmdVar = RO.KeyVariable.CmdVar (
			actor = "tcc",
			cmdStr = cmdStr,
			timeLim = 0,
			timeLimKeyword="CmdDTime",
			isRefresh = False,
		)
		self.statusBar.doCmd(cmdVar)
	
	def doSet(self, btn):
		currFocus, isCurrent = self.tccModel.secFocus.getInd(0)
		if isCurrent and currFocus != None:
			default = currFocus
		else:
			default = None

		newFocus = tkSimpleDialog.askfloat(
			title = "Set Focus",
			prompt = u"New secondary focus (%sm)" % (RO.StringUtil.MuStr,),
			initialvalue = default,
			minvalue = -_MaxFocus,
			maxvalue = _MaxFocus,
		)
		if newFocus == None:
			return
			
		cmdStr = "set focus=%s" % newFocus

		cmdVar = RO.KeyVariable.CmdVar (
			actor = "tcc",
			cmdStr = cmdStr,
			timeLim = 0,
			timeLimKeyword="CmdDTime",
			isRefresh = False,
		)
		self.statusBar.doCmd(cmdVar)

	def _doCmdDTime(self, cmdDTime, isCurrent, keyVar):
		"""Called when CmdDTime seen, to put up a timer.
		"""
		if not isCurrent:
			return
		msgDict = keyVar.getMsgDict()
		for key in msgDict["data"].keys():
			if key.lower() == "seccmdmount":
				self.timerWdg.grid()
				self.timerWdg.start(newMax = cmdDTime)
	
	def _doSecActMount(self, secActMount, isCurrent, **kargs):
		"""Called when SecActMount seen. Kill timer.
		"""
		if not isCurrent:
			return
		self.timerWdg.clear()
		self.timerWdg.grid_remove()


if __name__ == "__main__":
	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = SecFocusWdg(root)
	testFrame.pack(anchor="nw")

	dataDict = {
		"SecFocus": (325.0,),
	}
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
	kd.dispatch(msgDict)

	root.mainloop()
