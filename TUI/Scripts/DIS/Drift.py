"""Script to drift along the DIS slit during an exposure.

To do:
- When the hub supports it, get the slit length from the hub.

According to Russet McMillan (email 2004-09-17)
DIS has a slit length of 400", but only the middle 150"
of the slit is visible in the slitviewer.

History:
2004-10-01 ROwen
"""
import Tkinter
import RO.Wdg
import RO.PhysConst
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.ExposeStatusWdg
import TUI.Inst.ExposeInputWdg

# constants
InstName = "DIS"
RampTime = 3.0 # time for TCC to ramp up to drift speed
SlitLengthAS = 400.0 # slit length, in arcsec (Russet 2004-09-17)
HelpURL = "Scripts/BuiltInScripts/DISDrift.html"

# global variables
g_didMove = False
g_begBoreXY = [None, None]
g_expWdg = None
g_driftSpeedAS = None
g_driftRangeAS = None


def init(sr):
	"""Set up widgets to set input exposure time,
	drift amount and drift speed.
	"""
	global InstName, SlitLengthAS
	global g_expWdg

	row=0
	
	# standard exposure status widget
	expStatusWdg = TUI.Inst.ExposeStatusWdg.ExposeStatusWdg(sr.master, InstName)
	expStatusWdg.grid(row=row, column=0, sticky="news")
	row += 1

	# separator
	Tkinter.Frame(sr.master,
		bg = "black",
	).grid(row=row, column=0, pady=2, sticky="ew")
	row += 1
	
	# standard exposure input widget
	g_expWdg = TUI.Inst.ExposeInputWdg.ExposeInputWdg(sr.master, InstName, expTypes="object")
	g_expWdg.numExpWdg.helpText = "# of exposures at each point"
	g_expWdg.grid(row=row, column=0, sticky="news")
	row += 1
	
	# add some controls to the exposure input widget
	
	# drift range
	driftSpeedWdg = RO.Wdg.FloatEntry (
		master = g_expWdg,
		minValue = 0,
		maxValue = 300,
		width = 10,
		helpText = "Drift speed",
		helpURL = HelpURL,
	)
	g_expWdg.gridder.gridWdg("Drift Speed", driftSpeedWdg, '"/sec')
	
	# drift speed
	driftRangeWdg = RO.Wdg.FloatLabel (
		master = g_expWdg,
		helpText = "Range of drift (centered on starting point)",
		helpURL = HelpURL,
	)
	g_expWdg.gridder.gridWdg("Drift Range", driftRangeWdg, '"', sticky="ew")
	
	driftRangePercentWdg = RO.Wdg.FloatLabel (
		master = g_expWdg,
		precision = 1,
		width = 5,
		helpText = "Range of drift as % of slit length",
		helpURL = HelpURL,
	)
	g_expWdg.gridder.gridWdg("=", driftRangePercentWdg, '%', sticky="w", row=-1, col=3)
	
	g_expWdg.gridder.allGridded()
	
	# set up automatic computation of drift range
	def updateRange(*args):
		global g_driftSpeedAS, g_driftRangeAS
		expTime = g_expWdg.timeWdg.getNum()
		if not expTime:
			driftRangeWdg.set(None, isCurrent=False)
			driftRangePercentWdg.set(None, isCurrent=False)
			return

		g_driftSpeedAS = driftSpeedWdg.getNum()
		g_driftRangeAS = g_driftSpeedAS * float(expTime)
		driftRangeWdg.set(g_driftRangeAS)
		
		driftRangePercent = 100.0 * g_driftRangeAS / float(SlitLengthAS)
		driftRangePercentWdg.set(driftRangePercent)
	
	driftSpeedWdg.addCallback(updateRange)
	g_expWdg.timeWdg.addCallback(updateRange, callNow=True)

def run(sr):
	"""Take one or more exposures while moving the object
	in the +X direction along the slit.
	"""
	global InstName, RampTime
	global g_expWdg, g_driftSpeedAS, g_driftRangeAS
	global g_begBoreXY, g_didMove

	g_begBoreXY = [None, None]
	g_didMove = False
	tccModel = TUI.TCC.TCCModel.getModel()
	expModel = TUI.Inst.ExposeModel.getModel(InstName)

	# make sure the current instrument matches the desired instrument
	currInst = sr.getKeyVar(tccModel.instName)
	if InstName.lower() != currInst.lower():
		raise sr.ScriptError("%s is not the current instrument!" % InstName)
	
	# record the current boresight position (in a global area
	# so "end" can restore it).
	begBorePVTs = sr.getKeyVar(tccModel.boresight, ind=None)
	g_begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
	if None in g_begBoreXY:
		raise sr.ScriptError("Current boresight position unknown")
#	print "g_begBoreXY=%r" % g_begBoreXY
	
	# sanity check exposure inputs
	# (will raise an exception if no expTime or file name)
	try:
		g_expWdg.getString()
	except Exception, e:
		raise sr.ScriptError(str(e))
	
	# get drift info and related info
	# time is in seconds
	# distance is in arcsec (AS suffix) or degrees (no suffix)
	expTime = g_expWdg.timeWdg.getNum()
	driftSpeed = g_driftSpeedAS / RO.PhysConst.ArcSecPerDeg
	driftRange = g_driftRangeAS / RO.PhysConst.ArcSecPerDeg
	
	# compute starting position
	startPosX = g_begBoreXY[0] - (driftRange / 2.0) - (driftSpeed * RampTime)
	startPosY = g_begBoreXY[1]
	
	# should probably check against axis limits
	# but for now let's assume the user has a clue...
	
	numExpWdg = g_expWdg.numExpWdg
	numExp = numExpWdg.getNum()
	if numExp <= 0:
		sr.showMsg("No exposures wanted, nothing done", 2)
	
	# slew to start position
	sr.showMsg("Slewing to starting position")

	tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
		(startPosX, startPosY)
#		print "sending tcc command %r" % tccCmdStr
	g_didMove = True
	yield sr.waitCmd(
		actor = "tcc",
		cmdStr = tccCmdStr,
	)
	
	for expNum in range(1, numExp + 1):
		isLast = (expNum == numExp)
		cycleStr = "Exposure %d of %d" % (expNum, numExp)
			
		# start drift
		sr.showMsg("%s: starting drift" % cycleStr)
		tccCmdStr = "offset boresight %.7f, %.7f, %.7f, 0.0/pabs/vabs" % \
			(startPosX, startPosY, driftSpeed)
#		print "sending tcc command %r" % tccCmdStr
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
		
		# wait for ramp time
		sr.showMsg("%s: waiting %s sec for ramp-up" % (cycleStr, RampTime))
		yield sr.waitMS(RampTime * 1000)

		# expose
		sr.showMsg("%s: starting exposure" % cycleStr)
		expCmdStr = g_expWdg.getString(
			numExp = 1,
			startNum = expNum,
			totNum = numExp,
		)
#		print "sending %s command %r" % (InstName, expCmdStr)
		expCmdVar = sr.startCmd(
			actor = expModel.actor,
			cmdStr = expCmdStr,
			abortCmdStr = "abort",
		)
		
		# wait for integration to end and reading to begin
		while True:
			yield sr.waitKeyVar(expModel.expState, ind=1, waitNext=False)
			if sr.value.lower() == "reading":
				break
		
		if not isLast:
			# slew to start position for next exposure
			sr.showMsg("%s: slewing to start pos. for next exposure" % cycleStr)
		
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
				(startPosX, startPosY)
#				print "sending tcc command %r" % tccCmdStr
			g_didMove = True
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
		else:
			# slew back to initial position
			sr.showMsg("Slewing to initial position")
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(g_begBoreXY)
			g_didMove = False
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
			
		# wait for exposure and slew to both end
		sr.showMsg("%s: waiting for exposure to end" % cycleStr)
		yield sr.waitCmdVars(expCmdVar)
		
def end(sr):
	"""If telescope moved, restore original boresight position.
	"""
	global g_didMove, g_begBoreXY
#	print "end called"
	if g_didMove:
		# restore original boresight position
# the following is commented out because it is not displayed anyway
#		sr.showMsg("Done: slewing to original boresight")
		if None in g_begBoreXY:
			return
			
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
			(g_begBoreXY[0], g_begBoreXY[1])
#		print "sending tcc command %r" % tccCmdStr
		sr.startCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
