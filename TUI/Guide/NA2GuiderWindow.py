#!/usr/bin/env python
"""GCam NA2 guider window

To do:
- Consider a cancel button for Apply -- perhaps replace Current with Cancel
  while applying changes. (That might be a nice thing for all Configure windows).
  If implemented, ditch the time limit.
- Reimplement mech components as a separate widget that is brought in.
  That would greatly reduce the chance for collision.

History:
2005-05-26 ROwen
2005-06-16 ROwen    Changed to not use a command status bar for gmech changes
                    (this part of the code is not enabled anyway).
                    Imported RO.Wdg again in the test code (found by pychecker).
2005-06-17 ROwen    Renamed window from "GCam" to "NA2 Guider".
2005-06-21 ROwen    Fixed the test code.
2005-06-22 ROwen    Improved the test code.
2005-07-14 ROwen    Removed local test mode support.
2006-05-19 ROwen    Bug fix: doCurrent was colliding with parent class.
2008-02-01 ROwen    Modified to load GMech model.
2008-02-11 ROwen    Modified to use relPiston command.
"""
import Tkinter
import RO.InputCont
import RO.ScriptRunner
import RO.StringUtil
import TUI.Base.FocusWdg
import TUI.Guide.GMechModel
import RO.Wdg
import GuideWdg
import GMechModel

_HelpURL = "Guiding/NA2GuiderWin.html"

# time limit for filter or focus change (sec)
_ApplyTimeLim = 200
_InitWdgWidth = 5

MicronStr = RO.StringUtil.MuStr + "m"

def addWindow(tlSet):
    return tlSet.createToplevel (
        name = "Guide.NA2 Guider",
        defGeom = "+452+280",
        resizable = True,
        wdgFunc = NA2GuiderWdg,
        visible = False,
    )


class NA2GuiderWdg(GuideWdg.GuideWdg):
    def __init__(self,
        master,
    **kargs):
        GuideWdg.GuideWdg.__init__(self,
            master = master,
            actor = "gcam",
        )
        
        self.focusWdg = GMechFocusWdg(
            master = self.devSpecificFrame,
            statusBar = self.statusBar,
        )
        self.focusWdg.grid(row=0, column=0, sticky="w")

        self.filterWdg = GMechFilterWdg(
            master = self.devSpecificFrame,
            statusBar = self.statusBar,
        )
        self.filterWdg.grid(row=1, column=0, sticky="w")

       
        self.devSpecificFrame.grid_columnconfigure(1, weight=1)


class GMechFocusWdg(TUI.Base.FocusWdg.FocusWdg):
    def __init__(self, master, statusBar):
        TUI.Base.FocusWdg.FocusWdg.__init__(self,
            master,
            name = "gcam",
            statusBar = statusBar,
            increments = (1000, 2000, 4000),
            defIncr = 2000,
            helpURL = _HelpURL,
            label = "Focus",
            minFocus = 0,
            maxFocus = 800000,
            fmtStr = "%.1f",
            currWidth = 8,
        )

        gmechModel = TUI.Guide.GMechModel.getModel()
        gmechModel.desFocus.addCallback(self.endTimer)
        gmechModel.pistonMoveTime.addCallback(self._pistonMoveTime)
        gmechModel.focus.addIndexedCallback(self.updFocus)
        
    def _pistonMoveTime(self, elapsedPredTime, isCurrent, keyVar=None):
        """Called when CmdDTime seen, to put up a timer.
        """
        if not isCurrent or None in elapsedPredTime:
            return
        elapsedTime, predTime = elapsedPredTime
        self.startMove(predTime, elapsedTime)
    
    def createFocusCmd(self, newFocus, isIncr=False):
        """Create and return the focus command"""
        if isIncr:
            incrStr = "relPiston"
        else:
            incrStr = "focus"
        cmdStr = "%s %s" % (incrStr, newFocus)

        return RO.KeyVariable.CmdVar (
            actor = "gmech",
            cmdStr = cmdStr,
#            timeLim = 0,
#            timeLimKeyword="CmdDTime",
        )

class GMechFilterWdg(Tkinter.Frame):
    def __init__(self,
        master,
        statusBar,
    ):
        Tkinter.Frame.__init__(self, master)
        self.statusBar = statusBar

        self.gmechModel = GMechModel.getModel()
        
        self.filterCmd = None

        col = 0
        
        RO.Wdg.StrLabel(master=self, text="Filter").grid(row=0, column=col)
        col += 1
        
        self.currFilterWdg = RO.Wdg.StrLabel(
            master = self,
            width = _InitWdgWidth,
            helpText = "Current NA2 guider filter",
            helpURL = _HelpURL,
        )
#        self.currFilterWdg.grid(row=0, column=col)
        col += 1
        
        self.userFilterWdg = RO.Wdg.OptionMenu(
            master = self,
            items = (),
            autoIsCurrent = True,
            width = _InitWdgWidth,
            callFunc = self.enableButtons,
            helpText = "Desired NA2 guider filter",
            helpURL = _HelpURL,
            defMenu = "Current",
        )
        self.userFilterWdg.grid(row=0, column=col)
        col += 1

        self.setFilterBtn = RO.Wdg.Button(
            master = self,
            text = "Set Filter",
            callFunc = self.setFilter,
            helpText = "Set NA2 guider filter",
            helpURL = _HelpURL,
        )
        self.setFilterBtn.grid(row=0, column=col)
        col += 1

        self.setCurrBtn = RO.Wdg.Button(
            master = self,
            text = "Current",
            callFunc = self.doCurrent,
            helpText = "Set filter control to current filter",
            helpURL = _HelpURL,
        )
        self.setCurrBtn.grid(row=0, column=col)
        self.cancelBtn = RO.Wdg.Button(
            master = self,
            text = "Cancel",
            callFunc = self.doCancel,
            helpText = "Cancel filter command",
            helpURL = _HelpURL,
        )
        self.cancelBtn.grid(row=0, column=col)
        col += 1
 
        self.gmechModel.filter.addIndexedCallback(self._updFilter)
        self.gmechModel.filterNames.addCallback(self._updFilterNames)
    
    def _updFilter(self, filterNum, isCurrent, keyVar=None):
        if filterNum == None:
            return

        self.currFilterWdg.set(filterNum)
        filterInd = filterNum - self.getMinFilterNum()
        filterName = self.userFilterWdg._items[filterInd]
        self.currFilterWdg.set(filterName)
        self.userFilterWdg.setDefault(filterName)
    
    def _updFilterNames(self, filtNames, isCurrent, keyVar=None):
        if None in filtNames:
            return
        
        maxNameLen = 0
        for name in filtNames:
            maxNameLen = max(maxNameLen, len(name))

        self.currFilterWdg["width"] = maxNameLen
        self.userFilterWdg["width"] = maxNameLen
        self.userFilterWdg.setItems(filtNames)
    
    def cmdDone(self, *args, **kargs):
        self.filterCmd = None
        self.enableButtons()
    
    def doCancel(self, *args, **kargs):
        if self.filterCmd and not self.filterCmd.isDone():
            self.filterCmd.abort()
            self.doCurrent()
        
    def doCurrent(self, wdg=None):
        self.userFilterWdg.restoreDefault()

    def enableButtons(self, wdg=None):
        """Enable the various buttons depending on the current state"""
        if self.filterCmd and not self.filterCmd.isDone():
            self.setCurrBtn.grid_remove()
            self.cancelBtn.grid()
            #self.userFilterWdg["state"] = "disabled"
            self.setFilterBtn["state"] = "disabled"
        else:
            #self.userFilterWdg["state"] = "normal"
            self.cancelBtn.grid_remove()
            self.setCurrBtn.grid()
            if not self.userFilterWdg.isDefault():
                self.setFilterBtn["state"] = "normal"
                self.setCurrBtn["state"] = "normal"
            else:
                self.setFilterBtn["state"] = "disabled"
                self.setCurrBtn["state"] = "disabled"
    
    def getMinFilterNum(self):
        """Return the minimum filter number; raise RuntimeError if unavailable"""
        minFilter = self.gmechModel.minFilter.getInd(0)[0]
        if minFilter == None:
            raise RuntimeError("Minimum filter number unknown")
        return minFilter

    def setFilter(self, wdg=None):
        """Command a new filter"""
        desFilterInd = self.userFilterWdg.getIndex()
        if desFilterInd == None:
            raise RuntimeError("No filter selected")
        desFilterNum = desFilterInd + self.getMinFilterNum()
        cmdStr = "filter %s" % (desFilterNum,)
        self.filterCmd = RO.KeyVariable.CmdVar (
            actor = "gmech",
            cmdStr = cmdStr,
            callFunc = self.cmdDone,
            callTypes = RO.KeyVariable.DoneTypes,
        )
        self.statusBar.doCmd(self.filterCmd)
        self.enableButtons()


if __name__ == "__main__":
    import GuideTest
    
    root = RO.Wdg.PythonTk()

    GuideTest.init("gcam")

    testTL = addWindow(GuideTest.tuiModel.tlSet)
    testTL.makeVisible()
    testTL.wait_visibility() # must be visible to download images
    testFrame = testTL.getWdg()
    
    for msg in (
        'i filterNames="red", "red nd1", "red nd2", "blue", "", "", ""; minFilter=0; maxFilter=6',
        'i minFocus=-10, maxFocus=20000',
        'i filter=0; focus=10',
    ):
        GuideTest.dispatch(msg, actor="gmech")

#    GuideTest.runDownload(
#        basePath = "keep/gcam/UT050422/",
#        imPrefix = "g",
#        startNum = 101,
#        numImages = 3,
#        waitMs = 2500,
#    )

    root.mainloop()
