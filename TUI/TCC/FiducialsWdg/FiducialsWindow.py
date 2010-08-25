"""Fiducial Crossing monitor

Based on a script by Elena Malanushenko
"""
import time
import Tkinter
import RO.Wdg
import TUI.Models

WindowName = "TCC.Fidicials"
_HelpPrefix = "Telescope/FiducialsWin.html#"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+200+100",
        resizable = (False, True),
        wdgFunc = FiducialsWdg,
    )

def getTAITimeStr():
    return time.strftime("%H:%M:%S", time.gmtime(time.time() -  - RO.Astro.Tm.getUTCMinusTAI()))

class FiducialsWdg(Tkinter.Frame):
    """Display information about telescope fiducial crossings
    
    To do: add an alert line when error is too large to correct
    (it's a separate message, so will be a separate line -- in red)
    """
    def __init__(self, master, maxEntries = 100, width = 25, height = 15, **kargs):
        """
        Inputs:
        - maxEntries: maximum number of entries for each axis
        - width: width of each log (chars); total window width adds some overhead
        - height: height of each log (chars); total window height is 3 x height plus some overhead
        **kargs: additional keyword arguments for Tkinter.Frame
        """
        Tkinter.Frame.__init__(self, master, **kargs)

        self.mcpModel = TUI.Models.getModel("mcp")
        self.maxEntries = int(maxEntries)

        self.axisNameList = ("Az", "Alt", "Rot")
        self.logWdgDict = dict()
        row = 0

        Tkinter.Label(
            master = self,
            text = "TAI time   ind  angle   error",
        ).grid(row = row, column=1, sticky="w")
        row += 1

        for axisName in self.axisNameList:
            logWdg = RO.Wdg.LogWdg(
                master = self,
                helpText = "%s fiducial wondow" % (axisName,),
                relief = "ridge",
                borderwidth = 2,
                width = width,
                height = height,
            )
            self.logWdgDict[axisName] = logWdg
            Tkinter.Label(master = self, text = axisName).grid(row = row, column = 0, sticky="nw")
            logWdg.grid(row = row, column = 1, sticky="nwes")
            self.grid_rowconfigure(row, weight=1)
            row += 1

            keyVar = getattr(self.mcpModel, "%sFiducialCrossing" % (axisName.lower()))
            def callFunc(keyVar, axisName=axisName):
                self.updateFiducialInfo(axisName, keyVar)
            keyVar.addCallback(callFunc, callNow=False)
            
        self.grid_columnconfigure(1, weight=1)
        

    def updateFiducialInfo(self, axisName, keyVar):
        if not keyVar.isGenuine:
            # ignore cached info
            return

        logWdg = self.logWdgDict[axisName]
        timeStr = getTAITimeStr()
        logWdg.addMsg("%s %2i %6.1f %10d" % (timeStr, keyVar[0], keyVar[1], keyVar[3]))


if __name__ == "__main__":
    import sys
    import random
    import TestData
    
    tuiModel = TestData.tuiModel
    root = tuiModel.tkRoot
    
    testFrame = FiducialsWdg(
        master=root,
    )
    testFrame.grid(row=0, column=0, sticky="nsew")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    
    TestData.start()
    TestData.animate()
    
    tuiModel.reactor.run()
