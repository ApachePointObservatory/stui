#!/usr/local/bin/python
"""ECam echelle slitviewer window

History:
2005-05-26 ROwen
2005-06-17 ROwen	Renamed window from "ECam" to "Echelle Slitviewer".
2005-06-21 ROwen	Improved the test code.
2005-06-22 ROwen	Improved the test code.
"""
import RO.InputCont
import RO.Wdg
import TUI.Inst.Echelle.EchelleModel
import GuideWdg

_HelpURL = "Guiding/EchelleSlitviewerWin.html"

_InitWdgWidth = 5

def addWindow(tlSet):
	return tlSet.createToplevel (
		name = "Guide.Echelle Slitviewer",
		defGeom = "+452+280",
		resizable = True,
		wdgFunc = EchelleSlitviewerWdg,
		visible = False,
	)

class EchelleSlitviewerWdg(GuideWdg.GuideWdg):
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
		fr.configure(bd=2, relief="sunken")
		gr = RO.Wdg.StatusConfigGridder(fr)
		
		self.currFiltWdg = RO.Wdg.StrLabel(
			master = fr,
			width = _InitWdgWidth,
			helpText = "Current echelle slitviewer filter",
			helpURL = _HelpURL,
		)
		self.userFiltWdg = RO.Wdg.OptionMenu(
			master = fr,
			items = (),
			autoIsCurrent = True,
			width = _InitWdgWidth,
			helpText = "Desired echelle slitviewer filter",
			helpURL = _HelpURL,
		)
		gr.gridWdg("Filter", self.currFiltWdg, None, self.userFiltWdg)

		col = gr.getNextCol()
		nRows = gr.getNextRow()

		self.applyWdg = RO.Wdg.Button(
			master = fr,
			text = "Apply",
			callFunc = self.doApply,
			helpText = "Set echelle slitviewer filter",
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
		
		def fmtStrArg(argStr):
			return RO.StringUtil.quoteStr(argStr.lower())

		self.inputCont = RO.InputCont.WdgCont (
			name = "svfilter",
			wdgs = self.userFiltWdg,
			formatFunc = RO.InputCont.BasicFmt(
				valFmt=fmtStrArg,
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

		self.doCmd(cmdStr, actor=self.echelleModel.actor)
	
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
	
	isLocal = True  # run local tests?
	
	root = RO.Wdg.PythonTk()

	GuideTest.init("ecam", isLocal = isLocal)

	testTL = addWindow(GuideTest.tuiModel.tlSet)
	testTL.makeVisible()
	testTL.wait_visibility() # must be visible to download images
	testFrame = testTL.getWdg()

	echelleData = (
		'i svFilterNames = x, y, z, open, "", ""',
		'i svFilter = "open"',
	)
	for data in echelleData:
		GuideTest.dispatch(data, actor="echelle")
	
	def anime():
		echelleData = (
			'i svFilter = "x"',
		)
		for data in echelleData:
			GuideTest.dispatch(data, actor="echelle")

	if isLocal:
		GuideTest.runLocalDemo()
	else:
		GuideTest.runDownload(
			basePath = "keep/gcam/UT050422/",
			startNum = 101,
			numImages = 20,
			maskNum = 1,
			waitMs = 2500,
		)

	root.mainloop()
