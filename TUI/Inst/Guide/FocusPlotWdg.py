#!/usr/bin/env python
"""Plot showing guider focus

History:
2009-11-05 ROwen
2009-11-06 ROwen    Added display of seeing if available.
                    Bug fix: error reporing called StatusBar.showMsg instead of setMsg.
"""
import itertools
import os
import sys
import Tkinter

import numpy
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg

import RO.Constants
import RO.StringUtil
import TUI.Base.Wdg.StatusBar
import GuideImage

_HelpURL = "Instruments/FocusPlotWin.html"

ShowToolbar = False # show matplotlib toolbar on graph?

class FocusPlotWdg(Tkinter.Frame):
    def __init__(self,
        master,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)

        plotFig = matplotlib.figure.Figure()
        self.figCanvas = FigureCanvasTkAgg(plotFig, self)
        self.figCanvas.show()
        self.figCanvas.get_tk_widget().grid(row=0, column=0, sticky="news")
        if ShowToolbar:
            toolbar = NavigationToolbar2TkAgg(self.figCanvas, self)
            toolbar.update()
            toolbar.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.plotAxis = plotFig.add_subplot(1, 1, 1)
        
        self.statusBar = TUI.Base.Wdg.StatusBar(
            master = self,
            helpURL = _HelpURL,
        )
        self.statusBar.grid(row=1, column=0, sticky="ew")
        

    def plot(self, imObj):
        """Show plot for a new image; clear if imObj is None or has no plate info.
        """
#        print "FocusPlotWdg.plot(imObj=%s)" % (imObj,)
        self.clear()
        if imObj == None:
            return
        
        try:
            probeDataSeeing = self.getProbeData(imObj)
            if probeDataSeeing == None:
                return
            probeData, seeing = probeDataSeeing
        except Exception, e:
            print "FocusPlotWdg: would not get probe data: %s" % (e,)
            return
        try:
            isGoodArr = probeData.field("exists") & probeData.field("enabled") & \
                numpy.isfinite(probeData.field("fwhm"))
            if len(isGoodArr) == 0:
                return
            focusOffsetArr = numpy.extract(isGoodArr, probeData.field("focusOffset"))
            fwhmArr = numpy.extract(isGoodArr, probeData.field("fwhm"))
        except Exception, e:
            sys.stderr.write("FocusPlotWdg could not parse data in image %s: %s\n" % \
                (imObj.imageName, RO.StringUtil.strFromException(e)))
            return
        probeNumberArr = numpy.arange(1, len(fwhmArr), dtype=int)

        self.plotAxis.plot(focusOffsetArr, fwhmArr, color='black', linestyle="", marker='o', label="probe")
        
        # add probe numbers
        for focusOffset, fwhm, probeNumber in itertools.izip(focusOffsetArr, fwhmArr, probeNumberArr):
            self.plotAxis.annotate("%s" % (probeNumber,), (focusOffset, fwhm), xytext=(5, -5),
            textcoords="offset points")
         
        # add invisible 0,0 point to force autoscale to include origin
        self.plotAxis.plot([0.0], [0.0], linestyle="", marker="")
        
        # fit data and show the fit
        fitCoeff = self.fitFwhmSqVsFocusOffset(focusOffsetArr, fwhmArr)
        if fitCoeff != None:
            fitX = numpy.linspace(min(focusOffsetArr), max(focusOffsetArr), 50)
            fitY = numpy.sqrt((fitX * fitCoeff[0]) + fitCoeff[1])
            self.plotAxis.plot(fitX, fitY, color='blue', linestyle="-", label="best fit")

        # add seeing
        if numpy.isfinite(seeing):
            self.plotAxis.plot([0.0], [seeing], linestyle="", marker="x", markersize=12,
                color="green", markeredgewidth=1, label="seeing")
            
        self.plotAxis.set_title(imObj.imageName)
        
        legend = self.plotAxis.legend(loc=4, numpoints=1)
        legend.draw_frame(False)

        self.figCanvas.draw()
    
    def getProbeData(self, imObj):
        """Get guide probe data table, or None if the file is not a GPROC file
        
        Returns:
        - dataTable: guide probe data table (HDU[6].data)
        - seeing: seeing from HDU[0].header, if available, else nan
        """
        fitsObj = imObj.getFITSObj()
        try:
            sdssFmtStr = fitsObj[0].header["SDSSFMT"]
        except Exception:
            self.statusBar.setMsg("No SDSSFMT header entry",
                severity = RO.Constants.sevWarning, isTemp=True)

        try:
            formatName, versMajStr, versMinStr = sdssFmtStr.split()
            formatMajorVers = int(versMajStr)
            formatMinorVers = int(versMinStr)
        except Exception:
            self.statusBar.setMsg("Could not parse SDSSFMT=%r" % (sdssFmtStr,),
                severity = RO.Constants.sevWarning, isTemp=True)
            return None

        if formatName.lower() != "gproc":
            self.statusBar.setMsg("SDSSFMT = %s != gproc" % (formatName.lower(),),
                severity = RO.Constants.sevWarning, isTemp=True)
            return None
        
        try:
            seeingStr = fitsObj[0].header["SEEING"]
            seeing = float(seeingStr)
        except Exception:
            seeing = numpy.nan
        
        self.statusBar.clearTempMsg()
        return (fitsObj[6].data, seeing)
    
    def fitFwhmSqVsFocusOffset(self, focusOffsetArr, fwhmArr):
        """Fit FWHM^2 vs focus offset.
        
        Returns [coeff1, coeff0] if the fit succeeds; None otherwise.
        """
        if len(focusOffsetArr) < 2:
            return None
        if min(focusOffsetArr) == max(focusOffsetArr):
            return None
        
        fwhmSqArr = numpy.array(fwhmArr)**2
        
        return numpy.polyfit(focusOffsetArr, fwhmSqArr, 1)

    def clear(self):
        self.plotAxis.clear()
        self.plotAxis.grid(True)
        # start with autoscale disabled due to bug in matplotlib
        self.plotAxis.set_autoscale_on(True)
        self.plotAxis.set_xlabel("Guide probe focus offset (um)")
        self.plotAxis.set_ylabel("Guide star FWHM (arcsec)")
        self.figCanvas.draw()


if __name__ == "__main__":
    import GuideTest
    import GuideImage
    #import gc
    #gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages
    
    currDir = os.path.dirname(__file__)

    root = GuideTest.tuiModel.tkRoot

    GuideTest.init("guider")

    testFrame = FocusPlotWdg(root)
    testFrame.pack(expand="yes", fill="both")
    gim = GuideImage.GuideImage(
        localBaseDir = currDir,
        imageName = "proc-gimg-0072.fits",
        isLocal = True,
    )
    gim.getFITSObj()
    testFrame.plot(gim)

    root.mainloop()
