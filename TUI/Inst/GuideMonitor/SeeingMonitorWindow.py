#!/usr/bin/env python
"""Seeing monitor

History:
2012-04-23 Elena Malanushenko, converted from a script to a window by Russell Owen
"""
import Tkinter
import matplotlib
import RO.Wdg
import TUI.Base.StripChartWdg
import TUI.Models

WindowName = "Inst.Seeing Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+346+110",
        visible = False,
        resizable = True,
        wdgFunc = SeeingMonitorWdg,
    )

class SeeingMonitorWdg(Tkinter.Frame):
    def __init__(self, master, timeRange=3600, width=8, height=2.4):
        """Create a SeeingMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - height: height of plot (inches)
        """
        Tkinter.Frame.__init__(self, master)
        self.guiderModel = TUI.Models.getModel("guider")
        
        self.stripChartWdg = TUI.Base.StripChartWdg.StripChartWdg(
            master = self,
            timeRange = timeRange,
            numSubplots = 1, 
            width = width,
            height = height,
            cnvTimeFunc = TUI.Base.StripChartWdg.TimeConverter(useUTC=True),
        )
        self.stripChartWdg.grid(row=0, column=0, sticky="nwes")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # the default ticks are not nice, so be explicit
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=range(0, 61, 10)))

        subplotInd = 0

        self.stripChartWdg.plotKeyVar(
            label = "seeing",
            subplotInd = subplotInd,
            keyVar = self.guiderModel.seeing,
            keyInd = 0,
            color = "green",
        )
        self.stripChartWdg.showY(0.0, 2.0, subplotInd=subplotInd)
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("seeing")
        self.stripChartWdg.addConstantLine(1.0, subplotInd=subplotInd, color="grey")
        self.stripChartWdg.addConstantLine(2.0, subplotInd=subplotInd, color="grey")
        self.stripChartWdg.subplotArr[0].legend(loc=3, frameon=False)

        self.clearWdg = RO.Wdg.Button(master = self, text = "C", callFunc = self.stripChartWdg.clear)
        self.clearWdg.grid(row=0, column=0, sticky = "sw")

if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
