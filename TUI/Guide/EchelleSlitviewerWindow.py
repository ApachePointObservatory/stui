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
2008-02-06 ROwen    Tweaked the layout a bit.
2008-02-11 ROwen    Modified the code to match NA2 Guider window, including:
                    - Added a cancel button
                    - Hid the current filter by default
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
        
        self.ECamFilterWdg = ECamFilterWdg(
            master = self.devSpecificFrame,
            statusBar = self.statusBar,
        )
        self.ECamFilterWdg.pack(side="left", expand=True, fill="x")
        
        self.devSpecificFrame.configure(border=5, relief="sunken")
    

class ECamFilterWdg(Tkinter.Frame):
    def __init__(self,
        master,
        statusBar
    ):
        Tkinter.Frame.__init__(self, master = master)
        self.statusBar = statusBar

        self.echelleModel = TUI.Inst.Echelle.EchelleModel.getModel()
        self.currCmd = None
        
        # show current filter as well as user filter menu?
        showCurrFilter = False

        col = 0
        
        RO.Wdg.StrLabel(
            master = self,
            text = "Filter",
            helpText = "Echelle slitviewer filter",
            helpURL = _HelpURL,
        ).grid(row=0, column=col)
        col += 1
        
        self.currFilterWdg = RO.Wdg.StrLabel(
            master = self,
            width = _FiltWidth,
            helpText = "Current Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        if showCurrFilter:
            self.currFilterWdg.grid(row=0, column=col)
            col += 1
        
        if showCurrFilter:
            userFilterHelp = "Desired Echelle slitviewer filter"
        else:
            userFilterHelp = "Echelle slitviewer filter"

        self.userFilterWdg = RO.Wdg.OptionMenu(
            master = self,
            items = (),
            autoIsCurrent = True,
            width = _FiltWidth,
            callFunc = self.enableButtons,
            defMenu = "Current",
            helpText = userFilterHelp,
            helpURL = _HelpURL,
        )
        self.userFilterWdg.grid(row=0, column=col)
        col += 1

        nCols = col

        self.applyBtn = RO.Wdg.Button(
            master = self,
            text = "Set Filter",
            callFunc = self.doApply,
            helpText = "Set Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        self.applyBtn.grid(row=0, column=col)
        col += 1

        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self.doCancel,
            helpText = "Cancel filter command",
            helpURL = _HelpURL,
        )
        self.cancelBtn.grid(row=0, column=col)
        col += 1

        self.currentBtn = RO.Wdg.Button(
            master = self,
            text = "Current Filter",
            callFunc = self.doCurrent,
            helpText = "Show current Echelle slitviewer filter",
            helpURL = _HelpURL,
        )
        self.currentBtn.setEnable(False)
        self.currentBtn.grid(row=0, column=col)
        col += 1
        
        self.grid_columnconfigure(col, weight=1)
        
        def fmtStrArg(argStr):
            return RO.StringUtil.quoteStr(argStr.lower())

        self.echelleModel.svFilter.addIndexedCallback(self.updFilter)
        self.echelleModel.svFilterNames.addCallback(self.updFilterNames)
    
    def cmdDone(self, *args, **kargs):
        self.currCmd = None
        self.enableButtons()

    def doApply(self, wdg=None):
        """Apply changes to configuration"""
        desFilter = self.userFilterWdg.getString()
        cmdStr = 'svfilter "%s"' % (desFilter,)

        self.currCmd = RO.KeyVariable.CmdVar (
            actor = self.echelleModel.actor,
            cmdStr = cmdStr,
            callFunc = self.cmdDone,
            callTypes = RO.KeyVariable.DoneTypes,
        )
        self.statusBar.doCmd(self.currCmd)
        self.enableButtons()
    
    def doCancel(self, *args, **kargs):
        if self.currCmd and not self.currCmd.isDone():
            self.currCmd.abort()
            self.doCurrent()
    
    def doCurrent(self, wdg=None):
        self.userFilterWdg.restoreDefault()

    def enableButtons(self, wdg=None):
        """Enable the various buttons depending on the current state"""
        if self.currCmd and not self.currCmd.isDone():
            self.userFilterWdg.setEnable(False)
            self.currentBtn.setEnable(False)
            self.cancelBtn.setEnable(True)
            self.applyBtn.setEnable(False)
        else:
            allowChange = not self.userFilterWdg.isDefault()
            self.userFilterWdg.setEnable(True)
            self.applyBtn.setEnable(allowChange)
            self.cancelBtn.setEnable(False)
            self.currentBtn.setEnable(allowChange)
    
    def updFilter(self, filt, isCurrent, keyVar=None):
        #print "updFilter(filt = %s, isCurrent = %s)" % (filt, isCurrent)
        self.currFilterWdg.set(filt, isCurrent = isCurrent)
        self.userFilterWdg.setDefault(filt, isCurrent = isCurrent)
    
    def updFilterNames(self, filtNames, isCurrent, keyVar=None):
        #print "updFilterNames(filtNames = %s, isCurrent = %s)" % (filtNames, isCurrent)
        if not isCurrent:
            return
        
        maxNameLen = 0
        for name in filtNames:
            if name != None:
                maxNameLen = max(maxNameLen, len(name))

        self.currFilterWdg["width"] = maxNameLen
        self.userFilterWdg["width"] = maxNameLen
        self.userFilterWdg.setItems(filtNames)


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
