import RO.Wdg
import Tkinter
import TUI.Inst.ExposeModel as ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg

def init(sr):
	"""Display exposure status and a few user input widgets.
	"""
	expStatusWdg = ExposeStatusWdg(
		master = sr.master,
		instName = "DIS",
	)
	expStatusWdg.grid(row=0, column=0, sticky="w")
	
	wdgFrame = Tkinter.Frame(sr.master)
 
	gr = RO.Wdg.Gridder(wdgFrame)
	
	expModel = ExposeModel.getModel("DIS")

	timeUnitsVar = Tkinter.StringVar()
	timeWdg = RO.Wdg.DMSEntry (
		master = wdgFrame,
		minValue = expModel.instInfo.minExpTime,
		maxValue = expModel.instInfo.maxExpTime,
		isRelative = True,
		isHours = True,
		unitsVar = timeUnitsVar,
		width = 10,
		helpText = "Exposure time",
	)
	gr.gridWdg("Time", timeWdg, timeUnitsVar)
	
	numExpWdg = RO.Wdg.IntEntry(
		master = wdgFrame,
		defValue = 1,
		minValue = 1,
		maxValue = 999,
		helpText = "Number of exposures in the sequence",
	)
	gr.gridWdg("#Exp", numExpWdg)
	
	wdgFrame.grid(row=1, column=0, sticky="w")
	
	sr.globals.expModel = expModel
	sr.globals.timeWdg = timeWdg
	sr.globals.numExpWdg = numExpWdg
	
def run(sr):
	"""Take a series of DIS darks with user input.
	"""
	expType = "dark"
	expTime = sr.globals.timeWdg.getNum()
	numExp = sr.globals.numExpWdg.getNum()

	fileName = "dis_" + expType
	expModel = sr.globals.expModel
	
	if expTime <= 0:
		raise sr.ScriptError("Specify exposure time")

	cmdStr = expModel.formatExpCmd(
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
