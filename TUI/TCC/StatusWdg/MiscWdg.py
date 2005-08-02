#!/usr/local/bin/python
"""Displays time, airmass, instrument name, focus...

History:
2003-03-26 ROwen	Modified to use the tcc model.
2003-03-31 ROwen	Switched from RO.Wdg.LabelledWdg to RO.Wdg.Gridder.
2003-04-24 ROwen	Modified to use Gridder startNewCol.
2003-06-09 Rowen	Removed dispatcher arg.
2003-06-12 ROwen	Added helpText entries.
2003-06-25 ROwen	Modified test case to handle message data as a dict
2003-10-29 ROwen	Modified to accommodate moved TelConst.
2003-12-03 ROwen	Added guide status, including sound cues.
2004-02-04 ROwen	Modified _HelpURL to match minor help reorg.
2004-08-26 ROwen	Made the instrument name field wider (8->10).
2004-09-23 ROwen	Modified to allow callNow as the default for keyVars.
2005-06-07 ROwen	Disabled guide state display (until I figure out how
					to make it work with the new guide system).
2005-06-10 ROwen	Rewrote guide state display to work with new guide system.
2005-06-15 ROwen	Updated for guide model change guiding->guideState.
2005-08-02 ROwen	Modified for TUI.Sounds->TUI.PlaySound.
"""
import time
import Tkinter
import RO.Astro.Tm
import RO.Astro.Sph
import RO.PhysConst
import RO.StringUtil
import RO.Wdg
import TUI.PlaySound
import TUI.TCC.TelConst
import TUI.TCC.TCCModel
import TUI.Guide.GuideModel

# add instrument angles

_HelpPrefix = "Telescope/StatusWin.html#"

class MiscWdg (Tkinter.Frame):
	def __init__ (self, master=None, **kargs):
		"""Displays miscellaneous information, such as current time and az/alt

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		self.model = TUI.TCC.TCCModel.getModel()
		gr = RO.Wdg.Gridder(self, sticky="e")

		# magic numbers
		AzAltRotPrec = 1	# number of digits past decimal point
		
		self.haWdg = RO.Wdg.DMSLabel(self,
			precision = 0,
			nFields = 3,
			cvtDegToHrs = 1,
			width = 8,
			helpText = "Hour angle of the object",
			helpURL = _HelpPrefix + "HA",
		)
		gr.gridWdg (
			label = "HA",
			dataWdg = self.haWdg,
			units = "hms",
		)
		
		self.lmstWdg = RO.Wdg.DMSLabel(self,
			precision = 0,
			nFields = 3,
			width = 8,
			justify="right",
			helpText = "Local mean sidereal time",
			helpURL = _HelpPrefix + "LMST",
		)
		gr.gridWdg (
			label = "LMST",
			dataWdg = self.lmstWdg,
			units = "hms",
		)
		
		self.utcWdg = RO.Wdg.StrLabel(self,
			width=8,
			helpText = "Coordinated universal time",
			helpURL = _HelpPrefix + "UTC",
		)
		gr.gridWdg (
			label = "UTC",
			dataWdg = self.utcWdg,
			units = "hms",
		)
		
		# start the second column of widgets
		gr.startNewCol(spacing=1)
		
		self.guideWdg = RO.Wdg.StrLabel(self,
			width = 3,
			anchor = "w",
			helpText = "State of guiding",
			helpURL = _HelpPrefix + "Guiding",
		)
		gr.gridWdg (
			label = "Guiding",
			dataWdg = self.guideWdg,
			colSpan = 2,
			units = False,
			sticky = "ew",
		)
		self.guideKeyVars = []
		for guideModel in TUI.Guide.GuideModel.modelIter():
			self.guideKeyVars.append(guideModel.guideState)
			guideModel.guideState.addIndexedCallback(self._updGuideState)

		# airmass and zenith distance
		self.airmassWdg = RO.Wdg.FloatLabel(self,
			precision=3,
			width=5,
			helpURL = _HelpPrefix + "Airmass",
		)
		gr.gridWdg (
			label = "Airmass",
			dataWdg = self.airmassWdg,
			units = "",
		)
#		self.model.axePos.addCallback(self.setAxePos)
		
		self.zdWdg = RO.Wdg.FloatLabel(self,
			precision=AzAltRotPrec,
			helpText = "Zenith distance",
			helpURL = _HelpPrefix + "ZD",
			width=5,
		)
		gr.gridWdg (
			label = "ZD",
			dataWdg = self.zdWdg,
			units = RO.StringUtil.DegStr,
		)
		
		# start the third column of widgets
		gr.startNewCol(spacing=1)
		
		self.instNameWdg = RO.Wdg.StrLabel(self,
			width = 10,
			anchor = "w",
			helpText = "Current instrument",
			helpURL = _HelpPrefix + "Inst",
		)
		gr.gridWdg (
			label = "Inst",
			dataWdg = self.instNameWdg,
			colSpan = 3,
			units = False,
			sticky = "w",
		)
		self.model.instName.addROWdg(self.instNameWdg)
		
		self.secFocusWdg = RO.Wdg.FloatLabel(self,
			precision=0,
			width=5,
			helpText = "Secondary mirror focus offset",
			helpURL = _HelpPrefix + "Focus",
		)
		gr.gridWdg (
			label = "Focus",
			dataWdg = self.secFocusWdg,
			units = u"\N{MICRO SIGN}m",
		)
		self.model.secFocus.addROWdg(self.secFocusWdg)
		
		self.gcFocusWdg = RO.Wdg.FloatLabel(self,
			precision=0,
			width=5,
			helpText = "Guide camera focus offset",
			helpURL = _HelpPrefix + "GCFocus",
		)
		gr.gridWdg (
			label = "GC Focus",
			dataWdg = self.gcFocusWdg,
			units = u"\N{MICRO SIGN}m",
		)
		self.model.gcFocus.addROWdg(self.gcFocusWdg)
		
		# all widgets are gridded
		gr.allGridded()
		
		# add callbacks that deal with multiple widgets
		self.model.axePos.addCallback(self.setAxePos)
		
		# start clock updates		
		self.updateClock()
		
		# allow the last+1 column to grow to fill the available space
		self.columnconfigure(gr.getMaxNextCol(), weight=1)

	
	def updateClock(self):
		"""Automatically update the time displays in this widget.
		Call once to get things going
		"""
		# update utc
		currUTCTuple= time.gmtime(time.time())
		self.utcWdg.set("%s:%02i:%02i" % currUTCTuple[3:6])
		currUTCMJD = RO.Astro.Tm.mjdFromPyTuple(currUTCTuple)
	
		# update local (at APO) mean sidereal time, in degrees
		currLMST = RO.Astro.Tm.lmstFromUT1(currUTCMJD, TUI.TCC.TelConst.Longitude) * RO.PhysConst.HrsPerDeg
		self.lmstWdg.set(currLMST)
		
		# schedule the next event
		self.after (1000, self.updateClock)
	
	def setAxePos(self, axePos, isCurrent=True, keyVar=None):
		"""Updates ha, dec, zenith distance and airmass
		axePos values are: (az, alt, rot)
		"""
		az, alt = axePos[0:2]

		if alt != None:
			airmass = RO.Astro.Sph.airmass(alt)
			zd = 90.0 - alt
		else:
			airmass = None
			zd = None
		
		# set zd, airmass widgets
		self.zdWdg.set(zd, isCurrent=isCurrent)
		self.airmassWdg.set(airmass, isCurrent=isCurrent)
		
		# set hour angle (set in degrees, display in hours)
		try:
			(ha, dec), atPole = RO.Astro.Sph.haDecFromAzAlt((az, alt), TUI.TCC.TelConst.Latitude)
			if atPole:
				ha = None
		except (TypeError, ValueError):
			ha = None
		self.haWdg.set(ha, isCurrent=isCurrent)
	
	def _updGuideState(self, *args, **kargs):
		"""Check state of all guiders.
		Display "best" state as follows:
		- is current and not off
		- is current and off
		- not current and not off
		- not current and off
		"""
		stateInfo = [] # is not off, is current, state for each actor
		for keyVar in self.guideKeyVars:
			state, isCurr = keyVar.getInd(0)
			notOff = state != None and state.lower() != "off"
			stateInfo.append((isCurr, notOff, state))
		stateInfo.sort()
		bestCurr, bestNotOff, bestState = stateInfo[-1]
		self.guideWdg.set(bestState, isCurrent = bestCurr)

if __name__ == "__main__":
	import TUI.TUIModel

	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher
		
	testFrame = MiscWdg (root)
	testFrame.pack()

	dataDict = {
		"AxePos": (-350.999, 45, "NaN"),
		"SecFocus": (570,),
		"GCFocus": (-300,),
		"Inst": ("DIS",),
		"TCCStatus": ("TTT", "NNN"),
	}
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}

	kd.dispatch(msgDict)

	root.mainloop()
