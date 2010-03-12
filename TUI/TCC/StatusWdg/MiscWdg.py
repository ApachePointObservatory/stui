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
"""
import time
import Tkinter
import RO.Astro.Tm
import RO.Astro.Sph
import RO.Constants
import RO.PhysConst
import RO.StringUtil
import RO.Wdg
import TUI.PlaySound
import TUI.TCC.TelConst
import TUI.Models

# add instrument angles

_HelpPrefix = "Telescope/StatusWin.html#"

class MiscWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """Displays miscellaneous information, such as current time and az/alt

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)
        self.tccModel = TUI.Models.getModel("tcc")
        self.plateDBModel = TUI.Models.getModel("platedb")
        
        gr = RO.Wdg.Gridder(self, sticky="e")

        self.haWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Hour angle of the object",
            helpURL = _HelpPrefix + "HA",
        )
        gr.gridWdg("HA", self.haWdg, "hms")
        
        self.designHAWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Hour angle the plate was designed for",
            helpURL = _HelpPrefix + "DesignHA",
        )
        gr.gridWdg("Design HA", self.designHAWdg, "hms")
        
        self.deltaHAWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Design - current hour angle",
            helpURL = _HelpPrefix + "DeltaHA",
        )
        gr.gridWdg("Des-Curr HA", self.deltaHAWdg, "hms")
        
        self.taiWdg = RO.Wdg.StrLabel(
            master = self,
            width=8,
            helpText = "International Atomic Time",
            helpURL = _HelpPrefix + "TAI",
        )
        gr.gridWdg("TAI", self.taiWdg, "hms")

        # start the second column of widgets
        gr.startNewCol(spacing=1)
        
        gr._nextCol -= 2 # allow overlap with widget to the right

        # airmass and zenith distance
        self.airmassWdg = RO.Wdg.FloatLabel(
            master = self,
            precision=3,
            width = 5,
            helpText = "Airmass",
            helpURL = _HelpPrefix + "Airmass",
        )
        gr.gridWdg("Airmass", self.airmassWdg)
        
        self.zdWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 1,
            helpText = "Zenith distance (90 - altitude)",
            helpURL = _HelpPrefix + "ZD",
            width = 5,
        )
        gr.gridWdg("ZD", self.zdWdg, RO.StringUtil.DegStr)
        
        gr.setNextRow(gr.getNextRow() + 1)

        self.lmstWdg = RO.Wdg.DMSLabel(
            master = self,
            precision = 0,
            nFields = 3,
            width = 8,
            justify="right",
            helpText = "Local mean sidereal time at APO",
            helpURL = _HelpPrefix + "LMST",
        )
        gr.gridWdg("LMST", self.lmstWdg, "hms")
        
        # start the third column of widgets
        gr.startNewCol(spacing=1)
        
        self.instNameWdg = RO.Wdg.StrLabel(
            master = self,
            width = 10,
            helpText = "Current instrument",
            helpURL = _HelpPrefix + "Inst",
        )
        gr.gridWdg("Inst", self.instNameWdg, units=False)
        self.tccModel.inst.addValueCallback(self.instNameWdg.set)

        self.plateIDWdg = RO.Wdg.IntLabel(
            master = self,
            width = 8,
            helpText = "currently mounted plug plate",
            helpURL = _HelpPrefix + "PlateID",
        )
        gr.gridWdg("Plate", self.plateIDWdg)
        
        self.cartridgeIDWdg = RO.Wdg.IntLabel(
            master = self,
            width = 8,
            helpText = "currently mounted plug plate cartridge",
            helpURL = _HelpPrefix + "CartridgeID",
        )
        gr.gridWdg("Cartridge", self.cartridgeIDWdg)

        self.platePointingWdg = RO.Wdg.StrLabel(
            master = self,
            width = 8,
            helpText = "plug-plate pointing",
            helpURL = _HelpPrefix + "PlatePointing",
        )
        gr.gridWdg("Pointing", self.platePointingWdg)
        
        # all widgets are gridded
        gr.allGridded()
        
        # add callbacks
        self.tccModel.axePos.addCallback(self._axePosCallback)
        self.plateDBModel.pointingInfo.addCallback(self._pointingInfoCallback)
        
        # start clock updates       
        self._updateClock()
        
        # allow the last+1 column to grow to fill the available space
        self.columnconfigure(gr.getMaxNextCol(), weight=1)
    
    def _axePosCallback(self, keyVar):
        """Updates ha, dec, zenith distance and airmass
        axePos values are: (az, alt, rot)
        """
        isCurrent = keyVar.isCurrent
        az, alt = keyVar[0:2]

        if alt != None:
            airmass = RO.Astro.Sph.airmass(alt)
            zd = 90.0 - alt
        else:
            airmass = None
            zd = None
        
        # set zd, airmass widgets
        self.zdWdg.set(zd, isCurrent=isCurrent)
        self.airmassWdg.set(airmass, isCurrent=isCurrent)
        
        # set hour angle (set in degrees, display in hours)
        try:
            (ha, dec), atPole = RO.Astro.Sph.haDecFromAzAlt((az, alt), TUI.TCC.TelConst.Latitude)
            if atPole:
                ha = None
        except (TypeError, ValueError):
            ha = None
        self.haWdg.set(ha, isCurrent=isCurrent)
        
        designHA = self.plateDBModel.pointingInfo[5]
        if designHA != None:
            deltaHA = (ha - designHA)
        else:
            deltaHA = None
        self.deltaHAWdg.set(deltaHA, isCurrent=isCurrent and self.plateDBModel.pointingInfo.isCurrent)

    def _pointingInfoCallback(self, keyVar):
        isCurrent = keyVar.isCurrent
        self.plateIDWdg.set(keyVar[0], isCurrent=keyVar.isCurrent)
        self.cartridgeIDWdg.set(keyVar[1], isCurrent=keyVar.isCurrent)
        self.platePointingWdg.set(keyVar[2], isCurrent=keyVar.isCurrent)
        self.designHAWdg.set(keyVar[5], isCurrent=keyVar.isCurrent)

    def _updateClock(self):
        """Automatically update the time displays in this widget.
        Call once to get things going
        """
        # update utc
        currPythonSeconds = time.time()
        currTAITuple= time.gmtime(currPythonSeconds - RO.Astro.Tm.getUTCMinusTAI())
        self.taiWdg.set("%s:%02i:%02i" % currTAITuple[3:6])
    
        # update local (at APO) mean sidereal time, in degrees
        currUTCTuple= time.gmtime(currPythonSeconds)
        currUTCMJD = RO.Astro.Tm.mjdFromPyTuple(currUTCTuple)
        currLMST = RO.Astro.Tm.lmstFromUT1(currUTCMJD, TUI.TCC.TelConst.Longitude) * RO.PhysConst.HrsPerDeg
        self.lmstWdg.set(currLMST)
        
        # schedule the next event for the next integer second plus a bit
        msecToNextSec = int(1000 * time.time() % 1.0)
        self.after (msecToNextSec + 10, self._updateClock)


if __name__ == "__main__":
    import TestData

    tuiModel = TestData.tuiModel

    testFrame = MiscWdg(tuiModel.tkRoot)
    testFrame.pack()

    dataList = (
        "AxePos=-350.999, 45, NaN",
        "SecFocus=570",
        "GCFocus=-300",
        "Inst=DIS",
        "TCCStatus=TTT, NNN",
    )

    TestData.testDispatcher.dispatch(dataList)

    tuiModel.reactor.run()
