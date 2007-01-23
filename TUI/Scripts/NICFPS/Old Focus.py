#!/usr/local/bin/python
"""Take a series of NICFPS exposures at different focus positions to estimate best focus.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.

To do:
- Overhaul to work more like DIS:Focus:
  - Tolerate a few missing images from the sequence.
  - Incorporate graph into main window
- Fail unless NICFPS is in imaging mode.

History:
2005-04-30 SBeland  Copied/enhanced from NICFPS Dither script
2006-02-01 SBeland  Modified to use full window mode to try to avoid the persistence
                    seen on the chip in window mode.
2006-04-24 ROwen    Modified to not use pylab.
                    Graph windows are now normal TUI toplevels, so their position is remembered.
                    Improved backlash compensation to use a constant amount of compensation
                    and to apply for first focus move as well as final move to best focus.
                    Changed OffsetWaitMS to FocusWaitMS.
                    Changed to be a class, so requires TUI 1.2 or later.
                    Added Default button and DefDeltaFoc constant.
                    Added code to usefully run in debug mode.
                    Warning: not tested talking to NICFPS.
2006-06-01 ROwen    Added Centroid Radius control.
                    Added a log panel to output results.
2006-06-05 ROwen    Added matplotlib.use("TkAgg") and matplotlib.rcParams["numerix"] = "numarray"
                    to avoid problems with user's configuration files.
                    Fixed radius->cradius.
                    Changed default radius from 50 to 20.
                    Changed backlash compensation from 500um to 50um.
2006-09-27 ROwen    Changed to graph as data comes in.
                    PR 451: graph only worked for the first execution.
2006-11-01 ROwen    Tweaked for the new RO.Wdg.LogWdg.
                    Another fix for PR 451: graph only worked for the first execution.
2006-11-07 ROwen    Stopping the script during an exposure will now stop the exposure.
2006-11-09 ROwen    Removed any attempt to show images.
"""
import math
import numarray
import Tkinter
import Image
import RO.Wdg
import RO.Constants
import RO.StringUtil
import TUI.TUIModel
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.NICFPS.NICFPSModel
import TUI.Guide.GuideModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

import matplotlib
matplotlib.use("TkAgg")
matplotlib.rcParams["numerix"] = "numarray"
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# constants
InstName = "NICFPS"
DefStarXPos = 512   # default initial pixel coordinates of star to measure
DefStarYPos = 512
DefRadius = 20 # default centroid radius
DefFocusNPos = 6  # number of focus positions
DefDeltaFoc = 200 # default focus range around current focus
FocusWaitMS = 1000 # time to wait after every focus adjustment (ms)
BacklashComp = 50 # amount of backlash compensation, in microns (0 for none)

PlotTitle = "Private.NICFPS Focus Plot"
HelpURL = "Scripts/BuiltInScripts/NICFPSFocus.html"

MicronStr = RO.StringUtil.MuStr + "m"

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?

class ScriptClass(object):
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        self.currNFS = None
        self.sr = sr
        sr.debug = Debug
        
        # values passed between subroutines
        self.focDir = None
        self.starXPos = None
        self.starYPos = None
        
        # fake data for debug mode
        self.debugIterFWHM = None
        
        # get various models
        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.tuiModel = TUI.TUIModel.getModel()
        self.nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()
        self.nfocusModel = TUI.Guide.GuideModel.getModel("nfocus")
        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
        
        row=0
        
        # standard exposure status widget
        expStatusWdg = ExposeStatusWdg(sr.master, InstName)
        expStatusWdg.grid(row=row, column=0, sticky="news")
        row += 1
        
        # standard exposure input widget
        self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
        self.expWdg.numExpWdg.helpText = "# of exposures at each focus position"
        self.expWdg.grid(row=row, column=0, sticky="news")
        row += 1
        
        starPosFrame = Tkinter.Frame(self.expWdg)
    
        self.starXPosWdg = RO.Wdg.IntEntry(
            master = starPosFrame,
            minValue = 1,
            maxValue = 1024,
            defValue = DefStarXPos,
            helpText = "X coordinate of star to measure",
            helpURL = HelpURL,
        )
        self.starXPosWdg.pack(side="left")

        self.starYPosWdg = RO.Wdg.IntEntry(
            master = starPosFrame,
            minValue = 0,
            maxValue = 1024,
            defValue = DefStarYPos,
            helpText = "Y coordinate of star to measure",
            helpURL = HelpURL,
        )
        self.starYPosWdg.pack(side="left")
        
        self.expWdg.gridder.gridWdg("Star Position", starPosFrame, "pixels")
        
        self.centroidRadWdg = RO.Wdg.IntEntry(
            master = self.expWdg,
            minValue = 5,
            maxValue = 1024,
            defValue = DefRadius,
            helpText = "Centroid radius",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Centroid Radius", self.centroidRadWdg, "pixels", sticky="ew")

        setDefFocusWdg = RO.Wdg.Button(
            master = self.expWdg,
            text = "Default",
            callFunc = self.setDefFocus,
            helpText = "Set default start and end focus",
            helpURL = HelpURL,
        )
    
        self.startFocusPosWdg = RO.Wdg.IntEntry(
            master = self.expWdg,
            minValue = -2000,
            helpText = "Initial focus position",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Start Focus", self.startFocusPosWdg, MicronStr, sticky="ew")
        setDefFocusWdg.grid(
            row = self.expWdg.gridder.getNextRow() - 1,
            column = self.expWdg.gridder.getNextCol(),
        )
    
        self.endFocusPosWdg = RO.Wdg.IntEntry(
            master = self.expWdg,
            maxValue = 2000,
            helpText = "Final focus position",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("End Focus", self.endFocusPosWdg, MicronStr, sticky="ew")
    
        self.numFocusPosWdg = RO.Wdg.IntEntry(
            master = self.expWdg,
            minValue = 2,
            defValue = DefFocusNPos,
            helpText = "Number of focus positions",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Focus Positions", self.numFocusPosWdg, "", sticky="ew")
        
        self.focusIncrWdg = RO.Wdg.FloatEntry(
            master = self.expWdg,
            defFormat = "%.0f",
            readOnly = True,
            relief = "flat",
            helpText = "Focus step size",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Focus Increment", self.focusIncrWdg, MicronStr, sticky="ew")
        
       # create the move to best focus checkbox
        self.moveBestFocus = RO.Wdg.Checkbutton(
            master = self.expWdg,
            text = "Move to Best Focus",
            defValue = True,
            relief = "flat",
            helpText = "Move to Best Focus when done?",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg(None, self.moveBestFocus, colSpan = 3)
    
        # create the plotfwhm checkbox
        self.plotFitWdg = RO.Wdg.Checkbutton(
            master = self.expWdg,
            text = "Plot FWHM",
            defValue = True,
            relief = "flat",
            helpText = "Plot FWHM vs focus?",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg(None, self.plotFitWdg, colSpan = 3)
        
        self.logWdg = RO.Wdg.LogWdg(
            master = self.expWdg,
            height = 5,
            width = 10,
            helpText = "Measured and fit results",
            helpURL = HelpURL,
            relief = "sunken",
            bd = 2,
        )
        self.expWdg.gridder.gridWdg("Results", self.logWdg, sticky="ew", colSpan = 10)
        self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
        self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
    
        # plot toplevel window and associated objects
        self.plotTL = self.tuiModel.tlSet.getToplevel(PlotTitle)
        if not self.plotTL:
            # create a new plot toplevel
            self.plotTL = self.tuiModel.tlSet.createToplevel(PlotTitle, defVisible=False)
        else:
            # reuse existing plot window; clear out widgets
            wdgs = self.plotTL.winfo_children()
            for wdg in wdgs:
                wdg.destroy()
        self.plotFig = Figure()
        self.figCanvas = FigureCanvasTkAgg(self.plotFig, self.plotTL)
        self.figCanvas.get_tk_widget().grid(row=0, column=0, sticky="news")
        self.plotAxis = self.plotFig.add_subplot(1, 1, 1, autoscale_on=False)
    
        self.endFocusPosWdg.addCallback(self.updFocusIncr, callNow=False)
        self.startFocusPosWdg.addCallback(self.updFocusIncr, callNow=False)
        self.numFocusPosWdg.addCallback(self.updFocusIncr, callNow=True)
        
        if sr.debug:
            self.expWdg.timeWdg.set("1")
            self.expWdg.fileNameWdg.set("DEBUG_MODE")
            self.startFocusPosWdg.set(-50)
            self.endFocusPosWdg.set(100)
            self.numFocusPosWdg.set(3)
    
    def updFocusIncr(self, *args):
        """Update focus increment widget.
        """
        startPos = self.startFocusPosWdg.getNumOrNone()
        endPos = self.endFocusPosWdg.getNumOrNone()
        numPos = self.numFocusPosWdg.getNumOrNone()
        if None in (startPos, endPos, numPos):
            self.focusIncrWdg.set(None, isCurrent = False)
            return

        focusIncr = (endPos - startPos) / (numPos - 1)
        self.focusIncrWdg.set(focusIncr, isCurrent = True)
    
    def setDefFocus(self, *args):
        """Set focus start and end widgets to default values
        based on the current focus.
        """
        currFocus = self.sr.getKeyVar(self.tccModel.secFocus)
        self.startFocusPosWdg.set(currFocus - (DefDeltaFoc / 2))
        self.endFocusPosWdg.set(currFocus + (DefDeltaFoc / 2))
    
    def run(self, sr):
        """Take the series of focus exposures.
        """
        # clear the plot and results
        self.logWdg.clearOutput()
        self.logWdg.addOutput("\tfocus\tFWHM\tFWHM\n")
        self.logWdg.addOutput("\t%s\tpixels\tarcsec\n" % MicronStr)
        
        # fake data for debug mode
        # iteration #, FWHM
        self.debugIterFWHM = (1, 2.0)

        if not sr.debug:
            # Make sure current instrument is NICFPS
            currInstName = sr.getKeyVar(self.tccModel.instName)
            if not currInstName.lower().startswith(InstName.lower()):
                raise sr.ScriptError("%s is not the current instrument (%s)!" % (InstName,currInstName))
        
            # make sure we are in CDS mode for the focus script
            self.currNFS = sr.getKeyVar(self.nicfpsModel.fowlerSamples) 
            yield sr.waitCmd(
                actor = "nicfps",
                cmdStr = "fowler nfs=1"
            )
    
        # record parameters now so they will not change if the user
        # modifies them while the script is running
        self.starXPos   = self.starXPosWdg.getNum()
        self.starYPos   = self.starYPosWdg.getNum()
        self.centroidRad = self.centroidRadWdg.getNum()
        startFocPos = self.startFocusPosWdg.getNum()
        endFocPos   = self.endFocusPosWdg.getNum()
        numFocPos   = self.numFocusPosWdg.getNum()
        if numFocPos < 2:
            raise sr.ScriptError("# Focus Positions < 2")
        incFocus    = self.focusIncrWdg.getNum()
        numExpPerFoc = self.expWdg.numExpWdg.getNum()
        self.focDir = (endFocPos > startFocPos)
        doPlot = self.plotFitWdg.getBool()
        
        # get exposure command prefix (without startNum and totNum)
        expCmdPrefix = self.expWdg.getString()
    
        # arrays for holding values as we take exposures
        focPosArr = numarray.zeros(numFocPos, "Float")
        fwhmArr  = numarray.zeros(numFocPos, "Float")
        coeffArr = numarray.zeros(numFocPos, "Float")
        weightArr = numarray.ones(numFocPos, "Float")

        for focInd in range(numFocPos):
            focPosArr[focInd] = int(startFocPos + round(focInd*incFocus))

        if doPlot:
            self.plotAxis.clear()
            self.plotAxis.set_xlabel('Focus Position (microns)')
            self.plotAxis.set_ylabel('FWHM (pixels)')
            self.plotAxis.set_xlim((focPosArr.min(), focPosArr.max()))
            self.plotAxis.grid(True)
            self.plotLine = self.plotAxis.plot([], [], 'bo')[0]
            self.figCanvas.draw()
            self.plotTL.makeVisible()
        else:
            self.plotTL.withdraw()
        
        numExpTaken = 0
        for focInd in range(numFocPos):
            focPos = focPosArr[focInd]

            # compute # of exposures & format expose command
            if self.moveBestFocus.getBool():
                totFocPos = numFocPos + 1
            else:
                totFocPos = numFocPos
            totNumExp = totFocPos * numExpPerFoc

            startNum = numExpTaken + 1
            expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNumExp)
            
            doBacklashComp = (numExpTaken == 0)
            yield self.waitSetFocus(sr, focPos, expCmdStr, doBacklashComp)
            
            fwhmArr[focInd] = sr.value
            self.logFocusMeas("Exp %d" % focInd, focPos, fwhmArr[focInd])
            # print "********************************************************************"
            # print "Exposure: %d,  Focus: %d,  FWHM:%0.1f" % (focInd,focPos, fwhmArr[focInd])
            # print "********************************************************************"
            
            if doPlot:
                self.plotLine.set_data(focPosArr[:focInd+1], fwhmArr[:focInd+1])
                self.plotAxis.set_xlim(focPosArr.min(), focPosArr.max())
                self.plotAxis.set_ylim(fwhmArr.min(), fwhmArr.max())
                self.figCanvas.draw()
            
            numExpTaken += numExpPerFoc
    
        #Fit a curve to the data
        coeffArr = polyfitw(focPosArr,fwhmArr,weightArr, 2, 0)
        
        # find the best focus position
        bestEstFocPos = (-1.0*coeffArr[1])/(2.0*coeffArr[2])
        bestEstFWHM = coeffArr[0]+coeffArr[1]*bestEstFocPos+coeffArr[2]*bestEstFocPos*bestEstFocPos
        
        self.logFocusMeas("BestEst", bestEstFocPos, bestEstFWHM)
    
    
        ######################################################################
        # move to best focus if "Move to best Focus" checked
        movebest = self.moveBestFocus.getBool()
        if movebest:
            totNum = numExpTaken + numExpPerFoc
            startNum = numExpTaken + 1
            
            expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)

            yield self.waitSetFocus(sr, bestEstFocPos, expCmdStr, doBacklashComp=True)
            finalFWHM = sr.value
            
            self.logFocusMeas("Exp %d" % totNum, bestEstFocPos, finalFWHM)
    
    
        ######################################################################
        # verify if the "Plot FWHM" has been checked
        if doPlot:
            
            # generate the data from the 2nd order fit
            x = numarray.arange(min(focPosArr),max(focPosArr),1)
            y = coeffArr[0] + coeffArr[1]*x + coeffArr[2]*(x**2.0)
            
            # plot the fit
            self.plotAxis.set_autoscale_on(True)
            self.plotAxis.plot(x, y, '-k', linewidth=2)
            
            # ...and the chosen focus position in green
#           print "bestEstFocPos=",bestEstFocPos
#           print "bestEstFWHM=",bestEstFWHM
            self.plotAxis.plot([bestEstFocPos], [bestEstFWHM], 'go')
            
            # ...and the final focus position in red (if image taken there)
            if movebest:
#               print "finalFWHM=",finalFWHM
                self.plotAxis.plot([bestEstFocPos], [finalFWHM], 'ro')
            
            if movebest:
                self.plotAxis.set_title('Best Focus at %0.0f (est. = %0.1f; measured = %0.1f pixels = %0.1f arcsec)' % (bestEstFocPos,bestEstFWHM,finalFWHM, finalFWHM*self.nicfpsModel.arcsecPerPixel))
            else:
                self.plotAxis.set_title('Best Focus at %0.0f (est.: %0.1f pixels (%0.1f arcsec))' % (bestEstFocPos,bestEstFWHM,bestEstFWHM*self.nicfpsModel.arcsecPerPixel))
            self.figCanvas.draw()
            
    def logFocusMeas(self, name, focPos, fwhm):
        """Log a focus measurement.
        The name should be less than 8 characters long.
        """
        self.logWdg.addOutput("%s\t%d\t%0.1f\t%0.1f\n" % \
            (name, focPos, fwhm, fwhm * self.nicfpsModel.arcsecPerPixel)
        )
    
    
    def waitSetFocus(self, sr, focPos, expCmdStr, doBacklashComp=False):
        """Adjust focus, take an exposure and measure fwhm.

        To use: yield waitSetFocus(...)
        
        Inputs:
        - focPos: new focus position in um
        - expCmdStr: the exposure command
        
        Sets sr.value to the new fwhm (in binned pixels)        
        """
        # to try to eliminate the backlash in the secondary mirror drive move back 1/2 the
        # distance between the start and end position from the bestEstFocPos
        if doBacklashComp and BacklashComp:
            backlashFocPos = focPos - (abs(BacklashComp) * self.focDir)
            sr.showMsg("Backlash comp: moving focus to %d %sm" % (backlashFocPos, RO.StringUtil.MuStr))
            yield sr.waitCmd(
               actor = "tcc",
               cmdStr = "set focus=%d" % (backlashFocPos),
            )
            yield sr.waitMS(FocusWaitMS)
        
        # move to best position, take another image and measure the final FWHM at that focus position
        sr.showMsg("Moving focus to %d %sm" % (focPos, RO.StringUtil.MuStr))
        yield sr.waitCmd(
           actor = "tcc",
           cmdStr = "set focus=%d" % (focPos),
        )
        yield sr.waitMS(FocusWaitMS)
        
        # take exposure sequence
        sr.showMsg("Expose at focus position %d %sm" % (focPos, RO.StringUtil.MuStr))
        yield sr.waitCmd(
           actor = self.expModel.actor,
           cmdStr = expCmdStr,
           abortCmdStr = "stop",
        )
        
        fileComponents = sr.getKeyVar(self.expModel.files, ind=None)
        if sr.debug:
            fileComponents = ["cmdr", "host", "/common/root/", "prog/date/", "subdir/", "debugmode.fits"]
        shortFilePath = "".join(fileComponents[3:6])
        filePath = "".join(fileComponents[2:6])
        
        # get the FWHM from the guide camera model
        sr.showMsg("Analyzing %s for FWHM" % shortFilePath)
        yield sr.waitCmd(
           actor = "nfocus",
           cmdStr = "centroid file=%s on=%d,%d cradius=%d" % (filePath, self.starXPos, self.starYPos, self.centroidRad),
        )
        
        sr.value = sr.getKeyVar(self.nfocusModel.star, 8)
        if sr.debug:
            iterNum, fwhm = self.debugIterFWHM
            sr.value = fwhm
            if iterNum == 1:
                nextFWHM = fwhm - 0.2
            else:
                nextFWHM = fwhm + 0.2
            self.debugIterFWHM = (iterNum + 1, nextFWHM)
    
    def end(self, sr):
        """If telescope moved, restore original boresight position.
        """
        if self.currNFS != None:
            sr.startCmd(
                actor = "nicfps",
                cmdStr = "fowler nfs=%d" % self.currNFS
            )
    
    
import Numeric
import LinearAlgebra

############################################################
def polyfitw(x, y, w, ndegree, return_fit=0):
    """
    Performs a weighted least-squares polynomial fit with optional error estimates.

    Inputs:
        x: 
            The independent variable vector.

        y: 
            The dependent variable vector.  This vector should be the same 
            length as X.

        w: 
            The vector of weights.  This vector should be same length as 
            X and Y.

        ndegree: 
            The degree of polynomial to fit.

    Outputs:
        If return_fit==0 (the default) then polyfitw returns only C, a vector of 
        coefficients of length ndegree+1.
        If return_fit!=0 then polyfitw returns a tuple (c, yfit, yband, sigma, a)
            yfit:   
            The vector of calculated Y's.  Has an error of + or - Yband.

            yband: 
            Error estimate for each point = 1 sigma.

            sigma: 
            The standard deviation in Y units.

            a: 
            Correlation matrix of the coefficients.

    Written by:  George Lawrence, LASP, University of Colorado,
                    December, 1981 in IDL.
                    Weights added, April, 1987,  G. Lawrence
                    Fixed bug with checking number of params, November, 1998, 
                    Mark Rivers.  
                    Python version, May 2002, Mark Rivers
    """
    n = min(len(x), len(y)) # size = smaller of x,y
    m = ndegree + 1             # number of elements in coeff vector
    a = Numeric.zeros((m,m),Numeric.Float)  # least square matrix, weighted matrix
    b = Numeric.zeros(m,Numeric.Float)   # will contain sum w*y*x^j
    z = Numeric.ones(n,Numeric.Float)    # basis vector for constant term

    a[0,0] = Numeric.sum(w)
    b[0] = Numeric.sum(w*y)

    for p in range(1, 2*ndegree+1):      # power loop
        z = z*x # z is now x^p
        if (p < m):  b[p] = Numeric.sum(w*y*z)  # b is sum w*y*x^j
        sum = Numeric.sum(w*z)
        for j in range(max(0,(p-ndegree)), min(ndegree,p)+1):
            a[j,p-j] = sum

    a = LinearAlgebra.inverse(a)
    c = Numeric.matrixmultiply(b, a)
    if (return_fit == 0):
        return c         # exit if only fit coefficients are wanted

    # compute optional output parameters.
    yfit = Numeric.zeros(n,Numeric.Float)+c[0]  # one-sigma error estimates, init
    for k in range(1, ndegree +1):
        yfit = yfit + c[k]*(x**k)  # sum basis vectors
    var = Numeric.sum((yfit-y)**2 )/(n-m)  # variance estimate, unbiased
    sigma = Numeric.sqrt(var)
    yband = Numeric.zeros(n,Numeric.Float) + a[0,0]
    z = Numeric.ones(n,Numeric.Float)
    for p in range(1,2*ndegree+1):      # compute correlated error estimates on y
        z = z*x      # z is now x^p
        sum = 0.
        for j in range(max(0, (p - ndegree)), min(ndegree, p)+1):
            sum = sum + a[j,p-j]
        yband = yband + sum * z      # add in all the error sources
    yband = yband*var
    yband = Numeric.sqrt(yband)
    return c, yfit, yband, sigma, a
    

