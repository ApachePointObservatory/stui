#!/usr/bin/env python
"""Seeing monitor

History:
2010-10-01 ROwen    Initial version.
2010-11-17 ROwen    Added measured and applied offsets for all guider corrections.
                    Split RA, Dec and rotator into separate graphs.
                    Added net rotator offset.
2010-11-19 ROwen    Display scaleFac as "percent": (scaleFac - 1) * 100
"""
import math
import Tkinter
import matplotlib
import RO.CnvUtil
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
    def __init__(self, master, timeRange=1800, width=9, height=9):
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
            numSubplots = 6,
            width = width,
            height = height,
            cnvTimeFunc = TUI.Base.StripChartWdg.TimeConverter(useUTC=True),
        )
        self.stripChartWdg.grid(row=0, column=0, sticky="nwes")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # the default ticks are not nice, so be explicit
        self.stripChartWdg.xaxis.set_major_locator(matplotlib.dates.MinuteLocator(byminute=range(0, 61, 5)))
        
        # mag subplot -- once we get the ref. mags we will replace with throughput.
        def plotFilteredKeyVar(plot, name, subplotInd, keyVar, keyInd=0, func=None, keyFilter=None, **kargs):
            """Plot one value of one keyVar, filtered though a passed in function.
        
            Inputs:
            - name: name of plot line (must be unique on the strip chart)
            - subplotInd: index of line on Subplot
            - keyVar: keyword variable to plot
            - keyInd: index of keyword variable to plot
            - func: function to transform the value; if None then there is no transformation
            - keyFilter: function to accept the value; if it returns False the key is ignored.
            **kargs: keyword arguments for StripChartWdg.addLine
            """
            plot.addLine(name, subplotInd=subplotInd, **kargs)
        
            if func == None:
                func = lambda x: x
        
            def callFunc(keyVar, name=name, keyInd=keyInd, func=func, keyFilter=keyFilter):
                if not keyVar.isCurrent or not keyVar.isGenuine:
                    return
                if keyFilter and not keyFilter(keyVar):
                    return
                val = keyVar[keyInd]
                if val == None:
                    return
                self.addPoint(name, func(val))
        
            keyVar.addCallback(callFunc, callNow=False)

        def plotProbe(owner, probeId, subplotInd, **kargs):
            def keyFilter(keyVar, probeId=probeId):
                return keyVar[1] == probeId

            plotFilteredKeyVar(owner.stripChartWdg, "probe %d" % (probeId), subplotInd,
                               owner.guiderModel.probe, keyInd=8, keyFilter=keyFilter, **kargs)

        subplotInd = 0
        # This isn't working yet, but without an error which I can sink my teeth into. pdb, Ho!
        #plotProbe(self, 3, subplotInd, color='red')
        #self.stripChartWdg.showY(19.0, 16.0, subplotInd=subplotInd)
        #self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Mag")
        #self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        #subplotInd += 1

        # RA/Dec arc offset subplot
        def arcsecFromPVT(val):
            return 3600.0 * RO.CnvUtil.posFromPVT(val)
        self.stripChartWdg.plotKeyVar("RA net offset", subplotInd=subplotInd, keyVar=self.tccModel.objArcOff, keyInd=0, func=arcsecFromPVT, color="blue")
        self.stripChartWdg.plotKeyVar("RA measured err", subplotInd=subplotInd, keyVar=self.guiderModel.axisError, keyInd=0, color="gray")
        self.stripChartWdg.plotKeyVar("RA applied corr", subplotInd=subplotInd, keyVar=self.guiderModel.axisChange, keyInd=0, color="green")
        self.stripChartWdg.showY(-0.5, 0.5, subplotInd=subplotInd)
        self.stripChartWdg.addConstantLine("RAOffsetZero", 0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("RA Arc Off (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

        self.stripChartWdg.plotKeyVar("Dec net offset", subplotInd=subplotInd, keyVar=self.tccModel.objArcOff, keyInd=1, func=arcsecFromPVT, color="blue")
        self.stripChartWdg.plotKeyVar("Dec measured err", subplotInd=subplotInd, keyVar=self.guiderModel.axisError, keyInd=1, color="gray")
        self.stripChartWdg.plotKeyVar("Dec applied corr", subplotInd=subplotInd, keyVar=self.guiderModel.axisChange, keyInd=1, color="green")
        self.stripChartWdg.showY(-0.5, 0.5, subplotInd=subplotInd)
        self.stripChartWdg.addConstantLine("DecOffsetZero", 0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Dec Arc Off (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

        # rotator offset subplot
        self.stripChartWdg.plotKeyVar("Rot net offset", subplotInd=subplotInd, keyVar=self.tccModel.guideOff, keyInd=2, func=arcsecFromPVT, color="blue")
        self.stripChartWdg.plotKeyVar("Rot measured err", subplotInd=subplotInd, keyVar=self.guiderModel.axisError, keyInd=2, color="gray")
        self.stripChartWdg.plotKeyVar("Rot applied corr", subplotInd=subplotInd, keyVar=self.guiderModel.axisChange, keyInd=2, color="green")
        self.stripChartWdg.showY(-2.0, 2.0, subplotInd=subplotInd)
        self.stripChartWdg.addConstantLine("RotOffsetZero", 0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Rot Off (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

        # seeing subplot
        self.stripChartWdg.plotKeyVar("Seeing", subplotInd=subplotInd, keyVar=self.guiderModel.seeing, keyInd=0, color="blue")
        self.stripChartWdg.showY(1.0, 1.2, subplotInd=subplotInd)
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Seeing (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1
        
        # focus subplot
        self.stripChartWdg.plotKeyVar("Focus net offset", subplotInd=subplotInd, keyVar=self.tccModel.secFocus, color="blue")
        self.stripChartWdg.plotKeyVar("Focus measured err", subplotInd=subplotInd, keyVar=self.guiderModel.focusError, color="gray")
        self.stripChartWdg.plotKeyVar("Focus applied corr", subplotInd=subplotInd, keyVar=self.guiderModel.focusChange, color="green")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Focus (um)")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1
        
        # scale subplot
        def cnvAbsScale(val):
            return 100.0 * (val - 1.0)
        def cnvDeltaScale(val):
            return 100 * val
        self.stripChartWdg.plotKeyVar("Scale net", subplotInd=subplotInd, keyVar=self.tccModel.scaleFac, func=cnvAbsScale, color="blue")
        self.stripChartWdg.plotKeyVar("Scale measured err", subplotInd=subplotInd, func=cnvDeltaScale, keyVar=self.guiderModel.scaleError, color="gray")
        self.stripChartWdg.plotKeyVar("Scale applied corr", subplotInd=subplotInd, func=cnvDeltaScale, keyVar=self.guiderModel.scaleChange, color="green")
        self.stripChartWdg.addConstantLine("ScaleFac0", 0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.showY(-1.0e-4, 1.0e-4, subplotInd=subplotInd)
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Scale-1 %")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
