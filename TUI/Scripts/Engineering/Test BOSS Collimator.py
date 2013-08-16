import numpy
from RO.Constants import sevWarning, sevError
import RO.Wdg
import TUI.Models

MaxPosErr = 10

class ScriptClass(object):
    """Check spectrograph collimator motors by moving back and forth
    """
    def __init__(self, sr):
        """Construct a script to test collimator motors
        """
        self.bossModel = TUI.Models.getModel("boss")
        self.desOnBits  = 0x00 # I'd prefer 0x01 motor stopped, but it's not reliably on after a move!
        self.desOffBits = 0x52 # find edge | slew mode | limit switch
        self.logWdg = RO.Wdg.LogWdg(
            master = sr.master,
            width = 45,
            height = 35,
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
        self.posErrList = []
    
    def run(self, sr):
        """For each axis move the collimator motors back and forth and check for success
        """
        self.posErrList = []
        self.startPos = numpy.array(self.bossModel.motorPosition, dtype=int)
        self.desPos = self.startPos[:]
        self.logWdg.addMsg("Starting position: %s" % " ".join(str(val) for val in self.startPos))
        for spec in ("sp1", "sp2"):
            for mult in (1, -1):
                for a in (0, 1000):
                    for b in (0, 1000):
                        for c in (0, 1000):
                            yield self.waitMove(sr, spec=spec, a=a*mult, b=b*mult, c=c*mult)
    
    def waitMove(self, sr, spec, a, b, c):
        """Check motor status, move motors and check position
        """
        if a == b == c == 0:
            return
        self.logWdg.addMsg("Test spec=%s a=%s b=%s c=%s" % (spec, a, b, c))
        startInd = dict(sp1=0, sp2=3)[spec]
        self.desPos[startInd:startInd+3] += numpy.array((a, b, c), dtype=int)
            
        cmdStr = "moveColl spec=%s a=%s b=%s c=%s" % (spec, a, b, c)
        yield sr.waitCmd(actor="boss", cmdStr=cmdStr)
        
        motorStatus = [int(val) for val in self.bossModel.motorStatus]
        stateOK = [
            (state & self.desOffBits == 0) and (state & self.desOnBits  == self.desOnBits)
            for state in motorStatus
        ]
        if False in stateOK:
            motorStateStr = " ".join(("0x%x" % (val) for val in motorStatus))
            self.logWdg.addMsg("Bad motor state: %s" % motorStateStr, severity=sevWarning)
        
        currPos = numpy.array(self.bossModel.motorPosition, dtype=int)
        posErr = currPos - self.desPos
        self.posErrList.append(posErr)
        if numpy.any(numpy.abs(posErr) > MaxPosErr):
            self.logWdg.addMsg("Pos error > %s: %s" % (MaxPosErr, posErr), severity=sevWarning)
            
    def end(self, sr):
        """Finish up by printing position error statistics
        """
        posErrArr = numpy.array(self.posErrList, dtype=float)
        meanPosErr = numpy.mean(posErrArr, axis=0)
        stdDevPosErr = numpy.std(posErrArr, axis=0)
        maxPosErr = numpy.max(numpy.abs(posErrArr), axis=0)
        self.logWdg.addMsg("Mean pos err=%s" % " ".join("%0.1f" % (val,) for val in meanPosErr))
        self.logWdg.addMsg("StdDev pos err=%s" % " ".join("%0.1f" % (val,) for val in stdDevPosErr))
        self.logWdg.addMsg("Max pos err=%s" % " ".join("%0.1f" % (val,) for val in maxPosErr))
