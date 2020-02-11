#!/usr/bin/env python
"""Focus monitor

History:
2012-04-23 Elena Malanushenko, converted from a script to a window by Russell Owen
2012-06-04 ROwen    Fix clear button.
"""
import tkinter
import matplotlib
import RO.Wdg
import TUI.Base.StripChartWdg
import TUI.Models

WindowName = "Inst.Focus Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+390+66",
        visible = False,
        resizable = True,
        wdgFunc = FocusMonitorWdg,
    )

class FocusMonitorWdg(tkinter.Frame):
    def __init__(self, master, timeRange=3600, width=8, height=2.4):
        """Create a FocusMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - height: height of plot (inches)
        """
        tkinter.Frame.__init__(self, master)
        self.tccModel = TUI.Models.getModel("tcc")
        self.focusPadding = 50 # minimum padding around initial focus line

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
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=list(range(0, 61, 10))))

        subplotInd = 0
        
        self.stripChartWdg.plotKeyVar(
            label = "focus",
            subplotInd = subplotInd,
            keyVar = self.tccModel.secFocus,
            keyInd = 0,
            color = "green",
        )
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Sec Focus Offset")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)

        self.clearWdg = RO.Wdg.Button(master = self, text = "C", callFunc = self.clearCharts)
        self.clearWdg.grid(row=0, column=0, sticky = "sw")
    
    def clearCharts(self, wdg=None):
        """Clear all strip charts
        """
        self.stripChartWdg.clear()


if __name__ == "__main__":
    from . import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
