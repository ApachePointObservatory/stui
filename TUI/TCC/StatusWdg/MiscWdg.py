#!/usr/bin/env python
"""Displays time, airmass, instrument name, focus...

History:
2003-03-26 ROwen    Modified to use the tcc model.
2003-03-31 ROwen    Switched from RO.Wdg.LabelledWdg to RO.Wdg.Gridder.
2003-04-24 ROwen    Modified to use Gridder startNewCol.
2003-06-09 Rowen    Removed dispatcher arg.
2003-06-12 ROwen    Added helpText entries.
2003-06-25 ROwen    Modified test case to handle message data as a dict
2003-10-29 ROwen    Modified to accommodate moved TelConst.
2003-12-03 ROwen    Added guide status, including sound cues.
2004-02-04 ROwen    Modified _HelpURL to match minor help reorg.
2004-08-26 ROwen    Made the instrument name field wider (8->10).
2004-09-23 ROwen    Modified to allow callNow as the default for keyVars.
2005-06-07 ROwen    Disabled guide state display (until I figure out how
                    to make it work with the new guide system).
2005-06-10 ROwen    Rewrote guide state display to work with new guide system.
2005-06-15 ROwen    Updated for guide model change guiding->guideState.
2005-08-02 ROwen    Modified for TUI.Sounds->TUI.PlaySound.
2008-02-01 ROwen    Modified GC Focus to get its value from the new gmech actor.
                    Improved guide state output to show camera (if state not Off or unknown).
2008-03-25 ROwen    Actually modified GC Focus to get its value from the new gmech actor
                    (somehow that change did not actually occur on 2008-02-01).
2009-03-31 ROwen    Updated for new TCC model.
2009-07-19 ROwen    Modified to use KeyVar.addValueCallback instead of addROWdg.
2010-01-12 ROwen    Modified to show TAI instead of UTC.
                    Updated for new GuiderModel.
2010-03-11 ROwen    Removed Focus and Guiding (moved to OffsetWdg).
                    Added Plate ID, Cartridge ID, Design HA and Curr-Des HA.
2010-03-12 ROwen    Changed to use Models.getModel.
2010-03-19 ROwen    Overhaul the way cartridge ID, etc. are shown: just use platedb for the design HA;
                    use the MCP and guider for the remaining information.
                    Simplified help URLs to all point to the same section.
2010-05-04 ROwen    Bug fix: traceback when hour angle unknown and designHA known.
2010-06-28 ROwen    Added parenthesis to clarify an expression.
2010-11-05 ROwen    Show TAI date as well as time.
2010-11-12 ROwen    Added MJD and combined Inst ID and Cartridge into one field.
2010-11-18 ROwen    Bug fix: SDSS MJD = int(TAI MJD + 0.3) not -0.3.
                    Bug fix: cartridge was empty if the numbers matched due to a typo.
2010-01-10 ROwen    Display instrumentNum=18 as cartridge 18 instead of Eng Cam (changed at APO
                    when cartridge 18 came on line). Once the new value for the Eng Cam is known
                    add it to InstNameDict.
2011-02-16 ROwen    Moved Focus, Scale and Guiding state here from OffsetWdg.
                    Made the display expand to the right of the displayed data.
2012-07-10 ROwen    Modified to user RO.TkUtil.Timer
2012-12-07 ROwen    Modified to use RO.Astro.Tm clock correction to show correct time
                    even if user's clock is keeping TAI or is drifting.
                    Bug fix: timing of next update was miscomputed.
2014-10-02 ROwen    Relabelled "MJD" to "SJD" to reduce confusion.
2015-11-03 ROwen    Replace "== None" with "is None" and "!= None" with "is not None" to modernize the code.
"""
import time
import Tkinter
import RO.Astro.Tm
import RO.Astro.Sph
import RO.Constants
import RO.PhysConst
import RO.StringUtil
from RO.TkUtil import Timer
import RO.Wdg
import TUI.PlaySound
import TUI.TCC.TelConst
import TUI.Models

# add instrument angles

_HelpURL = "Telescope/StatusWin.html#Misc"

class MiscWdg (Tkinter.Frame):
    InstNameDict = {0: "None"} # add a value for Eng Cam once known
    def __init__ (self, master=None, **kargs):
        """Displays miscellaneous information, such as current time and az/alt

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)
        self.tccModel = TUI.Models.getModel("tcc")
        self.guiderModel = TUI.Models.getModel("guider")
        self.mcpModel = TUI.Models.getModel("mcp")
        self.plateDBModel = TUI.Models.getModel("platedb")
        self._cartridgeInfo = [None]*3 # (cartID, plateID, pointing)
        self._clockTimer = Timer()
        
        gr = RO.Wdg.Gridder(self, sticky="e")

        self.haWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Hour angle of the object",
            helpURL = _HelpURL,
        )
        gr.gridWdg("HA", self.haWdg, "hms")
        
        self.designHAWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Hour angle the plate was designed for (from platedb)",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Design HA", self.designHAWdg, "hms")
        
        self.deltaHAWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Design - current hour angle",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Des-Curr HA", self.deltaHAWdg, "hms")
        
        self.taiWdg = RO.Wdg.StrLabel(
            master = self,
            width=19,
            helpText = "International Atomic Time",
            helpURL = _HelpURL,
        )
        gr.gridWdg("TAI", self.taiWdg, colSpan=2)

        # secondary focus
        self.secFocusWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 0,
            width = 5,
            helpText = "Secondary mirror focus",
            helpURL = _HelpURL,
        )
        gr.gridWdg (
            label = "Focus",
            dataWdg = self.secFocusWdg,
            units = "\N{MICRO SIGN}m",
        )
        self.tccModel.secFocus.addValueCallback(self.secFocusWdg.set)

        # start the second column of widgets
        gr.startNewCol(spacing=1)
        
        gr._nextCol -= 2 # allow overlap with widget to the right

        self.airmassWdg = RO.Wdg.FloatLabel(
            master = self,
            precision=3,
            width = 5,
            helpText = "Airmass",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Airmass", self.airmassWdg)
        
        self.zdWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 1,
            helpText = "Zenith distance (90 - altitude)",
            helpURL = _HelpURL,
            width = 5,
        )
        gr.gridWdg("ZD", self.zdWdg, RO.StringUtil.DegStr)

        self.lmstWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            width = 8,
            justify="right",
            helpText = "Local mean sidereal time at APO",
            helpURL = _HelpURL,
        )
        gr.gridWdg("LMST", self.lmstWdg, "hms")
        
        self.sjdWdg = RO.Wdg.IntLabel(
            master = self,
            helpText = "SDSS MJD (rolls over at TAI MJD-0.3)",
            helpURL = _HelpURL,
            width = 6,
        )
        gr.gridWdg("SJD", self.sjdWdg, "days")

        self.scaleWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 1,
            width = 8,
            helpText = "scale ((plate/nominal - 1) * 1e6); larger is higher resolution",
            helpURL = _HelpURL,
        )
        gr.gridWdg (
            label = "Scale",
            dataWdg = self.scaleWdg,
            units = "1e6",
        )
        self.tccModel.scaleFac.addCallback(self._scaleFacCallback)
        
        # start the third column of widgets
        gr.startNewCol(spacing=1)
        
        self.instNameWdg = RO.Wdg.StrLabel(
            master = self,
            width = 10,
            helpText = "Current instrument (from the TCC)",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Inst", self.instNameWdg, units=False)
        self.tccModel.inst.addValueCallback(self.instNameWdg.set)
        
        self.cartridgeIDWdg = RO.Wdg.StrLabel(
            master = self,
            width = 13,
            helpText = "currently mounted cartridge (from MCP and guider)",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Cartridge", self.cartridgeIDWdg)

        self.plateIDWdg = RO.Wdg.IntLabel(
            master = self,
            width = 8,
            helpText = "currently mounted plug plate (from the guider)",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Plate", self.plateIDWdg)

        self.platePointingWdg = RO.Wdg.StrLabel(
            master = self,
            width = 8,
            helpText = "plug-plate pointing (from the guider)",
            helpURL = _HelpURL,
        )
        gr.gridWdg("Pointing", self.platePointingWdg)

        # state of guiding
        self.guideWdg = RO.Wdg.StrLabel(
            master = self,
            anchor = "e",
            helpText = "State of guiding",
            helpURL = _HelpURL,
        )
        gr.gridWdg (
            label = "Guiding",
            dataWdg = self.guideWdg,
            units = False,
            sticky = "ew",
        )
        
        # all widgets are gridded
        gr.allGridded()
        
        # add callbacks
        self.tccModel.axePos.addCallback(self._setAxePos)
        self.guiderModel.cartridgeLoaded.addCallback(self.setCartridgeInfo)
        self.mcpModel.instrumentNum.addCallback(self.setCartridgeInfo)
        self.plateDBModel.pointingInfo.addCallback(self._setAxePos)
        self.guiderModel.guideState.addCallback(self._guideStateCallback)
        
        # start clock updates       
        self._updateClock()
        
        # allow the last+1 column to grow to fill the available space
        self.columnconfigure(gr.getMaxNextCol(), weight=1)

    def _guideStateCallback(self, keyVar):
        """Display guider state
        """
        state = self.guiderModel.guideState[0] or ""
        self.guideWdg.set(state.title(), isCurrent = keyVar.isCurrent)

    def _scaleFacCallback(self, keyVar):
        val = keyVar[0]
        if val is not None:
            val = (val - 1) * 1.0e6
        self.scaleWdg.set(val, keyVar.isCurrent)
    
    def _setAxePos(self, keyVar=None):
        """Updates ha, dec, zenith distance, airmass and plate design ha
        """
        # axePos values are: (az, alt, rot)
        axePosIsCurrent = self.tccModel.axePos.isCurrent
        az, alt = self.tccModel.axePos[0:2]

        if alt is not None:
            airmass = RO.Astro.Sph.airmass(alt)
            zd = 90.0 - alt
        else:
            airmass = None
            zd = None
        
        # set zd, airmass widgets
        self.zdWdg.set(zd, isCurrent=axePosIsCurrent)
        self.airmassWdg.set(airmass, isCurrent=axePosIsCurrent)
        
        # set hour angle (set in degrees, display in hours)
        try:
            (ha, dec), atPole = RO.Astro.Sph.haDecFromAzAlt((az, alt), TUI.TCC.TelConst.Latitude)
            if atPole:
                ha = None
        except (TypeError, ValueError):
            ha = None
        self.haWdg.set(ha, isCurrent=axePosIsCurrent)

        designHA = self._getDesignHA()
        plateInfoIsCurrent = self.plateDBModel.pointingInfo.isCurrent
        self.designHAWdg.set(designHA, plateInfoIsCurrent)
        
        designHA = self._getDesignHA()
        if None in (ha, designHA):
            deltaHA = None
        else:    
            deltaHA = (ha - designHA)
        self.deltaHAWdg.set(deltaHA, isCurrent=axePosIsCurrent and plateInfoIsCurrent)

    def setCartridgeInfo(self, keyVar=None):
        """Set cartridge info based on guider and MCP.
        """
        severity = RO.Constants.sevNormal
        mcpInstNum = self.mcpModel.instrumentNum[0]
        isCurrent = self.mcpModel.instrumentNum.isCurrent
        mcpInstName = self.InstNameDict.get(mcpInstNum)
        cartridgeStr = None
        if mcpInstName:
            # known instrument that is not a cartridge;
            # ignore self.guiderModel.cartridgeLoaded and show no cartridge info
            self._cartridgeInfo = [None]*3
            cartridgeStr = mcpInstName
        else:
            # MCP thinks a cartridge is mounted or does not know what is mounted;
            # base the output on a combination of mcp instrumentNum and guider cartridgeLoaded
            isCurrent = isCurrent and self.guiderModel.cartridgeLoaded.isCurrent
            self._cartridgeInfo = self.guiderModel.cartridgeLoaded[0:3]
            guiderInstNum = self._cartridgeInfo[0]

            # avoid dictionary lookup since -1 -> Invalid which is None but does not look up properly
            if mcpInstNum in (None, "?"):
                mcpInstName = "?"
            else:
                mcpInstName = str(mcpInstNum)

            if guiderInstNum == mcpInstNum:
                # MCP and guider agree on the loaded cartridge; output the value
                cartridgeStr = mcpInstName
            else:
                if guiderInstNum is None:
                    guiderInstName = "?"
                else:
                    guiderInstName = str(guiderInstNum)
                cartridgeStr = "%s mcp %s gdr" % (mcpInstName, guiderInstName)
                severity = RO.Constants.sevError

        self.cartridgeIDWdg.set(cartridgeStr, isCurrent=isCurrent, severity=severity)
        self.plateIDWdg.set(self._cartridgeInfo[1], isCurrent=isCurrent, severity=severity)
        self.platePointingWdg.set(self._cartridgeInfo[2], isCurrent=isCurrent, severity=severity)
        self._setAxePos()

    def _getDesignHA(self):
        for ptgInd, cartInd in ((0, 1), (1, 0), (2, 2)):
            if self.plateDBModel.pointingInfo[ptgInd] != self._cartridgeInfo[cartInd]:
                return None
        return self.plateDBModel.pointingInfo[5]

    def _updateClock(self):
        """Automatically update the time displays in this widget.
        Call once to get things going
        """
        # update utc
        currPythonSeconds = RO.Astro.Tm.getCurrPySec()
        currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
        self.taiWdg.set(time.strftime("%Y-%m-%d %H:%M:%S", currTAITuple))
    
        # update local (at APO) mean sidereal time, in degrees
        currUTCTuple= time.gmtime(currPythonSeconds)
        currUTCMJD = RO.Astro.Tm.mjdFromPyTuple(currUTCTuple)
        currLMST = RO.Astro.Tm.lmstFromUT1(currUTCMJD, TUI.TCC.TelConst.Longitude) * RO.PhysConst.HrsPerDeg
        self.lmstWdg.set(currLMST)
        
        currTAIDays = RO.Astro.Tm.taiFromPySec(currPythonSeconds)
        currSDSSMJD = int(currTAIDays + 0.3) # assumes int truncates
        self.sjdWdg.set(currSDSSMJD)
        
        # schedule the next event for the next integer second plus a bit
        clockDelay = 1.01 - (currPythonSeconds % 1.0)
        self._clockTimer.start(clockDelay, self._updateClock)


if __name__ == "__main__":
    from . import TestData

    tuiModel = TestData.tuiModel

    testFrame = MiscWdg(tuiModel.tkRoot)
    testFrame.pack()

    TestData.init()

    tuiModel.reactor.run()
