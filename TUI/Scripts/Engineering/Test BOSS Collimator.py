import numpy
from RO.Constants import sevWarning, sevError
import RO.Wdg
import TUI.Models

MaxPosErr = 10

class SpecInfo(object):
    """Information about collimation motors for one spectrograph ("sp1" or "sp2")
    """
    SliceDict = dict(sp1=slice(0,3), sp2=slice(3,6))
    def __init__(self, spec, bossModel):
        """Construct a SliceInfo
        
        @param[in] spec: spectrograph name: one of "sp1" or "sp2"
        @param[in] bossModel: keyword model for boss actor
        
        The intended usage is:
        - construct a SliceDict for the desired spectrograph
        - call addPos to set initial values in posList and desPosList
        - for each test position:
          - call addDesPos
          - move the actuators
          - call addPos
        """
        self.spec = spec
        self.bossModel = bossModel
        try:
            self.slice = self.SliceDict[spec]
        except KeyError:
            raise RuntimeError("unrecognized spec=%r; must be one of %r" % (spec, self.SliceDict.keys()))
        self.posList = []
        self.desPosList = []
        self.posErrList = []
        self.statusList = []
    
    def addPos(self):
        """Add a position to posList
        
        Also update posErrList if desPosList exists, else initialise desPosList to the current position.
        """
        pos = numpy.array(self.bossModel.motorPosition[self.slice], dtype=int)
        self.posList.append(pos)
        if self.desPosList:
            currDesPos = self.desPosList[-1]
            posErr = pos - currDesPos
            self.posErrList.append(posErr)
        else:
            self.desPosList.append(numpy.copy(pos))
        return pos
    
    def addDesPos(self, a, b, c):
        """Add a new desired position based on a, b, c delta positions
        
        Return the new desPos
        """
        prevDesPos = self.desPosList[-1]
        desPos = prevDesPos + (a, b, c)
        self.desPosList.append(desPos)
        return desPos
    
    def addStatus(self):
        """Add current status to list from boss motorStatus keyword
        
        Return status
        """
        status = numpy.array(self.bossModel.motorStatus[self.slice], dtype=int)
        self.statusList.append(status)
        return status

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
            width = 35,
            height = 42,
        )
        self.logWdg.grid(row=0, column=0, sticky="news")
        self.specList = SpecInfo.SliceDict.keys()
        self.specInfoDict = dict()
        for spec in self.specList:
            self.specInfoDict[spec] = SpecInfo(spec=spec, bossModel=self.bossModel)
    
    def run(self, sr):
        """For each axis move the collimator motors back and forth and check for success
        """
        for spec, specInfo in self.specInfoDict.iteritems():
            startPos = specInfo.addPos()
            self.logWdg.addMsg("%s start position: %s" % (spec, " ".join(str(val) for val in startPos)))
            
            for mult in (1, -1):
                for a in (0, 1000):
                    for b in (0, 1000):
                        for c in (0, 1000):
                            yield self.waitMove(sr, spec=spec, a=a*mult, b=b*mult, c=c*mult)
            endPos = specInfo.posList[-1] # waitMove calls addPos after the move, so posList is current
            self.logWdg.addMsg("%s end position: %s" % (spec, " ".join(str(val) for val in endPos)))
            posErrArr = numpy.array(specInfo.posErrList, dtype=float)
            meanPosErr = numpy.mean(posErrArr, axis=0)
            stdDevPosErr = numpy.std(posErrArr, axis=0)
            maxPosErr = numpy.max(numpy.abs(posErrArr), axis=0)
            self.logWdg.addMsg("%s mean pos err=%s" % (spec, " ".join("%0.1f" % (val,) for val in meanPosErr)))
            self.logWdg.addMsg("%s std dev pos err=%s" % (spec, " ".join("%0.1f" % (val,) for val in stdDevPosErr)))
            self.logWdg.addMsg("%s max pos err=%s" % (spec, " ".join("%0.1f" % (val,) for val in maxPosErr)))
            self.logWdg.addMsg("")
    
    def waitMove(self, sr, spec, a, b, c):
        """Move motors and record desired position, motor status, actual position and position error
        """
        if a == b == c == 0:
            return
        self.logWdg.addMsg("%s a=%s b=%s c=%s" % (spec, a, b, c))
        specInfo = self.specInfoDict[spec]
        specInfo.addDesPos(a, b, c)
            
        cmdStr = "moveColl spec=%s a=%s b=%s c=%s" % (spec, a, b, c)
        yield sr.waitCmd(actor="boss", cmdStr=cmdStr)
        
        status = specInfo.addStatus()
        stateOK = numpy.logical_and(status & self.desOffBits == 0, status & self.desOnBits  == self.desOnBits)
        if not numpy.all(stateOK):
            motorStateStr = " ".join(("0x%x" % (val) for val in status))
            self.logWdg.addMsg("%s bad motor state: %s" % (spec, motorStateStr), severity=sevWarning)
        
        specInfo.addPos()
        posErr = specInfo.posErrList[-1]
        if numpy.any(numpy.abs(posErr) > MaxPosErr):
            self.logWdg.addMsg("%s pos error > %s: %s" % (spec, MaxPosErr, posErr), severity=sevWarning)
