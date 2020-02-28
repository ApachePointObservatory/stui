#!/usr/bin/env python
"""Seeing monitor

History:
2012-04-23 Elena Malanushenko, converted from a script to a window by Russell Owen
2012-06-04 ROwen    Fix clear button.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import Tkinter
import matplotlib
import RO.Wdg
import TUI.Base.StripChartWdg
import TUI.Models

WindowName = "Inst.Flux Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+412+44",
        visible = False,
        resizable = True,
        wdgFunc = FluxMonitorWdg,
    )

class FluxMonitorWdg(Tkinter.Frame):
    def __init__(self, master, timeRange=3600, width=8, height=2.4):
        """Create a FluxMonitorWdg
        
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
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=list(range(0, 61, 10))))

        subplotInd = 0

        def fluxFun(modelFlux):
            focOff = self.guiderModel.probe[6]
            if focOff == None:
                # ignore out-of-focus probes
                return None

            expTime = self.guiderModel.expTime[0]
            if expTime == None:
                return None
            return modelFlux/expTime

        self.stripChartWdg.plotKeyVar(
            label = "Model Flux",
            subplotInd = subplotInd,
            keyVar = self.guiderModel.probe,
            keyInd = 7,
            func = fluxFun,
            color = "green",
        )
        self.stripChartWdg.showY(0.0, 1.0, subplotInd=0)
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("Model Flux (ADU/sec)")

        self.clearWdg = RO.Wdg.Button(master = self, text = "C", callFunc = self.clearCharts)
        self.clearWdg.grid(row=0, column=0, sticky = "sw")
    
    def clearCharts(self, wdg=None):
        """Clear all strip charts
        """
        self.stripChartWdg.clear()


if __name__ == "__main__":
    from . import TestData

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)

    # there isn't any flux data yet    
#    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
