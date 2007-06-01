import math
import time
import RO.Wdg
import RO.Astro.Tm
import Tkinter
import TUI.TCC.TelConst
import TUI.Inst.ExposeModel as ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
import TUI.Inst.SPIcam.SPIcamModel

_HelpURL = "Scripts/BuiltInScripts/SPIcamFlats.html"
MinExpTime = 1.0
MaxExpTime = 150.0

class ScriptClass(object):
    """Take a series of SPIcam twilight or morning flats
    """
    def __init__(self, sr):
        """Display exposure status and a few user input widgets.
        """
        # if True, run in debug-only mode (which doesn't DO anything, it just pretends)
        sr.debug = False
        self.spicamModel = TUI.Inst.SPIcam.SPIcamModel.getModel()

        expStatusWdg = ExposeStatusWdg(
            master = sr.master,
            instName = "SPIcam",
        )
        expStatusWdg.grid(row=0, column=0, sticky="w")
        
        wdgFrame = Tkinter.Frame(sr.master)
     
        gr = RO.Wdg.Gridder(wdgFrame)
        
        self.expModel = ExposeModel.getModel("SPIcam")

        timeUnitsVar = Tkinter.StringVar()
        self.filterWdg = RO.Wdg.OptionMenu(
            master = wdgFrame,
            items = [],
            helpText = "filter",
            helpURL = _HelpURL,
            defMenu = "Current",
            autoIsCurrent = True,
        )
        gr.gridWdg("Filter", self.filterWdg, sticky="w", colSpan=3)
    
        timeUnitsVar = Tkinter.StringVar()
        self.expTimeWdg = RO.Wdg.DMSEntry (
            master = wdgFrame,
            minValue = self.expModel.instInfo.minExpTime,
            maxValue = self.expModel.instInfo.maxExpTime,
            isRelative = True,
            isHours = True,
            unitsVar = timeUnitsVar,
            width = 10,
            helpText = "Exposure time",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Time", self.expTimeWdg, timeUnitsVar)
        
        self.numExpWdg = RO.Wdg.IntEntry(
            master = wdgFrame,
            defValue = 1,
            minValue = 1,
            maxValue = 999,
            helpText = "Number of exposures in the sequence",
            helpURL = _HelpURL,
        )
        gr.gridWdg("#Exp", self.numExpWdg)
        
        wdgFrame.grid(row=1, column=0, sticky="w")

        self.spicamModel.filterNames.addCallback(self.filterWdg.setItems)
        self.spicamModel.filterName.addIndexedCallback(self.filterWdg.setDefault, 0)
        
    def run(self, sr):
        """Take a series of SPIcam flats"""

        # record user inputs
        filtName = self.filterWdg.getString()
        expTime = self.expTimeWdg.getNum()
        numExp = self.numExpWdg.getNum()
        expName = "flat_%s" % (filtName.lower().replace(" ", "_"),)
        print "expName=", expName

        if not filtName:
            raise sr.ScriptError("Specify filter")
        if expTime <= 0:
            raise sr.ScriptError("Specify exposure time")
        if numExp <= 0:
            raise sr.ScriptError("Specify number of exposures")
            
        # morning or evening?
        utcHours = time.gmtime().tm_hour
        locHours = utcHours + (TUI.TCC.TelConst.Longitude / 15.0)
        isMorning = locHours < 12.0
        
        # if filter is different, set it
        if not self.filterWdg.isDefault():
            desFiltNum = self.filterWdg.getIndex() + 1
            cmdStr = "filt %d" % (desFiltNum,)
            yield sr.waitCmd(
                actor = self.spicamModel.actor,
                cmdStr = cmdStr,
            )
        
        for expNum in range(numExp):
            if expNum > 0:
                # compute next exposure time
                if isMorning:
                    expTime = self.nextMorningExpTime(expTime)
                else:
                    expTime = self.nextTwilightExpTime(expTime)
                self.expTimeWdg.set(expTime)
            
            cmdStr = self.expModel.formatExpCmd(
                expType = "flat",
                expTime = expTime,
                fileName = expName,
                numExp = 1,
                startNum = expNum + 1,
                totNum = numExp,
            )
    
            yield sr.waitCmd(
                actor = "spicamExpose",
                cmdStr = cmdStr,
                abortCmdStr = "abort",
            )
    
    def nextTwilightExpTime(self, prevExpTime):
        temp = math.exp(-1.0 * prevExpTime / 288.0) + math.exp((prevExpTime + 45.0) / -288.0) - 1.0
        if temp <= 0:
            return MaxExpTime
        desExpTime = -288.0 * (math.log(temp)) - (prevExpTime + 45.0)
        return min(MaxExpTime, desExpTime)
    
    def nextMorningExpTime(self, prevExpTime):
        temp = math.exp(prevExpTime / 288.0) + math.exp((prevExpTime + 45.0) / 288.0) - 1.0
        desExpTime = 288.0 * (math.log(temp)) - (prevExpTime + 45.0)
        return max(MinExpTime, desExpTime)
