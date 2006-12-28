#!/usr/local/bin/python
"""Take NICFPS exposures in a square pattern plus a point in the middle.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select which portions of the chip to visit.

To do:
- Fail unless NICFPS is in imaging mode.

History:
2004-10-19 ROwen	first cut; direct copy of GRIM:Square
2005-01-24 ROwen	Changed order to ctr, UL, UR, LR, LL.
					Changed Offset Size to Box Size (2x as big)
					and made 20" the default box size.
					Modified to record dither points in advance
					(instead of allowing change 'on the fly').
					Renamed from Dither.py to Dither/Point Source.py
2006-04-20 ROwen	Changed to a class.
					Changed all offsets to /computed.
2006-04-27 ROwen	Bug fix: would try to run (but send bogus commands)
					if required exposure fields were blank.
					Added debug support.
2006-12-28 ROwen	Fix PR 515: modified to abort the exposure if the script is aborted.
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
HelpURL = "Scripts/BuiltInScripts/NICFPSDitherPointSource.html"

class ScriptClass(object):	
	def __init__(self, sr):
		"""The setup script; run once when the script runner
		window is created.
		"""
		# if sr.debug True, run in debug-only mode (which doesn't DO anything, it just pretends)
		sr.debug = False

		self.didMove = False
		self.tccModel = TUI.TCC.TCCModel.getModel()
		self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
	
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
		self.quadWdgSet = []
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
			
			self.quadWdgSet.append(wdg)
		
		quadFrame.grid(row=row, column=0, sticky="news")
		row += 1
	
		# standard exposure input widget
		self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
		self.expWdg.numExpWdg.helpText = "# of exposures at each point"
		self.expWdg.grid(row=row, column=0, sticky="news")
		row += 1
	
		self.boxSizeWdg = RO.Wdg.IntEntry(
			master = self.expWdg,
			minValue = 0,
			defValue = DefBoxSize,
			helpText = "size of dither box",
			helpURL = HelpURL,
		)
		self.expWdg.gridder.gridWdg("Box Size", self.boxSizeWdg, "arcsec")
	        
	def run(self, sr):
		"""Take an exposure sequence.
		"""
		self.didMove = False
	
		# get current NICFPS focal plane geometry from the TCC
		# but first make sure the current instrument
		# is actually NICFPS
		if not sr.debug:
			currInstName = sr.getKeyVar(self.tccModel.instName)
			if not currInstName.lower().startswith(InstName.lower()):
				raise sr.ScriptError("%s is not the current instrument!" % InstName)
	
		# record the current boresight position
		begBorePVTs = sr.getKeyVar(self.tccModel.boresight, ind=None)
		if not sr.debug:
			self.begBoreXY = [pvt.getPos() for pvt in begBorePVTs]
			if None in self.begBoreXY:
				raise sr.ScriptError("Current boresight position unknown")
		self.begBoreXY = [0.0, 0.0]
		#print "self.begBoreXY=%r" % self.begBoreXY
		
		# exposure command without startNum and totNum
		# get it now so that it will not change if the user messes
		# with the controls while the script is running
		numExp = self.expWdg.numExpWdg.getNum()
		expCmdPrefix = self.expWdg.getString()
		if not expCmdPrefix:
			raise sr.ScriptError("missing inputs")
		
		offsetSize =  self.boxSizeWdg.getNum() / 2.0
		
		# record which points to use in the dither pattern in advance
		# (rather than allowing the user to change it during execution)
		doPtArr = [wdg.getBool() for wdg in self.quadWdgSet]
		
		numExpTaken = 0
		numPtsToGo = sum(doPtArr)
		for ind in range(len(self.quadWdgSet)):
			wdg = self.quadWdgSet[ind]
			wdg["relief"] = "sunken"
			
			if not doPtArr[ind]:
				continue
				
			posName = str(wdg["text"])
			
			if ind > 0:
				# slew telescope
				sr.showMsg("Offset to %s position" % posName)
				borePosXY = [
					self.begBoreXY[0] + (wdg.boreOffMult[0] * (offsetSize / 3600.0)),
					self.begBoreXY[1] + (wdg.boreOffMult[1] * (offsetSize / 3600.0)),
				]
				self.didMove = True
				
				yield sr.waitCmd(
					actor = "tcc",
					cmdStr = "offset boresight %.6f, %.6f/pabs/computed" % (borePosXY[0], borePosXY[1]),
				)
				
			# compute # of exposures & format expose command
			totNum = numExpTaken + (numPtsToGo * numExp)
			startNum = numExpTaken + 1
			
			expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNum)
			
			# take exposure sequence
			sr.showMsg("Expose at %s position" % posName)
			yield sr.waitCmd(
				actor = self.expModel.actor,
				cmdStr = expCmdStr,
				abortCmdStr = "abort",
			)
	
			numExpTaken += numExp
			numPtsToGo -= 1
		
		# slew back to starting position
		if self.didMove:
			sr.showMsg("Finishing up: slewing to initial position")
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begBoreXY)
			self.didMove = False
			yield sr.waitCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
			
	def end(self, sr):
		"""If telescope moved, restore original boresight position.
		"""
		for wdg in self.quadWdgSet:
			wdg["relief"] = "flat"
		
		#print "end called"
		if self.didMove:
			# restore original boresight position
			if None in self.begBoreXY:
				return
				
			tccCmdStr = "offset boresight %.7f, %.7f/pabs/vabs/computed" % tuple(self.begBoreXY)
			#print "sending tcc command %r" % tccCmdStr
			sr.startCmd(
				actor = "tcc",
				cmdStr = tccCmdStr,
			)
	
