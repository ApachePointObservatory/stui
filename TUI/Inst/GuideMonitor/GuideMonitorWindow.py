#!/usr/bin/env python
"""Seeing monitor

History:
2010-10-01 ROwen    Initial version.
2010-11-17 ROwen    Added measured and applied offsets for all guider corrections.
                    Split RA, Dec and rotator into separate graphs.
                    Added net rotator offset.
2010-11-19 ROwen    Display scaleFac as "percent": (scaleFac - 1) * 100
2010-11-22 ROwen    Changed Scale scaling from 1e2 to 1e6.
2010-12-10 ROwen    Reduced the memory leak by increasing updateInterval from its default value of 0.9 sec
                    to 10 seconds. Return to the default value again once the matplotlib bug is fixed.
2011-01-03 ROwen    Modified to use new version of StripChartWdg.
                    Added measured FWHM to the seeing plot.
                    Added preliminary display of measured FWHM of each in-focus probe (no labelling).
2011-01-18 ROwen    Net values are shown as steps, since that properly reflects reality.
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
        self.probeInfoDict = dict() # dict of probe number (starting from 1): ProbeInfo
        
        self.stripChartWdg = TUI.Base.StripChartWdg.StripChartWdg(
            master = self,
            timeRange = timeRange,
            updateInterval = 10,
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

        subplotInd = 0
        
        # RA/Dec arc offset subplot
        def arcsecFromPVT(val):
            return 3600.0 * RO.CnvUtil.posFromPVT(val)
        self.stripChartWdg.plotKeyVar(
            label="RA net offset",
            subplotInd=subplotInd,
            keyVar=self.tccModel.objArcOff,
            keyInd=0,
            func=arcsecFromPVT,
            color="blue",
            drawstyle="steps-post",
        )
        self.stripChartWdg.plotKeyVar(
            label="RA measured err",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.axisError,
            keyInd=0,
            color="gray",
        )
        self.stripChartWdg.plotKeyVar(
            label="RA applied corr",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.axisChange,
            keyInd=0,
            color="green",
        )
        self.stripChartWdg.showY(-0.5, 0.5, subplotInd=subplotInd)
        self.stripChartWdg.addConstantLine(0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("RA Arc Off (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

        self.stripChartWdg.plotKeyVar(
            label="Dec net offset",
            subplotInd=subplotInd,
            keyVar=self.tccModel.objArcOff,
            keyInd=1,
            func=arcsecFromPVT,
            color="blue",
            drawstyle="steps-post",
        )
        self.stripChartWdg.plotKeyVar(
            label="Dec measured err",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.axisError,
            keyInd=1,
            color="gray",
        )
        self.stripChartWdg.plotKeyVar(
            label="Dec applied corr",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.axisChange,
            keyInd=1,
            color="green",
        )
        self.stripChartWdg.showY(-0.5, 0.5, subplotInd=subplotInd)
        self.stripChartWdg.addConstantLine(0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Dec Arc Off (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

        # rotator offset subplot
        self.stripChartWdg.plotKeyVar(
            label="Rot net offset",
            subplotInd=subplotInd,
            keyVar=self.tccModel.guideOff,
            keyInd=2,
            func=arcsecFromPVT,
            color="blue",
            drawstyle="steps-post",
        )
        self.stripChartWdg.plotKeyVar(
            label="Rot measured err",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.axisError,
            keyInd=2,
            color="gray",
        )
        self.stripChartWdg.plotKeyVar(
            label="Rot applied corr",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.axisChange,
            keyInd=2,
            color="green",
        )
        self.stripChartWdg.showY(-2.0, 2.0, subplotInd=subplotInd)
        self.stripChartWdg.addConstantLine(0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Rot Off (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1

        # seeing subplot
        self.seeingSubplotInd = subplotInd
        self.stripChartWdg.plotKeyVar(
            label="Measured",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.fwhm,
            keyInd=1,
            color="blue",
        )
        self.stripChartWdg.plotKeyVar(
            label="Theoretical",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.seeing,
            keyInd=0,
            color="green",
        )
        self.stripChartWdg.showY(1.0, 1.2, subplotInd=subplotInd)
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Seeing (\")")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1
        
        # focus subplot
        self.stripChartWdg.plotKeyVar(
            label="Focus net offset",
            subplotInd=subplotInd,
            keyVar=self.tccModel.secFocus,
            color="blue",
            drawstyle="steps-post",
        )
        self.stripChartWdg.plotKeyVar(
            label="Focus measured err",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.focusError,
            color="gray",
        )
        self.stripChartWdg.plotKeyVar(
            label="Focus applied corr",
            subplotInd=subplotInd,
            keyVar=self.guiderModel.focusChange,
            color="green",
        )
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Focus (um)")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1
        
        # scale subplot
        def cnvAbsScale(val):
            return (val - 1.0) * 1.0e6
        def cnvDeltaScale(val):
            return val * 1.0e6
        self.stripChartWdg.plotKeyVar(
            label="Scale net",
            subplotInd=subplotInd,
            keyVar=self.tccModel.scaleFac,
            func=cnvAbsScale,
            color="blue",
            drawstyle="steps-post",
        )
        self.stripChartWdg.plotKeyVar(
            label="Scale measured err",
            subplotInd=subplotInd,
            func=cnvDeltaScale,
            keyVar=self.guiderModel.scaleError,
            color="gray",
        )
        self.stripChartWdg.plotKeyVar(
            label="Scale applied corr",
            subplotInd=subplotInd,
            func=cnvDeltaScale,
            keyVar=self.guiderModel.scaleChange,
            color="green",
        )
        self.stripChartWdg.addConstantLine(0.0, subplotInd=subplotInd, color="gray")
        self.stripChartWdg.subplotArr[subplotInd].yaxis.set_label_text("Scale 1e6")
        self.stripChartWdg.subplotArr[subplotInd].legend(loc=3, frameon=False)
        subplotInd += 1
        
        self.guiderModel.probe.addCallback(self.probeCallback)

    def cartridgeLoadedCallback(self, keyVar):
        """guider.cartridgeLoaded keyvar callback
        
        When seen ditch all guide-probe-specific lines
        """
        self.clearProbeInfo()

    def clearProbeInfo(self):
        """Clear self.probeInfoDict and remove associated lines from plots
        """
        for probeInfo in self.probeInfoDict.itervalues():
            probeInfo.remove()
        self.probeInfoDict = dict()

    def probeCallback(self, keyVar):
        """guider.probe callback
        
        If guide probe is broken, unused or out of focus do nothing. Otherwise:
        - If probeInfo does not exist, create it and the associated plot line
        - Plot data. If probe is disabled then plot "nan" so that no point shows
            and lines remain broken if the probe is re-enabled later.
        """
#        print "%s.probeCallback(%s)" % (self, keyVar)
        if (not keyVar.isCurrent) or (not keyVar.isGenuine) or (keyVar[1] == None):
            return
        if (not self.guiderModel.fullGProbeBits.isCurrent) or (self.guiderModel.fullGProbeBits[0] == None):
            return

        probeNum = keyVar[1]
        if self.guiderModel.fullGProbeBits[probeNum - 1] & 3 > 0:
            # broken or unused
            return
        if abs(keyVar[6]) > 50:
            # not an in-focus probe
            return

        probeInfo = self.probeInfoDict.get(probeNum)
        if probeInfo == None:
            probeInfo = ProbeInfo(num=probeNum, guideMonitorWdg=self)
            self.probeInfoDict[probeNum] = probeInfo

        probeInfo.plotData(keyVar)


class ProbeInfo(object):
    def __init__(self, num, guideMonitorWdg):
        """Information about a guide probe, including lines on the strip chart
        """
        self.num = int(num)
        self.guiderModel = guideMonitorWdg.guiderModel
        self.stripChartWdg = guideMonitorWdg.stripChartWdg
        self.fwhmLine = self.stripChartWdg.addLine(
            subplotInd=guideMonitorWdg.seeingSubplotInd,
            color = "blue",
            linestyle = "",
            marker = ",",
        )

    def plotData(self, keyVar):
        """guider.probe callback
        
        Plot data. If probe is disabled then plot "nan" so that no point shows
        an lines remain broken if the probe is re-enabled later.
        """
#        print "%s.probeCallback(%s)" % (self, keyVar)
        if self.guiderModel.fullGProbeBits[self.num - 1] & 7 > 0:
            # broken, unused or disabled; testing broken or unused is paranoia
            # since this object should never have been created, but costs no extra time
#            print "%s.plotData(%s); plot NaN" % (self, keyVar)
            self.fwhmLine.addPoint(float("nan"))
        else:
#            print "%s.plotData(%s); plot %s" % (self, keyVar, keyVar[5])
            self.fwhmLine.addPoint(keyVar[5])
        
    def remove(self):
        """Remove all associated plot lines
        """
        self.stripChartWdg.remove(self.fwhmLine)
    
    def __str__(self):
        return "ProbeInfo(%s)" % (self.num,)


if __name__ == "__main__":
    import TestData
    import RO.Wdg

    addWindow(TestData.tuiModel.tlSet)
    TestData.tuiModel.tlSet.makeVisible(WindowName)
    
    TestData.runTest()
    
    TestData.tuiModel.reactor.run()
