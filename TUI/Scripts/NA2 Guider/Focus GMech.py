#!/usr/bin/env python
"""Take a series of NA2 guider (gcam) exposures
at different gmech focus positions to estimate best focus.
Does not touch the secondary mirror's focus

History:
2008-02-01 ROwen
2008-02-12 ROwen    Fix PR 735: commanded the secondary mirror instead of gmech for two moves:
                    - setCurrFocus: focus backlash compensation
                    - end: restore original focus
2008-02-13 ROwen    Disabled windowing due to PRs 739 and 740.
2008-03-17 ROwen    Re-enabled windowing now that PR 739 and 740 are fixed.
"""
import TUI.Base.BaseFocusScript
import RO.Constants
import TUI.Guide.GMechModel
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
OffsetGuiderFocusScript = TUI.Base.BaseFocusScript.OffsetGuiderFocusScript

MicronStr = TUI.Base.BaseFocusScript.MicronStr

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?
HelpURL = "Scripts/BuiltInScripts/InstFocus.html"

class ScriptClass(OffsetGuiderFocusScript):
    DefFocusRange = 6000 # default focus range around current focus
    MinFocusIncr = 1500 # minimum focus increment, in um
    def __init__(self, sr):
        """The setup script; run once when the script runner window is created.
        """
        self.gmechModel = TUI.Guide.GMechModel.getModel()
        OffsetGuiderFocusScript.__init__(self,
            sr = sr,
            gcamActor = "gcam",
            instPos = "NA2",
            imageViewerTLName = "Guide.NA2 Guider",
            defBinFactor = 3,
            maxFindAmpl = 30000,
            doWindow = True,
            helpURL = HelpURL,
            debug = Debug,
        )
    
    def end(self, sr):
        """Run when script exits (normally or due to error)
        """
        self.enableCmdBtns(False)

        if self.restoreFocPos != None:
            sr.startCmd(
                actor = "gmech",
                cmdStr =  "focus %0.0f" % (self.restoreFocPos,),
            )

    def setCurrFocus(self, *args):
        """Set center focus to current focus.
        """
        currFocus = self.sr.getKeyVar(self.gmechModel.desFocus, defVal=None)
        if currFocus == None:
            currFocus = self.sr.getKeyVar(self.gmechModel.focus, defVal=None)
            if currFocus == None:
                self.sr.showMsg("Current focus not known",
                    severity=RO.Constants.sevWarning,
                )
                return

        self.centerFocPosWdg.set(currFocus)
        self.sr.showMsg("")

    def waitSetFocus(self, focPos, doBacklashComp=False):
        """Adjust focus.

        To use: yield waitSetFocus(...)
        
        Inputs:
        - focPos: new focus position in um
        - doBacklashComp: if True, perform backlash compensation
        """
        sr = self.sr

        focPos = float(focPos)
        focusActor = "gmech"
        
        # to try to eliminate the backlash in the secondary mirror drive move back 1/2 the
        # distance between the start and end position from the bestEstFocPos
        if doBacklashComp and self.BacklashComp:
            backlashFocPos = focPos - (abs(self.BacklashComp) * self.focDir)
            sr.showMsg("Backlash comp: moving focus to %0.0f %s" % (backlashFocPos, MicronStr))
            yield sr.waitCmd(
               actor = focusActor,
               cmdStr = "set focus=%0.0f" % (backlashFocPos,),
            )
            yield sr.waitMS(self.FocusWaitMS)
        
        # move to desired focus position
        sr.showMsg("Moving focus to %0.0f %s" % (focPos, MicronStr))
        yield sr.waitCmd(
           actor = focusActor,
           cmdStr = "focus %0.0f" % (focPos,),
        )
        yield sr.waitMS(self.FocusWaitMS)
