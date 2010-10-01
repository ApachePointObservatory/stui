#!/usr/bin/env python
"""Seeing monitor

History:
2010-10-01 ROwen    Initial version.
"""
import math
import Tkinter
import matplotlib
import RO.PhysConst
import RO.Wdg
import TUI.Base.StripChartWdg
import TUI.Models

WindowName = "Inst.Guide Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+434+22",
        visible = False,
        resizable = True,
        wdgFunc = GuideMonitorWdg,
    )

class GuideMonitorWdg(Tkinter.Frame):
    """Monitor guide corrections
    """
    def __init__(self, master, timeRange=1800, width=9, height=5):
        """Create a GuideMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - hiehgt: height of plot (inches)
        """
        Tkinter.Frame.__init__(self, master)
        self.tccModel = TUI.Models.getModel("tcc")
        self.guiderModel = TUI.Models.getModel("guider")
        
        self.stripChartWdg = TUI.Base.StripChartWdg.StripChartWdg(
            master = self,
            timeRange = timeRange,
            numSubplots = 3,
            width = width,
            height = height,
            cnvTimeFunc = TUI.Base.StripChartWdg.TimeConverter(useUTC=True),
        )
        self.stripChartWdg.grid(row=0, column=0, sticky="nwes")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # the default ticks are not nice, so be explicit
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=range(0, 61, 5)))
        
        # guide offset subplot
        self.stripChartWdg.plotKeyVar("RA (on sky)", subplotInd=0, keyVar=self.guiderModel.axisChange, keyInd=0, color="green")
        self.stripChartWdg.plotKeyVar("Dec", subplotInd=0, keyVar=self.guiderModel.axisChange, keyInd=1, color="blue")
        self.stripChartWdg.plotKeyVar("Rot", subplotInd=0, keyVar=self.guiderModel.axisChange, keyInd=2, color="red")
        self.stripChartWdg.showY(-3.0, 3.0, subplotInd=0)
        self.stripChartWdg.addConstantLine("GuideZero", 0.0, subplotInd=0, color="gray")
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("Axis Off (\")")
        self.stripChartWdg.subplotArr[0].legend(loc=3, frameon=False)

        # focus subplot
        self.stripChartWdg.plotKeyVar("Sec Piston", subplotInd=1, keyVar=self.tccModel.secOrient, color="green")
        self.stripChartWdg.plotKeyVar("User Focus", subplotInd=1, keyVar=self.tccModel.secFocus, color="blue")
        self.stripChartWdg.subplotArr[1].yaxis.set_label_text("Focus (um)")
        self.stripChartWdg.subplotArr[1].legend(loc=3, frameon=False)
        
        # scale subplot
        def minusOne(val):
            return val - 1.0
        self.stripChartWdg.plotKeyVar("Scale Fac", subplotInd=2, keyVar=self.tccModel.scaleFac, func=minusOne, color="green")
        self.stripChartWdg.addConstantLine("ScaleFac0", 0.0, subplotInd=2, color="gray")
        self.stripChartWdg.showY(-1.0e-4, 1.0e-4, subplotInd=2)
        self.stripChartWdg.subplotArr[2].yaxis.set_label_text("ScaleFac - 1")


if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
