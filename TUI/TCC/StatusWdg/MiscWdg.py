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
import TUI.Models.TCCModel
import TUI.Models.GuiderModel

# add instrument angles

_HelpPrefix = "Telescope/StatusWin.html#"

class MiscWdg (Tkinter.Frame):
    def __init__ (self, master=None, **kargs):
        """Displays miscellaneous information, such as current time and az/alt

        Inputs:
        - master        master Tk widget -- typically a frame or window
        """
        Tkinter.Frame.__init__(self, master=master, **kargs)
        self.tccModel = TUI.Models.TCCModel.Model()
        self.guiderModel = TUI.Models.GuiderModel.Model()
        
        gr = RO.Wdg.Gridder(self, sticky="e")

        # magic numbers
        AzAltRotPrec = 1    # number of digits past decimal point
        
        self.haWdg = RO.Wdg.DMSLabel(self,
            precision = 0,
            nFields = 3,
            cvtDegToHrs = 1,
            width = 8,
            helpText = "Hour angle of the object",
            helpURL = _HelpPrefix + "HA",
        )
        gr.gridWdg (
            label = "HA",
            dataWdg = self.haWdg,
            units = "hms",
        )
        
        self.lmstWdg = RO.Wdg.DMSLabel(self,
            precision = 0,
            nFields = 3,
            width = 8,
            justify="right",
            helpText = "Local mean sidereal time at APO",
            helpURL = _HelpPrefix + "LMST",
        )
        gr.gridWdg (
            label = "LMST",
            dataWdg = self.lmstWdg,
            units = "hms",
        )
        
        self.taiWdg = RO.Wdg.StrLabel(self,
            width=8,
            helpText = "International Atomic Time",
            helpURL = _HelpPrefix + "TAI",
        )
        gr.gridWdg (
            label = "TAI",
            dataWdg = self.taiWdg,
            units = "hms",
        )
        
        # start the second column of widgets
        gr.startNewCol(spacing=1)
        
        self.guideWdg = RO.Wdg.StrLabel(self,
            width = 13,
            anchor = "w",
            helpText = "State of guiding",
            helpURL = _HelpPrefix + "Guiding",
        )
        gr.gridWdg (
            label = "Guiding",
            dataWdg = self.guideWdg,
            colSpan = 4,
            units = False,
            sticky = "ew",
        )
        gr._nextCol -= 2 # allow overlap with widget to the right

        # airmass and zenith distance
        self.airmassWdg = RO.Wdg.FloatLabel(self,
            precision=3,
            width=5,
            helpURL = _HelpPrefix + "Airmass",
        )
        gr.gridWdg (
            label = "Airmass",
            dataWdg = self.airmassWdg,
            units = "",
        )
        
        self.zdWdg = RO.Wdg.FloatLabel(self,
            precision=AzAltRotPrec,
            helpText = "Zenith distance",
            helpURL = _HelpPrefix + "ZD",
            width=5,
        )
        gr.gridWdg (
            label = "ZD",
            dataWdg = self.zdWdg,
            units = RO.StringUtil.DegStr,
        )
        
        # start the third column of widgets
        gr.startNewCol(spacing=1)
        
        self.instNameWdg = RO.Wdg.StrLabel(self,
            width = 10,
            anchor = "w",
            helpText = "Current instrument",
            helpURL = _HelpPrefix + "Inst",
        )
        gr.gridWdg (
            label = "Inst",
            dataWdg = self.instNameWdg,
            colSpan = 3,
            units = False,
            sticky = "w",
        )
        self.tccModel.inst.addValueCallback(self.instNameWdg.set)
        
        self.secFocusWdg = RO.Wdg.FloatLabel(self,
            precision=0,
            width=5,
            helpText = "Secondary mirror focus",
            helpURL = _HelpPrefix + "Focus",
        )
        gr.gridWdg (
            label = "Focus",
            dataWdg = self.secFocusWdg,
            units = u"\N{MICRO SIGN}m",
        )
        self.tccModel.secFocus.addValueCallback(self.secFocusWdg.set)
        
        # all widgets are gridded
        gr.allGridded()
        
        # add callbacks
        self.tccModel.axePos.addCallback(self._axePosCallback)
        self.guiderModel.guideState.addCallback(self._updGuideStateSummary)
        
        # start clock updates       
        self._updateClock()
        
        # allow the last+1 column to grow to fill the available space
        self.columnconfigure(gr.getMaxNextCol(), weight=1)

    
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
    
    def _updGuideStateSummary(self, *args, **kargs):
        """Display guider state
        """
        state = self.guiderModel.guideState[0] or ""
        isCurrent = self.guiderModel.guideState.isCurrent
        self.guideWdg.set(state.title(), isCurrent = isCurrent)


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
