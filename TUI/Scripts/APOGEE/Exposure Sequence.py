"""Script to take a sequence of APOGEE exposures at various dither positions.

History:
2011-05-04 ROwen
"""
import numpy
import Tkinter
import opscore.actor
import RO.Wdg
import TUI.Models
import TUI.Inst.APOGEE.StatusWdg
import TUI.Inst.APOGEE.ExposeWdg

# constants
InstName = "apogee"
MaxCycles = 99
HelpURL = None

class ScriptClass(object):  
    def __init__(self, sr):
        """Set up widgets
        """
        # if True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        self.sr = sr

        self.apogeeModel = TUI.Models.getModel("apogee")
    
        row=0
        
        # standard APOGEE status widget
        self.statusWdg = TUI.Inst.APOGEE.StatusWdg.StatusWdg(
            master = sr.master,
            helpURL = HelpURL,
        )
        self.statusWdg.grid(row=row, column=0, sticky="w")
        row += 1
    
        # separator
        Tkinter.Frame(sr.master,
            bg = "black",
        ).grid(row=row, column=0, pady=2, sticky="ew")
        row += 1
        
        # standard APOGEE exposure widget
        self.exposeWdg = TUI.Inst.APOGEE.ExposeWdg.ExposeWdg(
            master = sr.master,
            helpURL = HelpURL,
        )
        # tweak standard controls
        self.exposeWdg.showDither(False)
        self.exposeWdg.numReadsWdg.helpText = "# of reads at dither position"
        self.exposeWdg.grid(row=row, column=0, sticky="w")
        row += 1
        
        # add some controls to the exposure input widget
        
        # dither positions
        self.ditherPosWdg = RO.Wdg.StrEntry(
            master = self.exposeWdg,
            width = 15,
            helpText = "Space-separated dither positions (A, B or pixels)",
            helpURL = HelpURL,
        )
        self.exposeWdg.gridder.gridWdg("Dither Positions", self.ditherPosWdg)

        # number of cycles
        self.numCyclesWdg = RO.Wdg.IntEntry (
            master = self.exposeWdg,
            minValue = 1,
            maxValue = MaxCycles,
#            width = 10,
            helpText = "Number of cycles through the dither positions",
            helpURL = HelpURL,
        )
        self.exposeWdg.gridder.gridWdg("Cycles", self.numCyclesWdg)
        
        self.exposeWdg.gridder.allGridded()

        if sr.debug:
            # set useful debug defaults
            self.exposeWdg.numReadsWdg.set(5)
            self.ditherPosWdg.set("A B 0.5")
            self.numCyclesWdg.set(2)

    def run(self, sr):
        """Take a sequence of exposures
        """
        # parse dither positions to produce a list of: (position, isNamed)
        ditherPosIsNamedList = []
        ditherPositions = self.ditherPosWdg.getString().split()
        for posStr in ditherPositions:
            if posStr.lower() in ("a", "b"):
                ditherPosIsNamedList.append((posStr, True))
            else:
                try:
                    posFloat = float(posStr)
                except:
                    raise sr.ScriptError("Cannot parse %r as a float" % (posStr,))
                ditherPosIsNamedList.append((posFloat, False))
        if not ditherPosIsNamedList:
            raise sr.ScriptError("Must specify one or more dither positions")
        
        numCycles = self.numCyclesWdg.getNum()
        if not numCycles:
            raise sr.ScriptError("Must specify number of cycles")

        # save exposure command so that it will not change if the user messes
        # with the controls while the script is running
        exposureCmdStr = self.exposeWdg.getExposureCmd()

        numExpTaken = 0
        for cycle in range(numCycles):
            for ditherPos, isNamed in ditherPosIsNamedList:
                if isNamed:
                    cmdStr = "dither namedpos=%s" % (ditherPos,)
                else:
                    cmdStr = "dither pixelpos=%0.2f" % (ditherPos,)
                yield sr.waitCmd(
                    actor = "apogee",
                    cmdStr = cmdStr,
                )
                
                yield sr.waitCmd(
                    actor = "apogee",
                    cmdStr = exposureCmdStr,
                )
    def end(self, sr):
        pass
