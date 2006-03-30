import RO.Wdg
import Tkinter
import TUI.Inst.ExposeModel as ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg

class ScriptClass(object):
	"""Take a series of DIS darks with user input.
	"""
	def __init__(self, sr):
		"""Display exposure status and a few user input widgets.
		"""
		expStatusWdg = ExposeStatusWdg(
			master = sr.master,
			instName = "DIS",
		)
		expStatusWdg.grid(row=0, column=0, sticky="w")
		
		wdgFrame = Tkinter.Frame(sr.master)
	 
		gr = RO.Wdg.Gridder(wdgFrame)
		
		self.expModel = ExposeModel.getModel("DIS")
	
		timeUnitsVar = Tkinter.StringVar()
		self.timeWdg = RO.Wdg.DMSEntry (
			master = wdgFrame,
			minValue = self.expModel.instInfo.minExpTime,
			maxValue = self.expModel.instInfo.maxExpTime,
			isRelative = True,
			isHours = True,
			unitsVar = timeUnitsVar,
			width = 10,
			helpText = "Exposure time",
		)
		gr.gridWdg("Time", self.timeWdg, timeUnitsVar)
		
		self.numExpWdg = RO.Wdg.IntEntry(
			master = wdgFrame,
			defValue = 1,
			minValue = 1,
			maxValue = 999,
			helpText = "Number of exposures in the sequence",
		)
		gr.gridWdg("#Exp", self.numExpWdg)
		
		wdgFrame.grid(row=1, column=0, sticky="w")
		
	def run(self, sr):
		"""Take a series of DIS darks"""
		expType = "dark"
		expTime = self.timeWdg.getNum()
		numExp = self.numExpWdg.getNum()
	
		fileName = "dis_" + expType
		
		if expTime <= 0:
			raise sr.ScriptError("Specify exposure time")
	
		cmdStr = self.expModel.formatExpCmd(
			expType = expType,
			expTime = expTime,
			fileName = fileName,
			numExp = numExp,
		)
	
		yield sr.waitCmd(
			actor = "disExpose",
			cmdStr = cmdStr,
			abortCmdStr = "abort",
		)
