"""A basic focus script for slitviewers
(changes will be required for gcam and instruments).

Subclass for more functionality.

Take a series of exposures at different focus positions to estimate best focus.

Note:
- The script runs in two phases:
  1) If a slitviewer:
        Move the boresight and take an exposure. Then pause.
        The user is expected to acquire a suitable star before resuming.
        Once this phase begins (i.e. once you start the script)
        changes to boresight offset are ignored.
    Other imagers:
        Take an exposure and look for the best centroidable star. Then pause.
        The user is expected to acquire a suitable star before resuming.
  2) Take the focus sweep.
    Once this phase begins all inputs are ignored.

History:
2006-11-07 ROwen    From DIS:Focus, which was from NICFPS:Focus.
2006-11-09 ROwen    Removed use of plotAxis.autoscale_view(scalex=False, scaley=True)
                    since it was not compatible with older versions of matplotlib.
                    Stopped using float("nan") since it doesn't work on all pythons.
                    Modified to always pause before the focus sweep.
                    Modified to window the exposure.
2006-11-13 ROwen    Modified to have user set center focus and range.
                    Added Expose and Sweep buttons.
2006-12-01 ROwen    Refactored to make it easier to use for non-slitviewers:
                    - Added waitFocusSweep method.
                    - Modified to use focPosFWHMList instead of two lists.
                    Improved sanity-checking the best focus fit.
                    Created SlitviewerFocusScript and OffsetGuiderFocusScript classes;
                    the latter is not yet fully written.
2006-12-08 ROwen    More refactoring. Created ImagerFocusScript class.
                    Needs extensive testing.
2006-12-13 ROwen    Added Find button and changed Centroid to Measure.
                    Data is always nulled at start of sweep. This is much easier than
                    trying to be figure out when I can safely keep existing data.
                    Fit error is logged.
                    Fit is logged and graphed even if fit is rejected (unless fit is a maximum).
                    Changed from Numeric to numarray to avoid a bug in matplotlib 0.87.7
                    Changed test for max fit focus error to a multiple of the focus range.
2006-12-28 ROwen    Bug fix: tried to send <inst>Expose time=<time> bin=<binfac>
                    command for imaging instruments. The correct command is:
                    <inst>Expose object time=<time>.
                    Noted that bin factor and window must be configured via special
                    instrument-specific commands.
                    ImagerFocusScript no longer makes use of windowing (while centroiding),
                    though a subclass could do so.
2006-12-28 ROwen    ImagerFocusScript.waitExpose now aborts the exposure if the script is aborted.
                    This change did not get into TUI 1.3a11. Note that this fix only applies to imaging
                    instruments; there is not yet any documented way to abort a guider exposure.
2007-01-02 ROwen    Fixed a bug in waitExpose: <inst> <inst>Expose -> <instExpose>.
                    Fixed a bug in waitFindStar: centroidRad used but not supplied.
                    Improved help text for Star Pos entry widgets.
2007-01-03 ROwen    Bug fixes:
                    - Used sr instead of self.sr in two places.
                    - ImagerFocusScript.getCentroidArgs returned bad
                      starpos due to wanting to window.
                    - ImagerFocusScript.waitCentroid failed if no star found
                      rather than returning sr.value = None.
2007-01-12 ROwen    Added a threshold for star finding (maxFindAmpl).
                    Added logging of sky and star amplitude.
2007-01-26 ROwen	Tweak various formats:
					- All reported and command floats use %0.xf (some used %.xf).
					- Focus is rounded to nearest integer for logging and setting.
					If new focus found, set Center Focus to the new value.
					Increased minimum # of focus positions from 2 to 3.
					Bug fix: if only 3 measurements, divided by zero while computing std. dev.
					Bug fix: could not restore initial focus (missing = in set focus command).
					Minor bug fix: focus interval was computed as int, not float.
2007-01-29 ROwen    Improved OffsetGuiderFocusScript to get guider info based on instPos
                    instead of insisting that the guider be the current instrument.
                    Modified to take advantage of RO.Wdg.Entry's new label attribute.
2007-01-29 ROwen    Fixed ImagerFocusScript (it was giving an illegal arg to OffsetGuiderFocusScript).
                    Refactored so run is in BaseFocusScript and ImagerFocusScript inherits from that.
                    Renamed extraSetup method to waitExtraSetup.
2007-02-13 ROwen    Added a Clear button.
                    Never auto-clears the log.
                    Waits to auto-clear the graph until new data is about to be graphed.
                    Simplified graph range handling.
2007-04-24 ROwen    Modified to use numpy instead of numarray.
2007-06-01 ROwen    Hacked in support for sfocus for SPIcam.
2007-06-04 ROwen    Added doWindow argument to BaseFocusScript.
2007-07-25 ROwen    ImagerFocusScript modified to sending windowing info as part of the expose command
                    if windowing is being used (due to improvements in spicamExpose).
                    Pings the gcam actor when it starts. This eliminates the situation where the actor
                    is dead and the script should halt, but keeps exposing and reporting fwhm=NaN instead.
2007-07-26 ROwen    Added user-settable bin factor.
                    Modified to take a final exposure (after restoring boresight) if boresight moved.
2007-07-27 ROwen    Increased the fidelity of debug mode and fixed some bugs.
2007-07-30 ROwen    Added windowOrigin and windowIsInclusive arguments.
                    Bug fix: if the user changed the bin factor during script execution,
                    it would change the bin factor used in the script (and not necessarily properly).
2007-09-12 ROwen    SlitviewerFocusScript bug fix: Cancel would fail if no image ever taken.
2007-12-20 ROwen    Moved matplotlib configuration statements to TUI's startup because
                    in matplotlib 0.91.1 one may not call "use" after importing matplotlib.backends.
2008-01-24 ROwen    BaseFocusScript bug fixes:
                    - PR 686: Find button broken (waitFindStar ran "expose" instead of "findstars"
                      and so never found anything.).
                    - recordUserParams didn't round window so relStarPos could be off by a fraction of a pixel.
2008-01-25 ROwen    Added a digit after the decimal point for reporting fwhm in arcsec.
                    Implemented a lower limit on focus increment.
2008-02-01 ROwen    Changed configuration constants from globals to class variables of BaseFocusScript
                    so subclasses can more easily override them.
                    Fixed debug mode to use proper defaults for number of steps and focus range.
                    Setting current focus successfully clears the status bar.
2008-03-28 ROwen    PR 775: used exposeModel in classes where it did not exist.
                    Fixed by adding tccInstPrefix argument.
2008-04-02 ROwen    PR 781: Many focus scripts fail to start with TypeError...:
                    BaseFocusScript.getInstInfo was missing () on a string method lower()
2008-04-22 ROwen    Modified to use new Log.addMsg method.
2008-04-23 ROwen    Added some diagnostic output for PR 777 and its kin.
2008-04-29 ROwen    Open guide image window *after* checking for correct instrument.
2008-08-14 ROwen    CR 818: take a final full-frame exposure if script windows
                    (or, as before, if boresight was restored).
2009-03-02 ROwen    Added a brief header for PR 777 diagnostic output.
"""
import inspect
import math
import random # for debug
import numpy
import Tkinter
import RO.Wdg
import RO.Constants
import RO.StringUtil
import TUI.TUIModel
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Guide.GuideModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

MicronStr = RO.StringUtil.MuStr + "m"

def formatNum(val, fmt="%0.1f"):
    """Convert a number into a string
    None is returned as NaN
    """
    if val == None:
        return "NaN"
    try:
        return fmt % (val,)
    except TypeError:
        raise TypeError("formatNum failed on fmt=%r, val=%r" % (fmt, val))

class Extremes(object):
    """Class to keep track of minimum and maximum value.
    """
    def __init__(self, val=None):
        self.minVal = None
        self.maxVal = None
        if val != None:
            self.addVal(val)
        
    def addVal(self, val):
        if val == None:
            return
        if self.isOK():
            self.minVal = min(self.minVal, val)
            self.maxVal = max(self.maxVal, val)
        else:
            self.minVal = val
            self.maxVal = val
    
    def isOK(self):
        return self.minVal != None
    
    def __eq__(self, other):
        return (self.minVal == other.minVal) and (self.maxVal == other.maxVal)
    
    def __str__(self):
        return "[%s, %s]" % (self.minVal, self.maxVal)
    
    def __repr__(self):
        return "Extremes(%s, %s)" % (self.minVal, self.maxVal)

class StarMeas(object):
    def __init__(self,
        xyPos = None,
        sky = None,
        ampl = None,
        fwhm = None,
    ):
        self.xyPos = xyPos
        self.sky = sky
        self.ampl = ampl
        self.fwhm = fwhm
    
    def fromStarKey(cls, starKeyData):
        """Create an instance from star keyword data.
        """
        return cls(
            fwhm = starKeyData[8],
            sky = starKeyData[13],
            ampl = starKeyData[14],
            xyPos = starKeyData[2:4],
        )
    fromStarKey = classmethod(fromStarKey)

def makeStarData(
    typeChar = "f",
    xyPos = (10.0, 10.0),
    sky = 200,
    ampl = 1500,
    fwhm = 2.5,
):
    """Make a list containing one star data list for debug mode"""
    xyPos = [float(xyPos[ii]) for ii in range(2)]
    fwhm = float(fwhm)
    return [[typeChar, 1, xyPos[0], xyPos[1], 1.0, 1.0, fwhm * 5, 1, fwhm, fwhm, 0, 0, ampl, sky, ampl]]

class BaseFocusScript(object):
    """Basic focus script object.
    
    This is a virtual base class. The inheritor must:
    - Provide widgets
    - Provide a "run" method
    
    Inputs:
    - gcamActor: name of guide camera actor (e.g. "dcam")
    - instName: name of instrument (e.g. "DIS"); must be a name known to TUI.Inst.ExposeModel.
    - tccInstPrefix: instrument name as known by the TCC; defaults to instName;
        if the instrument has multiple names in the TCC then supply the common prefix
    - imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
    - defRadius: default centroid radius, in arcsec
    - defBinFactor: default bin factor; if None then bin factor cannot be set
    - canSetStarPos: if True the user can set the star position;
        if False then the Star Pos entries and Find button are not shown.
    - maxFindAmpl: maximum star amplitude for finding stars (peak - sky in ADUs);
        if None then star finding is disabled.
    - doWindow: if True, subframe images during focus sequence
    - windowOrigin: index of left or lower pixel for window (0 or 1 unless very wierd);
        this is not use for star positions, which all have the same convention
    - windowIsInclusive: is the upper-right window coord included in the image?
    - helpURL: URL of help file
    - debug: if True, run in debug mode, which uses fake data and does not communicate with the hub.
    """
    cmd_Find = "find"
    cmd_Measure = "measure"
    cmd_Sweep = "sweep"

    # constants
    #DefRadius = 5.0 # centroid radius, in arcsec
    #NewStarRad = 2.0 # amount of star position change to be considered a new star
    DefFocusNPos = 5  # number of focus positions
    DefFocusRange = 200 # default focus range around current focus
    FocusWaitMS = 1000 # time to wait after every focus adjustment (ms)
    BacklashComp = 0 # amount of backlash compensation, in microns (0 for none)
    WinSizeMult = 2.5 # window radius = centroid radius * WinSizeMult
    FocGraphMargin = 5 # margin on graph for x axis limits, in um
    MaxFocSigmaFac = 0.5 # maximum allowed sigma of best fit focus as a multiple of focus range
    MinFocusIncr = 50 # minimum focus increment, in um
    def __init__(self,
        sr,
        gcamActor,
        instName,
        tccInstPrefix = None,
        imageViewerTLName = None,
        defRadius = 5.0,
        defBinFactor = 1,
        canSetStarPos = True,
        maxFindAmpl = None,
        doWindow = True,
        windowOrigin = 0,
        windowIsInclusive = True,
        helpURL = None,
        debug = False,
    ):
        """The setup script; run once when the script runner
        window is created.
        """
        self.sr = sr
        sr.debug = bool(debug)
        self.gcamActor = gcamActor
        self.instName = instName
        self.tccInstPrefix = tccInstPrefix or self.instName
        self.imageViewerTLName = imageViewerTLName
        if defBinFactor == None:
            self.defBinFactor = None
            self.binFactor = 1
            self.dispBinFactor = 1
        else:
            self.defBinFactor = int(defBinFactor)
            self.binFactor = self.defBinFactor
            self.dispBinFactor = self.defBinFactor
        self.defRadius = defRadius
        self.helpURL = helpURL
        self.canSetStarPos = canSetStarPos
        self.maxFindAmpl = maxFindAmpl
        self.doWindow = bool(doWindow)
        self.windowOrigin = int(windowOrigin)
        self.windowIsInclusive = bool(windowIsInclusive)
        
        # fake data for debug mode
        self.debugIterFWHM = None
        
        # get various models
        self.tccModel = TUI.TCC.TCCModel.Model()
        self.tuiModel = TUI.TUIModel.Model()
        self.guideModel = TUI.Guide.GuideModel.getModel(self.gcamActor)
        
        # create and grid widgets
        self.gr = RO.Wdg.Gridder(sr.master, sticky="ew")
        
        self.createSpecialWdg()
        
        self.createStdWdg()
        
        self.initAll()
        # try to get focus away from graph (but it doesn't work; why?)
        self.expTimeWdg.focus_set()
        self.setCurrFocus()
    
    def createSpecialWdg(self):
        """Create script-specific widgets.
        """
        pass
    
    def createStdWdg(self):
        """Create the standard widgets.
        """
        sr = self.sr
        
        self.expTimeWdg = RO.Wdg.FloatEntry(
            sr.master,
            label = "Exposure Time",
            minValue = self.guideModel.gcamInfo.minExpTime,
            maxValue = self.guideModel.gcamInfo.maxExpTime,
            defValue = self.guideModel.gcamInfo.defExpTime,
            defFormat = "%0.1f",
            defMenu = "Default",
            minMenu = "Minimum",
            helpText = "Exposure time",
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(self.expTimeWdg.label, self.expTimeWdg, "sec")
        
        self.binFactorWdg = RO.Wdg.IntEntry(
            master = sr.master,
            label = "Bin Factor",
            minValue = 1,
            maxValue = 1024,
            defValue = self.defBinFactor or 1,
            defMenu = "Default",
            callFunc = self.updBinFactor,
            helpText = "Bin factor (for rows and columns)",
            helpURL = self.helpURL,
        )
        if self.defBinFactor != None:
            self.gr.gridWdg(self.binFactorWdg.label, self.binFactorWdg)

        self.starPosWdgSet = []
        for ii in range(2):
            letter = ("X", "Y")[ii]
            starPosWdg = RO.Wdg.FloatEntry(
                master = sr.master,
                label = "Star Pos %s" % (letter,),
                minValue = 0,
                maxValue = 5000,
                helpText = "Star %s position (binned, full frame)" % (letter,),
                helpURL = self.helpURL,
            )
            if self.canSetStarPos:
                self.gr.gridWdg(starPosWdg.label, starPosWdg, "pix")
            self.starPosWdgSet.append(starPosWdg)
        
        self.centroidRadWdg = RO.Wdg.IntEntry(
            master = sr.master,
            label = "Centroid Radius",
            minValue = 5,
            maxValue = 1024,
            defValue = self.defRadius,
            defMenu = "Default",
            helpText = "Centroid radius; don't skimp",
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(self.centroidRadWdg.label, self.centroidRadWdg, "arcsec", sticky="ew")

        setCurrFocusWdg = RO.Wdg.Button(
            master = sr.master,
            text = "Center Focus",
            callFunc = self.setCurrFocus,
            helpText = "Set to current focus",
            helpURL = self.helpURL,
        )
    
        self.centerFocPosWdg = RO.Wdg.IntEntry(
            master = sr.master,
            label = "Center Focus",
            defValue = 0,
            defMenu = "Default",
            helpText = "Center of focus sweep",
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(setCurrFocusWdg, self.centerFocPosWdg, MicronStr)
    
        self.focusRangeWdg = RO.Wdg.IntEntry(
            master = sr.master,
            label = "Focus Range",
            maxValue = self.DefFocusRange * 10,
            defValue = self.DefFocusRange,
            defMenu = "Default",
            helpText = "Range of focus sweep",
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(self.focusRangeWdg.label, self.focusRangeWdg, MicronStr)
    
        self.numFocusPosWdg = RO.Wdg.IntEntry(
            master = sr.master,
            label = "Focus Positions",
            minValue = 3,
            defValue = self.DefFocusNPos,
            defMenu = "Default",
            helpText = "Number of focus positions for sweep",
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(self.numFocusPosWdg.label, self.numFocusPosWdg, "")
        
        self.focusIncrWdg = RO.Wdg.FloatEntry(
            master = sr.master,
            label = "Focus Increment",
            defFormat = "%0.1f",
            readOnly = True,
            relief = "flat",
            helpText = "Focus step size; must be at least %s %s" % (self.MinFocusIncr, MicronStr),
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(self.focusIncrWdg.label, self.focusIncrWdg, MicronStr)
        
        # create the move to best focus checkbox
        self.moveBestFocus = RO.Wdg.Checkbutton(
            master = sr.master,
            text = "Move to Best Focus",
            defValue = True,
            relief = "flat",
            helpText = "Move to estimated best focus and measure FWHM after sweep?",
            helpURL = self.helpURL,
        )
        self.gr.gridWdg(None, self.moveBestFocus, colSpan = 3, sticky="w")
        
        graphCol =  self.gr.getNextCol()
        graphRowSpan = self.gr.getNextRow()

        # table of measurements (including separate unscrolled header)
        TableWidth = 32
        self.logHeader = RO.Wdg.Text(
            master = sr.master,
            readOnly = True,
            height = 2,
            width = TableWidth,
            helpText = "Measured and fit results",
            helpURL = self.helpURL,
            relief = "sunken",
            bd = 0,
        )
        self.logHeader.insert("0.0", """\tfocus\tFWHM\tFWHM\tsky\tampl\tsky+ampl
\t%s\tpixels\tarcsec\tADUs\tADUs\tADUs""" % MicronStr)
        self.logHeader.setEnable(False)
        self.gr.gridWdg(False, self.logHeader, sticky="ew", colSpan = 10)
        self.logWdg = RO.Wdg.LogWdg(
            master = sr.master,
            height = 10,
            width = TableWidth,
            helpText = "Measured and fit results",
            helpURL = self.helpURL,
            relief = "sunken",
            bd = 2,
        )
        self.gr.gridWdg(False, self.logWdg, sticky="ew", colSpan = 10)
        
        # graph of measurements
        plotFig = matplotlib.figure.Figure(figsize=(4, 1), frameon=True)
        self.figCanvas = FigureCanvasTkAgg(plotFig, sr.master)
        self.figCanvas.get_tk_widget().grid(row=0, column=graphCol, rowspan=graphRowSpan, sticky="news")
        self.plotAxis = plotFig.add_subplot(1, 1, 1)

        self.focusRangeWdg.addCallback(self.updFocusIncr, callNow=False)
        self.numFocusPosWdg.addCallback(self.updFocusIncr, callNow=True)
        
        # add command buttons
        cmdBtnFrame = Tkinter.Frame(sr.master)
        self.findBtn = RO.Wdg.Button(
            master = cmdBtnFrame,
            text = "Find",
            callFunc = RO.Alg.GenericCallback(self.doCmd, self.cmd_Find),
            helpText = "Update focus, expose and find best star",
            helpURL = self.helpURL,
        )
        if self.maxFindAmpl != None:
            self.findBtn.pack(side="left")
        self.measureBtn = RO.Wdg.Button(
            master = cmdBtnFrame,
            text = "Measure",
            callFunc = RO.Alg.GenericCallback(self.doCmd, self.cmd_Measure),
            helpText = "Update focus, expose and measure FWHM",
            helpURL = self.helpURL,
        )
        self.measureBtn.pack(side="left")
        self.sweepBtn = RO.Wdg.Button(
            master = cmdBtnFrame,
            text = "Sweep",
            callFunc = RO.Alg.GenericCallback(self.doCmd, self.cmd_Sweep),
            helpText = "Start focus sweep",
            helpURL = self.helpURL,
        )
        self.sweepBtn.pack(side="left")
        
        self.clearBtn = RO.Wdg.Button(
            master = cmdBtnFrame,
            text = "Clear",
            callFunc = self.doClear,
            helpText = "Clear table and graph",
            helpURL = self.helpURL,
        )
        self.clearBtn.pack(side="right")
        nCol = self.gr.getMaxNextCol() 
        self.gr.gridWdg(False, cmdBtnFrame, colSpan=nCol)
        
        if sr.debug:
            self.expTimeWdg.set("1")
            self.centerFocPosWdg.set(0)
    
    def clearGraph(self):
        self.plotAxis.clear()
        self.plotAxis.grid(True)
        # start with autoscale disabled due to bug in matplotlib
        self.plotAxis.set_autoscale_on(False)
        self.figCanvas.draw()
        self.plotLine = None
    
    def doClear(self, wdg=None):
        self.logWdg.clearOutput()
        self.clearGraph()
    
    def doCmd(self, cmdMode, wdg=None):
        if cmdMode not in (
            self.cmd_Measure,
            self.cmd_Find,
            self.cmd_Sweep,
        ):
            raise self.sr.RuntimeError("Unknown command mode %r" % (cmdMode,))
        self.cmdMode = cmdMode
        self.sr.resumeUser()
    
    def enableCmdBtns(self, doEnable):
        """Enable or disable command buttons (e.g. Expose and Sweep).
        """
        self.findBtn.setEnable(doEnable)
        self.measureBtn.setEnable(doEnable)
        self.sweepBtn.setEnable(doEnable)
        self.clearBtn.setEnable(doEnable)

    def end(self, sr):
        """Run when script exits (normally or due to error)
        """
        self.enableCmdBtns(False)

        if self.focPosToRestore != None:
            tccCmdStr = "set focus=%0.0f" % (self.focPosToRestore,)
            if self.sr.debug:
                print "end is restoring the focus: %r" % tccCmdStr
            sr.startCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )

        doRestoreBoresight = self.begBoreXYDeg != self.currBoreXYDeg
        if doRestoreBoresight:
            if self.sr.debug:
                print "end is restoring the boresight"
            self.moveBoresight(
                self.begBoreXYDeg,
                doWait = False,
            )

        if self.didTakeImage and (self.doWindow or doRestoreBoresight):
            if self.sr.debug:
                print "end is taking a final exposure"
            exposeCmdDict = self.getExposeCmdDict(doWindow=False)
            sr.startCmd(**exposeCmdDict)

    def formatBinFactorArg(self):
        """Return bin factor argument for expose/centroid/findstars command"""
        #print "defBinFactor=%r, binFactor=%r" % (self.defBinFactor, self.binFactor)
        # if defBinFactor None then bin factor cannot be set
        if self.defBinFactor == None:
            return ""
        return "bin=%d" % (self.binFactor,)
    
    def formatExposeArgs(self, doWindow=True):
        """Format arguments for exposure command.
        
        Inputs:
        - doWindow: if true, window the exposure (if permitted)
        """
        argList = [
            "time=%s" % (self.expTime,),
            self.formatBinFactorArg(),
            self.formatWindowArg(doWindow),
        ]
        argList = [arg for arg in argList if arg]
        return " ".join(argList)
    
    def formatWindowArg(self, doWindow=True):
        """Format window argument for expose/centroid/findstars command.
        
        Inputs:
        - doWindow: if true, window the exposure (if permitted)
        """
        if not doWindow or not self.doWindow:
            return ""
        if self.windowIsInclusive:
            urOffset = self.windowOrigin
        else:
            urOffset = self.windowOrigin + 1
        windowLL = [self.window[ii] + self.windowOrigin for ii in range(2)]
        windowUR = [self.window[ii+2] + urOffset for ii in range(2)]
        return "window=%d,%d,%d,%d" % (windowLL[0], windowLL[1], windowUR[0], windowUR[1])

    def getInstInfo(self):
        """Obtains instrument data.
        
        Verifies the correct instrument and sets these attributes:
        - instScale: x,y image scale in unbinned pixels/degree
        - instCtr: x,y image center in unbinned pixels
        - instLim: xmin, ymin, xmax, ymax image limits, inclusive, in unbinned pixels
        - arcsecPerPixel: image scale in arcsec/unbinned pixel;
            average of x and y scales
        
        Raises ScriptError if wrong instrument.
        """
        sr = self.sr
        if self.tccInstPrefix and not sr.debug:
            # Make sure current instrument is correct
            try:
                currInstName = sr.getKeyVar(self.tccModel.inst)
            except sr.ScriptError:
                raise sr.ScriptError("current instrument unknown")
            if not currInstName.lower().startswith(self.tccInstPrefix.lower()):
                raise sr.ScriptError("%s is not the current instrument (%s)!" % (self.instName, currInstName))
            
            self.instScale = sr.getKeyVar(self.tccModel.iimScale, ind=None)
            self.instCtr = sr.getKeyVar(self.tccModel.iimCtr, ind=None)
            self.instLim = sr.getKeyVar(self.tccModel.iimLim, ind=None)
        else:
            # data from tcc tinst:I_NA2_DIS.DAT 18-OCT-2006
            self.instScale = [-12066.6, 12090.5] # unbinned pixels/deg
            self.instCtr = [240, 224]
            self.instLim = [0, 0, 524, 511]
        
        self.arcsecPerPixel = 3600.0 * 2 / (abs(self.instScale[0]) + abs(self.instScale[1]))
    
    def getEntryNum(self, wdg):
        """Return the numeric value of a widget, or raise ScriptError if blank.
        """
        numVal = wdg.getNumOrNone()
        if numVal != None:
            return numVal
        raise self.sr.ScriptError(wdg.label + " not specified")

    def getExposeCmdDict(self, doWindow=True):
        """Get basic command arument dict for an expose command
        
        This includes actor, cmdStr, abortCmdStr
        """
        return dict(
            actor = self.gcamActor,
            cmdStr = "expose " + self.formatExposeArgs(doWindow),
            abortCmdStr = "abort",
        )
    
    def graphFocusMeas(self, focPosFWHMList, extremeFocPos=None, extremeFWHM=None):
        """Graph measured fwhm vs focus.
        
        Inputs:
        - focPosFWHMList: list of data items:
            - focus position (um)
            - measured FWHM (binned pixels)
        - extremeFocPos: extremes of focus position
        - extremeFWHM: extremes of FWHM
        - setFocRange: adjust displayed focus range?
        
        extremes are an Extremes object with .minVal and .maxVal
        """
        # "graphFocusMeas(focPosFWHMList=%s, extremeFocPos=%r, extremeFWHM=%r)" % (focPosFWHMList, extremeFocPos, extremeFWHM)
        numMeas = len(focPosFWHMList)
        if numMeas == 0:
            return

        focList, fwhmList = zip(*focPosFWHMList)
        if not self.plotLine:
            self.plotLine = self.plotAxis.plot(focList, fwhmList, 'bo')[0]
        else:
            self.plotLine.set_data(focList[:], fwhmList[:])
        
        self.setGraphRange(extremeFocPos=extremeFocPos, extremeFWHM=extremeFWHM)
        
    def initAll(self):
        """Initialize variables, table and graph.
        """
        # initialize shared variables
        self.didTakeImage = False
        self.focDir = None
        self.currBoreXYDeg = None
        self.begBoreXYDeg = None
        self.instScale = None
        self.arcsecPerPixel = None
        self.instCtr = None
        self.instLim = None
        self.cmdMode = None
        self.focPosToRestore = None
        self.expTime = None
        self.absStarPos = None
        self.relStarPos = None
        self.binFactor = None
        self.window = None # LL pixel is 0, UL pixel is included

        self.enableCmdBtns(False)
    
    def logFitFWHM(self, name, focPos, fwhm):
        """Log a fit value of FWHM or FWHM error.
        """
        if fwhm != None:
            fwhmArcSec = fwhm * self.arcsecPerPixel * self.binFactor
        else:
            fwhmArcSec = None
        
        dataStrs = (
            formatNum(focPos, "%0.0f"),
            formatNum(fwhm, "%0.1f"),
            formatNum(fwhmArcSec, "%0.2f"),
        )
        outStr = "%s\t%s" % (name, "\t".join(dataStrs))
        self.logWdg.addMsg(outStr)
    
    def logStarMeas(self, name, focPos, starMeas):
        """Log a star measurement.
        The name should be less than 8 characters long.
        
        Any or all data fields in starMeas may be None.
        
        Inputs:
        - focPos: focus position, in um
        - starMeas: StarMeas object
        
        If fwhm is None, it is reported as NaN.
        """
        fwhm = starMeas.fwhm
        if fwhm != None:
            fwhmArcSec = fwhm * self.arcsecPerPixel * self.binFactor
        else:
            fwhmArcSec = None
        if None not in (starMeas.ampl, starMeas.sky):
            skyPlusAmpl = starMeas.ampl + starMeas.sky
        else:
            skyPlusAmpl = None
        
        
        dataStrs = (
            formatNum(focPos, "%0.0f"),
            formatNum(fwhm, "%0.1f"),
            formatNum(fwhmArcSec, "%0.2f"),
            formatNum(starMeas.sky, "%0.0f"),
            formatNum(starMeas.ampl, "%0.0f"),
            formatNum(skyPlusAmpl, "%0.0f"),
        )
        outStr = "%s\t%s" % (name, "\t".join(dataStrs))
        self.logWdg.addMsg(outStr)
    
    def recordUserParams(self, doStarPos=True):
        """Record user-set parameters relating to exposures but not to focus
        
        Inputs:
        - doStarPos: if true: save star position and related information;
            warning: if doStarPos true then there must *be* a valid star position
        
        Set the following instance variables:
        - expTime
        - centroidRadPix
        The following are set to None if doStarPos false:
        - absStarPos
        - relStarPos
        - window
        """
        self.expTime = self.getEntryNum(self.expTimeWdg)
        self.binFactor = self.dispBinFactor
        centroidRadArcSec = self.getEntryNum(self.centroidRadWdg)
        self.centroidRadPix =  centroidRadArcSec / (self.arcsecPerPixel * self.binFactor)
        
        if doStarPos:
            winRad = self.centroidRadPix * self.WinSizeMult
            
            self.absStarPos = [None, None]
            for ii in range(2):
                wdg = self.starPosWdgSet[ii]
                self.absStarPos[ii] = self.getEntryNum(wdg)
            
            if self.doWindow:
                windowMinXY = [max(self.instLim[ii],   int(0.5 + self.absStarPos[ii] - winRad)) for ii in range(2)]
                windowMaxXY = [min(self.instLim[ii-2], int(0.5 + self.absStarPos[ii] + winRad)) for ii in range(2)]
                self.window = windowMinXY + windowMaxXY
                self.relStarPos = [self.absStarPos[ii] - windowMinXY[ii] for ii in range(2)]
                #print "winRad=%s, windowMinXY=%s, relStarPos=%s" % (winRad, windowMinXY, self.relStarPos)
            else:
                self.window = None
                self.relStarPos = self.absStarPos[:]
        else:
            self.absStarPos = None
            self.relStarPos = None
            self.window = None
    
    def run(self, sr):
        """Run the focus script.
        """
        self.initAll()
        
        # fake data for debug mode
        # iteration #, FWHM
        self.debugIterFWHM = (1, 2.0)
        
        self.getInstInfo()
        yield self.waitExtraSetup()

        # open image viewer window, if any
        if self.imageViewerTLName:
            self.tuiModel.tlSet.makeVisible(self.imageViewerTLName)
        self.sr.master.winfo_toplevel().lift()

        focPosFWHMList = []
        extremeFocPos = Extremes()
        extremeFWHM = Extremes()
        
        # check that the gcam actor is alive. This is important because
        # centroid commands can fail due to no actor or no star
        # so we want to halt in the former case
        yield sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = "ping",
        )
        
        # command loop; repeat until error or user explicitly presses Stop
        if self.maxFindAmpl == None:
            btnStr = "Measure or Sweep"
        else:
            btnStr = "Find, Measure or Sweep"
        waitMsg = "Press %s to continue" % (btnStr,)
        testNum = 0
        while True:

            # wait for user to press the Expose or Sweep button
            # note: the only time they should be enabled is during this wait
            self.enableCmdBtns(True)
            sr.showMsg(waitMsg, RO.Constants.sevWarning)
            yield sr.waitUser()
            self.enableCmdBtns(False)
            
            if self.cmdMode == self.cmd_Sweep:
                break
             
            if testNum == 0:
                self.clearGraph()
                if self.maxFindAmpl == None:
                    self.logWdg.addMsg("===== Measure =====")
                else:
                    self.logWdg.addMsg("===== Find/Measure =====")
               
            testNum += 1
            focPos = float(self.centerFocPosWdg.get())
            if focPos == None:
                raise sr.ScriptError("must specify center focus")
            yield self.waitSetFocus(focPos, False)

            if self.cmdMode == self.cmd_Measure:
                cmdName = "Meas"
                self.recordUserParams(doStarPos=True)
                yield self.waitCentroid()
            elif self.cmdMode == self.cmd_Find:
                cmdName = "Find"
                self.recordUserParams(doStarPos=False)
                yield self.waitFindStar()
                starData = sr.value
                if starData.xyPos != None:
                    sr.showMsg("Found star at %0.1f, %0.1f" % tuple(starData.xyPos))
                    self.setStarPos(starData.xyPos)
            else:
                raise RuntimeError("Unknown command mode: %r" % (self.cmdMode,))

            starMeas = sr.value
            self.logStarMeas("%s %d" % (cmdName, testNum,), focPos, starMeas)
            fwhm = starMeas.fwhm
            if fwhm == None:
                waitMsg = "No star found! Fix and then press %s" % (btnStr,)
                self.setGraphRange(extremeFocPos=extremeFocPos)
            else:
                extremeFocPos.addVal(focPos)
                extremeFWHM.addVal(starMeas.fwhm)
                focPosFWHMList.append((focPos, fwhm))
                self.graphFocusMeas(focPosFWHMList, extremeFocPos, extremeFWHM)
                waitMsg = "%s done; press %s to continue" % (cmdName, btnStr,)

        self.recordUserParams(doStarPos=True)
        yield self.waitFocusSweep()
        
        doRestoreBoresight = self.begBoreXYDeg != self.currBoreXYDeg
        if doRestoreBoresight:
            yield self.moveBoresight(
                self.begBoreXYDeg,
                msgStr ="Restoring original boresight position",
                doWait = True,
            )
        
        if self.didTakeImage and (self.doWindow or doRestoreBoresight):
            self.didTakeImage = False # to prevent end from taking another image
            self.sr.showMsg("Taking a final image")
            exposeCmdDict = self.getExposeCmdDict(doWindow=False)
            yield sr.waitCmd(**exposeCmdDict)
    
    def setCurrFocus(self, *args):
        """Set center focus to current focus.
        """
        currFocus = self.sr.getKeyVar(self.tccModel.secFocus, defVal=None)
        if currFocus == None:
            self.sr.showMsg("Current focus not known",
                severity=RO.Constants.sevWarning,
            )
            return

        self.centerFocPosWdg.set(currFocus)
        self.sr.showMsg("")
    
    def setGraphRange(self, extremeFocPos=None, extremeFWHM=None):
        """Sets the displayed range of the graph.
        
        Inputs:
        - extremeFocPos: focus extremes
        - extremeFWHM: FWHM extremes
        """
        # "setGraphRange(extremeFocPos=%s, extremeFWHM=%s)" % (extremeFocPos, extremeFWHM)
        if extremeFocPos and extremeFocPos.isOK():
            minFoc = extremeFocPos.minVal - self.FocGraphMargin
            maxFoc = extremeFocPos.maxVal + self.FocGraphMargin
            if maxFoc - minFoc < 50:
                minFoc -= 25
                maxFoc += 25
            self.plotAxis.set_xlim(minFoc, maxFoc)
            
        if extremeFWHM and extremeFWHM.isOK():
            minFWHM = extremeFWHM.minVal * 0.95
            maxFWHM = extremeFWHM.maxVal * 1.05
            self.plotAxis.set_ylim(minFWHM, maxFWHM)

        self.figCanvas.draw()
    
    def setStarPos(self, starXYPix):
        """Set star position widgets.
        
        Inputs:
        - starXYPix: star x, y position (binned pixels)
        """
        for ii in range(2):
            wdg = self.starPosWdgSet[ii]
            wdg.set(starXYPix[ii])
    
    def updBinFactor(self, *args, **kargs):
        """Called when the user changes the bin factor"""
        newBinFactor = self.binFactorWdg.getNum()
        if newBinFactor <= 0:
            return
        oldBinFactor = self.dispBinFactor
        if oldBinFactor == newBinFactor:
            return

        self.dispBinFactor = newBinFactor
        
        # adjust displayed star position
        posFactor = float(oldBinFactor) / float(newBinFactor)
        for ii in range(2):
            oldStarPos = self.starPosWdgSet[ii].getNum()
            if oldStarPos == 0:
                continue
            newStarPos = oldStarPos * posFactor
            self.starPosWdgSet[ii].set(newStarPos)
   
    def updFocusIncr(self, *args):
        """Update focus increment widget.
        """
        focusRange = self.focusRangeWdg.getNumOrNone()
        numPos = self.numFocusPosWdg.getNumOrNone()
        if None in (focusRange, numPos):
            self.focusIncrWdg.set(None, isCurrent = False)
            return

        focusIncr = focusRange / float(numPos - 1)
        isOK = focusIncr >= self.MinFocusIncr
        if not isOK:
            errMsg = "Focus increment too small (< %s %s)" % (self.MinFocusIncr, MicronStr)
            self.sr.showMsg(errMsg, RO.Constants.sevWarning)
        self.focusIncrWdg.set(focusIncr, isCurrent = isOK)

    def waitCentroid(self):
        """Take an exposure and centroid using 1x1 binning.
        
        If the centroid is found, sets sr.value to the FWHM.
        Otherwise sets sr.value to None.
        """
        sr = self.sr
        centroidCmdStr = "centroid on=%0.1f,%0.1f cradius=%0.1f %s" % \
            (self.relStarPos[0], self.relStarPos[1], self.centroidRadPix, self.formatExposeArgs())
        yield sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = centroidCmdStr,
           keyVars = (self.guideModel.files, self.guideModel.star),
           checkFail = False,
        )
        cmdVar = sr.value
        self.didTakeImage = True
        if sr.debug:
            starData = makeStarData("c", self.relStarPos)
        else:
            starData = cmdVar.getKeyVarData(self.guideModel.star)
        if starData:
            sr.value = StarMeas.fromStarKey(starData[0])
            return
        else:
            sr.value = StarMeas()

        if not cmdVar.getKeyVarData(self.guideModel.files):
            raise sr.ScriptError("exposure failed")

    def waitExtraSetup(self):
        """Executed once at the start of each run
        after calling initAll and getInstInfo but before doing anything else.
        
        Override to do things such as move the boresight or put the instrument into a particular mode.
        """
        yield self.sr.waitMS(1)

    def waitFindStar(self):
        """Take a full-frame exposure and find the best star that can be centroided.

        Sets sr.value to StarMeas.
        Displays a warning if no star found.
        """
        sr = self.sr

        if self.maxFindAmpl == None:
            raise RuntimeError("Find disabled; maxFindAmpl=None")

        self.sr.showMsg("Exposing %s sec to find best star" % (self.expTime,))
        findStarCmdStr = "findstars " + self.formatExposeArgs(doWindow=False)
        
        yield sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = findStarCmdStr,
           keyVars = (self.guideModel.files, self.guideModel.star),
           checkFail = False,
        )
        cmdVar = sr.value
        self.didTakeImage = True
        if self.sr.debug:
            filePath = "debugFindFile"
        else:
            if not cmdVar.getKeyVarData(self.guideModel.files):
                raise sr.ScriptError("exposure failed")
            fileInfo = cmdVar.getKeyVarData(self.guideModel.files)[0]
            filePath = "".join(fileInfo[2:4])

        if self.sr.debug:               
            starDataList = makeStarData("f", (50.0, 75.0))
        else:
            starDataList = cmdVar.getKeyVarData(self.guideModel.star)
        if not starDataList:
            sr.value = StarMeas()
            self.sr.showMsg("No stars found", severity=RO.Constants.sevWarning)
            return
        
        yield self.waitFindStarInList(filePath, starDataList)

    def waitFindStarInList(self, filePath, starDataList):
        """Find best centroidable star in starDataList.

        If a suitable star is found: set starXYPos to position
        and sr.value to the star FWHM.
        Otherwise log a warning and set sr.value to None.
        
        Inputs:
        - filePath: image file path on hub, relative to image root
            (e.g. concatenate items 2:4 of the guider Files keyword)
        - starDataList: list of star keyword data
        """
        sr = self.sr

        if self.maxFindAmpl == None:
            raise RuntimeError("Find disabled; maxFindAmpl=None")
        
        for starData in starDataList:
            starXYPos = starData[2:4]
            starAmpl = starData[14]
            if (starAmpl == None) or (starAmpl > self.maxFindAmpl):
                continue
                
            sr.showMsg("Centroiding star at %0.1f, %0.1f" % tuple(starXYPos))
            centroidCmdStr = "centroid file=%s on=%0.1f,%0.1f cradius=%0.1f" % \
                (filePath, starXYPos[0], starXYPos[1], self.centroidRadPix)
            yield sr.waitCmd(
               actor = self.gcamActor,
               cmdStr = centroidCmdStr,
               keyVars = (self.guideModel.star,),
               checkFail = False,
            )
            cmdVar = sr.value
            if sr.debug:
                starData = makeStarData("f", starXYPos)
            else:
                starData = cmdVar.getKeyVarData(self.guideModel.star)
            if starData:
                sr.value = StarMeas.fromStarKey(starData[0])
                return

        sr.showMsg("No usable star fainter than %s ADUs found" % self.maxFindAmpl,
            severity=RO.Constants.sevWarning)
        sr.value = StarMeas()
    
    def waitFocusSweep(self):
        """Conduct a focus sweep.
        
        Sets sr.value to True if successful.
        """
        sr = self.sr

        focPosFWHMList = []
        self.logWdg.addMsg("===== Sweep =====")
        self.clearGraph()

        centerFocPos = float(self.getEntryNum(self.centerFocPosWdg))
        focusRange = float(self.getEntryNum(self.focusRangeWdg))
        startFocPos = centerFocPos - (focusRange / 2.0)
        endFocPos = startFocPos + focusRange
        numFocPos = self.getEntryNum(self.numFocusPosWdg)
        if numFocPos < 3:
            raise sr.ScriptError("need at least three focus positions")
        focusIncr = self.focusIncrWdg.getNum()
        if focusIncr < self.MinFocusIncr:
            raise sr.ScriptError("focus increment too small (< %s %s)" % (self.MinFocusIncr, MicronStr))
        numExpPerFoc = 1
        self.focDir = (endFocPos > startFocPos)
        
        extremeFocPos = Extremes(startFocPos)
        extremeFocPos.addVal(endFocPos)
        extremeFWHM = Extremes()
        self.setGraphRange(extremeFocPos=extremeFocPos)
        numMeas = 0
        self.focPosToRestore = centerFocPos
        for focInd in range(numFocPos):
            focPos = float(startFocPos + (focInd*focusIncr))

            doBacklashComp = (focInd == 0)
            yield self.waitSetFocus(focPos, doBacklashComp)
            sr.showMsg("Exposing for %s sec at focus %0.0f %s" % \
                (self.expTime, focPos, MicronStr))
            yield self.waitCentroid()
            starMeas = sr.value
            if sr.debug:
                starMeas.fwhm = 0.0001 * (focPos - centerFocPos) ** 2
                starMeas.fwhm += random.gauss(1.0, 0.25)
            extremeFWHM.addVal(starMeas.fwhm)

            self.logStarMeas("Sw %d" % (focInd+1,), focPos, starMeas)
            
            if starMeas.fwhm != None:
                focPosFWHMList.append((focPos, starMeas.fwhm))
                self.graphFocusMeas(focPosFWHMList, extremeFWHM=extremeFWHM)
        
        # Fit a curve to the data
        numMeas = len(focPosFWHMList)
        if numMeas < 3:
            raise sr.ScriptError("need at least 3 measurements to fit best focus")
        focList, fwhmList = zip(*focPosFWHMList)
        focPosArr = numpy.array(focList, dtype=float)
        fwhmArr  = numpy.array(fwhmList, dtype=float)
        weightArr = numpy.ones(numMeas, dtype=float)
        if numMeas > 3:
            coeffs, dumYFit, dumYBand, fwhmSigma, dumCorrMatrix = polyfitw(focPosArr, fwhmArr, weightArr, 2, True)
        elif numMeas == 3:
            # too few points to measure fwhmSigma
            coeffs = polyfitw(focPosArr, fwhmArr, weightArr, 2, False)
            fwhmSigma = None
        
        # Make sure fit curve has a minimum
        if coeffs[2] <= 0.0:
            raise sr.ScriptError("could not find minimum focus")
        
        # find the best focus position
        bestEstFocPos = (-1.0*coeffs[1])/(2.0*coeffs[2])
        bestEstFWHM = coeffs[0]+coeffs[1]*bestEstFocPos+coeffs[2]*bestEstFocPos*bestEstFocPos
        extremeFocPos.addVal(bestEstFocPos)
        extremeFWHM.addVal(bestEstFWHM)
        self.logFitFWHM("Fit", bestEstFocPos, bestEstFWHM)

        # compute and log standard deviation, if possible
        if fwhmSigma != None:
            focSigma = math.sqrt(fwhmSigma / coeffs[2])
            self.logFitFWHM(u"Fit \N{GREEK SMALL LETTER SIGMA}", focSigma, fwhmSigma)
        else:
            focSigma = None
            self.logWdg.addMsg(u"Warning: too few points to compute \N{GREEK SMALL LETTER SIGMA}")

        # plot fit as a curve and best fit focus as a point
        fitFocArr = numpy.arange(min(focPosArr), max(focPosArr), 1)
        fitFWHMArr = coeffs[0] + coeffs[1]*fitFocArr + coeffs[2]*(fitFocArr**2.0)
        self.plotAxis.plot(fitFocArr, fitFWHMArr, '-k', linewidth=2)
        self.plotAxis.plot([bestEstFocPos], [bestEstFWHM], 'go')
        self.setGraphRange(extremeFocPos=extremeFocPos, extremeFWHM=extremeFWHM)

        # check fit error
        if focSigma != None:
            maxFocSigma = self.MaxFocSigmaFac * focusRange
            if focSigma > maxFocSigma:
                raise sr.ScriptError("focus std. dev. too large: %0.0f > %0.0f" % (focSigma, maxFocSigma))
        
        # check that estimated best focus is in sweep range
        if not startFocPos <= bestEstFocPos <= endFocPos:
            raise sr.ScriptError("best focus=%0.0f out of sweep range" % (bestEstFocPos,))

        # move to best focus if "Move to best Focus" checked
        moveBest = self.moveBestFocus.getBool()
        if not moveBest:
            return
            
        self.setCurrFocus()
        yield self.waitSetFocus(bestEstFocPos, doBacklashComp=True)
        sr.showMsg("Exposing for %s sec at estimated best focus %d %s" % \
            (self.expTime, bestEstFocPos, MicronStr))
        yield self.waitCentroid()
        finalStarMeas = sr.value
        if sr.debug:
            finalStarMeas.fwhm = 1.1
        extremeFWHM.addVal(finalStarMeas.fwhm)
        
        self.logStarMeas("Meas", bestEstFocPos, finalStarMeas)
        
        finalFWHM = finalStarMeas.fwhm
        if finalFWHM != None:
            self.plotAxis.plot([bestEstFocPos], [finalFWHM], 'ro')
            self.setGraphRange(extremeFocPos=extremeFocPos, extremeFWHM=extremeFWHM)
        else:
            raise sr.ScriptError("could not measure FWHM at estimated best focus")
        
        # A new best focus was picked; don't restore the original focus
        # and do set Center Focus to the new focus
        self.focPosToRestore = None
        self.centerFocPosWdg.set(int(round(bestEstFocPos)))
    
    def waitSetFocus(self, focPos, doBacklashComp=False):
        """Adjust focus.

        To use: yield waitSetFocus(...)
        
        Inputs:
        - focPos: new focus position in um
        - doBacklashComp: if True, perform backlash compensation
        """
        sr = self.sr

        focPos = float(focPos)
        
        # to try to eliminate the backlash in the secondary mirror drive move back 1/2 the
        # distance between the start and end position from the bestEstFocPos
        if doBacklashComp and self.BacklashComp:
            backlashFocPos = focPos - (abs(self.BacklashComp) * self.focDir)
            sr.showMsg("Backlash comp: moving focus to %0.0f %s" % (backlashFocPos, MicronStr))
            yield sr.waitCmd(
               actor = "tcc",
               cmdStr = "set focus=%0.0f" % (backlashFocPos,),
            )
            yield sr.waitMS(self.FocusWaitMS)
        
        # move to desired focus position
        sr.showMsg("Moving focus to %0.0f %s" % (focPos, MicronStr))
        yield sr.waitCmd(
           actor = "tcc",
           cmdStr = "set focus=%0.0f" % (focPos,),
        )
        yield sr.waitMS(self.FocusWaitMS)


class SlitviewerFocusScript(BaseFocusScript):
    """Focus script for slitviewers
    
    Inputs:
    - gcamActor: name of guide camera actor (e.g. "dcam")
    - instName: name of instrument (e.g. "DIS"); must be a name known to TUI.Inst.ExposeModel.
    - imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
    - defBoreXY: default boresight position in [x, y] arcsec;
        If an entry is None then no offset widget is shown for that axis
        and 0 is used.
    - defRadius: default centroid radius, in arcsec
    - defBinFactor: default bin factor; if None then bin factor cannot be set
    - doWindow: if True, subframe images during focus sequence
    - windowOrigin: index of left or lower pixel for window (0 or 1 unless very wierd);
        this is not use for star positions, which all have the same convention
    - windowIsInclusive: is the upper-right window coord included in the image?
    - helpURL: URL of help file
    - debug: if True, run in debug mode, which uses fake data and does not communicate with the hub.
    """
    def __init__(self,
        sr,
        gcamActor,
        instName,
        imageViewerTLName,
        defBoreXY,
        defRadius = 5.0,
        defBinFactor = 1,
        doWindow = True,
        windowOrigin = 0,
        windowIsInclusive = True,
        helpURL = None,
        debug = False,
    ):
        """The setup script; run once when the script runner
        window is created.
        """
        if len(defBoreXY) != 2:
            raise ValueError("defBoreXY=%s must be a pair of values" % defBoreXY)
        self.defBoreXY = defBoreXY
        
        BaseFocusScript.__init__(self,
            sr = sr,
            gcamActor = gcamActor,
            instName = instName,
            imageViewerTLName = imageViewerTLName,
            defRadius = defRadius,
            defBinFactor = defBinFactor,
            canSetStarPos = False,
            maxFindAmpl = None,
            doWindow = doWindow,
            windowOrigin = windowOrigin,
            windowIsInclusive = windowIsInclusive,
            helpURL = helpURL,
            debug = debug,
        )

    def createSpecialWdg(self):
        """Create boresight widget(s).
        """
        sr = self.sr

        self.boreNameWdgSet = []
        for ii in range(2):
            showWdg = (self.defBoreXY[ii] != None)
            if showWdg:
                defVal = float(self.defBoreXY[ii])
            else:
                defVal = 0.0

            letter = ("X", "Y")[ii]
            wdgLabel = "Boresight %s" % (letter,)
            boreWdg = RO.Wdg.FloatEntry(
                master = sr.master,
                label = wdgLabel,
                minValue = -60.0,
                maxValue = 60.0,
                defValue = defVal,
                defMenu = "Default",
                helpText = wdgLabel + " position",
                helpURL = self.helpURL,
            )
            if showWdg:
                self.gr.gridWdg(boreWdg.label, boreWdg, "arcsec")
            self.boreNameWdgSet.append(boreWdg)

    def moveBoresight(self, boreXYDeg, msgStr="Moving the boresight", doWait=True):
        """Move the boresight to the specified position and sets starPos accordingly.

        Waits if doWait true (in which case you must use "yield").
        
        Records the initial boresight position in self.begBoreXYDeg, if not already done.
        """
        sr = self.sr

        cmdStr = "offset boresight %0.7f, %0.7f/pabs/computed" % (boreXYDeg[0], boreXYDeg[1])

        # save the initial boresight position, if not already done
        if self.begBoreXYDeg == None:
            begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
            if not sr.debug:
                begBoreXYDeg = [pvt.getPos() for pvt in begBorePVTs]
                if None in begBoreXYDeg:
                    raise sr.ScriptError("current boresight position unknown")
                self.begBoreXYDeg = begBoreXYDeg
            else:
                self.begBoreXYDeg = [0.0, 0.0]
            # "self.begBoreXYDeg=%r" % self.begBoreXYDeg

        # move boresight and adjust star position accordingly
        starXYPix = [(boreXYDeg[ii] * self.instScale[ii]) + self.instCtr[ii] for ii in range(2)]
        if msgStr:
            sr.showMsg(msgStr)
        self.currBoreXYDeg = boreXYDeg
        self.setStarPos(starXYPix)
        if doWait:
            yield sr.waitCmd(
                actor = "tcc",
                cmdStr = cmdStr,
            )
        else:
            sr.startCmd(
                actor = "tcc",
                cmdStr = cmdStr,
            )
    
    def waitExtraSetup(self):
        """Executed once at the start of each run
        after calling initAll and getInstInfo but before doing anything else.
        
        Override to do things such as put the instrument into a particular mode.
        """
        # set boresight and star position and shift boresight
        boreXYDeg = [self.getEntryNum(wdg) / 3600.0 for wdg in self.boreNameWdgSet]
        yield self.moveBoresight(boreXYDeg, doWait=True)

class OffsetGuiderFocusScript(BaseFocusScript):
    """Focus script for offset guiders
    
    Inputs:
    - gcamActor: name of guide camera actor (e.g. "dcam")
    - instPos: name of instrument position (e.g. "NA2"); case doesn't matter
    - imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
    - defBoreXY: default boresight position in [x, y] arcsec;
        If an entry is None then no offset widget is shown for that axis
        and 0 is used.
    - defRadius: default centroid radius, in arcsec
    - defBinFactor: default bin factor; if None then bin factor cannot be set
    - maxFindAmpl: maximum star amplitude for finding stars (peak - sky in ADUs);
        if None then star finding is disabled.
    - doWindow: if True, subframe images during focus sequence
    - windowOrigin: index of left or lower pixel for window (0 or 1 unless very wierd);
        this is not use for star positions, which all have the same convention
    - windowIsInclusive: is the upper-right window coord included in the image?
    - helpURL: URL of help file
    - debug: if True, run in debug mode, which uses fake data and does not communicate with the hub.
    """
    def __init__(self,
        sr,
        gcamActor,
        instPos,
        imageViewerTLName,
        defRadius = 5.0,
        defBinFactor = 1,
        maxFindAmpl = None,
        doWindow = True,
        windowOrigin = 0,
        windowIsInclusive = True,
        helpURL = None,
        debug = False,
    ):
        """The setup script; run once when the script runner
        window is created.
        """
        BaseFocusScript.__init__(self,
            sr = sr,
            gcamActor = gcamActor,
            instName = None,
            imageViewerTLName = imageViewerTLName,
            defRadius = defRadius,
            defBinFactor = defBinFactor,
            maxFindAmpl = maxFindAmpl,
            doWindow = doWindow,
            windowOrigin = windowOrigin,
            windowIsInclusive = windowIsInclusive,
            helpURL = helpURL,
            debug = debug,
        )
        self.instPos = instPos

    def getInstInfo(self):
        """Obtains instrument data (in this case guider data).
        
        Verifies the correct instrument and sets these attributes:
        - instScale: x,y image scale in unbinned pixels/degree
        - instCtr: x,y image center in unbinned pixels
        - instLim: xmin, ymin, xmax, ymax image limits, inclusive, in unbinned pixels
        - arcsecPerPixel: image scale in arcsec/unbinned pixel;
            average of x and y scales
        
        Raises ScriptError if wrong instrument.
        """
        sr = self.sr
        if not sr.debug:
            # Make sure current instrument is correct
            try:
                currInstPosName = sr.getKeyVar(self.tccModel.instPos)
            except sr.ScriptError:
                raise sr.ScriptError("current instrument position unknown")
            if not currInstPosName.lower() == self.instPos.lower():
                raise sr.ScriptError("%s is not the current instrument position (%s)!" % (self.instPos, currInstPosName))
            
            self.instScale = sr.getKeyVar(self.tccModel.gimScale, ind=None)
            self.instCtr = sr.getKeyVar(self.tccModel.gimCtr, ind=None)
            self.instLim = sr.getKeyVar(self.tccModel.gimLim, ind=None)
        else:
            # data from tcc tinst:I_NA2_DIS.DAT 18-OCT-2006
            self.instScale = [-12066.6, 12090.5] # unbinned pixels/deg
            self.instCtr = [240, 224]
            self.instLim = [0, 0, 524, 511]
        
        self.arcsecPerPixel = 3600.0 * 2 / (abs(self.instScale[0]) + abs(self.instScale[1]))

class ImagerFocusScript(BaseFocusScript):
    """Focus script for imaging instrument.
    
    This is like an Offset Guider but the exposure commands
    are sent to the instrument actor and centroid and findstars commands
    are sent to nexpose using the image just taken.
    
    For now there is no standard way to handle windowing and binning
    so each instrument must override waitExpose to use windowing.
    As a result the default value of doWindow is false.
    However, if the exposure command gets arguments for windowing
    then this will all change.
    
    Inputs:
    - instName: name of instrument (e.g. "DIS"); must be a name known to TUI.Inst.ExposeModel.
    - imageViewerTLName: name of image viewer toplevel (e.g. "Guide.DIS Slitviewer")
    - defRadius: default centroid radius, in arcsec
    - defBinFactor: default bin factor; if None then bin factor cannot be set
    - maxFindAmpl: maximum star amplitude for finding stars (peak - sky in ADUs);
        if None then star finding is disabled.
    - doWindow: if True, subframe images during focus sequence
    - windowOrigin: index of left or lower pixel for window (0 or 1 unless very wierd);
        this is not use for star positions, which all have the same convention
    - windowIsInclusive: is the upper-right window coord included in the image?
    - doZeroOverscan: if True then set overscan to zero
    - helpURL: URL of help file
    - debug: if True, run in debug mode, which uses fake data and does not communicate with the hub.
    """
    def __init__(self,
        sr,
        instName,
        imageViewerTLName = None,
        defRadius = 5.0,
        defBinFactor = 1,
        maxFindAmpl = None,
        doWindow = False,
        windowOrigin = 1,
        windowIsInclusive = True,
        doZeroOverscan = False,
        helpURL = None,
        debug = False,
    ):
        """The setup script; run once when the script runner
        window is created.
        """
        # this is a hack for now
        gcamActor = {
            "nicfps": "nfocus",
            "spicam": "sfocus",
        }[instName.lower()]
        BaseFocusScript.__init__(self,
            sr = sr,
            gcamActor = gcamActor,
            instName = instName,
            imageViewerTLName = imageViewerTLName,
            defRadius = defRadius,
            defBinFactor = defBinFactor,
            maxFindAmpl = maxFindAmpl,
            doWindow = doWindow,
            windowOrigin = windowOrigin,
            windowIsInclusive = windowIsInclusive,
            helpURL = helpURL,
            debug = debug,
        )
        self.exposeModel = TUI.Inst.ExposeModel.getModel(instName)
        self.doZeroOverscan = bool(doZeroOverscan)

    def formatBinFactorArg(self):
        """Return bin factor argument for expose/centroid/findstars command"""
        if self.defBinFactor == None:
            return ""
        return "bin=%d,%d" % (self.binFactor, self.binFactor)

    def formatExposeArgs(self, doWindow=True):
        """Format arguments for exposure command.
        
        Inputs:
        - doWindow: if true, window the exposure (if permitted)
        """
        try:
            retStr = BaseFocusScript.formatExposeArgs(self, doWindow)
        except TypeError:
            # try to shed light on an intermittent bug
            print "Focus script bug diagnostic information"
            print "self.__class__ =", self.__class__
            print "inheritance tree =", inspect.getclasstree([self.__class__]) 
            raise
        
        retStr += " name=%s_focus" % (self.exposeModel.instInfo.instActor,)
        if self.doZeroOverscan:
            retStr += " overscan=0,0"
        return retStr
    
    def waitCentroid(self):
        """Take an exposure and centroid using 1x1 binning.
        
        If the centroid is found, sets sr.value to the FWHM.
        Otherwise sets sr.value to None.
        """
        sr = self.sr
        
        yield self.waitExpose()
        filePath = sr.value
        
        centroidCmdStr = "centroid file=%s on=%0.1f,%0.1f cradius=%0.1f" % \
            (filePath, self.relStarPos[0], self.relStarPos[1], self.centroidRadPix)
        yield sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = centroidCmdStr,
           keyVars = (self.guideModel.star,),
           checkFail = False,
        )
        cmdVar = sr.value
        if sr.debug:
            starData = makeStarData("c", self.relStarPos)
        else:
            starData = cmdVar.getKeyVarData(self.guideModel.star)
        if starData:
            sr.value = StarMeas.fromStarKey(starData[0])
        else:
            sr.value = StarMeas()
    
    def getExposeCmdDict(self, doWindow=True):
        """Get basic command arument dict for an expose command
        
        This includes actor, cmdStr, abortCmdStr
        """
        return dict(
            actor = self.exposeModel.actor,
            cmdStr = "object " + self.formatExposeArgs(doWindow),
            abortCmdStr = "abort",
        )

    def waitExpose(self, doWindow=True):
        """Take an exposure.
        Return the file path of the exposure in sr.value.
        Raise ScriptError if the exposure fails.
        """
        sr = self.sr
        
        self.sr.showMsg("Exposing for %s sec" % (self.expTime,))
        basicCmdDict = self.getExposeCmdDict(doWindow)
        yield sr.waitCmd(
           keyVars = (self.exposeModel.files,),
           checkFail = False,
           **basicCmdDict
        )
        cmdVar = sr.value
        fileInfoList = cmdVar.getKeyVarData(self.exposeModel.files)
        if self.sr.debug:
            fileInfoList = [("me", "localhost", "tmp", "debug", "me", "test.fits")]
        if not fileInfoList:
            raise self.sr.ScriptError("exposure failed")
        filePath = "".join(fileInfoList[0][2:6])
        sr.value = filePath

    def waitFindStar(self):
        """Take a full-frame exposure and find the best star that can be centroided.

        Set sr.value to StarMeas for found star.
        
        If no star found displays a warning and sets sr.value to empty StarMeas.
        """
        sr = self.sr
        
        yield self.waitExpose(doWindow=False)
        filePath = sr.value
        
        findStarCmdStr = "findstars file=%s" % (filePath,)
        
        yield sr.waitCmd(
           actor = self.gcamActor,
           cmdStr = findStarCmdStr,
           keyVars = (self.guideModel.star,),
           checkFail = False,
        )
        cmdVar = sr.value
        self.didTakeImage = True
        if self.sr.debug:
            starDataList = makeStarData("f", (50.0, 75.0))
        else:
            starDataList = cmdVar.getKeyVarData(self.guideModel.star)
        
        if not starDataList:
            sr.value = StarMeas()
            self.sr.showMsg("No stars found", severity=RO.Constants.sevWarning)
            return
        
        yield self.waitFindStarInList(filePath, starDataList)


def polyfitw(x, y, w, ndegree, return_fit=False):
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
        If return_fit is false (the default) then polyfitw returns only C, a vector of 
        coefficients of length ndegree+1.
        If return_fit is true then polyfitw returns a tuple (c, yfit, yband, sigma, a)
            yfit:   
            The vector of calculated Y's.  Has an error of + or - yband.

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
    a = numpy.zeros((m,m), float)  # least square matrix, weighted matrix
    b = numpy.zeros(m, float)  # will contain sum w*y*x^j
    z = numpy.ones(n, float)   # basis vector for constant term

    a[0,0] = numpy.sum(w)
    b[0] = numpy.sum(w*y)

    for p in range(1, 2*ndegree+1):      # power loop
        z = z*x # z is now x^p
        if (p < m):  b[p] = numpy.sum(w*y*z)  # b is sum w*y*x^j
        sum = numpy.sum(w*z)
        for j in range(max(0,(p-ndegree)), min(ndegree,p)+1):
            a[j,p-j] = sum

    a = numpy.linalg.inv(a)
    c = numpy.dot(b, a)
    if not return_fit:
        return c         # exit if only fit coefficients are wanted

    # compute optional output parameters.
    yfit = numpy.zeros(n, float)+c[0]  # one-sigma error estimates, init
    for k in range(1, ndegree +1):
        yfit = yfit + c[k]*(x**k)  # sum basis vectors
    var = numpy.sum((yfit-y)**2 )/(n-m)  # variance estimate, unbiased
    sigma = numpy.sqrt(var)
    yband = numpy.zeros(n, float) + a[0,0]
    z = numpy.ones(n, float)
    for p in range(1,2*ndegree+1):      # compute correlated error estimates on y
        z = z*x      # z is now x^p
        sum = 0.
        for j in range(max(0, (p - ndegree)), min(ndegree, p)+1):
            sum = sum + a[j,p-j]
        yband = yband + sum * z      # add in all the error sources
    yband = yband*var
    yband = numpy.sqrt(yband)
    return c, yfit, yband, sigma, a
