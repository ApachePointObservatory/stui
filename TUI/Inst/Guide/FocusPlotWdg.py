#!/usr/bin/env python
"""Plot showing guider focus

History:
2009-11-05 ROwen
2009-11-06 ROwen    Added display of seeing if available.
                    Bug fix: error reporing called StatusBar.showMsg instead of setMsg.
                    Bug fix: the number of the last guide probe was not shown.
2009-11-10 ROwen    Bug fix: if SDSSFMT card missing sdssFmtStr was accessed without being defined.
2009-11-13 ROwen    Bug fix: if probes were missing then probe labels were wrong.
                    Bug fix: was fitting the wrong equation.
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
            fitsObj = self.getFITSObj(imObj)
            if fitsObj == None:
                return
        except Exception, e:
            sys.stderr.write("FocusPlotWdg: could not get FITS object: %s\n" % \
                (RO.StringUtil.strFromException(e),))
            return
        try:
            probeData = fitsObj[6].data        
            numProbes = len(probeData)
            isGoodArr = probeData.field("exists") & probeData.field("enabled") & \
                numpy.isfinite(probeData.field("fwhm"))
            if len(isGoodArr) == 0:
                return
            focusOffsetArr = numpy.extract(isGoodArr, probeData.field("focusOffset"))
            fwhmArr = numpy.extract(isGoodArr, probeData.field("fwhm"))
            probeNumberArr = numpy.extract(isGoodArr, numpy.arange(1, numProbes + 1, dtype=int))
        except Exception, e:
            sys.stderr.write("FocusPlotWdg could not parse data in image %s: %s\n" % \
                (imObj.imageName, RO.StringUtil.strFromException(e)))
            return

        self.plotAxis.plot(focusOffsetArr, fwhmArr, color='black', linestyle="", marker='o', label="probe")
        
        # add probe numbers
        for focusOffset, fwhm, probeNumber in itertools.izip(focusOffsetArr, fwhmArr, probeNumberArr):
            self.plotAxis.annotate("%s" % (probeNumber,), (focusOffset, fwhm), xytext=(5, -5),
            textcoords="offset points")
         
        # add invisible 0,0 point to force autoscale to include origin
        self.plotAxis.plot([0.0], [0.0], linestyle="", marker="")
        
        # fit data and show the fit
        fitArrays = self.fitFocus(focusOffsetArr, fwhmArr, fitsObj)
        if fitArrays != None:
            self.plotAxis.plot(fitArrays[0], fitArrays[1], color='blue', linestyle="-", label="best fit")

        # add seeing
        try:
            seeingStr = fitsObj[0].header["SEEING"]
            seeing = float(seeingStr)
        except Exception:
            seeing = numpy.nan
        if numpy.isfinite(seeing):
            self.plotAxis.plot([0.0], [seeing], linestyle="", marker="x", markersize=12,
                color="green", markeredgewidth=1, label="seeing")
            
        self.plotAxis.set_title(imObj.imageName)
        
        legend = self.plotAxis.legend(loc=4, numpoints=1)
        legend.draw_frame(False)

        self.figCanvas.draw()
    
    def getFITSObj(self, imObj):
        """Get pyfits fits object, or None if the file is not a usable version of a GPROC file
        """
        fitsObj = imObj.getFITSObj()
        try:
            sdssFmtStr = fitsObj[0].header["SDSSFMT"]
        except Exception:
            self.statusBar.setMsg("No SDSSFMT header entry",
                severity = RO.Constants.sevWarning, isTemp=True)
            return None

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
        
        self.statusBar.clearTempMsg()
        return fitsObj

    def fitFocus(self, focusOffsetArr, fwhmArr, fitsObj, nPoints=50):
        """Fit a line to rms^2 - focus offset^2 vs. focus offset
        
        (after converting to suitable units)
        
        Inputs:
        - focusOffsetArr: array of focus offset values (um)
        - fwhmArr: array of FWHM values (arcsec)
        - nPoints: number of points desired in the returned fit arrays
        
        Returns [newFocusOffArr, fitFWHMArr] if the fit succeeds; None otherwise
        """
        if len(focusOffsetArr) < 2:
            self.statusBar.setMsg("Cannot fit data: too few data points",
                severity = RO.Constants.sevWarning, isTemp=True)
            return None
        if min(focusOffsetArr) == max(focusOffsetArr):
            self.statusBar.setMsg("Cannot fit data: no focus offset range",
                severity = RO.Constants.sevWarning, isTemp=True)
            return None
        try:
            plateScale = float(fitsObj[0].header["PLATSCAL"])

            focalRatio = 5.0
            C = 5.0 / (32.0 * focalRatio**2)

            # compute RMS in microns
            # RMS = FWHM / 2.35, but FWHM is in arcsec
            # plateScale is in mm/deg
            micronsPerArcsec = plateScale * 1.0e3 / 3600.0
            rmsArr = fwhmArr * (micronsPerArcsec / 2.35) # in microns
    
            yArr = rmsArr**2 - (C * focusOffsetArr**2)
            
            fitCoeff = numpy.polyfit(focusOffsetArr, yArr, 1)
    
            fitFocusOffsetArr = numpy.linspace(min(focusOffsetArr), max(focusOffsetArr), nPoints)
            fitYArr = (fitFocusOffsetArr * fitCoeff[0]) + fitCoeff[1]
            fitRMSSqArr = fitYArr + (C * fitFocusOffsetArr**2)
            
            fitFWHM = numpy.sqrt(fitRMSSqArr) * (2.35 / micronsPerArcsec)
            
            return [fitFocusOffsetArr, fitFWHM]
        except Exception, e:
            self.statusBar.setMsg("Cannot fit data: %s" % (RO.StringUtil.strFromException(e),),
                severity = RO.Constants.sevWarning, isTemp=True)
            return None
    
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

    testFrame = FocusPlotWdg(root)
    testFrame.pack(expand="yes", fill="both")
    gim = GuideImage.GuideImage(
        localBaseDir = currDir,
        imageName = "proc-gimg-1310.fits",
        isLocal = True,
    )
    gim.getFITSObj()
    testFrame.plot(gim)

    GuideTest.tuiModel.reactor.run()
