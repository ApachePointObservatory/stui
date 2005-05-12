#!/usr/local/bin/python
from __future__ import generators
"""Configuration input panel for the Echelle.

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
2005-05-12 ROwen	Modified for new Echelle ICC.
"""
import Tkinter
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import EchelleModel

_HelpPrefix = "Instruments/Echelle/EchelleWin.html#"

# category names
_ConfigCat = "config"
_LampPrefix = "lamp" # full lamp name has index appended, e.g. "lamp0".

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to show status for and configure the Dual Imaging Spectrograph
		"""
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		self.model = EchelleModel.getModel()
		
		mirLens = [len(name) for name in self.model.mirStatesConst]
		mirMaxNameLen = max(mirLens)

		gr = RO.Wdg.StatusConfigGridder(
			master = self,
			sticky = "",
			clearMenu = None,
			defMenu = "Current",
		)
		self.gridder = gr
		
		self.mirrorCurrWdg = RO.Wdg.StrLabel(
			master = self,
			width = mirMaxNameLen,
			anchor = "c",
			helpText = "Current state of calibration mirror",
			helpURL = _HelpPrefix + "mirror",
		)
		
		self.mirrorUserWdg = RO.Wdg.Checkbutton(
			master = self,
			offvalue = self.model.mirStatesConst[0].capitalize(),
			onvalue = self.model.mirStatesConst[1].capitalize(),
			showValue = True,
			width = mirMaxNameLen,
			helpText = "Desired state of calibration mirror",
			helpURL = _HelpPrefix + "mirror",
			autoIsCurrent = True,
		)
		
		gr.gridWdg (
			label = "Cal. Mirror",
			dataWdg = self.mirrorCurrWdg,
			units = False,
			cfgWdg = self.mirrorUserWdg,
		)
		
		self.lampNameWdgSet = []
		self.lampCurrWdgSet = []
		self.lampUserWdgSet = []
		for ii in range(self.model.numLamps):
			lampNameWdg = RO.Wdg.StrLabel(self)
								
			lampCurrWdg = RO.Wdg.BoolLabel(
				master = self,
				trueValue = "On",
				falseValue = "Off",
				width = 3,
				anchor = "c",
				helpURL = _HelpPrefix + "lamps",
			)
			
			lampUserWdg = RO.Wdg.Checkbutton(
				master = self,
				onvalue = "On",
				offvalue = "Off",
				width = 3,
				showValue = True,
				helpURL = _HelpPrefix + "lamps",
				autoIsCurrent = True,
			)
			gr.gridWdg (
				label = lampNameWdg,
				dataWdg = lampCurrWdg,
				units = False,
				cfgWdg = lampUserWdg,
				cat = _LampPrefix + str(ii),
			)

			self.lampNameWdgSet.append(lampNameWdg)
			self.lampCurrWdgSet.append(lampCurrWdg)
			self.lampUserWdgSet.append(lampUserWdg)

		self.calFilterCurrWdg = RO.Wdg.StrLabel(
			master = self,
			width = 4,
			anchor = "c",
			helpText = "Current calibration lamp filter",
			helpURL=_HelpPrefix + "filter",
		)
		self.model.calFilter.addROWdg(self.calFilterCurrWdg)

		self.calFilterUserWdg = RO.Wdg.OptionMenu(
			master = self,
			items = [],
			helpText = "Desired calibration lamp filter",
			helpURL = _HelpPrefix + "filter",
			width = 4,
			autoIsCurrent = True,
			defMenu = "Default",
		)
		self.model.calFilterNames.addCallback(self.setCalFilterNames)
		self.model.calFilter.addROWdg(self.calFilterUserWdg, setDefault=True)
		
		gr.gridWdg (
			label = "Cal. Filter",
			dataWdg = self.calFilterCurrWdg,
			units = False,
			cfgWdg = self.calFilterUserWdg,
		)
		
		gr.allGridded()

		# add callbacks that need multiple widgets present
		self.model.mirror.addIndexedCallback(self.setMirrorState)
		self.model.lampNames.addCallback(self.setLampNames)
		self.model.lampStates.addCallback(self.setLampStates)
		for wdg in self.lampUserWdgSet:
			wdg.addCallback(self.doLamp, callNow=False)
		self.mirrorUserWdg.addCallback(self.doMirror, callNow=True)

		def lampValFmt(wdgVal):
			return str(int(wdgVal.lower() == "on"))

		# set up the input container set; this is what formats the commands
		# and allows saving and recalling commands
		self.inputCont = RO.InputCont.ContList (
			conts = [
				RO.InputCont.WdgCont (
					name = "mirror",
					wdgs = self.mirrorUserWdg,
					formatFunc = RO.InputCont.BasicFmt(
						valFmt=str.lower,
					),
				),
				RO.InputCont.WdgCont (
					name = "lamps",
					wdgs = self.lampUserWdgSet,
					formatFunc = RO.InputCont.BasicFmt(
						valFmt=lampValFmt,
						blankIfDisabled = False,
					),
				),
				RO.InputCont.WdgCont (
					name = "calfilter",
					wdgs = self.calFilterUserWdg,
					formatFunc = RO.InputCont.BasicFmt(),
				),
			],
		)

	def doMirror(self, *args):
		"""Called when the calibration mirror user control is toggled.
		
		If mirror out (instrument sees the sky, not the cal lamps)
		then turn off the cal lamps.
		"""
		if self.mirrorUserWdg.getBool():
			# mirror set to cal lamp position; do nothing
			self.mirrorUserWdg.setSeverity(RO.Constants.sevWarning)
			return
		self.mirrorUserWdg.setSeverity(RO.Constants.sevNormal)

		for lampUserWdg in self.lampUserWdgSet:
			if lampUserWdg.getBool():
				lampUserWdg.setBool(False)
	
	def doLamp(self, lampWdg):
		"""Called when a calibration lamp user control is toggled.
		
		If lamp control is on, then turn off the other lamps
		and set mirror to calibration position.
		"""
		if not lampWdg.getBool():
			lampWdg.setSeverity(RO.Constants.sevNormal)
			return
			
		for lampUserWdg in self.lampUserWdgSet:
			if (lampUserWdg is not lampWdg):
				if lampUserWdg.getBool():
					lampUserWdg.setBool(False, severity=RO.Constants.sevNormal)
			else:
				lampUserWdg.setSeverity(RO.Constants.sevWarning)
		self.mirrorUserWdg.setBool(True)
	
	def setCalFilterNames(self, filtNames, isCurrent, **kargs):
		nameList = [name for name in filtNames if name]
		self.calFilterUserWdg.setItems(nameList)

		if not nameList:
			return
		lenList = [len(name) for name in nameList]
		maxLen = max(lenList)
		self.calFilterCurrWdg["width"] = maxLen
		self.calFilterUserWdg["width"] = maxLen
		
	
	def setLampNames(self, lampNames, isCurrent, **kargs):
		"""Update lamp name labels and hide nonexistent lamps"""
		if len(lampNames) < self.model.numLamps:
			# append extra "" strings so there are at least numLamps elements
			lampNames = tuple(lampNames) + ("",)*self.model.numLamps
		
		showHideDict = {}

		for ii in range(self.model.numLamps):
			# if name is blank, hide corresp. widgets
			# else set lamp names wdg
			lampName = lampNames[ii] or ""
			self.lampNameWdgSet[ii].set("%s Lamp" % lampName, isCurrent)
			self.lampUserWdgSet[ii].helpText = "Desired state of %s cal lamp" % (lampName,)
			self.lampCurrWdgSet[ii].helpText = "Current state of %s cal lamp" % (lampName,)
			showHideDict[_LampPrefix + str(ii)] = bool(lampName)
			if not lampName:
				# turn off any user lamp that are hidden
				if self.lampUserWdgSet[ii].getBool():
					self.lampUserWdgSet[ii].setBool(False)
		self.gridder.showHideWdg(**showHideDict)
	
	def setLampStates(self, lampStates, isCurrent, **kargs):
		for ii in range(self.model.numLamps):
			lampState = lampStates[ii]
			if lampState:
				sev = RO.Constants.sevWarning
			else:
				sev = RO.Constants.sevNormal
			
			self.lampCurrWdgSet[ii].set(lampState, isCurrent=isCurrent, severity=sev)
			self.lampUserWdgSet[ii].setDefault(lampState)
	
	def setMirrorState(self, mirrorState, isCurrent, **kargs):
		mirrorState = mirrorState or "" # change None to a string
		if mirrorState.lower() != self.model.mirStatesConst[0].lower():
			mirSev = RO.Constants.sevWarning
		else:
			mirSev = RO.Constants.sevNormal
		
		mirrorState = mirrorState.capitalize()
		self.mirrorCurrWdg.set(mirrorState, isCurrent, severity=mirSev)
		self.mirrorUserWdg.setDefault(mirrorState)


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
