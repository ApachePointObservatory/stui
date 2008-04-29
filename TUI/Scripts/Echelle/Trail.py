"""Script to trail along the Echelle slit during an exposure.

To do:
- When the hub supports it, get the slit length from the hub.

History:
2004-10-01 ROwen
2005-01-05 ROwen    Modified for RO.Wdg.Label state -> severity.
2006-04-19 ROwen    Changed to a class.
2006-04-27 ROwen    Require # of trails >= 1.
                    Cannot change # of trails or exposure params while trailing.
                    Improved error output.
                    Added support for debug mode.
                    Improved handling of drift speed and range by eliminating
                    class attributes that matched the contents of widgets.
2008-04-29 ROwen    Fixed reporting of exceptions that contain unicode arguments.
"""
import Tkinter
import RO.Wdg
import RO.PhysConst
import RO.StringUtil
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.ExposeStatusWdg
import TUI.Inst.ExposeInputWdg

# constants
InstName = "Echelle"
SlitLengthAS = 3.2 # slit length, in arcsec
MaxTrailLengthAS = 200.0 # max trail length, in arcsec
MaxVelAS = 200.0 # maximum speed, in arcsec/sec
HelpURL = "Scripts/BuiltInScripts/EchelleTrail.html"

class ScriptClass(object):
    def __init__(self, sr):
        """Set up widgets to set input exposure time,
        trail cycles and trail range and display trail speed.
        """
        # if True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False

        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.ScriptError = sr.ScriptError
        
        row=0
        
        # standard exposure status widget
        expStatusWdg = TUI.Inst.ExposeStatusWdg.ExposeStatusWdg(
            master = sr.master,
            instName = InstName,
            helpURL = HelpURL,
        )
        expStatusWdg.grid(row=row, column=0, sticky="news")
        row += 1
    
        # separator
        Tkinter.Frame(sr.master,
            bg = "black",
        ).grid(row=row, column=0, pady=2, sticky="ew")
        row += 1
        
        # standard exposure input widget
        self.expWdg = TUI.Inst.ExposeInputWdg.ExposeInputWdg(
            master = sr.master,
            instName = InstName,
            expTypes = "object",
            helpURL = HelpURL,
        )
        self.expWdg.numExpWdg.helpText = "# of exposures at each point"
        self.expWdg.grid(row=row, column=0, sticky="news")
        row += 1
        
        # add some controls to the exposure input widget
        
        # number of moves
        self.numTrailsWdg = RO.Wdg.IntEntry (
            master = self.expWdg,
            minValue = 1,
            maxValue = 99,
            defValue = 5,
            width = 6,
            helpText = "Number of trails (2 is up, then down)",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("# of Trails", self.numTrailsWdg)
        
        # trail range
        rangeFrame = Tkinter.Frame(self.expWdg)
    
        self.trailRangeWdg = RO.Wdg.FloatEntry (
            master = rangeFrame,
            minValue = 0,
            maxValue = MaxTrailLengthAS,
            defValue = SlitLengthAS * 1.2,
            defFormat = "%.1f",
            defMenu = "Default",
            width = 6,
            helpText = "Length of trail (centered on starting point)",
            helpURL = HelpURL,
        )
        self.trailRangeWdg.pack(side="left")
        
        RO.Wdg.StrLabel(rangeFrame, text='" =').pack(side = "left")
    
        self.trailRangePercentWdg = RO.Wdg.FloatLabel (
            master = rangeFrame,
            precision = 0,
            width = 6,
            helpText = "Length of trail as % of length of DEFAULT slit",
            helpURL = HelpURL,
        )
        self.trailRangePercentWdg.pack(side = "left")
        
        RO.Wdg.StrLabel(rangeFrame, text="%").pack(side = "left")
        
        self.expWdg.gridder.gridWdg("Trail Length", rangeFrame, colSpan = 2, sticky="w")
        
        # trail speed
        speedFrame = Tkinter.Frame(self.expWdg)
    
        self.trailSpeedWdg = RO.Wdg.FloatEntry (
            master = speedFrame,
            defFormat = "%.1f",
            readOnly = True,
            relief = "flat",
            width = 6,
            helpText = "Speed of trailing",
            helpURL = HelpURL,
        )
        self.trailSpeedWdg.pack(side = "left")
        RO.Wdg.StrLabel(speedFrame, text = '"/sec').pack(side = "left")
    
        self.expWdg.gridder.gridWdg("Trail Speed", speedFrame)
        
        self.expWdg.gridder.allGridded()
        
        self.numTrailsWdg.addCallback(self.updateTrailSpeed)
        self.trailRangeWdg.addCallback(self.updateTrailSpeed)
        self.expWdg.timeWdg.addCallback(self.updateTrailSpeed, callNow=True)

    def updateTrailSpeed(self, *args):
        expTime = self.expWdg.timeWdg.getNumOrNone()
        numTrails = self.numTrailsWdg.getNumOrNone()
        trailRangeAS = self.trailRangeWdg.getNumOrNone()

        if trailRangeAS != None:
            self.trailRangePercentWdg.set(trailRangeAS * 100.0 / SlitLengthAS)
        else:
            self.trailRangePercentWdg.set(None, isCurrent = False)

        if None in (expTime, numTrails, trailRangeAS):
            self.trailSpeedWdg.set(None, isCurrent=False)
            return

        trailSpeedAS = abs(numTrails * trailRangeAS / expTime)

        trailSpeedOK = (trailSpeedAS <= MaxVelAS)
        if trailSpeedOK:
            severity = RO.Constants.sevNormal
        else:
            severity = RO.Constants.sevError

        self.trailSpeedWdg.set(trailSpeedAS, severity = severity)
        
    def getStartXY(self, trailRange, trailDir):
        return (
            self.begBoreXY[0],
            self.begBoreXY[1] - (trailRange * trailDir / 2.0)
        )
    
    def run(self, sr):
        """Take one or more exposures while moving the object
        back and forth along the slit.
        """
        self.begBoreXY = [None, None]
        self.didMove = False
    
        # make sure the current instrument matches the desired instrument
        if not sr.debug:
            currInst = sr.getKeyVar(self.tccModel.instName)
            if InstName.lower() != currInst.lower():
                raise sr.ScriptError("%s is not the current instrument!" % InstName)
        
        # record the current boresight position
        begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
        if not sr.debug:
            self.begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
            if None in self.begBoreXY:
                raise sr.ScriptError("Current boresight position unknown")
        else:
            self.begBoreXY = (0.0, 0.0)
    #   print "self.begBoreXY=%r" % self.begBoreXY
        
        # sanity check exposure inputs
        # (will raise an exception if no expTime or file name)
        try:
            self.expWdg.getString()
        except Exception, e:
            raise sr.ScriptError(RO.StringUtil.strFromException(e))
            
        # get basic exposure command
        expCmdPrefix = self.expWdg.getString(numExp = 1)
        if expCmdPrefix == None:
            raise sr.ScriptError("missing inputs")
        
        # get trail info and related info
        # time is in seconds
        # distance is in arcsec (AS suffix) or degrees (no suffix)
        expTime = self.getNumFromWdg(self.expWdg.timeWdg, "Specify Exposure Time")
        numExp = self.getNumFromWdg(self.expWdg.numExpWdg, "Specify # Exposures")
        if numExp <0:
            raise sr.ScriptError("# Exposures <= 0")
        numTrails = self.getNumFromWdg(self.numTrailsWdg, "Specify # of Trails")
        trailRangeAS = self.getNumFromWdg(self.trailRangeWdg, "Specify Trail Length")
        trailSpeedAS = self.getNumFromWdg(self.trailSpeedWdg, "Bug: Trail Speed unknown")
        
        if self.trailSpeedWdg.getSeverity() != RO.Constants.sevNormal:
            raise sr.ScriptError("Trail speed too fast!")       
            
        trailRange = trailRangeAS / RO.PhysConst.ArcSecPerDeg
        trailSpeed = trailSpeedAS / RO.PhysConst.ArcSecPerDeg
        
        # should probably check against axis limits
        # but for now let's assume the user has a clue...
        
        numExp = self.expWdg.numExpWdg.getNum()
        if numExp <= 0:
            sr.showMsg("No exposures wanted, nothing done", 2)
    
        trailDir = 1
    
        # slew to start position
        sr.showMsg("Slewing to start position")
        startPosXY = self.getStartXY(trailRange, trailDir)
        tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
            (startPosXY[0], startPosXY[1])
    #       print "sending tcc command %r" % tccCmdStr
        self.didMove = True
        yield sr.waitCmd(
            actor = "tcc",
            cmdStr = tccCmdStr,
        )
        
        for expNum in range(1, numExp + 1):
            isLast = (expNum >= numExp)
    
            expCycleStr = "exposure %d of %d" % (expNum, numExp)
    
            # start exposure
            sr.showMsg("Starting %s; waiting for shutter" % expCycleStr)
            expCmdStr = "%s startNum=%s totNum=%s" % (expCmdPrefix, expNum, numExp)
            #print "sending %s command %r" % (InstName, expCmdStr)
            expCmdVar = sr.startCmd(
                actor = self.expModel.actor,
                cmdStr = expCmdStr,
                abortCmdStr = "abort",
            )
            
            if numTrails > 0:
                trailTime = expTime / numTrails
            else:
                trailTime = 0.0
            
            # wait for flushing to end and exposure to begin
            if not sr.debug:
                while True:
                    yield sr.waitKeyVar(self.expModel.expState, ind=1, waitNext=True)
                    if sr.value.lower() == "integrating":
                        break
            else:
                yield sr.waitMS(1000)
            
            # execute trails
            for trailNum in range(1, numTrails + 1):
                sr.showMsg("Trail %d of %d for %s" % (trailNum, numTrails, expCycleStr))
                startPosXY = self.getStartXY(trailRange, trailDir)
                tccCmdStr = "offset boresight %.7f, %.7f, 0, %.7f/pabs/vabs" % \
                    (startPosXY[0], startPosXY[1], trailSpeed * trailDir)
                #print "sending tcc command %r" % tccCmdStr
                yield sr.waitCmd(
                    actor = "tcc",
                    cmdStr = tccCmdStr,
                )
                
                yield sr.waitMS(trailTime * 1000.0)
                
                trailDir = -trailDir
            
            # wait for integration to end; be sure to examine
            # the current state in case the timing got messed up
            # and integration already finished
            sr.showMsg("Ending %s; waiting for shutter" % (expCycleStr,))
            if not sr.debug:
                while True:
                    yield sr.waitKeyVar(self.expModel.expState, ind=1, waitNext=False)
                    if sr.value.lower() != "integrating":
                        break
            else:
                yield sr.waitMS(1000)
            
            # slew to next position
            if not isLast:
                # slew to start position for next exposure
                sr.showMsg("Slewing to start pos. for next exposure")
                startPosXY = self.getStartXY(trailRange, trailDir)
                tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
                    (startPosXY[0], startPosXY[1])
                #print "sending tcc command %r" % tccCmdStr
                self.didMove = True
                yield sr.waitCmd(
                    actor = "tcc",
                    cmdStr = tccCmdStr,
                )
            else:
                sr.showMsg("Cleaning up: slewing to initial position")
                tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begBoreXY)
                self.didMove = False
                yield sr.waitCmd(
                    actor = "tcc",
                    cmdStr = tccCmdStr,
                )
    
            # wait for exposure to end
            sr.showMsg("Waiting for %s to finish" % expCycleStr)
            yield sr.waitCmdVars(expCmdVar)
    
    def getNumFromWdg(self, wdg, errMsg):
        """Get a numeric value from a numeric RO.Wdg.Entry widget.
        Raise sr.ScriptError if the entry is blank.
        """
        val = wdg.getNumOrNone()
        if val == None:
            raise self.ScriptError(errMsg)
        return val
            
    def end(self, sr):
        """If telescope moved, restore original boresight position.
        """
        #print "end called"
        if self.didMove:
            # restore original boresight position
            if None in self.begBoreXY:
                return
                
            tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begBoreXY)
        #   print "sending tcc command %r" % tccCmdStr
            sr.startCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )
