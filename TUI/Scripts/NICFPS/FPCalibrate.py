#!/usr/bin/env python
"""Calibrate the NICFPS Fabrey-Perot by taking data
over a range of X, Y and Z positions as specified in a file.

The file format is:
- Zero or more lines of X Y Z position data, in steps
  - values may be separated with any whitespace, but not commas
  - values must be integers
  - leading and trailing whitespace are ignored.
- Blank lines are ignored.
- Comments: lines whose first non-whitespace character is # are ignored.

The whole file is parsed before measurement begins;
any errors are reported and must be corrected.

History:
2004-12-16 ROwen
2005-01-18 ROwen    Bug fix: missing = in fp set position command.
2006-04-20 ROwen    Changed to a class.
2006-04-27 ROwen    Bug fix: long paths failed (I asked for the path the wrong way).
                    Modified to use RO.Wdg.FileWdg (simpler than RO.Prefs...).
2006-12-28 ROwen    Modified to abort the exposure if the script is aborted.
"""
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.NICFPS.NICFPSModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
HelpURL = "Scripts/BuiltInScripts/NICFPSFPCalibrate.html"

class ScriptClass(object):  
    def __init__(self, sr):
        """Create widgets.
        """
        # if True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        
        self.file = None        
        
        self.nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()
        self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
        self.tccModel = TUI.TCC.TCCModel.getModel()
    
        row=0
        
        # standard exposure status widget
        expStatusWdg = ExposeStatusWdg(sr.master, InstName)
        expStatusWdg.grid(row=row, column=0, sticky="news")
        row += 1
    
        # standard exposure input widget
        self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
        self.expWdg.numExpWdg.helpText = "# of exposures at each spacing"
        self.expWdg.grid(row=row, column=0, sticky="news")
        row += 1
        
        gr = self.expWdg.gridder
            
        # add file widget
        self.fileWdg = RO.Wdg.FileWdg(
            master = self.expWdg,
            helpText = "file of x y z etalon positions",
            helpURL = HelpURL,
        )
        gr.gridWdg("Data File", self.fileWdg, colSpan=3)
        
        if sr.debug:
            self.expWdg.timeWdg.set(3)
            self.expWdg.fileNameWdg.set("debugtest")
        
    def run(self, sr):
        """Take a calibration sequence.
        """
        # get current NICFPS focal plane geometry from the TCC
        # but first make sure the current instrument
        # is actually NICFPS
        if not sr.debug:
            currInstName = sr.getKeyVar(self.tccModel.instName)
            if not currInstName.lower().startswith(InstName.lower()):
                raise sr.ScriptError("%s is not the current instrument!" % InstName)
        
        # get exposure data and verify we have enough info to proceed
        numExp = self.expWdg.numExpWdg.getNum()
        expCmdPrefix = self.expWdg.getString()
        if not expCmdPrefix:
            return
    
        # get data file and parse it
        fileName = self.fileWdg.getPath()
        if not fileName:
            raise sr.ScriptError("specify a calibration data file")
    
        self.file = file(fileName, 'rU')
        if not self.file:
            raise sr.ScriptError("could not open %r" % fileName)
        
        if sr.debug:
            print "Reading file %r" % (fileName,)
        
        # read the file in advance, so we know how many lines of data there are
        xyzList = []
        for rawLine in self.file:
            if sr.debug:
                print "Read:", rawLine,
            line = rawLine.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            try:
                x, y, z = [int(val) for val in line.split(None, 3)]
            except StandardError:
                raise sr.ScriptError("could not parse %r" % rawLine)
            xyzList.append((x, y, z))
        
        self.file.close()
        self.file = None
        
        if sr.debug:
            print "xyzList =", xyzList
        
        numPositions = len(xyzList)
            
        totNumExp = numExp * numPositions
    
        for seqInd in range(numPositions):
            xyzPos = xyzList[seqInd]
            
            # Set etalon position one axis at a time
            sr.showMsg("Step %s of %s: set etalon x,y,z = %s " % (seqInd+1, numPositions, xyzPos))
            for axis, pos in zip(("x", "y", "z"), xyzPos):
                yield sr.waitCmd(
                    actor = self.nicfpsModel.actor,
                    cmdStr = "fp set%s=%d" % (axis, pos),
                )
    
            # compute # of exposures & format expose command
            startNum = seqInd * numExp
            expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNumExp)
            
            # take exposure sequence
            sr.showMsg("Step %s of %s: expose at etalon x,y,z = %s" % (seqInd+1, numPositions, xyzPos))
            yield sr.waitCmd(
                actor = self.expModel.actor,
                cmdStr = expCmdStr,
                abortCmdStr = "abort",
            )
    
    def end(self, sr):
        if self.file:
            self.file.close()
