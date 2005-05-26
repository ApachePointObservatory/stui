#!/usr/local/bin/python
"""GCam NA2 guider window

History:
2005-05-26 ROwen
"""
import RO.InputCont
import RO.StringUtil
import RO.Wdg
import GuideWdg

_HelpURL = "Guiding/GCam.html"

_InitWdgWidth = 5

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "Guide.GCam",
		defGeom = "+452+280",
		resizable = True,
		wdgFunc = GCamWdg,
		visible = False,
	)

class GCamWdg(GuideWdg.GuideWdg):
	def __init__(self,
		master,
	**kargs):
		GuideWdg.GuideWdg.__init__(self,
			master = master,
			actor = "gcam",
		)

		# add focus and filterwheel controls to self.devSpecificFrame
		# once we have some reliable way to control them
		# (the current TCC intrface is challenging
		# because it has the concept of the current guider)
		# meanwhile...
		return
		
		fr = self.devSpecificFrame
		fr.configure(bd=2, relief="sunken")
		gr = RO.Wdg.StatusConfigGridder(fr)
		
		self.currFocusWdg = RO.Wdg.FloatLabel(
			master = fr,
			width = _InitWdgWidth,
			precision = 0,
			helpText = "Current NA2 guider focus",
			helpURL = _HelpURL,
		)
		self.userFocusWdg = RO.Wdg.OptionMenu(
			master = fr,
			items = (),
			autoIsCurrent = True,
			width = _InitWdgWidth,
			helpText = "Desired NA2 guider focus",
			helpURL = _HelpURL,
		)
		gr.gridWdg("Focus", self.currFocusWdg, RO.StringUtil.MuStr + "m", self.userFocusWdg)
		
		self.currFiltWdg = RO.Wdg.StrLabel(
			master = fr,
			width = _InitWdgWidth,
			helpText = "Current NA2 guider filter",
			helpURL = _HelpURL,
		)
		self.userFiltWdg = RO.Wdg.OptionMenu(
			master = fr,
			items = (),
			autoIsCurrent = True,
			width = _InitWdgWidth,
			helpText = "Desired NA2 guider filter",
			helpURL = _HelpURL,
		)
		gr.gridWdg("Filter", self.currFiltWdg, None, self.userFiltWdg)
		
		col = gr.getNextCol()
		nRows = gr.getNextRow()

		self.applyWdg = RO.Wdg.Button(
			master = fr,
			text = "Apply",
			callFunc = self.doApply,
			helpText = "Set NA2 guider filter",
			helpURL = _HelpURL,
		)
		self.applyWdg.setEnable(False)
		self.applyWdg.grid(row=0, column=col, rowspan=nRows)
		col += 1

		self.currWdg = RO.Wdg.Button(
			master = fr,
			text = "Current",
			callFunc = self.doCurrent,
			helpText = "Set filter control to current filter",
			helpURL = _HelpURL,
		)
		self.currWdg.setEnable(False)
		self.currWdg.grid(row=0, column=col, rowspan=nRows)
		col += 1
		
		fr.grid_columnconfigure(col, weight=1)

		self.inputCont = RO.InputCont.ContList (
			conts = [
				RO.InputCont.WdgCont (
					name = "set gfocus",
					wdgs = self.userFocusWdg,
					formatFunc = RO.InputCont.BasicFmt(
					),
				),
				RO.InputCont.WdgCont (
					name = "set gfilter",
					wdgs = self.userFiltWdg,
					formatFunc = RO.InputCont.BasicFmt(
					),
				),
			],
			callFunc = self.inputContCallback,
		)
		
		# put model callbacks here, once we have a model!
		
	def updFilterNames(self, filtNames, isCurrent, keyVar=None):
		if not isCurrent:
			return
		
		maxNameLen = 0
		for name in filtNames:
			if name != None:
				maxNameLen = max(maxNameLen, len(name))

		self.currFiltWdg["width"] = maxNameLen
		self.userFiltWdg["width"] = maxNameLen
		self.userFiltWdg.setItems(filtNames)

	def doApply(self, wdg=None):
		"""Apply changes to configuration"""
		cmdStr = self.inputCont.getString()
		if not cmdStr:
			return

		cmdVar = RO.KeyVariable.CmdVar(
			cmdStr = cmdStr,
			actor = self.tccModel.actor,
		)
		self.statusBar.doCmd(cmdVar)
	
	def doCurrent(self, wdg=None):
		self.inputCont.restoreDefault()
	
	def inputContCallback(self, inputCont=None):
		"""Disable Apply if all values default.
		"""
		cmdStr = self.inputCont.getString()
		doEnable = cmdStr != ""
		self.applyWdg.setEnable(doEnable)
		self.currWdg.setEnable(doEnable)


if __name__ == "__main__":
	import GuideTest
	import RO.Wdg

	root = RO.Wdg.PythonTk()
	GuideWdg._LocalMode = True
	GuideTest.init("gcam")

	addWindow(GuideTest.tuiModel.tlSet)

	gcamTL = GuideTest.tuiModel.tlSet.getToplevel("Guide.GCam")
	gcamTL.makeVisible()
	gcamFrame = gcamTL.getWdg()
	
	GuideTest.run()
	
	root.mainloop()
