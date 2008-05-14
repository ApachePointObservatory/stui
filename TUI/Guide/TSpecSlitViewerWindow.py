#!/usr/bin/env python
"""TripleSpec slitviewer window

History:
2008-03-14 ROwen
2008-05-14 Added support for background subtraction.
"""
import Tkinter
import RO.Alg
import GuideWdg
import TCameraModel

_HelpURL = "Guiding/TSpecSlitviewerWin.html"

def addWindow(tlSet):
    return tlSet.createToplevel (
        name = "Guide.TSpec Slitviewer",
        defGeom = "+452+280",
        resizable = True,
        wdgFunc = RO.Alg.GenericCallback(TSpecGuiderWdg),
        visible = False,
    )


class TSpecGuiderWdg(GuideWdg.GuideWdg):
    def __init__(self,
        master,
    **kargs):
        GuideWdg.GuideWdg.__init__(self,
            master = master,
            actor = "tcam",
        )
        
        self.bsubWdg = BSubWdg(
            master = self.devSpecificFrame,
            statusBar = self.statusBar,
        )
        self.bsubWdg.grid(row=0, column=0, sticky="w")

        self.devSpecificFrame.grid_columnconfigure(1, weight=1)
        self.devSpecificFrame.configure(border=5, relief="sunken")


class BSubWdg(Tkinter.Frame):
    def __init__(self,
        master,
        statusBar,
    ):
        Tkinter.Frame.__init__(self, master)
        self.statusBar = statusBar

        self.tcameraModel = TCameraModel.getModel()
        self.offCmd = None
        self.onCmd = None
        
        gr = RO.Wdg.Gridder(self, sticky="w")
        
        self.bsubStateWdg = RO.Wdg.StrLabel(
            master = self,
            width = 3,
            helpText = "State of background subtraction",
        )

        self.bsubOnWdg = RO.Wdg.Button(
            master = self,
            text = "On",
            callFunc = self.doOn,
            width = 3,
            helpText = "Start background subtraction",
            helpURL = _HelpURL,
        )
        self.bsubOffWdg = RO.Wdg.Button(
            master = self,
            text = "Off",
            callFunc = self.doOff,
            helpText = "Stop background subtraction",
            helpURL = _HelpURL,
        )
        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "X",
            callFunc = self.doCancel,
            helpText = "Cancel background subtraction command",
            helpURL = _HelpURL,
        )
        
        self.bsubFileWdg = RO.Wdg.StrLabel(
            master = self,
            helpText = "Name of background image",
        )

        gr.gridWdg("Bkgnd Sub", (self.bsubStateWdg, self.bsubOnWdg, self.bsubOffWdg, self.cancelBtn, self.bsubFileWdg))
 
        self.tcameraModel.isBSub.addIndexedCallback(self.updIsBSub)
        self.tcameraModel.bsubBase.addROWdg(self.bsubFileWdg)
        
        self.enableButtons()
    
    def doCancel(self, *args, **kargs):
        if self.runningOff():
            self.offCmd.abort()
        if self.runningOn():
            self.onCmd.abort()
        self.enableButtons()
    
    def doOff(self, wdg=None):
        self.offCmd = RO.KeyVariable.CmdVar (
            actor = self.tcameraModel.actor,
            cmdStr = "bsub state=off",
            callFunc = self.enableButtons,
            callTypes = RO.KeyVariable.DoneTypes,
        )
        self.statusBar.doCmd(self.offCmd)
        self.enableButtons()
    
    def doOn(self, wdg=None):
        self.onCmd = RO.KeyVariable.CmdVar (
            actor = self.tcameraModel.actor,
            cmdStr = "bsub state=on",
            callFunc = self.enableButtons,
            callTypes = RO.KeyVariable.DoneTypes,
        )
        self.statusBar.doCmd(self.onCmd)
        self.enableButtons()
        
    def enableButtons(self, *args, **kargs):
        """Enable the various buttons depending on the current state"""
        isBSub = self.tcameraModel.isBSub.getInd(0)[0]

        if isBSub:
            self.bsubOnWdg["text"] = "New"
            self.bsubOnWdg.helpText = "Take a new bsub image"
            self.bsubFileWdg.grid()
        else:
            self.bsubOnWdg["text"] = "On"
            self.bsubOnWdg.helpText = "Start background subtraction"
            self.bsubFileWdg.grid_remove()

        runningOff = self.runningOff()
        runningOn = self.runningOn()
        self.bsubOnWdg.setEnable(not runningOn)
        self.bsubOffWdg.setEnable(not runningOff)
        self.cancelBtn.setEnable(runningOff or runningOn)
    
    def runningOff(self):
        return not (self.offCmd == None or self.offCmd.isDone())
    
    def runningOn(self):
        return not (self.onCmd == None or self.onCmd.isDone())
    
    def updIsBSub(self, isBSub, isCurrent, keyVar=None):
        isBSubStr = {
            False: "Off",
            True: "On",
        }.get(isBSub)
            
        self.bsubStateWdg.set(isBSubStr, isCurrent)
        self.enableButtons()
        
    

if __name__ == "__main__":
    import RO.Wdg
    import GuideTest
    
    root = RO.Wdg.PythonTk()

    GuideTest.init("dcam")

    testTL = addWindow(GuideTest.tuiModel.tlSet)
    testTL.makeVisible()
    testTL.wait_visibility() # must be visible to download images
    testFrame = testTL.getWdg()

    GuideTest.runDownload(
        basePath = "keep/ecam/UT050422/",
        imPrefix = "e",
        startNum = 101,
        numImages = 3,
        waitMs = 2500,
    )

    root.mainloop()
