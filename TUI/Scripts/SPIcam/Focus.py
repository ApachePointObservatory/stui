#!/usr/bin/env python
"""Take a series of SPIcam exposures at different focus positions to estimate best focus.

To do:
- Fail unless SPIcam is in imaging mode and binned 1x1
  or put SPIcam into the required mode. To do the latter:
  - Override initAll to record the current mode and put into the correct mode.
  - Override end to restore the original mode.

History:
2007-05-22 ROwen
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
ImagerFocusScript = TUI.Base.BaseFocusScript.ImagerFocusScript

Debug = True # run in debug-only mode (which doesn't DO anything, it just pretends)?

class ScriptClass(ImagerFocusScript):
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        ImagerFocusScript.__init__(self,
            sr = sr,
            instName = "SPIcam",
            imageViewerTLName = "None.SPIcam Expose",
            maxFindAmpl = 5000,
            helpURL = "Scripts/BuiltInScripts/InstFocus.html",
            debug = Debug,
        )
