#!/usr/bin/env python
"""Fiducial Crossing monitor

Based on a script by Elena Malanushenko

History:
2010-08-25 ROwen
2010-08-26 ROwen    Added output for <axis>BadFiducial
2010-10-07 ROwen    Corrected a typo in the window name (caught by Dan Oravitz)
"""
import time
import Tkinter
import RO.Wdg
import TUI.Models

WindowName = "TCC.Fiducials"
_HelpURL = "Telescope/FiducialsWin.html"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+375+340",
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
    def __init__(self, master, maxEntries = 100, width = 25, height = 3, **kargs):
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
            text = "TAI Time  Ind  Pos   Error",
        ).grid(row = row, column=1, sticky="w")
        row += 1

        for axisName in self.axisNameList:
            logWdg = RO.Wdg.LogWdg(
                master = self,
                relief = "ridge",
                borderwidth = 2,
                width = width,
                height = height,
                helpText = "%s fiducial wondow" % (axisName,),
                helpURL = _HelpURL,
            )
            self.logWdgDict[axisName] = logWdg
            Tkinter.Label(master = self, text = axisName).grid(row = row, column = 0, sticky="nw")
            logWdg.grid(row = row, column = 1, sticky="nwes")
            self.grid_rowconfigure(row, weight=1)
            row += 1

            fidCrossKeyVar = getattr(self.mcpModel, "%sFiducialCrossing" % (axisName.lower()))
            def fidCrossCallFunc(fidCrossKeyVar, axisName=axisName):
                self.axisFiducialCrossingCallback(axisName, fidCrossKeyVar)
            fidCrossKeyVar.addCallback(fidCrossCallFunc, callNow=False)

            badFiducialKeyVar = getattr(self.mcpModel, "%sBadFiducial" % (axisName.lower()))
            def badFiducialCallFunc(badFiducialKeyVar, axisName=axisName):
                self.axisBadFiducialCallback(axisName, badFiducialKeyVar)
            badFiducialKeyVar.addCallback(badFiducialCallFunc, callNow=False)
            
        self.grid_columnconfigure(1, weight=1)
    
    def axisBadFiducialCallback(self, axisName, keyVar):
        """Callback for <axis>BadFidudial keyword
        
        Inputs:
        - axisName: one of Az, Alt or Rot
        - keyVar: mcp <axis>BadFidudial data:
            Int(help="fiducial index"),
            Float(units="deg", help="fiducial position")),
        """
        if not keyVar.isGenuine:
            # ignore cached info
            return

        logWdg = self.logWdgDict[axisName]
        timeStr = getTAITimeStr()
        logWdg.addOutput(
            "\n%8s  %2i %6.1f   bad" % (timeStr, keyVar[0], keyVar[1]),
            severity=RO.Constants.sevError,
        )

    def axisFiducialCrossingCallback(self, axisName, keyVar):
        """Callback for <axis>FiducialCrossing keyword
        
        Inputs:
        - axisName: one of Az, Alt or Rot
        - keyVar: mcp <axis>FiducialCrossing data:
            Int(help="fiducial index"),
            Float(units="deg", help="fiducial position"),
            Int(units="ticks", help="error since last crossing", invalid=99999),
            Int(units="ticks", help="error in reported position")),
        """
        if not keyVar.isGenuine:
            # ignore cached info
            return

        logWdg = self.logWdgDict[axisName]
        timeStr = getTAITimeStr()
        logWdg.addOutput("\n%8s  %2i %6.1f   %5d" % (timeStr, keyVar[0], keyVar[1], keyVar[3]))


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
