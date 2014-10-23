#!/usr/bin/env python
"""Guide status widget

History:
2011-06-13 ROwen    Extracted from GuideWdg and expanded to include CCD temperature.
2011-07-12 ROwen    Show guide and exposure state in color to indicate severity.
                    The only "normal" guide state is "on" because all science uses guiding.
2011-11-08 ROwen    Show error states in uppercase to make them more visible.
                    Set state label severity = state severity to make problems more visible.
                    Bug fix: exposure state was always displayed in normal color.
2012-06-04 ROwen    Play sound cues (this should have been done all along).
"""
import Tkinter

import RO.Alg
import RO.CanvasUtil
import RO.Constants
import RO.DS9
import RO.MathUtil
import RO.OS
import RO.Prefs
import RO.StringUtil
import RO.Wdg

import TUI.Base.Wdg
import TUI.Models
import TUI.PlaySound


class GuideStateWdg(Tkinter.Frame):
    def __init__(self,
        master,
        helpURL = None,
    **kargs):
        Tkinter.Frame.__init__(self, master, **kargs)
        
        self.gcameraModel = TUI.Models.getModel("gcamera")
        self.guiderModel = TUI.Models.getModel("guider")
        self.prevGuideSoundFunc = None

        gr = RO.Wdg.Gridder(self, sticky="w")
        
        line1Frame = Tkinter.Frame(self)
        self.guideStateWdg = RO.Wdg.StrLabel(
            master = line1Frame,
#            formatFunc = str.capitalize,
            anchor = "w",
            helpText = "Current state of guiding",
            helpURL = helpURL,
        )
        self.guideStateWdg.pack(side="left")
        
        RO.Wdg.StrLabel(master = line1Frame, text=" ").pack(side="left")
        
        self.simInfoWdg = RO.Wdg.StrLabel(
            master = line1Frame,
            helpText = "Simulation info (if simulation mode)",
            helpURL = helpURL,
        )
        self.simInfoWdg.pack(side="left")
        self.guideStateLabel = RO.Wdg.StrLabel(master = self, text = "Guider")
        gr.gridWdg(self.guideStateLabel, line1Frame, colSpan=2)

        expStateFrame = Tkinter.Frame(self)
        self.expStateWdg = RO.Wdg.StrLabel(
            master = expStateFrame,
            helpText = "Status of current exposure",
            helpURL = helpURL,
            anchor="w",
            width = 11
        )
        self.expStateWdg.grid(row=0, column=0)

        self.expTimer = RO.Wdg.TimeBar(
            master = expStateFrame,
            valueFormat = "%3.1f sec",
            isHorizontal = True,
            autoStop = True,
            helpText = "Status of current exposure",
            helpURL = helpURL,
        )
        self.expTimer.grid(row=0, column=1, sticky="ew")
        expStateFrame.grid_columnconfigure(1, weight=1)
        
        self.expStateLabel = RO.Wdg.StrLabel(master = self, text = "Exposure")
        gr.gridWdg(self.expStateLabel, expStateFrame, sticky="ew")
        self.expTimer.grid_remove()
        
        gr.startNewCol()
        
        self.ccdTempWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 1,
            helpText = "CCD temperature",
            helpURL = helpURL,
        )
        gr.gridWdg("CCD Temp", self.ccdTempWdg, "C", sticky="e")
        
        self.coolerLoadWdg = RO.Wdg.FloatLabel(
            master = self,
            precision = 0,
            helpText = "Load on the CCD cooler",
            helpURL = helpURL,
        )
        gr.gridWdg("Cooler Load", self.coolerLoadWdg, "%", sticky="e")
            
        self.columnconfigure(1, weight=1)
        
        # keyword variable bindings
        self.gcameraModel.cooler.addCallback(self._coolerCallback)
        self.gcameraModel.exposureState.addCallback(self._exposureStateCallback)
        self.gcameraModel.simulating.addCallback(self._simulatingCallback)
        self.guiderModel.guideState.addCallback(self._guideStateCallback)
    
    def _coolerCallback(self, keyVar):
        """cooler callback (gcamera keyword)

        Float(name="setpoint", help="CCD temperature setpoint", units="degC"),
        Float(name="ccdTemp", help="CCD temperature reported by the camera", units="degC"),
        Float(name="heatsinkTemp", help="Heatsink temperature reported by the camera", units="degC"),
        Float(name="coolerLoad", help="Load on the cooler", units="percent"),
        Int(name="fanStatus", help="Fan status. Always 0 with this camera"),
        Enum('Off', 'RampingToSetPoint', 'Correcting', 'RampingToAmbient', 'AtAmbient', 'AtMax', 'AtMin', 'AtSetPoint', 'Invalid',
             name="coolerStatus",
             help="Cooler status. Correcting appears to be the normal state, All others should be considered bad. AtSetPoint does not appear to occur.")),
        """
        self.ccdTempWdg.set(keyVar[1], isCurrent=keyVar.isCurrent)
        self.coolerLoadWdg.set(keyVar[3], isCurrent=keyVar.isCurrent)

    def _exposureStateCallback(self, keyVar):
        """exposureState callback (gcamera keyword)
        
        values are:
        - Enum('idle','integrating','reading','done','aborted','failed'),
        - Float(help="remaining time for this state (0 if none, short or unknown)", units="sec"),
        - Float(help="total time for this state (0 if none, short or unknown)", units="sec")),
        """
        expStateStr, remTime, netTime = keyVar[:]
        if expStateStr == None:
            expStateStr = "?"
        lowState = expStateStr.lower()
        if lowState in ("?", "aborted"):
            severity = RO.Constants.sevWarning
        elif lowState == "failed":
            expStateStr = expStateStr.upper()
            severity = RO.Constants.sevError
        else:
            severity = RO.Constants.sevNormal
        remTime = remTime or 0.0 # change None to 0.0
        netTime = netTime or 0.0 # change None to 0.0

        self.expStateLabel.setSeverity(severity)
        self.expStateWdg.set(expStateStr, isCurrent=keyVar.isCurrent, severity = severity)
        
        if not (keyVar.isGenuine and keyVar.isCurrent):
            # data is cached or not current; don't mess with the countdown timer
            return
        
        if netTime > 0:
            # print "starting a timer; remTime = %r, netTime = %r" % (remTime, netTime)
            # handle a countdown timer
            # it should be stationary if expStateStr = paused,
            # else it should count down
            if lowState == "integrating":
                # count up exposure
                self.expTimer.start(
                    value = netTime - remTime,
                    newMax = netTime,
                    countUp = True,
                )
            else:
                # count down anything else
                self.expTimer.start(
                    value = remTime,
                    newMax = netTime,
                    countUp = False,
                )
            self.expTimer.grid()
        else:
            # hide countdown timer
            self.expTimer.grid_remove()
            self.expTimer.clear()

    def _guideStateCallback(self, keyVar):
        """Guide state callback

        Key("guideState", 
            Enum("off", "starting", "on", "stopping", "failed", help="state of guider"),
        ),
        """
        guideState = keyVar[0]
        
        # guide summary state is for playing sounds; one of on/off/failed/None
        guideSoundFunc = {
            "off": TUI.PlaySound.guidingEnds,
            "starting": TUI.PlaySound.guidingBegins,
            "on": TUI.PlaySound.guidingBegins,
            "stopping": TUI.PlaySound.guidingEnds,
            "failed": TUI.PlaySound.guidingFailed,
        }.get(guideState, None)
        doPlaySound = guideSoundFunc is not None \
            and self.prevGuideSoundFunc is not None \
            and self.prevGuideSoundFunc != guideSoundFunc
        self.prevGuideSoundFunc = guideSoundFunc
        if doPlaySound:
            guideSoundFunc()
        
        if guideState == None:
            guideState = "?"
        gsLower = guideState.lower()
        if gsLower == "on":
            severity = RO.Constants.sevNormal
        elif gsLower == "failed":
            guideState = guideState.upper()
            severity = RO.Constants.sevError
        else:
            severity = RO.Constants.sevWarning
        self.guideStateLabel.setSeverity(severity)
        self.guideStateWdg.set(guideState, isCurrent=keyVar.isCurrent, severity=severity)

    def _simulatingCallback(self, keyVar):
        """Simulating callback (gcamera keyword)
        """
        isSim, simDir, seqNum = keyVar[:]
        
        severity = RO.Constants.sevNormal
        if isSim:
            simStr = "Simulation: # %d from %s" % (seqNum, simDir)
            severity = RO.Constants.sevWarning
        elif isSim == None:
            simStr = "?"
        else:
            simStr = ""
        self.simInfoWdg.set(simStr, isCurrent = keyVar.isCurrent, severity = severity)


if __name__ == "__main__":
    import GuideTest
    #import gc
    #gc.set_debug(gc.DEBUG_SAVEALL) # or gc.DEBUG_LEAK to print lots of messages

    root = GuideTest.tuiModel.tkRoot

    testFrame = GuideStateWdg(root)
    testFrame.pack(expand="yes", fill="both")
    testFrame.wait_visibility() # must be visible to download images
    
    GuideTest.start()

    GuideTest.tuiModel.reactor.run()
