#!/usr/local/bin/python
"""Allows entry of object name, position and rotator angle and type.

History:
2001-11-05 ROwen	First version with history.
2002-06-25 ROwen	Removed an unneeded keyword from inputCont.
2002-07-29 ROwen	Modified to raise ValueError, not RuntimeError,
					 if a position is missing.
2002-07-31 ROwen	Modified to use the RO.CoordSys module.
2002-08-01 ROwen	Modified to use the RO.CoordSys module
					and to be able to format the command string
					purely based on the value dictionary, ignoring the state of the csys widget.
2002-08-02 ROwen	Added neatenDisplay method.
2002-11-12 ROwen	Added help to the name and position widgets.
2002-11-22 ROwen	Fixed a range error in pos2 (thanks to Bill Ketzeback)
2002-11-26 ROwen	Changed to use URL-based help.
2003-03-07 ROwen	Changed RO.Wdg.StringEntry to RO.Wdg.StrEntry.
2003-03-26 ROwen	Added dispatcher arg (wanted by RotWdg).
2003-03-31 ROwen	Switched from RO.Wdg.LabelledWdg to RO.Wdg.Gridder
2003-04-09 ROwen	Added support for a status widget.
2003-04-14 ROwen	Modified to use TUI.TCC.UserModel;
					simplified handling of coordSys;
					fixed gridding column spans broken 2003-03-31.
2003-04-28 ROwen	Bug fix: referenced coordSysWdg.getCoordSysVar;
					removed getCoordSysVar, getDateVar.
2003-06-09 ROwen	Removed dispatcher arg.
2003-06-13 ROwen	Added help text (though it's not interesting).
2003-07-10 ROwen	Modified to use overhauled RO.InputCont;
					bug fix: object names containing " were not formatted correctly.
2003-07-24 ROwen	Modified object formatter to fail
					if either object position entry is blank.
2003-10-28 ROwen	Added userModel input.
2004-09-24 ROwen	Added az, alt, airmass output.
2004-10-11 ROwen	Mod. az/alt/airmass display to update itself
					and to to handle invalid targets gracefully.
"""
import Tkinter
import RO.CoordSys
import CoordSysWdg
import RO.Constants
import RO.InputCont
import RO.StringUtil
import RO.Wdg
import RotWdg
import TUI.TCC.UserModel
import TUI.TCC.TCCModel

_HelpPrefix = "Telescope/SlewWin/index.html#"

_AzAltRefreshDelayMS = 500

class ObjPosWdg(RO.Wdg.InputContFrame):
	"""A widget for specifying object positions

	Inputs:
	- master		master Tk widget -- typically a frame or window
	- userModel		a TUI.TCC.UserModel; specify only if global model
					not wanted (e.g. for checking catalog values)
	- **kargs		keyword arguments for Tkinter.Frame
	"""
	def __init__ (self,
		master = None,
		userModel = None,
	 **kargs):
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		gr = RO.Wdg.Gridder(self, sticky="w")
		
		# start out by not checking object position
		# set this true after all widgets are painted
		# and the formatting functions have had their test run
		self.checkObjPos = 0
		
		self._azAltRefreshID = None	
		
		self.objNameWdg = RO.Wdg.StrEntry(self,
			helpText = "Object name (optional)",
			helpURL = _HelpPrefix + "NameWdg",
			width=25,
		)
		self.objName = gr.gridWdg (
			label = "Name",
			dataWdg = self.objNameWdg,
			colSpan = 3,
		)
		lastCol = gr.getNextCol() - 2
		self.columnconfigure(lastCol, weight=1)
		
		objPos1UnitsVar = Tkinter.StringVar()
		self.objPos1 = gr.gridWdg (
			label = "",
			dataWdg = RO.Wdg.DMSEntry(self,
				minValue = 0,
				maxValue = 359.99999999,
				defValue = None,
				unitsVar=objPos1UnitsVar,
				isHours = 0,	# this will vary so no initial value is actually needed
				helpText = "Object position",
				helpURL = _HelpPrefix + "PosWdg",
			),
			units = objPos1UnitsVar,
		)
		
		objPos2UnitsVar = Tkinter.StringVar()
		self.objPos2 = gr.gridWdg (
			label = "",
			dataWdg = RO.Wdg.DMSEntry(self,
				minValue = 0,
				maxValue = 90,
				defValue = None,
				unitsVar=objPos2UnitsVar,
				isHours = 0,	# always in degrees
				helpText = "Object position",
				helpURL = _HelpPrefix + "PosWdg",
			),
			units = objPos2UnitsVar,
		)

		self.coordSysWdg = CoordSysWdg.CoordSysWdg(
			master = self,
			userModel = userModel,
		)
		gr.gridWdg (
			label = "CSys",
			dataWdg = self.coordSysWdg,
			colSpan = 3,
		)

		self.rotWdg = RotWdg.RotWdg(
			master = self,
			userModel = userModel,
		)
		gr.gridWdg (
			label = "Rot",
			dataWdg = self.rotWdg,
			colSpan = 3,
		)
		
		azAltFrame = Tkinter.Frame(self)
		
		self.azWdg = RO.Wdg.FloatLabel (
			master = azAltFrame,
			precision = 2,
			width = 6,
			helpText = "azimuth for proposed object",
			helpURL = _HelpPrefix + "Azimuth",
		)
		self.azWdg.pack(side="left")
		Tkinter.Label(azAltFrame,
			text="%s  Alt" % (RO.StringUtil.DegStr,)).pack(side="left")
		
		self.altWdg = RO.Wdg.FloatLabel (
			master = azAltFrame,
			precision = 2,
			width = 6,
			helpText = "altitude for proposed object",
			helpURL = _HelpPrefix + "Altitude",
		)
		self.altWdg.pack(side="left")
		Tkinter.Label(azAltFrame, text=RO.StringUtil.DegStr).pack(side="left")

		gr.gridWdg (
			label = "Az",
			dataWdg = azAltFrame,
			colSpan = 3,
		)

		self.airmassWdg = RO.Wdg.FloatLabel (
			master = self,
			precision = 3,
			width = 6,
			helpText = "airmass for proposed object",
			helpURL = _HelpPrefix + "Airmass",
		)
		gr.gridWdg (
			label = "Airmass",
			dataWdg = self.airmassWdg,
		)
	
		# create a set of input widget containers
		# this makes it easy to retrieve a command
		# and also to get and set all data using a value dictionary
		
		# note: the coordsys widget must be FIRST
		# because it has to be set (when restoring from a value dict)
		# before pos1 is set, to set the isHours flag correctly
		def formatObjPos(inputCont):
			wdgList = inputCont.getWdgList()

			# format data using the widgets
			valList = []
			for wdg in wdgList:
				if wdg.getString() == '':
					raise ValueError, "must specify position"
				
				val = wdg.getNum()
				if wdg.getIsHours():
					val = val * 15.0
				valList.append(val)
			return 'track %.7f, %.7f' % tuple(valList)
		
		def formatAll(inputCont):
			# container order is coordsys, objpos, rotator, name (optional)
			strList = inputCont.getStringList()
			return strList[1] + ' ' + strList[0] + ''.join(strList[2:])

		def vmsQuoteStr(astr):
			return RO.StringUtil.quoteStr(astr, '"')

		self.inputCont = RO.InputCont.ContList (
			conts = [
				self.coordSysWdg.inputCont,
				RO.InputCont.WdgCont (
					name = "ObjPos",
					wdgs = (self.objPos1.dataWdg, self.objPos2.dataWdg),
					formatFunc = formatObjPos,
				),
				RO.InputCont.WdgCont (
					name = "Name",
					wdgs = self.objNameWdg,
					formatFunc = RO.InputCont.VMSQualFmt(vmsQuoteStr),
				),
				self.rotWdg.inputCont,
			],
			formatFunc = formatAll,
		)
		
		self.userModel = userModel or TUI.TCC.UserModel.getModel()
		self.userModel.coordSysName.addCallback(self._coordSysChanged)
		self.userModel.potentialTarget.addCallback(self.setAzAltAirmass)
		
		self.tccModel = TUI.TCC.TCCModel.getModel()
#		self.tccModel.altLim.addCallback(self.setAzAltAirmass)

		# initialize display
		self.restoreDefault()
		
		self.objNameWdg.focus_set()
	
	def _coordSysChanged (self, coordSys):
		"""Update the display when the coordinate system is changed.
		"""
		pos1IsHours = 1
		csysObj = RO.CoordSys.getSysConst(coordSys)
		pos1IsHours = csysObj.eqInHours()
		posLabels = csysObj.posLabels()

		if coordSys in RO.CoordSys.AzAlt:
			if coordSys == RO.CoordSys.Mount:
				pos1Range = (-180, 360)
			else:
				pos1Range = (0, 360)
			pos2Range = (0, 90)
		elif pos1IsHours:
			pos1Range = (0, 24)
			pos2Range = (-90, 90)
		else:
			# no such coordsys, so makes a good sanity check
			raise RuntimeError, "ObjPosWdg bug: cannot handle coordinate system %r" % (coordSys,)
		
		self.objPos1.labelWdg["text"] = posLabels[0]
		self.objPos2.labelWdg["text"] = posLabels[1]
		self.objPos1.dataWdg.setIsHours(pos1IsHours)
		self.objPos1.dataWdg.setRange(*pos1Range)
		self.objPos2.dataWdg.setRange(*pos2Range)
	
	def getSummary(self):
		"""Returns (name, pos1, pos2, csys), all as the strings shown in the widgets
		(not the numeric values).
		It would be slightly nicer if the summary could be derived from the value dictionary
		but this is quite tricky to do right."""
		name = self.objNameWdg.get()
		pos1 = self.objPos1.dataWdg.getString()
		pos2 = self.objPos2.dataWdg.getString()
		csys = self.userModel.coordSysName.get()
		return (name, pos1, pos2, csys)
	
	def neatenDisplay(self):
		self.objPos1.dataWdg.neatenDisplay()
		self.objPos2.dataWdg.neatenDisplay()
	
	def setAzAltAirmass(self, *args, **kargs):
#		print "ObjPosWdg.setAzAltAirmass"
		if self._azAltRefreshID:
			self.after_cancel(self._azAltRefreshID)

		target = self.userModel.potentialTarget.get()
		if target == None:
			self.azWdg.set(None)
			self.altWdg.set(None)
			self.airmassWdg.set(None)
			return
		
		azalt = target.getAzAlt()
		if azalt == None:
			self.azWdg.set(None)
			self.altWdg.set(None)
			self.airmassWdg.set(None)
			return

		az, alt = azalt
		airmass = RO.Astro.Sph.airmass(alt)
		altData, limCurrent = self.tccModel.altLim.get()
		altState = RO.Constants.st_Normal
		minAlt = altData[0]
		if minAlt != None:
			if alt < minAlt:
				altState = RO.Constants.st_Error
		
		self.azWdg.set(az)
		self.altWdg.set(alt, state = altState)
		self.airmassWdg.set(airmass)
		self._azAltRefreshID = self.after(_AzAltRefreshDelayMS, self.setAzAltAirmass)

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	testFrame = ObjPosWdg()
	testFrame.pack()
	
	def doPrint():
		print testFrame.getString()
		
	def doSummary():
		print testFrame.getSummary()
	
	def defaultCommand():
		testFrame.restoreDefault()

	buttonFrame = Tkinter.Frame(root)
	Tkinter.Button (buttonFrame, command=doPrint, text="Print").pack(side="left")
	Tkinter.Button (buttonFrame, command=doSummary, text="Summary").pack(side="left")
	Tkinter.Button (buttonFrame, command=defaultCommand, text="Default").pack(side="left")
	Tkinter.Button (buttonFrame, command=testFrame.neatenDisplay, text="Neaten").pack(side="left")
	buttonFrame.pack()

	root.mainloop()
