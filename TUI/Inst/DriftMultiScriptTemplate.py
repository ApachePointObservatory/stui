"""Template script to drift along slit during an exposure.

Intended to be loaded by instrument-specific scripts, e.g.:
DISDrift.py:

from TUI.Inst.DriftScriptTemplate import *
def init(sr):
	basicInit(sr, "DIS")

To do:
- when <inst>Expose is improved to support user-specified
sequence numbering, switch to that system.
- if ScriptRunner is improved to automatically log commands, do that.

History:
2004-07-23 ROwen
2004-08-13 ROwen	Do not restore original boresight unless tel. moved.
					Added abort command for expose.
					Added separator bar.
"""
__all__ = ['basicInit', 'run', 'end']

import Tkinter
import RO.Wdg
import RO.PhysConst
import TUI.TCC.TCCModel
import TUI.Inst.ExposeStatusWdg
import TUI.Inst.ExposeInputWdg

def basicInit(sr, instName):
	"""Set up widgets to set input exposure time,
	drift amount and drift speed.
	"""
	row=0
	
	# standard exposure status widget
	expStatusWdg = TUI.Inst.ExposeStatusWdg.ExposeStatusWdg(sr.master, instName)
	expStatusWdg.grid(row=row, column=0, sticky="news")
	row += 1

	# separator
	Tkinter.Frame(sr.master,
		bg = "black",
	).grid(row=row, column=0, pady=2, sticky="ew")
	row += 1
	
	# standard exposure input widget
	expWdg = TUI.Inst.ExposeInputWdg.ExposeInputWdg(sr.master, instName, expTypes="object")
	expWdg.numExpWdg.helpText = "# of exposures at each point"
	expWdg.grid(row=row, column=0, sticky="news")
	row += 1
	
	#+
	# add some controls to the exposure input widget
	#-

	# drift range
	rangeUnitsVar = Tkinter.StringVar()
	rangeWdg = RO.Wdg.DMSEntry (
		master = expWdg,
		minValue = 0,
		maxValue = "0:03:00",
		isRelative = True,
		unitsVar = rangeUnitsVar,
		width = 10,
		helpText = "Range of drift (peak to peak)",
	)
	expWdg.gridder.gridWdg("Drift Range", rangeWdg, rangeUnitsVar)
	
	halfCyclesWdg = RO.Wdg.IntEntry (
		master = expWdg,
		defValue = 1,
		minValue = 0,
		maxValue = 99,
		width = 2,
		helpText = "Number of half cycles of drift per exposure",
	)
	expWdg.gridder.gridWdg("Half Cycles", halfCyclesWdg)
	
	# add stuff we'll need later to script runner globals
	sr.globals.instName = instName
	sr.globals.expWdg = expWdg
	sr.globals.rangeWdg = rangeWdg
	sr.globals.halfCyclesWdg = halfCyclesWdg
	sr.globals.begBoreXY = [None, None]

def run(sr):
	"""Take an exposure while moving the image along the slit.
	"""
	sr.globals.begBoreXY = [None, None]
	sr.globals.didMove = False
	tccModel = TUI.TCC.TCCModel.getModel()

	# make sure the current instrument matches the desired instrument
	desInst = sr.globals.instName
	currInst = sr.getKeyVar(tccModel.instName)
	if desInst.lower() != currInst.lower():
		raise sr.ScriptError("%s is not the current instrument!" % desInst)
	
	# record the current boresight position (in a global area
	# so "end" can restore it).
	begBorePVTs = sr.getKeyVar(tccModel.boresight, ind=None)
	begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
	if None in begBoreXY:
		raise sr.ScriptError("boresight offset unknown")
	sr.globals.begBoreXY = begBoreXY
#	print "begBoreXY=%r" % begBoreXY
	
	# sanity check exposure inputs
	# (will raise an exception if no expTime or file name)
	try:
		sr.globals.expWdg.getString()
	except Exception, e:
		raise sr.ScriptError(str(e))
	if sr.globals.rangeWdg.getString() == "":
		raise sr.ScriptError("specify the drift range")
	
	
	# useful local variables
	numExpWdg = sr.globals.expWdg.numExpWdg
	expActor = sr.expWdg.expModel.actor
	
	# conduct some preliminary tests to be sure
	# we have enough info to expose
	numExp = numExpWdg.getNum()
	if numExp <= 0:
		sr.showMsg("No exposures wanted, nothing done", 2)
	
	testExpCmd = sr.globals.expWdg.getString()
	if not testExpCmd:
		raise sr.ScriptError("Could not create expose cmd")
	
	# execute the drift-and-expose cycle
	expNum = 0 # incremented shortly, so 1 for first iteration, etc.
	while True:
		expNum += 1
		numExp = numExpWdg.getNum()
		if expNum >= numExp:
			return
		
		# get drift info and related info
		# time is in seconds
		# distance is in arcsec (AS suffix) or degrees (no suffix)
		expTime = sr.globals.expWdg.timeWdg.getNum()
		if not expTime:
			raise sr.ScriptError("Specify a nonzero exposure time")
		driftRangeAS = sr.globals.rangeWdg.getNum()
		halfCycles = sr.globals.halfCyclesWdg.getNum()
		driftSpeedAS = halfCycles * driftRangeAS / float(expTime)
		driftRange = driftRangeAS / RO.PhysConst.ArcSecPerDeg
		driftSpeed = driftSpeedAS / RO.PhysConst.ArcSecPerDeg
		halfCycleTime = expTime / float(halfCycles)
		dirMult = 1.0
	
		# should probably check against axis limits
		# but for now let's assume the user has a clue...
		
		# compute drift dir and startY
		startPosX, startPosY = getStartBore(begBoreXY, driftRange, dirMult)
	
		# slew to the start position
		sr.showMsg("Slew to starting position")
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
			(startPosX, startPosY)
#		print "sending tcc command %r" % tccCmdStr
		sr.globals.didMove = True
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)

		# start exposure
		expCmdStr = sr.expWdg.getString(numExp=1, startNum = expNum, totNum = numExp)
		if not testExpCmd:
			raise sr.ScriptError("Could not create expose cmd")
		sr.showMsg("Expose %d of %d" % (expNum, numExp))
#		print "sending %s command %r" % (desInst, expCmdStr)
		yield sr.waitCmd(
			actor = expActor,
			cmdStr = expCmdStr,
			abortCmdStr = "abort",
		)
			
		# start drift
		sr.showMsg("Drift at %.1f\"/sec" % (driftSpeedAS))
		tccCmdStr = "offset boresight %.7f, %.7f, 0, %.7f/pabs/vabs" % \
			(startPosX, startPosY, driftSpeed * driftDir)
#		print "sending tcc command %r" % tccCmdStr
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
		

def getStartBore(begBoreXY, driftRange, dirMult):
	return (
		begBoreXY[0],
		begBoreXY[1] - (0.5 * driftRange * dirMult),
	)
		
def end(sr):
	"""If telescope moved, restore original boresight position.
	"""
#	print "end called"
	if sr.globals.didMove:
		# restore original boresight position	
		begBoreXY = sr.globals.begBoreXY
		if None in begBoreXY:
			return
			
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
			(begBoreXY[0], begBoreXY[1])
	#	print "sending tcc command %r" % tccCmdStr
		sr.startCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
