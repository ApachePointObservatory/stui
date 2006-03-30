from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
import TUI.Inst.ExposeModel

class ScriptClass(object):
	"""Sample script to take a series of DIS calibration images
	and demonstrate looping through data in Python.
	The exposure times and  # of iterations are short so the demo runs quickly.
	"""
	def __init__(self, sr):
		"""Display the exposure status panel.
		"""
		expStatusWdg = ExposeStatusWdg(
			master = sr.master,
			instName = "DIS",
		)
		expStatusWdg.grid(row=0, column=0)
		
		# get the exposure model
		self.expModel = TUI.Inst.ExposeModel.getModel("DIS")
	
	def run(self, sr):
		"""Run the script"""
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
		
		# compute the total number of exposures
		totNum = 0
		for expType, expTime, numExp in typeTimeNumList:
			totNum += numExp
		
		# take the exposures
		startNum = 1
		for expType, expTime, numExp in typeTimeNumList:
			fileName = "dis_" + expType
			cmdStr = self.expModel.formatExpCmd(
				expType = expType,
				expTime = expTime,
				fileName = fileName,
				numExp = numExp,
				startNum = startNum,
				totNum = totNum,
			)
			startNum += numExp
	
			yield sr.waitCmd(
				actor = self.expModel.actor,
				cmdStr = cmdStr,
				abortCmdStr = "abort",
			)
