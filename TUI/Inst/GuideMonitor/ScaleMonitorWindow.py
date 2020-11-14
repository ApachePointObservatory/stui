import RO.Wdg
import TUI
#import Tkinter
#import TUI.PlaySound
import time
import matplotlib
"""Scale monitor

History:
2012-04-23 Elena Malanushenko, converted from a script to a window by Russell Owen
2012-06-04 ROwen    Fix clear button.
"""
import Tkinter
import matplotlib
import RO.Wdg
import TUI.Base.StripChartWdg
import TUI.Models

WindowName = "Inst.Scale Monitor"

def addWindow(tlSet):
    """Create the window for TUI.
    """
    tlSet.createToplevel(
        name = WindowName,
        defGeom = "+368+88",
        visible = False,
        resizable = True,
        wdgFunc = ScaleMonitorWdg,
    )

class ScaleMonitorWdg(Tkinter.Frame):
    def __init__(self, master, timeRange=1800, width=8, height=2.4):
        """Create a ScaleMonitorWdg
        
        Inputs:
        - master: parent Tk widget
        - timeRange: range of time displayed (seconds)
        - width: width of plot (inches)
        - height: height of plot (inches)
        """
        Tkinter.Frame.__init__(self, master)
        self.guiderModel = TUI.Models.getModel("guider")
        self.level=0.3
        
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
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=list(range(0, 61, 5))))

        subplotInd = 0

        def scaleCorr(val):
            vv = -val * 1.0e4
            if abs(vv) > self.level:
                pass
            return vv

        self.stripChartWdg.plotKeyVar(
            label = "Scale measured err",
            subplotInd = subplotInd,
            keyVar = self.guiderModel.scaleError,
            func = scaleCorr,
            keyInd = 0,
            color = "blue",
        )
        self.stripChartWdg.showY(self.level * 1.01, -self.level * 1.01, subplotInd=subplotInd)
        self.stripChartWdg.subplotArr[0].yaxis.set_label_text("Delta Scale x 1e-6")
        self.stripChartWdg.subplotArr[0].legend(loc=3, frameon=False)
        self.stripChartWdg.addConstantLine(0.0, subplotInd=subplotInd, color="grey")
        self.stripChartWdg.addConstantLine(self.level, subplotInd=subplotInd, color="red")
        self.stripChartWdg.addConstantLine(-self.level, subplotInd=subplotInd, color="red")

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
