#!/usr/bin/env python
"""Take a series of NA2 guider (gcam) exposures
at different (secondary) focus positions to estimate best focus.
Does not touch the NA2 guider's internal focus.

History:
2006-01-12 ROwen
2006-01-29 ROwen    instName->instPos for updated OffsetGuiderFocusScript.
2007-07-26 ROwen    Added default bin factor.
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
OffsetGuiderFocusScript = TUI.Base.BaseFocusScript.OffsetGuiderFocusScript

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?
HelpURL = "Scripts/BuiltInScripts/InstFocus.html"

class ScriptClass(OffsetGuiderFocusScript):
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        OffsetGuiderFocusScript.__init__(self,
            sr = sr,
            gcamActor = "gcam",
            instPos = "NA2",
            imageViewerTLName = "Guide.NA2 Guider",
            defBinFactor = 3,
            maxFindAmpl = 30000,
            helpURL = HelpURL,
            debug = Debug,
        )
