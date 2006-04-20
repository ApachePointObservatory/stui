"""Script to trail along the Echelle slit during an exposure.

To do:
- When the hub supports it, get the slit length from the hub.

History:
2004-10-01 ROwen
2005-01-05 ROwen	Modified for RO.Wdg.Label state -> severity.
2006-04-19 ROwen	Changed to a class.
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

class ScriptClass(object):
	def __init__(self, sr):
		"""Set up widgets to set input exposure time,
		trail cycles and trail range and display trail speed.
		"""
		self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
		self.tccModel = TUI.TCC.TCCModel.getModel()
		
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
		self.expWdg = TUI.Inst.ExposeInputWdg.ExposeInputWdg(sr.master, InstName, expTypes="object")
		self.expWdg.numExpWdg.helpText = "# of exposures at each point"
		self.expWdg.grid(row=row, column=0, sticky="news")
		row += 1
		
		# add some controls to the exposure input widget
		
		# number of moves
		numTrailsWdg = RO.Wdg.IntEntry (
			master = self.expWdg,
			minValue = 0,
			maxValue = 99,
			defValue = 5,
			width = 6,
			helpText = "Number of trails (2 is up, then down)",
			helpURL = HelpURL,
		)
		self.expWdg.gridder.gridWdg("# of Trails", numTrailsWdg)
		
		# trail range
		rangeFrame = Tkinter.Frame(self.expWdg)
	
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
		
		self.expWdg.gridder.gridWdg("Trail Length", rangeFrame, colSpan = 2, sticky="w")
		
		# trail speed
		speedFrame = Tkinter.Frame(self.expWdg)
	
		trailSpeedWdg = RO.Wdg.FloatLabel (
			master = speedFrame,
			precision = 1,
			width = 6,
			helpText = "Speed of trailing",
			helpURL = HelpURL,
		)
		trailSpeedWdg.pack(side = "left")
		RO.Wdg.StrLabel(speedFrame, text = '"/sec').pack(side = "left")
	
		self.expWdg.gridder.gridWdg("Trail Speed", speedFrame)
		
		self.expWdg.gridder.allGridded()
		
		self.trailSpeedOK = True
		
		# function of compute trail range in " and trail speed
		# and set self.trailSpeedOK
		def updateRange(*args):
			self.trailRangeAS = trailRangeWdg.getNum()
			trailRangePercentWdg.set(self.trailRangeAS * 100.0 / SlitLengthAS)
			self.numTrails = numTrailsWdg.getNum()
	
			expTime = self.expWdg.timeWdg.getNum()
			if not expTime:
				self.trailSpeedAS = None
				self.trailSpeedOK = False
				trailSpeedWdg.set(self.trailSpeedAS, isCurrent=False)
				return
	
			self.trailSpeedAS = abs(self.numTrails * self.trailRangeAS / expTime)
			self.trailSpeedOK = (self.trailSpeedAS <= MaxVelAS)
			
			if self.trailSpeedOK:
				severity = RO.Constants.sevNormal
			else:
				severity = RO.Constants.sevError
	
			trailSpeedWdg.set(self.trailSpeedAS, severity = severity)
		
		numTrailsWdg.addCallback(updateRange)
		trailRangeWdg.addCallback(updateRange)
		self.expWdg.timeWdg.addCallback(updateRange, callNow=True)
	
		
	def getStartXY(self, trailRange, trailDir):
		return (
			self.begBoreXY[0],
			self.begBoreXY[1] - (trailRange * trailDir / 2.0)
		)
	
	def run(self, sr):
		"""Take one or more exposures while moving the object
		back and forth along the slit.
		"""
		self.begBoreXY = [None, None]
		self.didMove = False
	
		# make sure the current instrument matches the desired instrument
		currInst = sr.getKeyVar(self.tccModel.instName)
		if InstName.lower() != currInst.lower():
			raise sr.ScriptError("%s is not the current instrument!" % InstName)
		
		# record the current boresight position
		begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
		self.begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
		if None in self.begBoreXY:
			raise sr.ScriptError("Current boresight position unknown")
	#	print "self.begBoreXY=%r" % self.begBoreXY
		
		# sanity check exposure inputs
		# (will raise an exception if no expTime or file name)
		try:
			self.expWdg.getString()
		except Exception, e:
			raise sr.ScriptError(str(e))
		
		# get trail info and related info
		# time is in seconds
		# distance is in arcsec (AS suffix) or degrees (no suffix)
		expTime = self.expWdg.timeWdg.getNum()
		
		if not self.trailSpeedOK:
			raise sr.ScriptError("Trail speed invalid!")
			
		trailRange = self.trailRangeAS / RO.PhysConst.ArcSecPerDeg
		trailSpeed = self.trailSpeedAS / RO.PhysConst.ArcSecPerDeg
		
		# should probably check against axis limits
		# but for now let's assume the user has a clue...
		
		numExpWdg = self.expWdg.numExpWdg
		numExp = numExpWdg.getNum()
		if numExp <= 0:
			sr.showMsg("No exposures wanted, nothing done", 2)
	
		trailDir = 1
	
		# slew to start position
		sr.showMsg("Slewing to start position")
		startPosXY = self.getStartXY(trailRange, trailDir)
		tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
			(startPosXY[0], startPosXY[1])
	#		print "sending tcc command %r" % tccCmdStr
		self.didMove = True
		yield sr.waitCmd(
			actor = "tcc",
			cmdStr = tccCmdStr,
		)
		
		for expNum in range(1, numExp + 1):
			isLast = (expNum >= numExp)
	
			expCycleStr = "exposure %d of %d" % (expNum, numExp)
	
			# expose
			sr.showMsg("Starting %s: wait for integration" % expCycleStr)
			expCmdStr = self.expWdg.getString(
				numExp = 1,
				startNum = expNum,
				totNum = numExp,
			)
	#		print "sending %s command %r" % (InstName, expCmdStr)
			expCmdVar = sr.startCmd(
				actor = self.expModel.actor,
				cmdStr = expCmdStr,
				abortCmdStr = "abort",
			)
			
			if self.numTrails > 0:
				trailTime = expTime / self.numTrails
			else:
				trailTime = 0.0
			
			# wait for flushing to end and exposure to begin
			while True:
				yield sr.waitKeyVar(self.expModel.expState, ind=1, waitNext=True)
				if sr.value.lower() == "integrating":
					break
			
			# execute trails
			for trailNum in range(1, self.numTrails + 1):
				sr.showMsg("Trail %d of %d for %s" % (trailNum, self.numTrails, expCycleStr))
				startPosXY = self.getStartXY(trailRange, trailDir)
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
				yield sr.waitKeyVar(self.expModel.expState, ind=1, waitNext=False)
				if sr.value.lower() != "integrating":
					break
			
			# slew to next position
			if not isLast:
				# slew to start position for next exposure
				sr.showMsg("Slewing to start pos. for next exposure")
				startPosXY = self.getStartXY(trailRange, trailDir)
				tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % \
					(startPosXY[0], startPosXY[1])
		#		print "sending tcc command %r" % tccCmdStr
				self.didMove = True
				yield sr.waitCmd(
					actor = "tcc",
					cmdStr = tccCmdStr,
				)
			else:
				sr.showMsg("Last exposure; slewing to initial position")
				tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begBoreXY)
				self.didMove = False
				yield sr.waitCmd(
					actor = "tcc",
					cmdStr = tccCmdStr,
				)
	
			# wait for exposure to end
			sr.showMsg("Waiting for %s to finish" % expCycleStr)
			yield sr.waitCmdVars(expCmdVar)
	
			
	def end(self, sr):
		"""If telescope moved, restore original boresight position.
		"""
	#	print "end called"
		if self.didMove:
			# restore original boresight position
	# the following is commented out because it is not displayed anyway
	#		sr.showMsg("Done: slewing to original boresight")
			if None in self.begBoreXY:
				return
				
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begBoreXY)
		#	print "sending tcc command %r" % tccCmdStr
			sr.startCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
