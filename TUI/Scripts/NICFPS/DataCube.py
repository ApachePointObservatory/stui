#!/usr/local/bin/python
"""Take a NICFPS spectral data cube.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select the etalon range and number of steps.

The data cube is taken in two interleaved passes
to cover the full desired range of wavelengths.
It is trivial to add an input for # of passes
(use this widget to set numPasses in run;
but be sure to deal with this GUI issue:
what to do if the user asks for fewer steps than passes).

History:
2004-10-22 ROwen
"""
import Tkinter
from RO.StringUtil import MuStr
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.NICFPS.NICFPSModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
OffsetWaitMS = 2000
HelpURL = "Scripts/BuiltInScripts/NICFPSDataCube.html"

# global variables
g_expWdg = None
g_fpBegWdg = None
g_fpEndWdg = None
g_fpStepsWdg = None
g_fpDeltaWdg = None
g_spacingIncr = None

UMStr = MuStr + "m"

SpacingWidth = 8
	
def updFPZWLim(newLim, isCurrent, **kargs):
	"""Called when the etalon z limits are changed.
	"""
	global g_fpBegWdg, g_fpEndWdg
	if not isCurrent:
		return
	g_fpBegWdg.setRange(newLim[0], newLim[1])
	g_fpEndWdg.setRange(newLim[0], newLim[1])

	
def updSpacingIncr(*args, **kargs):
	"""Called when FP beg Z, end Z or # steps changed.
	Updates g_spacingIncr and displayed Z delta.
	"""
	global g_fpBegWdg, g_fpEndWdg, g_fpStepsWdg, g_fpDeltaWdg, g_spacingIncr
	begSpacing = g_fpBegWdg.getNum()
	endSpacing = g_fpEndWdg.getNum()
	numSteps = g_fpStepsWdg.getNum()

	if numSteps < 2 or 0 in (begSpacing, endSpacing):
		g_spacingIncr = None
		isCurrent = False
	else:
		g_spacingIncr = (endSpacing - begSpacing) / float(numSteps - 1)
		isCurrent = True
		
	g_fpDeltaWdg.set(g_spacingIncr, isCurrent = isCurrent)

def init(sr):
	"""The setup script; run once when the script runner
	window is created.
	"""
	global g_expWdg, g_fpBegWdg, g_fpEndWdg, g_fpStepsWdg, g_fpDeltaWdg
	
	nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()

	row=0
	
	# standard exposure status widget
	expStatusWdg = ExposeStatusWdg(sr.master, InstName)
	expStatusWdg.grid(row=row, column=0, sticky="news")
	row += 1

	# standard exposure input widget
	g_expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
	g_expWdg.numExpWdg.helpText = "# of exposures at each spacing"
	g_expWdg.grid(row=row, column=0, sticky="news")
	row += 1
	
	gr = g_expWdg.gridder
		
	# add etalon controls to exposure input widget
	g_fpBegWdg = RO.Wdg.FloatEntry(
		master = g_expWdg,
		defFormat = "%.0f",
		width = SpacingWidth,
		helpText = "initial etalon Z spacing",
		helpURL = HelpURL,
	)
	gr.gridWdg("FP Beg Z", g_fpBegWdg, UMStr)
	
	g_fpEndWdg = RO.Wdg.FloatEntry(
		master = g_expWdg,
		defFormat = "%.0f",
		width = SpacingWidth,
		helpText = "final etalon Z spacing",
		helpURL = HelpURL,
	)
	gr.gridWdg("FP End Z", g_fpEndWdg, UMStr)
	
	g_fpStepsWdg = RO.Wdg.IntEntry(
		master = g_expWdg,
		helpText = "number of etalon steps",
		minValue = 2,
		maxValue = 999,
		helpURL = HelpURL,
	)
	gr.gridWdg("FP Steps", g_fpStepsWdg)
	
	g_fpDeltaWdg = RO.Wdg.FloatLabel(
		master = g_expWdg,
		precision = 0,
		width = SpacingWidth,
		helpText = "etalon Z spacing interval",
		helpURL = HelpURL,
		anchor = "e",
	)
	gr.gridWdg("FP Delta Z", g_fpDeltaWdg, UMStr)
	
	fpCurrWdg = RO.Wdg.FloatLabel(
		master = g_expWdg,
		precision = 3,
		width = SpacingWidth,
		helpText = "current actual etalon Z spacing",
		helpURL = HelpURL,
		anchor = "e",
	)
	gr.gridWdg("FP Curr Z", fpCurrWdg, UMStr)
	
	nicfpsModel.fpZWLim.addCallback(updFPZWLim)
	nicfpsModel.fpActZW.addROWdg(fpCurrWdg)
	
	g_fpBegWdg.addCallback(updSpacingIncr, callNow=False)
	g_fpEndWdg.addCallback(updSpacingIncr, callNow=False)
	g_fpStepsWdg.addCallback(updSpacingIncr, callNow=True)
	

def run(sr):
	"""Take an exposure sequence.
	"""
	# get current NICFPS focal plane geometry from the TCC
	# but first make sure the current instrument
	# is actually NICFPS
	global g_expWdg, g_fpBegWdg, g_fpEndWdg, g_fpStepsWdg, g_spacingIncr
	
	expModel = TUI.Inst.ExposeModel.getModel(InstName)
	nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()
	tccModel = TUI.TCC.TCCModel.getModel()

	currInstName = sr.getKeyVar(tccModel.instName)
	if not currInstName.lower().startswith(InstName.lower()):
		raise sr.ScriptError("%s is not the current instrument!" % InstName)
	
	# exposure command without startNum and totNum
	# get it now so that it will not change if the user messes
	# with the controls while the script is running
	numExp = g_expWdg.numExpWdg.getNum()
	expCmdPrefix = g_expWdg.getString()
	
	# get etalon step data in advance
	begSpacing = g_fpBegWdg.getNum()
	numSteps = g_fpStepsWdg.getNum()

	if g_spacingIncr == None:
		raise sr.ScriptError("One or more etalon fields is blank")

	totNumExp = numExp * numSteps
	
	numPasses = 2

	# for each pass through the data, create a list of multipliers,
	# where z = zo + delta-z * mult
	multList = range(numSteps)
	multListByPass = [multList[passInd::numPasses] for passInd in range(numPasses)]
	print "multListByPass =", multListByPass

	pointInd = 1
	for passInd in range(numPasses):
		for zMult in multListByPass[passInd]:
			currSpacing = begSpacing + g_spacingIncr * zMult
			
			# command etalon spacing
			sr.showMsg("Set etalon Z = %.3f %s" % (currSpacing, UMStr))
			yield sr.waitCmd(
				actor = nicfpsModel.actor,
				cmdStr = "fp setzw %.3f" % (currSpacing,),
			)
	
			# compute # of exposures & format expose command
			startNum = pointInd * numExp
			expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNumExp)
			
			# take exposure sequence
			sr.showMsg("Expose at etalon Z = %.3f %s" % (currSpacing, UMStr))
			yield sr.waitCmd(
				actor = expModel.actor,
				cmdStr = expCmdStr,
			)
			pointInd += 1
