"""Take a series of exposures at different focus positions to estimate best focus.
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
BaseFocusScript = TUI.Base.BaseFocusScript.BaseFocusScript

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?

class ScriptClass(BaseFocusScript):
	def __init__(self, sr):
		"""The setup script; run once when the script runner
		window is created.
		"""
		BaseFocusScript.__init__(self,
			sr = sr,
			gcamName = "ecam",
			instName = "Echelle",
			guideTLName = "Guide.Echelle Slitviewer",
			defBoreXY = [5.0, None],
			helpURL = "Scripts/BuiltInScripts/EchelleFocus.html",
			debug = Debug,
		)
