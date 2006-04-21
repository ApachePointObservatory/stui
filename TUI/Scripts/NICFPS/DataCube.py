#!/usr/local/bin/python
"""Take a NICFPS spectral data cube.

This script imports the standard NICFPS exposure widget
to allow the user to configure standard exposure options.
It also adds a few additional widgets that allow
the user to select the etalon range and number of steps.

The data cube is taken in two interleaved passes
to cover the full desired range of wavelengths.
It is trivial to add an input for # of passes
(use a widget to set numPasses in run;
but be sure to deal with this GUI issue:
what to do if the user asks for fewer steps than passes).

History:
2004-10-22 ROwen
2004-11-16 ROwen	Changed units of Z from um to steps.
2004-12-16 ROwen	Added widgets for initial and current index
					and number of passes.
					Modified to compute final Z and to report
					missing or invalid entries more clearly.
2005-01-18 ROwen	Bug fix: fp setz command missing an =.
2006-04-21 ROwen	Changed to a class.
"""
import RO.Wdg
import TUI.TCC.TCCModel
import TUI.Inst.ExposeModel
import TUI.Inst.NICFPS.NICFPSModel
from TUI.Inst.ExposeStatusWdg import ExposeStatusWdg
from TUI.Inst.ExposeInputWdg import ExposeInputWdg

# constants
InstName = "NICFPS"
HelpURL = "Scripts/BuiltInScripts/NICFPSDataCube.html"

SpacingWidth = 8

class ScriptClass(object):	
	def __init__(self, sr):
		"""Create widgets.
		"""
		self.errStr = ""
		sr.debug = False
		
		self.nicfpsModel = TUI.Inst.NICFPS.NICFPSModel.getModel()
		self.expModel = TUI.Inst.ExposeModel.getModel(InstName)
		self.tccModel = TUI.TCC.TCCModel.getModel()

		row=0
		
		# standard exposure status widget
		expStatusWdg = ExposeStatusWdg(sr.master, InstName)
		expStatusWdg.grid(row=row, column=0, sticky="news")
		row += 1
	
		# standard exposure input widget
		self.expWdg = ExposeInputWdg(sr.master, InstName, expTypes="object")
		self.expWdg.numExpWdg.helpText = "# of exposures at each spacing"
		self.expWdg.grid(row=row, column=0, sticky="news")
		row += 1
		
		gr = self.expWdg.gridder
			
		# add etalon controls to exposure input widget
		self.begSeqIndWdg = RO.Wdg.IntEntry(
			master = self.expWdg,
			minValue = 0,
			width = SpacingWidth,
			helpText = "initial z index (to finish a partial run)",
			helpURL = HelpURL,
		)
		gr.gridWdg("Initial Index", self.begSeqIndWdg, "(normally leave blank)")
	
		self.fpBegZWdg = RO.Wdg.IntEntry(
			master = self.expWdg,
			minValue = self.nicfpsModel.fpXYZLimConst[0],
			maxValue = self.nicfpsModel.fpXYZLimConst[1],
			width = SpacingWidth,
			helpText = "initial etalon Z spacing",
			helpURL = HelpURL,
		)
		gr.gridWdg("Initial Z", self.fpBegZWdg, "steps")
	
		self.fpDeltaZWdg = RO.Wdg.IntEntry(
			master = self.expWdg,
			minValue = self.nicfpsModel.fpXYZLimConst[0],
			maxValue = self.nicfpsModel.fpXYZLimConst[1],
			width = SpacingWidth,
			helpText = "etalon Z spacing interval",
			helpURL = HelpURL,
		)
		gr.gridWdg("Delta Z", self.fpDeltaZWdg, "steps")
		
		self.fpNumZWdg = RO.Wdg.IntEntry(
			master = self.expWdg,
			minValue = 1,
			maxValue = 9999,
			width = SpacingWidth,
			helpText = "number of etalon Z spacings",
			helpURL = HelpURL,
		)
		gr.gridWdg("Num Zs", self.fpNumZWdg, "steps")
		
		self.fpEndZWdg = RO.Wdg.IntLabel(
			master = self.expWdg,
			width = SpacingWidth,
			helpText = "final etalon Z spacing",
			helpURL = HelpURL,
			anchor = "e",
		)
		self.fpEndZUnitsWdg = RO.Wdg.StrLabel(
			master = self.expWdg,
			text = "steps",
			helpURL = HelpURL,
			anchor = "w",
		)
		gr.gridWdg("Final Z", self.fpEndZWdg, self.fpEndZUnitsWdg)
		
		self.fpNumPassesWdg = RO.Wdg.OptionMenu(
			master = self.expWdg,
			items = ("1", "2", "3"),
			defValue = "2",
			helpText = "number of passes in which to sample Z",
			helpURL = HelpURL,
		)
		gr.gridWdg("Num Passes", self.fpNumPassesWdg)
		
		self.currSeqIndWdg = RO.Wdg.IntLabel(
			master = self.expWdg,
			width = SpacingWidth,
			helpText = "index of current Z spacing",
			helpURL = HelpURL,
			anchor = "e",
		)
		gr.gridWdg("Current Index", self.currSeqIndWdg)
		
		fpCurrWdg = RO.Wdg.IntLabel(
			master = self.expWdg,
			width = SpacingWidth,
			helpText = "current actual etalon Z spacing",
			helpURL = HelpURL,
			anchor = "e",
		)
		gr.gridWdg("Current Z", fpCurrWdg, "steps")
		
		self.nicfpsModel.fpZ.addROWdg(fpCurrWdg)
		
		self.fpBegZWdg.addCallback(self.updEndZ, callNow=False)
		self.fpDeltaZWdg.addCallback(self.updEndZ, callNow=False)
		self.fpNumZWdg.addCallback(self.updEndZ, callNow=True)

	def updEndZ(self, *args, **kargs):
		"""Call when beg Z, delta Z or num Z changed to update end Z.
		"""
		begSpacing = self.fpBegZWdg.getNum()
		numSpacings = self.fpNumZWdg.getNum()
		deltaZ = self.fpDeltaZWdg.getNum()
		
		endZ = None
		self.errStr = ""
		if not self.fpBegZWdg.getString():
			self.errStr = "specify initial Z"
		elif not self.fpDeltaZWdg.getString():
			self.errStr = "specify delta z"
		elif numSpacings == 0:
			self.errStr = "specify number of zs"
		else:
			endZ = begSpacing + (deltaZ * (numSpacings - 1))
			isCurrent = True
			
			# check range
			minZ, maxZ = self.nicfpsModel.fpXYZLimConst
			if endZ < minZ:
				self.errStr = "final Z < %s" % minZ
			elif endZ > maxZ:
				self.errStr = "final Z > %s" % maxZ

		if self.errStr:
			isCurrent = False
			self.fpEndZUnitsWdg.set("error: %s" % self.errStr, isCurrent=isCurrent)
		else:
			isCurrent = True
			self.fpEndZUnitsWdg.set("steps", isCurrent=isCurrent)
		
		self.fpEndZWdg.set(endZ, isCurrent = isCurrent)
		
	def run(self, sr):
		"""Take an exposure sequence.
		"""
		# get current NICFPS focal plane geometry from the TCC
		# but first make sure the current instrument
		# is actually NICFPS
		self.errStr = ""
	
		if not sr.debug:
			currInstName = sr.getKeyVar(self.tccModel.instName)
			if not currInstName.lower().startswith(InstName.lower()):
				raise sr.ScriptError("%s is not the current instrument!" % InstName)
		
		# exposure command without startNum and totNum
		# get it now so that it will not change if the user messes
		# with the controls while the script is running
		numExp = self.expWdg.numExpWdg.getNum()
		expCmdPrefix = self.expWdg.getString()
		if not expCmdPrefix:
			return
		
		if self.errStr:
			raise sr.ScriptError(self.errStr)
		
		# get user data in advance
		begSeqInd = self.begSeqIndWdg.getNum()
		begSpacing = self.fpBegZWdg.getNum()
		numSpacings = self.fpNumZWdg.getNum()
		deltaZ = self.fpDeltaZWdg.getNum()
		numPasses = int(self.fpNumPassesWdg.getString())
	
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
			
			self.currSeqIndWdg.set(seqInd)
			
			# command etalon spacing
			sr.showMsg("Set etalon Z = %d %s" % (currSpacing, "steps"))
			yield sr.waitCmd(
				actor = self.nicfpsModel.actor,
				cmdStr = "fp setz=%d" % (currSpacing,),
			)
	
			# compute # of exposures & format expose command
			startNum = seqInd * numExp
			expCmdStr = "%s startNum=%d totNum=%d" % (expCmdPrefix, startNum, totNumExp)
			
			# take exposure sequence
			sr.showMsg("Expose at etalon Z = %d %s" % (currSpacing, "steps"))
			yield sr.waitCmd(
				actor = self.expModel.actor,
				cmdStr = expCmdStr,
			)
