#!/usr/bin/env python
"""Take a series of SPIcam exposures at different focus positions to estimate best focus.

History:
2007-05-22 ROwen
2007-07-25 ROwen    Changed doWindow to True and added doZeroOverscan to take advantage of
                    improvements to the spicamExpose actor and the ImagerFocusScript class.
2007-07-26 ROwen    Added default bin factor.
2007-07-30 ROwen    Changed maxFindAmpl from 5000 (the NICFPS value, a bad one to copy) to 20000
                    (recommended by Russet); SPIcam saturates at 59k and saturation is not very nasty.
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
ImagerFocusScript = TUI.Base.BaseFocusScript.ImagerFocusScript

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?
HelpURL = "Scripts/BuiltInScripts/InstFocus.html"

class ScriptClass(ImagerFocusScript):
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        ImagerFocusScript.__init__(self,
            sr = sr,
            instName = "SPIcam",
            imageViewerTLName = "None.SPIcam Expose",
            defBinFactor = 2,
            maxFindAmpl = 20000,
            doWindow = True,
            doZeroOverscan = True,
            helpURL = HelpURL,
            debug = Debug,
        )
