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
2004-11-16 ROwen	Changed units of Z from um to steps.
2004-12-15 ROwen	Added widgets for initial and current index
					and number of passes.
					Modified so user sets delta Z intead of num steps.
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
g_begSeqIndWdg = None
g_fpBegZWdg = None
g_fpEndZWdg = None
g_fpNumZWdg = None
g_fpNumPassesWdg = None
g_fpDeltaZWdg = None
g_currSeqIndWdg = None

SpacingWidth = 8
	
def updNumZs(*args, **kargs):
	"""Called when FP beg Z, end Z or delta Z changed.
	Updates num Zs
	"""
	global g_fpBegZWdg, g_fpEndZWdg, g_fpDeltaZWdg, g_fpNumZWdg
	begSpacing = g_fpBegZWdg.getNum()
	endSpacing = g_fpEndZWdg.getNum()
	deltaZ = g_fpDeltaZWdg.getNum()

	if deltaZ == 0 or "" in (g_fpBegZWdg.getString(), g_fpEndZWdg.getString()):
		numSpacings = None
		isCurrent = False
	else:
		numSpacings = 1 + int (round((endSpacing - begSpacing) / float (deltaZ)))
		isCurrent = True
		if numSpacings <= 0:
			isCurrent = False
		
	g_fpNumZWdg.set(numSpacings, isCurrent = isCurrent)

def init(sr):
	"""The setup script; run once when the script runner
	window is created.
	"""
	global g_expWdg, g_begSeqIndWdg, g_fpBegZWdg, g_fpEndZWdg, g_fpNumZWdg, g_fpNumPassesWdg
	global g_fpDeltaZWdg, g_currSeqIndWdg
	
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
	g_begSeqIndWdg = RO.Wdg.IntEntry(
		master = g_expWdg,
		minValue = 0,
		width = SpacingWidth,
		helpText = "initial z index (to restart partial cube)",
		helpURL = HelpURL,
	)
	gr.gridWdg("Initial Index", g_begSeqIndWdg, "(normally leave blank)")

	g_fpBegZWdg = RO.Wdg.IntEntry(
		master = g_expWdg,
		minValue = nicfpsModel.fpXYZLimConst[0],
		maxValue = nicfpsModel.fpXYZLimConst[1],
		width = SpacingWidth,
		helpText = "initial etalon Z spacing",
		helpURL = HelpURL,
	)
	gr.gridWdg("Initial Z", g_fpBegZWdg, "steps")
	
	g_fpEndZWdg = RO.Wdg.IntEntry(
		master = g_expWdg,
		minValue = nicfpsModel.fpXYZLimConst[0],
		maxValue = nicfpsModel.fpXYZLimConst[1],
		width = SpacingWidth,
		helpText = "approx. final etalon Z spacing",
		helpURL = HelpURL,
	)
	gr.gridWdg("Final Z", g_fpEndZWdg, "steps")

	g_fpDeltaZWdg = RO.Wdg.IntEntry(
		master = g_expWdg,
		minValue = nicfpsModel.fpXYZLimConst[0],
		maxValue = nicfpsModel.fpXYZLimConst[1],
		width = SpacingWidth,
		helpText = "etalon Z spacing interval",
		helpURL = HelpURL,
	)
	gr.gridWdg("Delta Z", g_fpDeltaZWdg, "steps")
	
	g_fpNumPassesWdg = RO.Wdg.OptionMenu(
		master = g_expWdg,
		items = ("1", "2", "3"),
		defValue = "2",
		helpText = "number of passes in which to sample Z",
		helpURL = HelpURL,
	)
	gr.gridWdg("Num Passes", g_fpNumPassesWdg)
	
	g_fpNumZWdg = RO.Wdg.IntLabel(
		master = g_expWdg,
		width = SpacingWidth,
		helpText = "number of etalon Z spacings",
		helpURL = HelpURL,
		anchor = "e",
	)
	gr.gridWdg("Num Zs", g_fpNumZWdg, "steps")
	
	g_currSeqIndWdg = RO.Wdg.IntLabel(
		master = g_expWdg,
		width = SpacingWidth,
		helpText = "index of current z spacing",
		helpURL = HelpURL,
		anchor = "e",
	)
	gr.gridWdg("Current Index", g_currSeqIndWdg)
	
	fpCurrWdg = RO.Wdg.IntLabel(
		master = g_expWdg,
		width = SpacingWidth,
		helpText = "current actual etalon Z spacing",
		helpURL = HelpURL,
		anchor = "e",
	)
	gr.gridWdg("Current Z", fpCurrWdg, "steps")
	
	nicfpsModel.fpZ.addROWdg(fpCurrWdg)
	
	g_fpBegZWdg.addCallback(updNumZs, callNow=False)
	g_fpEndZWdg.addCallback(updNumZs, callNow=False)
	g_fpDeltaZWdg.addCallback(updNumZs, callNow=True)
	

def run(sr):
	"""Take an exposure sequence.
	"""
	# get current NICFPS focal plane geometry from the TCC
	# but first make sure the current instrument
	# is actually NICFPS
	global g_expWdg, g_begSeqIndWdg, g_fpBegZWdg, g_fpEndZWdg, g_fpDeltaZWdg, g_fpNumPassesWdg
	global g_fpNumZWdg, g_currSeqIndWdg
	
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
	if not expCmdPrefix:
		return
	
	# get user data in advance
	begSeqInd = g_begSeqIndWdg.getNum()
	begSpacing = g_fpBegZWdg.getNum()
	deltaZ = g_fpDeltaZWdg.getNum()
	numPasses = int(g_fpNumPassesWdg.getString())
	
	numSpacings, isCurrent = g_fpNumZWdg.get()
	if numSpacings == None or not isCurrent:
		raise sr.ScriptError("Missing or invalid etalon settings")
	numSpacings = int(numSpacings)

	totNumExp = numExp * numSpacings

	# for each pass through the data, create a list of multipliers,
	# where z = zo + delta-z * mult
	multList = range(numSpacings)
	seqPassMultList = []
	for passInd in range(numPasses):
		for zMult in multList[passInd::numPasses]:
			seqInd = len(seqPassMultList)
			seqPassMultList.append((seqInd, passInd, zMult))
#	print "seqPassMultList =", seqPassMultList

	for seqInd, passInd, zMult in seqPassMultList[begSeqInd:]:
		currSpacing = begSpacing + (deltaZ * zMult)
		
		g_currSeqIndWdg.set(seqInd)
		
		# command etalon spacing
		sr.showMsg("Set etalon Z = %d %s" % (currSpacing, "steps"))
		yield sr.waitCmd(
			actor = nicfpsModel.actor,
			cmdStr = "fp setz %d" % (currSpacing,),
		)

		# compute # of exposures & format expose command
		startNum = seqInd * numExp
		expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNumExp)
		
		# take exposure sequence
		sr.showMsg("Expose at etalon Z = %d %s" % (currSpacing, "steps"))
		yield sr.waitCmd(
			actor = expModel.actor,
			cmdStr = expCmdStr,
		)
