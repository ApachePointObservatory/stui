#!/usr/local/bin/python
from __future__ import generators
"""Configuration input panel for the Echelle.

To do:
- when first starting up, the state of the config widgets
is unknown, so show blank (pink) instead of guessing
values.

Special logic:
- If the cal mirror is removed, both lamps are turned off
  (but they can be turned on again).
- If one lamp is turned on, then the other lamp is turned off
  (and there is no override).
  
History:
2003-12-09 ROwen
2003-12-19 ROwen	Modified to use RO.Wdg.BoolLabel for status.
2004-05-18 ROwen	Removed constant _MaxDataWidth; it wasn't used.
2004-09-23 ROwen	Modified to allow callNow as the default for keyVars.
2005-01-04 ROwen	Modified to use autoIsCurrent for input widgets.
"""
import Tkinter
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import EchelleModel

_HelpPrefix = "Instruments/Echelle/EchelleWin.html#"

_StatusWidth = 6	# width of status labels

# category names
_ConfigCat = "config"

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to show status for and configure the Dual Imaging Spectrograph
		"""
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		self.model = EchelleModel.getModel()

		self._doingLampCallback = False
		
		# save old state of user widgets so special button logic
		# is only appied when the state actually changes
		# (rather than for every time the associated keywords are seen)
		# note: it might be better to implement this logic in the Checkbutton itself
		self._oldLampTOn = None
		self._oldLampWOn = None
		self._oldCalMirrorIn = None

		gr = RO.Wdg.StatusConfigGridder(
			master = self,
			sticky = "w",
			clearMenu = None,
			defMenu = "Current",
		)
		self.gridder = gr
		
		calMirrorWdg = RO.Wdg.BoolLabel(self,
			trueValue = "Calib",
			falseValue = "Object",
			width = _StatusWidth,
			anchor = "w",
			helpText = "Current state of calibraton mirror",
			helpURL = _HelpPrefix + "calMirror",
		)
		self.model.calMirror.addROWdg(calMirrorWdg)
		
		self.calMirrorUserWdg = RO.Wdg.Checkbutton(self,
			onvalue = "Calib",
			offvalue = "Object",
			showValue = True,
			helpText = "Desired state of calibraton mirror",
			helpURL = _HelpPrefix + "calMirror",
			autoIsCurrent = True,
		)
		self.model.calMirror.addROWdg(self.calMirrorUserWdg, setDefault=True)
		
		gr.gridWdg (
			label = "Cal Mirror",
			dataWdg = calMirrorWdg,
			units = False,
			cfgWdg = self.calMirrorUserWdg,
		)


		lampTWdg = RO.Wdg.BoolLabel(self,
			trueValue = "On",
			falseValue = "Off",
			width = _StatusWidth,
			anchor = "w",
			helpText = "Current state of Th/Ar calibration lamp",
			helpURL = _HelpPrefix + "lampT",
		)
		self.model.lampT.addROWdg(lampTWdg)
		
		self.lampTUserWdg = RO.Wdg.Checkbutton(self,
			onvalue = "On",
			offvalue = "Off",
			showValue = True,
			callFunc = self.doLampT,
			helpText = "Desired state of Th/Ar calibration lamp",
			helpURL = _HelpPrefix + "lampT",
			autoIsCurrent = True,
		)
		self.model.lampT.addROWdg(self.lampTUserWdg, setDefault=True)
		
		gr.gridWdg (
			label = "Th/Ar Lamp",
			dataWdg = lampTWdg,
			units = False,
			cfgWdg = self.lampTUserWdg,
		)


		lampWWdg = RO.Wdg.BoolLabel(self,
			trueValue = "On",
			falseValue = "Off",
			width = _StatusWidth,
			anchor = "w",
			helpText = "Current state of white calibration lamp",
			helpURL = _HelpPrefix + "lampW",
		)
		self.model.lampW.addROWdg(lampWWdg)
		
		self.lampWUserWdg = RO.Wdg.Checkbutton(self,
			onvalue = "On",
			offvalue = "Off",
			showValue = True,
			callFunc = self.doLampW,
			helpText = "Desired state of white calibration lamp",
			helpURL = _HelpPrefix + "lampW",
			autoIsCurrent = True,
		)
		self.model.lampW.addROWdg(self.lampWUserWdg, setDefault=True)
		
		gr.gridWdg (
			label = "White Lamp",
			dataWdg = lampWWdg,
			units = False,
			cfgWdg = self.lampWUserWdg,
		)


		filterNames = self.model.filterNames.get()[0]
		filtWidth = _StatusWidth
		for fn in filterNames:
			filtWidth = max(filtWidth, len(fn))
		filterCurrWdg = RO.Wdg.StrLabel(self,
			width = filtWidth,
			anchor = "w",
			helpText = "Current filter (blue or none)",
			helpURL=_HelpPrefix + "filter",
		)
		self.model.filterName.addROWdg(filterCurrWdg, 0)

		self.filterUserWdg = RO.Wdg.OptionMenu(self,
			items = filterNames,
			helpText = "Desired filter (blue or none)",
			helpURL = _HelpPrefix + "filter",
			autoIsCurrent = True,
		)
		gr.gridWdg (
			label = "Filter",
			dataWdg = filterCurrWdg,
			units = False,
			cfgWdg = self.filterUserWdg,
		)
		
		gr.allGridded()

		# add callbacks that need multiple widgets present
		self.model.filterName.addIndexedCallback(self.filterUserWdg.setDefault, 0)
		self.calMirrorUserWdg.addCallback(self.doCalMirror, callNow = True)

		def lampFmt(inputCont):
			currValueList = inputCont.getValueList()
			if not currValueList:
				return ""
			
			# isOff is "No" if lamp should be off, "" otherwise
			# lampID is the string representation of an integer
			isOff, lampID = currValueList[0].split(".")
			
			if isOff:
				return "lampOff: " + lampID
			else:
				return "lampOn: " + lampID
		
		def moveFmt(inputCont):
			NoMove = 1e6
			valList = inputCont.getValueList()
			defList = inputCont.getDefValueList()
			
			if valList == defList:
				# nothing to move
				return ""
			
			# convert 1st value to int and 2nd and 3rd values from names to IDs
			outList = [
				self.calMirrorUserWdg.asBool(valList[0]),
				self.filterUserWdg.getIndex(valList[1]) + 1,
			]
			
			# apply defaults
			for ind in range(2):
				if valList[ind] == defList[ind]:
					outList[ind] = NoMove

			# the 3rd motor (guide camera filter) is not moved by this window
			# and the 4th motor is never moved
			outList += [NoMove]*6

			return "move: %d %d %d %d %d %d %d %d 8" % tuple(outList)
			

		# set up the input container set; this is what formats the commands
		# and allows saving and recalling commands
		self.inputCont = RO.InputCont.ContList (
			conts = [
				RO.InputCont.BoolNegCont (
					name = "lampT",
					wdgNames = ".84", # lamp ID with leading period
					wdgs = self.lampTUserWdg,
					formatFunc = lampFmt,
				),
				RO.InputCont.BoolNegCont (
					name = "lampW",
					wdgNames = ".87", # lamp ID with leading period
					wdgs = self.lampWUserWdg,
					formatFunc = lampFmt,
				),
				RO.InputCont.WdgCont (
					name = "move:",
					wdgs = (
						self.calMirrorUserWdg,
						self.filterUserWdg,
					),
					omitDef = False,
					formatFunc = moveFmt,
				),
			],
		)

	def doCalMirror(self, *args):
		"""Called when the user toggles the cal filter control."""
		calMirrorIn = self.calMirrorUserWdg.getBool()
		if self._oldCalMirrorIn in (None, not calMirrorIn):
			# state has changed or was unknown
			if not calMirrorIn:
				self.lampWUserWdg.set(False)
				self.lampTUserWdg.set(False)
		self._oldCalMirrorIn = calMirrorIn
	
	def doLampT(self, *args):
		"""Called when user-set LampT control is toggled."""
		self._doingLampCallback = True
		try:
			lampTOn = self.lampTUserWdg.getBool()
			if self._oldLampTOn in (None, not lampTOn):
				# state has changed or was unknown
				if lampTOn:
					self.lampWUserWdg.set(False)
			self._oldLampTOn = lampTOn
		finally:
			self._doingLampCallback = False
	
	def doLampW(self, *args):
		"""Called when user-set LampW control is toggled."""
		self._doingLampCallback = True
		try:
			lampWOn = self.lampWUserWdg.getBool()
			if self._oldLampWOn in (None, not lampWOn):
				# state has changed or was unknown
				if lampWOn:
					self.lampTUserWdg.set(False)
			self._oldLampWOn = lampWOn
		finally:
			self._doingLampCallback = False


if __name__ == "__main__":
	root = RO.Wdg.PythonTk()

	import TestData
		
	testFrame = StatusConfigInputWdg (root)
	testFrame.pack()
	
	TestData.dispatch()
	
	testFrame.restoreDefault()

	def printCmds():
		print "Commands:"
		cmdList = testFrame.getStringList()
		for cmd in cmdList:
			print cmd
	
	bf = Tkinter.Frame(root)
	cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
	cfgWdg.pack(side="left")
	Tkinter.Button(bf, text="Cmds", command=printCmds).pack(side="left")
	Tkinter.Button(bf, text="Current", command=testFrame.restoreDefault).pack(side="left")
	Tkinter.Button(bf, text="Demo", command=TestData.animate).pack(side="left")
	bf.pack()

	testFrame.gridder.addShowHideControl(_ConfigCat, cfgWdg)

	root.mainloop()
