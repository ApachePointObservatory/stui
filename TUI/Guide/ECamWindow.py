#!/usr/local/bin/python
"""Guiding support

To do:
- Write an HTML file for the ecam-specific controls,
  and reference that from those controls

History:
2005-05-25 ROwen
"""
import Tkinter
import RO.Constants
import RO.InputCont
import RO.Wdg
import TUI.TUIModel
import TUI.Inst.Echelle.EchelleModel
import GuideModel
import GuideWdg

_HelpPrefix = "Guiding/index.html#"

_InitWdgWidth = 5

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "Guide.ECam",
		defGeom = "+452+280",
		resizable = True,
		wdgFunc = ECamWdg,
		visible = False,
	)

class ECamWdg(GuideWdg.GuideWdg):
	def __init__(self,
		master,
	**kargs):
		GuideWdg.GuideWdg.__init__(self,
			master = master,
			actor = "ecam",
		)

		self.echelleModel = TUI.Inst.Echelle.EchelleModel.getModel()

		# add filterwheel controls to self.devSpecificFrame
		
		fr = self.devSpecificFrame
		gr = RO.Wdg.StatusConfigGridder(fr)
		self.currFiltWdg = RO.Wdg.StrLabel(
			master = fr,
			width = _InitWdgWidth,
			helpText = "Current echelle slitviewer filter",
		)
		self.userFiltWdg = RO.Wdg.OptionMenu(
			master = fr,
			items = (),
			autoIsCurrent = True,
			width = _InitWdgWidth,
			helpText = "Desired echelle slitviewer filter",
		)
		gr.gridWdg("Filter", self.currFiltWdg, self.userFiltWdg)

		self.applyWdg = RO.Wdg.Button(
			master = fr,
			text = "Apply",
			callFunc = self.doApply,
			helpText = "Set echelle slitviewer filter",
		)
		self.applyWdg.setEnable(False)
		self.applyWdg.grid(row=0, column=3)

		self.currWdg = RO.Wdg.Button(
			master = fr,
			text = "Current",
			callFunc = self.doCurrent,
			helpText = "Set filter control to current filter",
		)
		self.currWdg.setEnable(False)
		self.currWdg.grid(row=0, column=4)

		fr.grid_columnconfigure(10, weight=1)

		self.inputCont = RO.InputCont.WdgCont (
			name = "svfilter",
			wdgs = self.userFiltWdg,
			formatFunc = RO.InputCont.BasicFmt(
				valFmt=str.lower,
			),
			callFunc = self.inputContCallback,
		)
		
		self.echelleModel.svFilter.addROWdg(self.currFiltWdg)
		self.echelleModel.svFilter.addROWdg(self.userFiltWdg, setDefault=True)
		self.echelleModel.svFilterNames.addCallback(self.updFilterNames)
	
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
			actor = self.echelleModel.actor,
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

	root = RO.Wdg.PythonTk()
	GuideWdg._LocalMode = True
	GuideTest.init("ecam")

	addWindow(GuideTest.tuiModel.tlSet)

	echelleData = (
		'i svFilterNames = x, y, z, open, "", ""',
		'i svFilter = "open"',
	)
	for data in echelleData:
		GuideTest.dispatch(data, actor="echelle")

	ecamTL = GuideTest.tuiModel.tlSet.getToplevel("Guide.ECam")
	ecamTL.makeVisible()
	ecamFrame = ecamTL.getWdg()
	
	def anime():
		echelleData = (
			'i svFilter = "x"',
		)
		for data in echelleData:
			GuideTest.dispatch(data, actor="echelle")
	
	GuideTest.tuiModel.root.after(2000, anime)

	GuideTest.run()

	root.mainloop()
