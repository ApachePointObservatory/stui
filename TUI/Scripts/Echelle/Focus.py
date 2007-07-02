"""Take a series of exposures at different focus positions to estimate best focus.
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
SlitviewerFocusScript = TUI.Base.BaseFocusScript.SlitviewerFocusScript

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?
HelpURL = "Scripts/BuiltInScripts/InstFocus.html"

class ScriptClass(SlitviewerFocusScript):
    def __init__(self, sr):
        """The setup script; run once when the script runner
        window is created.
        """
        SlitviewerFocusScript.__init__(self,
            sr = sr,
            gcamActor = "ecam",
            instName = "Echelle",
            imageViewerTLName = "Guide.Echelle Slitviewer",
            defBoreXY = [5.0, None],
            helpURL = HelpURL,
            debug = Debug,
        )
