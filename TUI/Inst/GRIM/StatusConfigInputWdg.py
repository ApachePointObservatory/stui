#!/usr/local/bin/python
from __future__ import generators
"""Configuration input panel for Dual Imaging Spectrograph.

To do:
- make window size based on longest menu item and leave it instead of resizing as the menus are changed
- shorten menus and add extra info to help (sounds slightly messy but doable)

History:
2003-08-04 ROwen
2003-08-11 ROwen	Modified to use enhanced Gridder.
2003-12-05 ROwen	Modified for RO.Wdg changes.
2004-05-18 ROwen	Removed constants _MaxDataWidth and _DetailCat;
					they weren't used.
"""
import Tkinter
import RO.MathUtil
import RO.Wdg
import RO.KeyVariable
import GRIMModel

_HelpPrefix = 'Instruments/GRIM/GRIMWin.html#'

_DataWidth = 14	# width of data columns

# category names
_ConfigCat = 'config'

class StatusConfigInputWdg (RO.Wdg.InputContFrame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to show status for and configure GRIM
		"""
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		self.model = GRIMModel.getModel()
	
		def invDict(inDict):
			outDict = {}
			for key, value in inDict.iteritems():
				outDict[value] = str(key)
			return outDict
		
		self.modeNameIDDict = invDict(self.model.modeIDNameDict)
		self.scaleNameIDDict = invDict(self.model.scaleIDNameDict)
		self.filterNameIDDict = invDict(self.model.filterIDNameDict)
		
		gr = RO.Wdg.StatusConfigGridder(
			master = self,
			sticky = 'w',
			clearMenu = None,
			defMenu = 'Current',
		)
		self.gridder = gr

		
		self.darkWdg = RO.Wdg.Checkbutton(self,
			text = 'Dark',
			helpText = 'set dark mode',
			helpURL = _HelpPrefix + 'Dark',
			callFunc = self._updDark,
		)
		gr.gridWdg(
			label = None,
			dataWdg = self.darkWdg,
			col = 4,
			cat = _ConfigCat,
		)
		
		modeNameStatWdg = RO.Wdg.StrLabel(self,
			helpText = 'current mode',
			helpURL = _HelpPrefix + 'Mode',
			width = _DataWidth,
			anchor = "w",
		)
		self.model.modeName.addROWdg(modeNameStatWdg)
		
		# prohibit user from selecting Polarimetry (the final mode);
		# it works poorly with the 3.5m, it is very complicated to use
		# (more so than TUI's simple interface suggests),
		# and only a few experts ever use it
		# also add Dark preceded by a separator
		modeNames = self.model.modeIDNameDict.values()[:-2] # ditch Polarimetry & Dark
		self.modeNameWdg = RO.Wdg.OptionMenu(self,
			items = modeNames,
			helpText = 'requested mode',
			helpURL = _HelpPrefix + 'Mode',
			defMenu = 'Current',
			callFunc = self._updMode,
		)
		self.model.modeName.addIndexedCallback(self.modeNameWdg.setDefault)
		gr.gridWdg (
			label = 'Mode',
			dataWdg = modeNameStatWdg,
			units = False,
			cfgWdg = self.modeNameWdg,
			sticky = 'w',
			colSpan = 3,
		)

		scaleNameStatWdg = RO.Wdg.StrLabel(self,
			helpText = 'current scale',
			helpURL = _HelpPrefix + 'Scale',
			width = _DataWidth,
			anchor = "w",
		)
		self.model.scaleName.addROWdg(scaleNameStatWdg)

		# skip repeated scale names (omit final two values)
		self.scaleNameWdg = RO.Wdg.OptionMenu(self,
			items = self.model.scaleIDNameDict.values(),
			helpText = 'requested scale',
			helpURL = _HelpPrefix + 'Scale',
			defMenu = 'Current',
		)
		self.model.scaleName.addIndexedCallback(self.scaleNameWdg.setDefault)
		gr.gridWdg (
			label = 'Scale',
			dataWdg = scaleNameStatWdg,
			units = False,
			cfgWdg = self.scaleNameWdg,
			sticky = 'w',
			colSpan = 3,
		)

		filterNameStatWdg = RO.Wdg.StrLabel(self,
			helpText = 'current filter',
			helpURL = _HelpPrefix + 'Filter',
			width = _DataWidth,
			anchor = "w",
		)
		self.model.filterName.addROWdg(filterNameStatWdg)

		filterNames = self.model.filterIDNameDict.values()
		filterNames[-1:-1] = [None] # avoid insert bug in Python 2.2
		self.filterNameWdg = RO.Wdg.OptionMenu(self,
			items = filterNames,
			helpText = 'requested filter',
			helpURL = _HelpPrefix + 'Filter',
			defMenu = 'Current',
		)
		self.model.filterName.addIndexedCallback(self.filterNameWdg.setDefault)
		gr.gridWdg (
			label = 'Filter',
			dataWdg = filterNameStatWdg,
			units = False,
			cfgWdg = self.filterNameWdg,
			sticky = 'w',
			colSpan = 3,
		)
		
		gr.allGridded()
		
		nameIDDicts = (
			self.modeNameIDDict,
			self.scaleNameIDDict,
			self.filterNameIDDict,
		)
		
		def formatCmd(inputCont):
			valueList = inputCont.getValueList()
			
			# item 0 is dark checkbox
			darkVal = valueList[0]
			if darkVal == "1":
				return "movedark:"

			strList = []
			for ind in range(3):
				niDict = nameIDDicts[ind]
				name = valueList[ind+1]
				strList.append(niDict[name])
			return "move: " + " ".join(strList)

		# set up the input container set; this is what formats the commands
		# and allows saving and recalling commands
		self.inputCont = RO.InputCont.WdgCont (
			name = 'move',
			wdgs = (
				self.darkWdg,
				self.modeNameWdg,
				self.scaleNameWdg,
				self.filterNameWdg,
			),
			formatFunc = formatCmd,
			omitDef = False,
		)
		
		def repaint(evt):
			self.restoreDefault()
		self.bind('<Map>', repaint)
	
	def _updDark(self, darkWdg):
		"""Dark button checked or unchecked"""
		doDark = darkWdg.getBool()
		if doDark and self.modeNameWdg.getEnable():
			self.savedMode = self.modeNameWdg.getString()
			self.savedScale = self.scaleNameWdg.getString()
			self.savedFilter = self.filterNameWdg.getString()
			self.modeNameWdg.set("Dark", doCheck=False)
			self.scaleNameWdg.set("f/20")
			self.filterNameWdg.set("Blank Off")
		elif not doDark and not self.modeNameWdg.getEnable():
			self.modeNameWdg.set(self.savedMode)
			self.scaleNameWdg.set(self.savedScale)
			self.filterNameWdg.set(self.savedFilter)
		self.modeNameWdg.setEnable(not doDark)
		self.scaleNameWdg.setEnable(not doDark)
		self.filterNameWdg.setEnable(not doDark)
	
	def _updMode(self, modeWdg):
		"""Updates the display based on the requested mode"""
		mode = modeWdg.getString()
		scaleMenu = self.scaleNameWdg.getMenu()
		if self.model.isRestrictedMode(mode):
			if self.scaleNameWdg.getString().startswith("f/20 "):
				self.scaleNameWdg.set("f/20")
			scaleMenu.entryconfigure(3, state="disabled")
			scaleMenu.entryconfigure(4, state="disabled")
		else:					
			scaleMenu.entryconfigure(3, state="normal")
			scaleMenu.entryconfigure(4, state="normal")
	
		
if __name__ == '__main__':
	root = RO.Wdg.PythonTk()

	import TestData
		
	testFrame = StatusConfigInputWdg (root)
	testFrame.pack()
	
	TestData.dispatch()
	
	testFrame.restoreDefault()

	def printCmds():
		print testFrame.getString()
	
	bf = Tkinter.Frame(root)
	cfgWdg = RO.Wdg.Checkbutton(bf, text="Config", defValue=True)
	cfgWdg.pack(side="left")
	Tkinter.Button(bf, text='Cmds', command=printCmds).pack(side='left')
	Tkinter.Button(bf, text='Current', command=testFrame.restoreDefault).pack(side='left')
	Tkinter.Button(bf, text='Demo', command=TestData.animate).pack(side='left')
	bf.pack()
	
	testFrame.gridder.addShowHideControl(_ConfigCat, cfgWdg)

	root.mainloop()
