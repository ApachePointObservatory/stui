#!/usr/local/bin/python
"""Take NICFPS exposures in a square pattern plus a point in the middle.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select which portions of the chip to visit.

To do:
- Fail unless NICFPS is in imaging mode.
- Use uncomputed offsets if offset small enough.

History:
2004-10-19 ROwen	first cut; direct copy of GRIM:Square
2005-01-21 ROwen	Changed order to ctr, UL, UR, LR, LL.
					Changed Offset Size to Box Size (2x as big)
					and made 20" the default box size.
					Renamed to Dither/Point Source.
2005-01-24 ROwen	Modified to record dither points in advance
					(instead of allowing change 'on the fly')
					and to not slew to the first point if it's the center
					(since that's our starting poing).
"""
import math
import Tkinter
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
DefBoxSize = 20 # arcsec
OffsetWaitMS = 2000
HelpURL = "Scripts/BuiltInScripts/NICFPSDither.html"

# global variables
g_expWdg = None
g_quadWdgSet = None
g_begBoreXY = [None, None]
g_didMove = False
g_boxSizeWdg = None


def init(sr):
	"""The setup script; run once when the script runner
	window is created.
	"""
	global InstName
	global g_expWdg, g_quadWdgSet
	global g_boxSizeWdg

	tccModel = TUI.TCC.TCCModel.getModel()

	row=0
	
	# standard exposure status widget
	expStatusWdg = ExposeStatusWdg(sr.master, InstName)
	expStatusWdg.grid(row=row, column=0, sticky="news")
	row += 1
	
	# create checkbuttons showing where exposures will be taken
	quadFrame = Tkinter.Frame(sr.master)
	
	# quadrant data; each entry is:
	# - name of quadrant
	# - boresight offset multiplier in image x, image y
	quadData = [
		("Ctr", (0, 0)),
		("UL", (-1, 1)),
		("UR", (1, 1)),
		("LR", (1, -1)),
		("LL", (-1, -1)),
	]
	g_quadWdgSet = []
	for name, boreOffMult in quadData:
		wdg = RO.Wdg.Checkbutton(
			master = quadFrame,
			text = name,
			defValue = True,
			relief = "flat",
			helpText = "Expose here if checked",
			helpURL = HelpURL,
		)
		# add attribute "boreOffMult" to widget
		# so it can be read by "run"
		wdg.boreOffMult = boreOffMult
		
		# display quadrant checkbutton in appropriate location
		row = 1 - boreOffMult[1]
		col = 1 + boreOffMult[0]
		wdg.grid(row=row, column=col)
		
		g_quadWdgSet.append(wdg)
	
	quadFrame.grid(row=row, column=0, sticky="news")
	row += 1

	# standard exposure input widget
	g_expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
	g_expWdg.numExpWdg.helpText = "# of exposures at each point"
	g_expWdg.grid(row=row, column=0, sticky="news")
	row += 1

	g_boxSizeWdg = RO.Wdg.IntEntry(
		master = g_expWdg,
		minValue = 0,
		defValue = DefBoxSize,
		helpText = "size of dither box",
		helpURL = HelpURL,
	)
	g_expWdg.gridder.gridWdg("Box size", g_boxSizeWdg, "arcsec")
        
def run(sr):
	"""Take an exposure sequence.
	"""
	# get current NICFPS focal plane geometry from the TCC
	# but first make sure the current instrument
	# is actually NICFPS
	global InstName, OffsetWaitMS
	global g_begBoreXY, g_didMove, g_expWdg, g_quadWdgSet
	
	g_didMove = False

	tccModel = TUI.TCC.TCCModel.getModel()
	expModel = TUI.Inst.ExposeModel.getModel(InstName)

	currInstName = sr.getKeyVar(tccModel.instName)
	if not currInstName.lower().startswith(InstName.lower()):
		raise sr.ScriptError("%s is not the current instrument!" % InstName)

	# record the current boresight position (in a global area
	# so "end" can restore it).
	begBorePVTs = sr.getKeyVar(tccModel.boresight, ind=None)
	g_begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
	if None in g_begBoreXY:
		raise sr.ScriptError("Current boresight position unknown")
#	print "g_begBoreXY=%r" % g_begBoreXY
	
	# exposure command without startNum and totNum
	# get it now so that it will not change if the user messes
	# with the controls while the script is running
	numExp = g_expWdg.numExpWdg.getNum()
	expCmdPrefix = g_expWdg.getString()
	offsetSize =  g_boxSizeWdg.getNum() / 2.0
	
	# record which points to use in the dither pattern in advance
	# (rather than allowing the user to change it during execution)
	doPtArr = [wdg.getBool() for wdg in g_quadWdgSet]
	
	numExpTaken = 0
	numPtsToGo = sum(doPtArr)
	for doPt, wdg in zip(doPtArr, g_quadWdgSet):
		wdg["relief"] = "sunken"
		
		if not doPt:
			continue
			
		posName = str(wdg["text"])
		
		if ind > 0:
			# slew telescope
			sr.showMsg("Offset to %s position" % posName)
			borePosXY = [
				g_begBoreXY[0] + (wdg.boreOffMult[0] * (offsetSize / 3600.0)),
				g_begBoreXY[1] + (wdg.boreOffMult[1] * (offsetSize / 3600.0)),
			]
			g_didMove = True
			
			# Figure out whether the move is small enough to safely jog the telescope
			distance = math.sqrt(borePosXY[0] * borePosXY[0]  + borePosXY[1] * borePosXY[1])
			if distance >= (20.0 / 3600.0):
				computed = "/computed"
			else:
				computed = ""

			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = "offset boresight %.6f, %.6f%s/pabs" % (borePosXY[0], borePosXY[1], computed),
			)
			
			if not computed:
				yield sr.waitMS(OffsetWaitMS)
			
		# compute # of exposures & format expose command
		totNum = numExpTaken + (numPtsToGo * numExp)
		startNum = numExpTaken + 1
		
		expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)
		
		# take exposure sequence
		sr.showMsg("Expose at %s position" % posName)
		yield sr.waitCmd(
			actor = expModel.actor,
			cmdStr = expCmdStr,
		)

		numExpTaken += numExp
		numPtsToGo -= 1
	
	# slew back to starting position
	if g_didMove:
		sr.showMsg("Finishing up: slewing to initial position")
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(g_begBoreXY)
		g_didMove = False
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
		
def end(sr):
	"""If telescope moved, restore original boresight position.
	"""
	global g_didMove, g_begBoreXY, g_quadWdgSet
	for wdg in g_quadWdgSet:
		wdg["relief"] = "flat"
	
#	print "end called"
	if g_didMove:
		# restore original boresight position
# the following is commented out because it is not displayed anyway
#		sr.showMsg("Done: slewing to original boresight")
		if None in g_begBoreXY:
			return
			
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(g_begBoreXY)
	#	print "sending tcc command %r" % tccCmdStr
		sr.startCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)

