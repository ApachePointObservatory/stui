#!/usr/local/bin/python
"""Take GRIM exposures in a square pattern plus a point in the middle.

This script imports the standard GRIM exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select which portions of the chip to visit.

This script allows the user to change which portions of the chip
to visit "on the fly" (so long as a portion hasn't already been visited).
This is to allow the user to more easily dodge a quadrant that has gone bad.
However, all other inputs (such as exposure time and # of exposures)
are recorded when the script starts, so changes while the script is running
have no effect.

History:
2004-10-01 ROwen
2004-10-19 ROwen	Removed a bit of unused code.
2005-01-21 ROwen	Changed order to ctr, UL, UR, LR, LL.
"""
import Tkinter
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "GRIM"
OffsetWaitMS = 2000
HelpURL = "Scripts/BuiltInScripts/GRIMSquare.html"

# global variables
g_expWdg = None
g_quadWdgSet = None
g_begBoreXY = [None, None]
g_didMove = False

def init(sr):
	"""The setup script; run once when the script runner
	window is created.
	"""
	global InstName
	global g_expWdg, g_quadWdgSet

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

def run(sr):
	"""Take an exposure sequence.
	"""
	# get current GRIM focal plane geometry from the TCC
	# but first make sure the current instrument
	# is actually GRIM
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
	
	# image scale is in unbinned pixels/deg
	imScaleXY = sr.getKeyVar(tccModel.iimScale, ind=None)
	
	# limits are in unbinned pixels
	imLimXY = sr.getKeyVar(tccModel.iimLim, ind=None)
	
	# half radius of image in x,y deg on the sky
	# e.g. move to imhalfRadDeg to be in the center
	# of the upper-right quadrant
	imHalfRadDeg = [
		(imLimXY[2] - imLimXY[0]) * 0.5 / imScaleXY[0],
		(imLimXY[3] - imLimXY[1]) * 0.5 / imScaleXY[1],
	]
	
	# exposure command without startNum and totNum
	# get it now so that it will not change if the user messes
	# with the controls while the script is running
	numExp = g_expWdg.numExpWdg.getNum()
	expCmdPrefix = g_expWdg.getString()

	numExpTaken = 0
	for ind in range(len(g_quadWdgSet)):
		wdg = g_quadWdgSet[ind]
		wdg["relief"] = "sunken"
		
		if wdg.getBool():
			posName = str(wdg["text"])
			
			# slew telescope
			sr.showMsg("Offset to %s position" % posName)
			borePosXY = [
				g_begBoreXY[0] + (wdg.boreOffMult[0] * imHalfRadDeg[0]),
				g_begBoreXY[1] + (wdg.boreOffMult[1] * imHalfRadDeg[1]),
			]
			g_didMove = True
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = "offset boresight %.6f, %.6f" % tuple(borePosXY),
			)
			
			yield sr.waitMS(OffsetWaitMS)
			
			# compute # of exposures & format expose command
			numPtsToGo = 0
			for wdg in g_quadWdgSet[ind:]:
				numPtsToGo += wdg.getBool()
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
