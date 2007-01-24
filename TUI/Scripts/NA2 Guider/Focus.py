#!/usr/bin/env python
"""Take a series of NA2 guider (gcam) exposures at different focus positions to estimate best focus.

History:
2006-01-12 ROwen
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
OffsetGuiderFocusScript = TUI.Base.BaseFocusScript.OffsetGuiderFocusScript

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?

class ScriptClass(OffsetGuiderFocusScript):
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        OffsetGuiderFocusScript.__init__(self,
            sr = sr,
            gcamActor = "gcam",
            instName = "gcam",
            imageViewerTLName = "Guide.NA2 Guider",
            maxFindAmpl = 30000,
            helpURL = "Scripts/BuiltInScripts/InstFocus.html",
            debug = Debug,
        )
