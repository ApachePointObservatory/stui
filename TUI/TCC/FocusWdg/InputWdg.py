#!/usr/local/bin/python
"""Secondary mirror focus widget.

History:
2004-01-09 ROwen	first draft
"""
import Tkinter
import RO.CnvUtil
import RO.InputCont
import RO.StringUtil
import RO.Wdg
import TUI.TCC.TCCModel

_HelpPrefix = "Telescope/FocusWin.html#"
_MaxFocus = 9999 # microns; this is a bit larger than the current total range of the secondary, hence a bit more than twice what it needs to be

class InputWdg(RO.Wdg.InputContFrame):
	def __init__ (self,
		master = None,
	 **kargs):
		"""creates a new widget for specifying simple offsets

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		self.tccModel = TUI.TCC.TCCModel.getModel()
		gr = RO.Wdg.StatusConfigGridder(self)
		
		# focus display and focus entry
		self.currFocus = RO.Wdg.FloatLabel(
			master = self,
			formatStr = "%.1f",
			width = len(str(_MaxFocus)) + 3, # 3 is for "-.x"
			helpText = "Current sec focus",
			helpURL = _HelpPrefix + "Focus",
		)
		self.tccModel.secFocus.addROWdg(self.currFocus)
		
		self.reqFocus = RO.Wdg.FloatEntry(
			master = self,
			defFormat = "%.1f",
			minValue = -_MaxFocus,
			maxValue =  _MaxFocus,
			helpText = "Requested sec focus",
			helpURL = _HelpPrefix + "Focus",
			defMenu = "Current",
		)
		self.tccModel.secFocus.addROWdg(self.reqFocus, setDefault=True)

		gr.gridWdg(
			label = "Focus",
			dataWdg = self.currFocus,
			cfgWdg = self.reqFocus,
			units = RO.StringUtil.MuStr + "m",
			defMenu = "Current",
		)
		
		# mirror motion timer
		self.timerWdg = RO.Wdg.TimeBar(
			master = self,
			autoStop = True,
			helpText = "Estimated move time",
			helpURL = _HelpPrefix + "TimerWdg",
		)
		
		# decrement and increment buttons
		butFrame = Tkinter.Frame(master=self)
		butWdg = []
		butWdg.append(RO.Wdg.Button(
			master = butFrame,
			text = "-50",
			helpText = "Subtract 50 from requested value",
			helpURL = _HelpPrefix + "IncrWdg",
			callFunc = self.doIncr,
		))
		butWdg.append(RO.Wdg.Button(
			master = butFrame,
			text = "+50",
			helpText = "Add 50 to requested value",
			helpURL = _HelpPrefix + "IncrWdg",
			callFunc = self.doIncr,
		))
		for wdg in butWdg:
			wdg.pack(side="left")
		gr.gridWdg(
			label = False,
			dataWdg = self.timerWdg,
			units = False,
			sticky="ew",
			colSpan = 3,
			changed = None,
			cfgWdg = butFrame,
			cfgColSpan = 3,
		)
		self.timerWdg.grid_remove()
	
		self.inputCont = RO.InputCont.WdgCont (
			name = "focus",
			wdgs = self.reqFocus,
			omitDef = False,
			formatFunc = RO.InputCont.BasicFmt(
				begStr = "set ",
				nameSep = "=",				
			),
		)
		
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


		# initialize display
		self.restoreDefault()
	
	def incrReqFocus(self, incr=0.0):
		"""Increments the requested focus by the specified amount."""
		currReq = self.reqFocus.getNum()
		self.reqFocus.set(currReq + incr)
	
	def doIncr(self, wdg):
		incr = float(wdg["text"])
		self.incrReqFocus(incr)

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
	import TUI.TUIModel

	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = InputWdg(root)
	testFrame.pack(anchor="nw")

	dataDict = {
		"secfocus": (325,),
		"seccmdmount": (100, 100, 100),
		"cmddtime": (5,),
	}
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
	kd.dispatch(msgDict)
	
	def doPrint():
		print testFrame.getString()

	buttonFrame = Tkinter.Frame(root)
	Tkinter.Button (buttonFrame, command=doPrint, text="Print").pack(side="left")
	buttonFrame.pack()

	root.mainloop()
