#!/usr/local/bin/python
"""Take a series of NICFPS exposures at different focus positions to estimate best focus.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.

To do:
- Fail unless NICFPS is in imaging mode and binned 1x1
  or put NICFPS into the required mode. To do the latter:
  - Override initAll to record the current mode and put into the correct mode.
  - Override end to restore the original mode.

History:
2005-04-30 SBeland	Copied/enhanced from NICFPS Dither script
2006-02-01 SBeland	Modified to use full window mode to try to avoid the persistence
					seen on the chip in window mode.
2006-04-24 ROwen	Modified to not use pylab.
					Graph windows are now normal TUI toplevels, so their position is remembered.
					Improved backlash compensation to use a constant amount of compensation
					and to apply for first focus move as well as final move to best focus.
					Changed OffsetWaitMS to FocusWaitMS.
					Changed to be a class, so requires TUI 1.2 or later.
					Added Default button and DefDeltaFoc constant.
					Added code to usefully run in debug mode.
					Warning: not tested talking to NICFPS.
2006-06-01 ROwen	Added Centroid Radius control.
					Added a log panel to output results.
2006-06-05 ROwen	Added matplotlib.use("TkAgg") and matplotlib.rcParams["numerix"] = "numarray"
					to avoid problems with user's configuration files.
					Fixed radius->cradius.
					Changed default radius from 50 to 20.
					Changed backlash compensation from 500um to 50um.
2006-09-27 ROwen	Changed to graph as data comes in.
					PR 451: graph only worked for the first execution.
2006-11-01 ROwen	Tweaked for the new RO.Wdg.LogWdg.
					Another fix for PR 451: graph only worked for the first execution.
2006-11-07 ROwen	Stopping the script during an exposure will now stop the exposure.
2006-11-09 ROwen	Removed any attempt to show images.
2006-12-11 ROwen	Modified to use TUI.Base.BaseFocusScript
2006-12-28 ROwen	Modified "to do" comments.
"""
import TUI.Base.BaseFocusScript
# make script reload also reload BaseFocusScript
reload(TUI.Base.BaseFocusScript)
ImagerFocusScript = TUI.Base.BaseFocusScript.ImagerFocusScript

Debug = False # run in debug-only mode (which doesn't DO anything, it just pretends)?

class ScriptClass(ImagerFocusScript):
	def __init__(self, sr):
		"""The setup script; run once when the script runner
		window is created.
		"""
		ImagerFocusScript.__init__(self,
			sr = sr,
			instName = "NICFPS",
			imageViewerTLName = "None.NICFPS Expose",
			helpURL = "Scripts/BuiltInScripts/InstFocus.html",
			debug = Debug,
		)
