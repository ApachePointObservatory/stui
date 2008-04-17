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
2008-04-17 ROwen    Display order and state of execution of each node.
"""
import itertools
import math
import numpy
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
        self.sr = sr

        self.begOffset = (None, None)
        self.currOffset = self.begOffset[:]
        
        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
    
        row=0
        
        # standard exposure status widget
        expStatusWdg = ExposeStatusWdg(sr.master, InstName)
        expStatusWdg.grid(row=row, column=0, sticky="news")
        row += 1
        
        # create dither node controls
        ditherFrame = Tkinter.Frame(sr.master)
        
        # information about the dither nodes; each entry is:
        # - name of quadrant
        # - boresight offset multiplier in image x, image y
        ditherNodeData = [
            ("Ctr", (0, 0)),
            ("UL", (-1, 1)),
            ("UR", (1, 1)),
            ("LR", (1, -1)),
            ("LL", (-1, -1)),
        ]
        self.ditherWdgSet = [] # (stateWdg, orderWdg, boolWdg), one per dither node
        for name, offMult in ditherNodeData:
            nodeFrame = Tkinter.Frame(ditherFrame)

            stateWdg = RO.Wdg.StrLabel(
                master = nodeFrame,
                width = 7,
                relief = "flat",
                helpText = "State of node in dither sequence",
                helpURL = HelpURL,
            )
            orderWdg = RO.Wdg.IntLabel(
                master = nodeFrame,
                width = 1,
                relief = "flat",
                helpText = "Order of node in dither sequence",
                helpURL = HelpURL,
            )
            boolWdg = RO.Wdg.Checkbutton(
                master = nodeFrame,
                text = name,
                callFunc = self.updOrder,
                defValue = True,
                relief = "flat",
                helpText = "Check to use this dither node",
                helpURL = HelpURL,
            )
            # add attribute "offMult" to widget
            # so it can be read by "run"
            boolWdg.offMult = offMult
            
            self.ditherWdgSet.append((stateWdg, orderWdg, boolWdg))

            stateWdg.pack(side="left")
            orderWdg.pack(side="left")
            boolWdg.pack(side="left")
            
            # display quadrant checkbutton in appropriate location
            row = 1 - offMult[1]
            col = 1 + offMult[0]
            nodeFrame.grid(row=row, column=col)
            
        
        ditherFrame.grid(row=row, column=0, sticky="news")
        row += 1
        # standard exposure input widget
        self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
        self.expWdg.numExpWdg.helpText = "# of pairs of exposures at each node"
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

        self.skyOffsetWdgSet = []
        for ii in range(2):
            axisStr = ("RA", "Dec")[ii]
            unitsVar = Tkinter.StringVar()
            offsetWdg = RO.Wdg.DMSEntry(
                master = self.expWdg,
                minValue = -MaxOffset,
                maxValue = MaxOffset,
                defValue = DefOffset,
                isHours = False,
                isRelative = True,
                helpText = "Offset to sky in %s (typically)" % (axisStr,),
                helpURL = HelpURL,
                unitsVar = unitsVar,
            )
            self.skyOffsetWdgSet.append(offsetWdg)
            self.expWdg.gridder.gridWdg(
                "Sky Offset %s" % (ii + 1,),
                offsetWdg,
                units = unitsVar,
            )
            row += 1
            
    def end(self, sr):
        """If telescope offset, restore original position.
        """
        self.updOrder(doForce=True)
        
        #print "end called"
        # restore original boresight position, if changed
        if self.needMove(self.currOffset):
            tccCmdStr = "offset arc %.7f, %.7f/pabs/vabs/computed" % tuple(self.begOffset)
            #print "sending tcc command %r" % tccCmdStr
            sr.startCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )

    def needMove(self, desOffset):
        """Return True if telescope not at desired offset"""
        if None in self.begOffset:
            return False
        return not numpy.allclose(self.begOffset, desOffset)         
     
    def run(self, sr):
        """Take an exposure sequence.
        """
        # clear node state
        for wdgSet in self.ditherWdgSet:
            wdgSet[0].set(None)

        # get current NICFPS focal plane geometry from the TCC
        # but first make sure the current instrument is actually NICFPS
        if not sr.debug:
            currInstName = sr.getKeyVar(self.tccModel.instName)
            if not currInstName.lower().startswith(InstName.lower()):
                raise sr.ScriptError("%s is not the current instrument!" % InstName)
    
        # record the current object offset position
        begArcPVTs = sr.getKeyVar(self.tccModel.objArcOff, ind=None)
        if not sr.debug:
            self.begOffset = [pvt.getPos() for pvt in begArcPVTs]
            if None in self.begOffset:
                raise sr.ScriptError("Current object offset unknown")
        else:
            self.begOffset = [0.0, 0.0]
        self.begOffset = [0.0, 0.0]
        #print "self.begOffset=%r" % self.begOffset

        # vector describing how far away from the object to move
        # in order to do the second dither pattern
        skyOffset = [
            self.skyOffsetWdgSet[0].getNum(),
            self.skyOffsetWdgSet[1].getNum(),
        ]

        # exposure command without startNum and totNum
        # get it now so that it will not change if the user messes
        # with the controls while the script is running
        numExp = self.expWdg.numExpWdg.getNum()
        expCmdPrefix = self.expWdg.getString()
        if not expCmdPrefix:
            raise sr.ScriptError("missing inputs")

        # size of the offset for each node in the dither pattern
        ditherSize =  self.boxSizeWdg.getNum() / 2.0
        
        # record which points to use in the dither pattern in advance
        # (rather than allowing the user to change it during execution)
        doPtArr = [wdgs[-1].getBool() for wdgs in self.ditherWdgSet]
        
        numExpTaken = 0
        numPtsToGo = sum(doPtArr)
        totNum = numPtsToGo * numExp * 2

        # loop through each dither node
        # taking nExp exposures at each of:
        # node 1 source, node 1 sky, node 2 sky, node 2 source...
        onSkyIter = itertools.cycle((False, True, True, False))
        for ind, wdgSet in enumerate(self.ditherWdgSet):
            stateWdg, orderWdg, boolWdg = wdgSet
            if not doPtArr[ind]:
                stateWdg.set("Skipped")
                continue
            nodeName = str(boolWdg["text"])

            # Expose on object and sky at this dither point
            for i in range(2):
                onSky = onSkyIter.next()
                if onSky:
                    srcName = "Sky"
                else:
                    srcName = "Source"

                stateWdg.set(srcName)

                # compute # of exposures & format expose command
                startNum = numExpTaken + 1

                expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)
            
                # offset telescope
                desOffset = [
                    self.begOffset[0] + (((skyOffset[0] * onSky) + (boolWdg.offMult[0] * ditherSize)) / 3600.0),
                    self.begOffset[1] + (((skyOffset[1] * onSky) + (boolWdg.offMult[1] * ditherSize)) / 3600.0),
                ]
                if self.needMove(desOffset):
                    sr.showMsg("Offset to %s %s position" % (srcName, nodeName))
                    yield self.waitOffset(desOffset)
            
                # take exposure sequence
                sr.showMsg("Expose on %s %s position" % (srcName, nodeName))
                yield sr.waitCmd(
                    actor = self.expModel.actor,
                    cmdStr = expCmdStr,
                    abortCmdStr = "abort",
                )
                
                numExpTaken += numExp
            
            numPtsToGo -= 1
            stateWdg.set("Done")
        
        # slew back to starting position
        if self.needMove(self.currOffset):
            sr.showMsg("Finishing up: slewing to initial position")
            yield self.waitOffset(self.begOffset)

    def updOrder(self, wdg=None, doForce=False):
        """Update the order widgets
        
        If the script is executing then the widgets are left untouched
        unless doForce is True. This allows the order widgets to be correct
        while running even if the user messes with the checkboxes.
        """
        if not doForce and self.sr.isExecuting():
            return
        orderNum = 1
        for stateWdg, orderWdg, boolWdg in self.ditherWdgSet:
            if boolWdg.getBool():
                orderWdg.set(orderNum)
                orderNum += 1
            else:
                orderWdg.set(None)
    
    def waitOffset(self, desOffset):
        """Offset the telescope"""
        tccCmdStr = "offset arc %.7f, %.7f/pabs/vabs/computed" % tuple(desOffset)
        self.currOffset = desOffset[:]
        yield self.sr.waitCmd(
            actor = "tcc",
            cmdStr = tccCmdStr,
        )
