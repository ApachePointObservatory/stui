#!/usr/bin/env python
"""Take NICFPS exposures in a dither pattern appropriate to extended sources.

Take NICFPS exposures in a square pattern plus a point in the middle,
as well as a square pattern plus a point in the middle (nominally) 1 arcminute away.
Note: uses object (arc) offsets (unlike the Point Source script, which uses boresight offsets).

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select which portions of the chip to visit.

To do:
- Make offset labels change depending on coordinate system.
- Fail unless NICFPS is in imaging mode.

History:
2008-04-15 CWood    Modified from Point Source.py

Corey's to-do:
- Take off debug mode once at the telescope
"""
import math
import Tkinter
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
DefBoxSize = 20 # arcsec
MaxOffset = 3600 #arcsec
DefOffset = 300 # default offset along each axis, in arcsec.
HelpURL = "Scripts/BuiltInScripts/NICFPSDitherExtendedSource.html"

class ScriptClass(object):  
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        # if sr.debug True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        
        self.didMove = False
        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
    
        row=0
        
        # standard exposure status widget
        expStatusWdg = ExposeStatusWdg(sr.master, InstName)
        expStatusWdg.grid(row=row, column=0, sticky="news")
        row += 1
        
        # create checkbuttons showing where exposures will be taken
        quadFrame = Tkinter.Frame(sr.master)
        
        # quadrant data; each entry is:
        # - name of quadrant
        # - arc offset multiplier in image x, image y
        quadData = [
            ("Ctr", (0, 0)),
            ("UL", (-1, 1)),
            ("UR", (1, 1)),
            ("LR", (1, -1)),
            ("LL", (-1, -1)),
        ]
        self.quadWdgSet = []
        for name, arcOffMult in quadData:
            wdg = RO.Wdg.Checkbutton(
                master = quadFrame,
                text = name,
                defValue = True,
                relief = "flat",
                helpText = "Expose here if checked",
                helpURL = HelpURL,
            )
            # add attribute "arcOffMult" to widget
            # so it can be read by "run"
            wdg.arcOffMult = arcOffMult
            
            # display quadrant checkbutton in appropriate location
            row = 1 - arcOffMult[1]
            col = 1 + arcOffMult[0]
            wdg.grid(row=row, column=col)
            
            self.quadWdgSet.append(wdg)
        
        quadFrame.grid(row=row, column=0, sticky="news")
        row += 1
    
        # standard exposure input widget
        self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
        self.expWdg.numExpWdg.helpText = "# of pairs of exposures at each point"
        self.expWdg.grid(row=row, column=0, sticky="news")
        row += 1

        # add in the three offset input boxes
        self.boxSizeWdg = RO.Wdg.IntEntry(
            master = self.expWdg,
            minValue = 0,
            defValue = DefBoxSize,
            helpText = "size of dither box",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Box Size", self.boxSizeWdg, "arcsec")
        row += 1

        unitsVar = Tkinter.StringVar()
        self.offsetSizeXWdg = RO.Wdg.DMSEntry(
            master = self.expWdg,
            minValue = -MaxOffset,
            maxValue = MaxOffset,
            defValue = DefOffset,
            isHours = False,
            isRelative = True,
            helpText = "Object offset in RA for off-source dither",
            helpURL = HelpURL,
            unitsVar = unitsVar,
        )
        self.expWdg.gridder.gridWdg(
            "Offset RA",
            self.offsetSizeXWdg,
            units = self.offsetSizeXWdg.unitsVar,
        )
        row += 1

        self.offsetSizeYWdg = RO.Wdg.DMSEntry(
            master = self.expWdg,
            minValue = -MaxOffset,
            maxValue = MaxOffset,
            defValue = DefOffset,
            isHours = False,
            isRelative = True,
            helpText = "Object offset in Dec for off-source dither",
            helpURL = HelpURL,
            unitsVar = unitsVar,
        )
        self.expWdg.gridder.gridWdg(
            "Offset Dec",
            self.offsetSizeYWdg,
            units = self.offsetSizeYWdg.unitsVar,
        )
     
    def run(self, sr):
        """Take an exposure sequence.
        """
        self.didMove = False
    
        # get current NICFPS focal plane geometry from the TCC
        # but first make sure the current instrument
        # is actually NICFPS
        if not sr.debug:
            currInstName = sr.getKeyVar(self.tccModel.instName)
            if not currInstName.lower().startswith(InstName.lower()):
                raise sr.ScriptError("%s is not the current instrument!" % InstName)
    
        # record the current object offset position
        begArcPVTs = sr.getKeyVar(self.tccModel.objArcOff, ind=None)
        if not sr.debug:
            self.begArcXY = [pvt.getPos() for pvt in begArcPVTs]
            if None in self.begArcXY:
                raise sr.ScriptError("Current object offset position unknown")
        #else:
        #    self.begArcXY = [0.0, 0.0]
        self.begArcXY = [0.0, 0.0]
        #print "self.begArcXY=%r" % self.begArcXY

        # vector describing how far away from the object to move
        # in order to do the second dither pattern
        offVec = [
            self.offsetSizeXWdg.getNum(),
            self.offsetSizeYWdg.getNum(),
        ]

        # exposure command without startNum and totNum
        # get it now so that it will not change if the user messes
        # with the controls while the script is running
        numExp = self.expWdg.numExpWdg.getNum()
        expCmdPrefix = self.expWdg.getString()
        if not expCmdPrefix:
            raise sr.ScriptError("missing inputs")

        # size of the offset for each point in the dither pattern
        offsetSize =  self.boxSizeWdg.getNum() / 2.0
        
        # record which points to use in the dither pattern in advance
        # (rather than allowing the user to change it during execution)
        doPtArr = [wdg.getBool() for wdg in self.quadWdgSet]
        
        numExpTaken = 0
        numPtsToGo = sum(doPtArr)

        # totNum has 2x more than the point source dither, since
        # it does an entirely different dither pattern off-source
        totNum = 2 * numPtsToGo * numExp

        # The zero-indexed counter of how many actual dither points we've been to
        pointCounter = 0

        # A variable to keep track of being on- or off-source
        offSource = False

        # loop through each checkbox
        for ind in range(len(self.quadWdgSet)):
            wdg = self.quadWdgSet[ind]
            wdg["relief"] = "groove"
            
            if not doPtArr[ind]:
                wdg["relief"] = "sunken"
                continue
                
            posName = str(wdg["text"])

            # Looping twice, since we need to do two different positions 
            # for each of the 5 selected dither points.
            for i in range(2):
                # compute # of exposures & format expose command
                startNum = numExpTaken + 1

                expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)
            
                # Calculate the new offset
                if offSource:
                    sr.showMsg("Offset to off-source %s position" % posName)
                else:
                    sr.showMsg("Offset to on-source %s position" % posName)

                arcPosXY = [
                    self.begArcXY[0] + (((offVec[0] * offSource) + (wdg.arcOffMult[0] * offsetSize)) / 3600.0),
                    self.begArcXY[1] + (((offVec[1] * offSource) + (wdg.arcOffMult[1] * offsetSize)) / 3600.0),
                ]
                """ # Old and busted: Doesn't do ABBA
                arcPosXY = [
                    self.begArcXY[0] + (wdg.arcOffMult[0] * (offsetSize / 3600.0)),
                    self.begArcXY[1] + (wdg.arcOffMult[1] * (offsetSize / 3600.0)),
                ]
                """
                
                # Send the slew command
                if numExpTaken > 0:
                    yield sr.waitCmd(
                        actor = "tcc",
                        cmdStr = "offset arc %.6f, %.6f /pabs/computed" % (arcPosXY[0], arcPosXY[1]),
                    )

                    self.didMove = True
            
                # take exposure sequence
                if offSource:
                    sr.showMsg("Expose at off-source %s position" % posName)
                else:
                    sr.showMsg("Expose at on-source %s position" % posName)
                
                yield sr.waitCmd(
                    actor = self.expModel.actor,
                    cmdStr = expCmdStr,
                    abortCmdStr = "abort",
                )
                
                numExpTaken += numExp

                pointCounter += 1

                if pointCounter % 2:
                    offSource = not offSource

                wdg["relief"] = "sunken"

            numPtsToGo -= 1
        
        # slew back to starting position
        if self.didMove:
            sr.showMsg("Finishing up: slewing to initial position")
            tccCmdStr = "offset arc %.7f, %.7f /pabs/vabs/computed" % tuple(self.begArcXY)
            self.didMove = False
            yield sr.waitCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )
            
    def end(self, sr):
        """If telescope moved, restore original object offset position.
        """
        for wdg in self.quadWdgSet:
            wdg["relief"] = "flat"

        #print "end called"
        if self.didMove:
            # restore original offset position
            if None in self.begArcXY:
                return
                
            tccCmdStr = "offset arc %.7f, %.7f /pabs/vabs/computed" % tuple(self.begArcXY)
            #print "sending tcc command %r" % tccCmdStr
            sr.startCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )
