"""Script to nod between two fixed points in pattern ABBA.

History:
2008-04-23 ROwen
2008-07-24 ROwen    Fixed PR 852: end did not always restore the original boresight.
"""
import numpy
import Tkinter
import RO.Wdg
import RO.PhysConst
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.ExposeStatusWdg
import TUI.Inst.ExposeInputWdg

# constants
InstName = "TSpec"
# Offset from A to B in x, y pixels
# (85, 1) is from Matt Nelson 2008-04
ABOffsetPix = (85, 1)
MaxCycles = 9999
 # Instrument scale in unbinned pixels/degree on the sky
# as measured by APO 2008-03-21 but averaged x and y
InstScale = (-14352, 14342)
HelpURL = "Scripts/BuiltInScripts/TSpecNod.html"

class ScriptClass(object):  
    def __init__(self, sr):
        """Set up widgets to set input exposure time,
        drift amount and drift speed.
        """
        # if True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        self.sr = sr

        self.begOffset = numpy.array((numpy.nan, numpy.nan))
        self.currOffset = self.begOffset[:]

        self.tccModel = TUI.TCC.TCCModel.getModel()
        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
    
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

        # number of cycles
        self.numCyclesWdg = RO.Wdg.IntEntry (
            master = self.expWdg,
            minValue = 1,
            maxValue = MaxCycles,
#            width = 10,
            helpText = "Number of ABBA cycles",
            helpURL = HelpURL,
        )
        self.expWdg.gridder.gridWdg("Cycles", self.numCyclesWdg)

        
        self.expWdg.gridder.allGridded()

        if sr.debug:
            # set useful debug defaults
            self.expWdg.timeWdg.set("1.0")
            self.expWdg.numExpWdg.set(2)
            self.expWdg.fileNameWdg.set("debug")
            self.numCyclesWdg.set(2)

    def end(self, sr):
        """If telescope offset, restore original position.
        """
        # restore original boresight position, if changed
        if self.needMove(self.begOffset):
            tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begOffset)
            #print "sending tcc command %r" % tccCmdStr
            sr.startCmd(
                actor = "tcc",
                cmdStr = tccCmdStr,
            )

    def needMove(self, desOffset):
        """Return True if telescope not at desired offset"""
        if numpy.any(numpy.isnan(self.currOffset)):
            return False
        return not numpy.allclose(self.currOffset, desOffset)         

    def run(self, sr):
        """Take one or more exposures while moving the object
        in the +X direction along the slit.
        """
        # make sure the current instrument matches the desired instrument
        if not sr.debug:
            currInst = sr.getKeyVar(self.tccModel.instName)
            if InstName.lower() != currInst.lower():
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
            
        numCycles = self.numCyclesWdg.getNum()
        if not numCycles:
            raise sr.ScriptError("Must specify number of cycles")
            
        # exposure command without startNum and totNumExp
        # get it now so that it will not change if the user messes
        # with the controls while the script is running
        numExpPerNode = self.expWdg.numExpWdg.getNumOrNone()
        if numExpPerNode == None:
            raise sr.ScriptError("must specify #Exp")

        nodeNames = ("A1", "B1", "B2", "A2")
        numNodes = len(nodeNames)
        totNumExp = numCycles * numNodes * numExpPerNode
        expCmdPrefix = self.expWdg.getString(totNum = totNumExp)
        if expCmdPrefix == None:
            raise sr.ScriptError("missing inputs")
        
        NodeOffsetDict = dict (
            A = numpy.zeros(2, dtype=float),
            B = numpy.array(ABOffsetPix, dtype=float) / numpy.array(InstScale, dtype=float)
        )
        
        numExpTaken = 0
        for cycle in range(numCycles):
            for nodeName in nodeNames:
                iterName = "Cycle %s of %s, Pos %s" % (cycle + 1, numCycles, nodeName)
                nodeOffset = NodeOffsetDict[nodeName[0]]                
                desOffset = self.begOffset + nodeOffset
                if self.needMove(desOffset):
                    sr.showMsg("%s: Offsetting" % (iterName,))
                    yield self.waitOffset(desOffset)
        
                # expose
                sr.showMsg("%s: Exposing" % (iterName,))
                startNum = numExpTaken + 1
                expCmdStr = "%s startNum=%s" % (expCmdPrefix, startNum)
                #print "sending %s command %r" % (InstName, expCmdStr)
                yield sr.waitCmd(
                    actor = self.expModel.actor,
                    cmdStr = expCmdStr,
                    abortCmdStr = "abort",
                )
                numExpTaken += numExpPerNode
    
    def waitOffset(self, desOffset):
        """Offset the telescope"""
        tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(desOffset)
        self.currOffset = desOffset[:]
        yield self.sr.waitCmd(
            actor = "tcc",
            cmdStr = tccCmdStr,
        )
