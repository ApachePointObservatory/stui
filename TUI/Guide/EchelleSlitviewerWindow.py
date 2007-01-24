#!/usr/bin/env python
"""ECam echelle slitviewer window

History:
2005-05-26 ROwen
2005-06-17 ROwen    Renamed window from "ECam" to "Echelle Slitviewer".
2005-06-21 ROwen    Improved the test code.
2005-06-22 ROwen    Improved the test code.
2005-06-23 ROwen    Modified to disable Apply button while it executes.
2005-07-14 ROwen    Removed local test mode support.
2006-05-26 ROwen    Moved ecam-specific code to a separate class, to avoid name collisions.
                    Added Current menu to the filter menu.
"""
import Tkinter
import RO.InputCont
import RO.Wdg
import TUI.Inst.Echelle.EchelleModel
import GuideWdg

_HelpURL = "Guiding/EchelleSlitviewerWin.html"

_FiltWidth = 5 # initial width for widgets that show filter name

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
        
        self.ecamExtraWdg = ECamExtraWdg(
            master = self.devSpecificFrame,
            doCmd = self.doCmd,
        )
        self.ecamExtraWdg.pack(side="left")
    

class ECamExtraWdg(Tkinter.Frame):
    def __init__(self,
        master,
        doCmd,
    **kargs):
        Tkinter.Frame.__init__(self,
            master = master,
        )

        self.echelleModel = TUI.Inst.Echelle.EchelleModel.getModel()
        self.doCmd = doCmd

        gr = RO.Wdg.Gridder(self)
        
        self.currFiltWdg = RO.Wdg.StrLabel(
            master = self,
            width = _FiltWidth,
            helpText = "Current Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        
        self.userFiltWdg = RO.Wdg.OptionMenu(
            master = self,
            items = (),
            autoIsCurrent = True,
            width = _FiltWidth,
            defMenu = "Current",
            helpText = "Desired Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Filter", self.currFiltWdg, self.userFiltWdg)

        col = gr.getNextCol()
        nRows = gr.getNextRow()

        self.applyWdg = RO.Wdg.Button(
            master = self,
            text = "Apply",
            callFunc = self.doApply,
            helpText = "Set Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        self.applyWdg.setEnable(False)
        self.applyWdg.grid(row=0, column=col, rowspan=nRows)
        col += 1

        self.currWdg = RO.Wdg.Button(
            master = self,
            text = "Current",
            callFunc = self.doCurrent,
            helpText = "Show current Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        self.currWdg.setEnable(False)
        self.currWdg.grid(row=0, column=col, rowspan=nRows)
        col += 1
        
        self.grid_columnconfigure(col, weight=1)
        
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
        
        self.echelleModel.svFilter.addIndexedCallback(self.updFilter)
#       self.echelleModel.svFilter.addROWdg(self.currFiltWdg)
#       self.echelleModel.svFilter.addROWdg(self.userFiltWdg, setDefault=True)
        self.echelleModel.svFilterNames.addCallback(self.updFilterNames)

    def doApply(self, wdg=None):
        """Apply changes to configuration"""
        cmdStr = self.inputCont.getString()
        if not cmdStr:
            return

        self.doCmd(cmdStr, actor=self.echelleModel.actor, cmdBtn=self.applyWdg)
    
    def doCurrent(self, wdg=None):
        self.inputCont.restoreDefault()
    
    def inputContCallback(self, inputCont=None):
        """Disable Apply if all values default.
        """
        cmdStr = self.inputCont.getString()
        doEnable = cmdStr != ""
        self.applyWdg.setEnable(doEnable)
        self.currWdg.setEnable(doEnable)

    def updFilter(self, filt, isCurrent, keyVar=None):
        #print "updFilter(filt = %s, isCurrent = %s)" % (filt, isCurrent)
        self.currFiltWdg.set(filt, isCurrent = isCurrent)
        self.userFiltWdg.setDefault(filt, isCurrent = isCurrent)
    
    def updFilterNames(self, filtNames, isCurrent, keyVar=None):
        #print "updFilterNames(filtNames = %s, isCurrent = %s)" % (filtNames, isCurrent)
        if not isCurrent:
            return
        
        maxNameLen = 0
        for name in filtNames:
            if name != None:
                maxNameLen = max(maxNameLen, len(name))

        self.currFiltWdg["width"] = maxNameLen
        self.userFiltWdg["width"] = maxNameLen
        self.userFiltWdg.setItems(filtNames)



if __name__ == "__main__":
    import GuideTest
        
    root = RO.Wdg.PythonTk()

    GuideTest.init("ecam")

    testTL = addWindow(GuideTest.tuiModel.tlSet)
    testTL.makeVisible()
    testTL.wait_visibility() # must be visible to download images
    testFrame = testTL.getWdg()

    GuideTest.setParams(expTime=5, thresh=3, radMult=1, mode="field")

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

#   GuideTest.runDownload(
#       basePath = "keep/ecam/UT050422/",
#       imPrefix = "e",
#       startNum = 101,
#       numImages = 3,
#       waitMs = 2500,
#   )

    root.mainloop()
