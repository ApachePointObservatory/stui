import TUI.TUIModel

def init(sr):
	"""Open the DIS Expose window so the user can see what's going on."""
	tuiModel = TUI.TUIModel.getModel()
	tuiModel.tlSet.makeVisible("None.DIS Expose")

def run(sr):
	"""Sample script to take a series of DIS calibration images
	and demonstrate looping through data in Python.
	The exposure times and  # of iterations are short so the demo runs quickly.
	"""
	# typeTimeNumList is a list of calibration info
	# each element of the list is a list of:
	# - exposure type
	# - exposure time (sec)
	# - number of exposures
	typeTimeNumList = [
		["flat", 1, 2],
		["flat", 5, 2],
		["bias", 0, 2],
		["dark", 1, 2],
		["dark", 5, 2],
	]
	
	for expType, expTime, numExp in typeTimeNumList:
		if expType == "bias":
			# bias, so cannot specify time
			cmdStr = "%s n=%d name=dis%s" % (expType, numExp, expType)
		else:
			cmdStr = "%s time=%s n=%d name=dis%s" % (expType, expTime, numExp, expType)

		yield sr.waitCmd(
			actor = "disExpose",
			cmdStr = cmdStr,
			abortCmdStr = "abort",
		)
