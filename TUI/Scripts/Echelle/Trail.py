"""Script to trail along the Echelle slit during an exposure.

To do:
- When the hub supports it, get the slit length from the hub.

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
InstName = "Echelle"
SlitLengthAS = 3.2 # slit length, in arcsec
MaxTrailLengthAS = 200.0 # max trail length, in arcsec
MaxVelAS = 200.0 # maximum speed, in arcsec/sec
HelpURL = "Scripts/BuiltInScripts/EchelleTrail.html"

# global variables
g_expModel = TUI.Inst.ExposeModel.getModel(InstName)
g_tccModel = TUI.TCC.TCCModel.getModel()

g_expWdg = None

g_numTrails = 0
g_trailRangeAS = None
g_trailSpeedAS = None
g_trailSpeedOK = False
g_begBoreXY = [None, None]
g_didMove = False

def init(sr):
	"""Set up widgets to set input exposure time,
	trail cycles and trail range and display trail speed.
	"""
	global InstName, g_tccModel
	global SlitLengthAS, MaxTrailLengthAS, MaxVelAS
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
	
	# number of moves
	numTrailsWdg = RO.Wdg.IntEntry (
		master = g_expWdg,
		minValue = 0,
		maxValue = 99,
		defValue = 5,
		width = 6,
		helpText = "Number of trails (2 is up, then down)",
		helpURL = HelpURL,
	)
	g_expWdg.gridder.gridWdg("# of Trails", numTrailsWdg)
	
	# trail range
	rangeFrame = Tkinter.Frame(g_expWdg)

	trailRangeWdg = RO.Wdg.FloatEntry (
		master = rangeFrame,
		minValue = 0,
		maxValue = MaxTrailLengthAS,
		defValue = SlitLengthAS * 1.2,
		defFormat = "%.1f",
		defMenu = "Default",
		width = 6,
		helpText = "Length of trail (centered on starting point)",
		helpURL = HelpURL,
	)
	trailRangeWdg.pack(side="left")
	
	RO.Wdg.StrLabel(rangeFrame, text='" =').pack(side = "left")

	trailRangePercentWdg = RO.Wdg.FloatLabel (
		master = rangeFrame,
		precision = 0,
		width = 6,
		helpText = "Length of trail as % of length of DEFAULT slit",
		helpURL = HelpURL,
	)
	trailRangePercentWdg.pack(side = "left")
	
	RO.Wdg.StrLabel(rangeFrame, text="%").pack(side = "left")
	
	g_expWdg.gridder.gridWdg("Trail Length", rangeFrame, colSpan = 2, sticky="w")
	
	# trail speed
	speedFrame = Tkinter.Frame(g_expWdg)

	trailSpeedWdg = RO.Wdg.FloatLabel (
		master = speedFrame,
		precision = 1,
		width = 6,
		helpText = "Speed of trailing",
		helpURL = HelpURL,
	)
	trailSpeedWdg.pack(side = "left")
	RO.Wdg.StrLabel(speedFrame, text = '"/sec').pack(side = "left")

	g_expWdg.gridder.gridWdg("Trail Speed", speedFrame)
	
	g_expWdg.gridder.allGridded()
	
	g_trailSpeedOK = True
	
	# function of compute trail range in " and trail speed
	# and set g_trailSpeedOK
	def updateRange(*args):
		global g_numTrails, g_trailRangeAS, g_trailSpeedAS, g_trailSpeedOK
		g_trailRangeAS = trailRangeWdg.getNum()
		trailRangePercentWdg.set(g_trailRangeAS * 100.0 / SlitLengthAS)
		g_numTrails = numTrailsWdg.getNum()

		expTime = g_expWdg.timeWdg.getNum()
		if not expTime:
			g_trailSpeedAS = None
			g_trailSpeedOK = False
			trailSpeedWdg.set(g_trailSpeedAS, isCurrent=False)
			return

		g_trailSpeedAS = abs(g_numTrails * g_trailRangeAS / expTime)
		g_trailSpeedOK = (g_trailSpeedAS <= MaxVelAS)
		
		if g_trailSpeedOK:
			velState = RO.Constants.st_Normal
		else:
			velState = RO.Constants.st_Error

		trailSpeedWdg.set(g_trailSpeedAS, state = velState)
	
	numTrailsWdg.addCallback(updateRange)
	trailRangeWdg.addCallback(updateRange)
	g_expWdg.timeWdg.addCallback(updateRange, callNow=True)


def run(sr):
	"""Take one or more exposures while moving the object
	back and forth along the slit.
	"""
	global InstName, g_expModel, g_tccModel
	global g_numTrails, g_trailRangeAS, g_trailSpeedAS, g_trailSpeedOK
	global g_begBoreXY, g_didMove
	global g_expWdg
	g_begBoreXY = [None, None]
	g_didMove = False

	# make sure the current instrument matches the desired instrument
	currInst = sr.getKeyVar(g_tccModel.instName)
	if InstName.lower() != currInst.lower():
		raise sr.ScriptError("%s is not the current instrument!" % InstName)
	
	# record the current boresight position (in a global area
	# so "end" can restore it).
	begBorePVTs = sr.getKeyVar(g_tccModel.boresight, ind=None)
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
	
	# get trail info and related info
	# time is in seconds
	# distance is in arcsec (AS suffix) or degrees (no suffix)
	expTime = g_expWdg.timeWdg.getNum()
	
	if not g_trailSpeedOK:
		raise sr.ScriptError("Trail speed invalid!")
		
	trailRange = g_trailRangeAS / RO.PhysConst.ArcSecPerDeg
	trailSpeed = g_trailSpeedAS / RO.PhysConst.ArcSecPerDeg
	
	# should probably check against axis limits
	# but for now let's assume the user has a clue...
	
	numExpWdg = g_expWdg.numExpWdg
	numExp = numExpWdg.getNum()
	if numExp <= 0:
		sr.showMsg("No exposures wanted, nothing done", 2)
	
	def getStartXY(trailRange, trailDir):
		global g_begBoreXY

		return (
			g_begBoreXY[0],
			g_begBoreXY[1] - (trailRange * trailDir / 2.0)
		)

	trailDir = 1

	# slew to start position
	sr.showMsg("Slewing to start position")
	startPosXY = getStartXY(trailRange, trailDir)
	tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
		(startPosXY[0], startPosXY[1])
#		print "sending tcc command %r" % tccCmdStr
	g_didMove = True
	yield sr.waitCmd(
		actor = "tcc",
		cmdStr = tccCmdStr,
	)
	
	for expNum in range(1, numExp + 1):
		isLast = (expNum >= numExp)

		expCycleStr = "exposure %d of %d" % (expNum, numExp)

		# expose
		sr.showMsg("Starting %s: wait for integration" % expCycleStr)
		expCmdStr = g_expWdg.getString(
			numExp = 1,
			startNum = expNum,
			totNum = numExp,
		)
#		print "sending %s command %r" % (InstName, expCmdStr)
		expCmdVar = sr.startCmd(
			actor = g_expModel.actor,
			cmdStr = expCmdStr,
			abortCmdStr = "abort",
		)
		
		if g_numTrails > 0:
			trailTime = expTime / g_numTrails
		else:
			trailTime = 0.0
		
		# wait for flushing to end and exposure to begin
		while True:
			yield sr.waitKeyVar(g_expModel.expState, ind=1, waitNext=True)
			if sr.value.lower() == "integrating":
				break
		
		# execute trails
		for trailNum in range(1, g_numTrails + 1):
			sr.showMsg("Trail %d of %d for %s" % (trailNum, g_numTrails, expCycleStr))
			startPosXY = getStartXY(trailRange, trailDir)
			tccCmdStr = "offset boresight %.7f, %.7f, 0, %.7f/pabs/vabs" % \
				(startPosXY[0], startPosXY[1], trailSpeed * trailDir)
	#		print "sending tcc command %r" % tccCmdStr
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
			
			yield sr.waitMS(trailTime * 1000.0)
			
			trailDir = -trailDir
		
		# wait for integration to end; be sure to examine
		# the current state in case the timing got messed up
		# and integration already finished
		while True:
			yield sr.waitKeyVar(g_expModel.expState, ind=1, waitNext=False)
			if sr.value.lower() != "integrating":
				break
		
		# slew to next position
		if not isLast:
			# slew to start position for next exposure
			sr.showMsg("Slewing to start pos. for next exposure")
			startPosXY = getStartXY(trailRange, trailDir)
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
				(startPosXY[0], startPosXY[1])
	#		print "sending tcc command %r" % tccCmdStr
			g_didMove = True
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
		else:
			sr.showMsg("Last exposure; slewing to initial position")
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(g_begBoreXY)
			g_didMove = False
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)

		# wait for exposure to end
		sr.showMsg("Waiting for %s to finish" % expCycleStr)
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
			
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(g_begBoreXY)
	#	print "sending tcc command %r" % tccCmdStr
		sr.startCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
