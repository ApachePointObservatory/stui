#!/usr/bin/env python
"""Take NICFPS exposures in a square pattern plus a point in the middle.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select which portions of the chip to visit.

To do:
- Fail unless NICFPS is in imaging mode.

History:
2004-10-19 ROwen    first cut; direct copy of GRIM:Square
2005-01-24 ROwen    Changed order to ctr, UL, UR, LR, LL.
                    Changed Offset Size to Box Size (2x as big)
                    and made 20" the default box size.
                    Modified to record dither points in advance
                    (instead of allowing change 'on the fly').
                    Renamed from Dither.py to Dither/Point Source.py
2006-04-20 ROwen    Changed to a class.
                    Changed all offsets to /computed.
2006-04-27 ROwen    Bug fix: would try to run (but send bogus commands)
                    if required exposure fields were blank.
                    Added debug support.
2006-12-28 ROwen    Fix PR 515: modified to abort the exposure if the script is aborted.
2008-04-17 ROwen    Display order and state of execution of each node.
2008-04-18 ROwen    Added randomization option.
"""
import numpy
import random
import Tkinter
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
DefBoxSize = 20 # arcsec
DefDoRandom = False
RandomBoxSize = 10 # arcsec
HelpURL = "Scripts/BuiltInScripts/NICFPSDitherPointSource.html"

class ScriptClass(object):  
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        # if sr.debug True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        self.sr = sr

        self.begOffset = numpy.array((numpy.nan, numpy.nan))
        self.currOffset = self.begOffset[:]

        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
    
        row=0
        
        # standard exposure status widget
        expStatusWdg = ExposeStatusWdg(
            master = sr.master,
            instName = InstName,
            helpURL = HelpURL,
        )
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
            boolWdg.offMult = numpy.array(offMult, dtype=float)
            
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
        self.expWdg = ExposeInputWdg(
            master = sr.master,
            instName = InstName,
            expTypes = "object",
            helpURL = HelpURL,
        )
        self.expWdg.numExpWdg.helpText = "# of exposures at each point"
        self.expWdg.grid(row=row, column=0, sticky="news")
        row += 1
    
        # add controls to exposure input widget frame
        self.boxSizeWdg = RO.Wdg.IntEntry(
            master = self.expWdg,
            minValue = 0,
            defValue = DefBoxSize,
            helpText = "size of dither box",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Box Size", self.boxSizeWdg, "arcsec")
        
        self.doRandomWdg = RO.Wdg.Checkbutton(
            master = self.expWdg,
            defValue = DefDoRandom,
            helpText = "Add random scatter to dither pattern?",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Randomize?", self.doRandomWdg)
        
        if sr.debug:
            # set useful debug defaults
            self.expWdg.timeWdg.set("1.0")
            self.expWdg.numExpWdg.set(2)
            self.expWdg.fileNameWdg.set("debug")
            self.ditherWdgSet[1][-1].setBool(False)
            self.ditherWdgSet[3][-1].setBool(False)

        self.updOrder()
    
    def end(self, sr):
        """If telescope offset, restore original position.
        """
        self.updOrder(doForce=True)
        
        #print "end called"
        # restore original boresight position, if changed
        if self.needMove(self.currOffset):
            tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begOffset)
            #print "sending tcc command %r" % tccCmdStr
            sr.startCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )

    def needMove(self, desOffset):
        """Return True if telescope not at desired offset"""
        if numpy.any(numpy.isnan(self.begOffset)):
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
    
        # record the current boresight position
        begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
        if not sr.debug:
            begOffset = [pvt.getPos() for pvt in begBorePVTs]
            if None in begOffset:
                raise sr.ScriptError("Current boresight position unknown")
            self.begOffset = numpy.array(begOffset, dtype=float)
        else:
            self.begOffset = numpy.zeros(2, dtype=float)
        self.currOffset = self.begOffset[:]
        #print "self.begOffset=%r" % self.begOffset
        
        ditherSize = self.boxSizeWdg.getNum() / 2.0
        doRandom = self.doRandomWdg.getBool()
        
        # exposure command without startNum and totNumExp
        # get it now so that it will not change if the user messes
        # with the controls while the script is running
        numExp = self.expWdg.numExpWdg.getNumOrNone()
        if numExp == None:
            raise sr.ScriptError("must specify #Exp")
        if doRandom:
            # use randomization: take just one exposure and then apply a random offset
            self.expWdg.numExpWdg.set(1)
            expCmdPrefix = self.expWdg.getString()
            self.expWdg.numExpWdg.set(numExp)
        else:
            # no randomization: take all #Exp exposures at once
            expCmdPrefix = self.expWdg.getString()
        if not expCmdPrefix:
            raise sr.ScriptError("missing inputs")
        
        # record which points to use in the dither pattern in advance
        # (rather than allowing the user to change it during execution)
        doPtArr = [wdgs[-1].getBool() for wdgs in self.ditherWdgSet]      

        # loop through each dither node,
        # taking numExp exposures at each node
        ditherSizeDeg = ditherSize / 3600.0
        #randomRangeDeg = ditherSizeDeg / 2.0
        randomRangeDeg = RandomBoxSize / 3600.0
        numPtsToGo = sum(doPtArr)
        totNumExp = numPtsToGo * numExp
        numExpTaken = 0
        for ind, wdgSet in enumerate(self.ditherWdgSet):
            stateWdg, orderWdg, boolWdg = wdgSet
            if not doPtArr[ind]:
                stateWdg.set("Skipped")
                continue

            stateWdg.set("Running")
            nodeName = str(boolWdg["text"])
            
            desOffset = self.begOffset + (boolWdg.offMult * ditherSizeDeg)
            if doRandom:
                # apply random offset before each exposure at this position
                for expInd in range(numExp):
                    if numExpTaken == 0:
                        # do not randomize the first point; this saves a bit of time
                        randomScatter = numpy.zeros(2, dtype=float)
                        fullNodeName = "%s with no random scatter" % (nodeName,)
                    else:
                        randomScatter = (numpy.random.random(2) * randomRangeDeg) - (randomRangeDeg / 2.0)
                        randomScatterArcSec = randomScatter * 3600.0
                        fullNodeName = "%s + %0.1f, %0.1f random scatter" % \
                            (nodeName, randomScatterArcSec[0], randomScatterArcSec[1])
                    #print "Adding randomScatter", randomScatter
                    randomizedOffset = desOffset + randomScatter
                    if self.needMove(randomizedOffset):
                        # slew telescope
                        randomScatterArcSec = randomScatter * 3600.0
                        sr.showMsg("Offset to %s" % (fullNodeName,))
                        yield self.waitOffset(randomizedOffset)
                        
                    
                    # format exposure command
                    startNum = numExpTaken + 1
                    expCmdStr = "%s startNum=%d totNumExp=%d" % (expCmdPrefix, startNum, totNumExp)
                    
                    # take exposure sequence
                    sr.showMsg("Expose at %s" % (fullNodeName,))
                    yield sr.waitCmd(
                        actor = self.expModel.actor,
                        cmdStr = expCmdStr,
                        abortCmdStr = "abort",
                    )
                    numExpTaken += 1
            else:
                # no randomization; take all numExp exposures at this point
                if self.needMove(desOffset):
                    # slew telescope
                    sr.showMsg("Offset to %s position" % nodeName)
                    yield self.waitOffset(desOffset)
                    
                # format exposure command
                startNum = numExpTaken + 1
                expCmdStr = "%s startNum=%d totNumExp=%d" % (expCmdPrefix, startNum, totNumExp)
                
                # take exposure sequence
                sr.showMsg("Expose at %s position" % nodeName)
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
        tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(desOffset)
        self.currOffset = desOffset[:]
        yield self.sr.waitCmd(
            actor = "tcc",
            cmdStr = tccCmdStr,
        )
