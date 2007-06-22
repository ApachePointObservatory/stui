import math
import time
import RO.Wdg
import RO.Astro.Tm
import Tkinter
import TUI.TCC.TelConst
import TUI.Inst.ExposeModel as ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg
import TUI.Inst.SPIcam.SPIcamModel

InstName = "SPIcam"
_HelpURL = "Scripts/BuiltInScripts/SPIcamFlats.html"

class ScriptClass(object):
    """Take a series of SPIcam twilight or morning flats
    """
    def __init__(self, sr):
        """Display exposure status and a few user input widgets.
        """
        # if True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        self.spicamModel = TUI.Inst.SPIcam.SPIcamModel.getModel()
        self.expModel = ExposeModel.getModel(InstName)

        row = 0

        expStatusWdg = ExposeStatusWdg(
            master = sr.master,
            instName = InstName,
        )
        expStatusWdg.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
        self.expWdg.grid(row=row, column=0, columnspan=3, sticky="w")
        row += 1

        wdgFrame = Tkinter.Frame(sr.master)        
        gr = RO.Wdg.Gridder(wdgFrame, sticky="w")
        self.filterWdg = RO.Wdg.OptionMenu(
            master = self.expWdg,
            items = [],
            helpText = "filter",
            helpURL = _HelpURL,
            defMenu = "Current",
            autoIsCurrent = True,
        )
        self.expWdg.gridder.gridWdg("Filter", self.filterWdg, sticky="w", colSpan=3)

        self.spicamModel.filterNames.addCallback(self.filterWdg.setItems)
        self.spicamModel.filterName.addIndexedCallback(self.filterWdg.setDefault, 0)
        
    def run(self, sr):
        """Take a series of SPIcam flats"""

        # record user inputs
        filtName = self.filterWdg.getString()
        expTime = self.expWdg.timeWdg.getNum()
        numExp = self.expWdg.numExpWdg.getNum()
        fileName = self.expWdg.fileNameWdg.getString()
        comment = self.expWdg.commentWdg.getString()

        if not filtName:
            raise sr.ScriptError("Specify filter")
        if expTime <= 0:
            raise sr.ScriptError("Specify exposure time")
        if numExp <= 0:
            raise sr.ScriptError("Specify number of exposures")
        nTimeFields = self.expWdg.timeWdg.getString().count(":") + 1
        nTimeFields = max(1, min(3, nTimeFields))
        self.expWdg.timeWdg.defFormat = (nTimeFields, 1)
            
        # morning or evening?
        utcHours = time.gmtime().tm_hour
        locHours = utcHours + (TUI.TCC.TelConst.Longitude / 15.0)
        isMorning = locHours < 12.0
        
        # if filter is different, set it
        if not self.filterWdg.isDefault():
            desFiltNum = self.filterWdg.getIndex() + 1
            cmdStr = "filter %d" % (desFiltNum,)
            yield sr.waitCmd(
                actor = self.spicamModel.actor,
                cmdStr = cmdStr,
            )
        
        for expNum in range(numExp):
            # compute next exposure time
            if isMorning:
                expTime = self.nextMorningExpTime(expTime)
            else:
                expTime = self.nextTwilightExpTime(expTime)
            
            self.expWdg.timeWdg.set(expTime)
            
            cmdStr = self.expModel.formatExpCmd(
                expType = "flat",
                expTime = expTime,
                fileName = fileName,
                numExp = 1,
                comment = comment,
                startNum = expNum + 1,
                totNum = numExp,
            )
    
            yield sr.waitCmd(
                actor = "spicamExpose",
                cmdStr = cmdStr,
                abortCmdStr = "abort",
            )
    
    def nextTwilightExpTime(self, prevExpTime):
        """Compute next exposure time for a twilight flat
        (compensating for the darkening sky)
        
        This equation is from the original SPIcam scripts;
        it blows up around 180 seconds, so a ceiling is used.
        """
        maxExpTime = 160.0
        temp = math.exp(-1.0 * prevExpTime / 288.0) + math.exp((prevExpTime + 45.0) / -288.0) - 1.0
        if temp <= 0:
            return maxExpTime
        desExpTime = -288.0 * (math.log(temp)) - (prevExpTime + 45.0)
        return min(maxExpTime, desExpTime)
    
    def nextMorningExpTime(self, prevExpTime):
        """Compute next exposure time for a morning flat
        (compensating for the brightening sky)
        
        The equation is from the original SPIcam scripts.
        """
        temp = math.exp(prevExpTime / 288.0) + math.exp((prevExpTime + 45.0) / 288.0) - 1.0
        desExpTime = 288.0 * (math.log(temp)) - (prevExpTime + 45.0)
        return max(self.expModel.instInfo.minExpTime, desExpTime)
