#!/usr/local/bin/python
"""Allows entry of drift scan velocity as X,Y or velocity,angle

History:
2001-11-05 ROwen	First version with history.
2002-07-31 ROwen	Modified to use the RO.CoordSys module.
2002-11-15 ROwen	Added help and modified to use ROOptionMenu.
2002-12-04 ROwen	Modified to use URL-based help.
2003-03-11 ROwen	Changed to use OptionMenu instead of ROOptionMenu.
2003-04-14 ROwen	Modified to use TUI.TCC.UserModel.
2003-04-18 ROwen	Improved pop-up menu and added help strings.
2003-07-09 ROwen	Modified to show both axis vel and vel/angle,
					thereby simplifying the display and fixing a problem
					with restoring values from a value dictionary;
					modified to use overhauled RO.InputCont.
2003-07-30 ROwen	Bug fix: failed to trap ValueError
					from RO.Math.rThetaFromXY
2003-10-24 ROwen	Added userModel input.
2003-11-04 ROwen	Modified to show self if set non-default.
2004-05-18 ROwen	Eliminated unused constants _AxesName, _VelAngName
2004-09-24 ROwen	Added a Defaults button.
					Added and refined help strings.
					Added /sec to vel units (using improved RO.Wdg.DMSEntry).
"""
import Tkinter
import RO.CoordSys
import RO.InputCont
import RO.MathUtil
import RO.StringUtil
import RO.Wdg
import TUI.TCC.UserModel

# constants
_MaxVel = 3.0 * 3600.0 # arcsec
_VelFieldWidth = 9 # enough for -X:XX:XX.X
_AngFieldWidth = 6
_LabelWidth = 8 # enough for "Vel Long"

_HelpPrefix = "Telescope/SlewWin/DriftScanPanel.html#"

class DriftScanWdg(RO.Wdg.InputContFrame):
	"""Create a widget for specifying drift scans.

	Inputs:
	- master		master Tk widget -- typically a frame or window
	- userModel		a TUI.TCC.UserModel; specify only if global model
					not wanted (e.g. for checking catalog values)
	- **kargs		keyword arguments for Tkinter.Frame
	"""
	def __init__ (self,
		master,
		userModel = None,
	**kargs):
		RO.Wdg.InputContFrame.__init__(self, master, **kargs)
		
		self._axesUpdating = False
		self._velAngUpdating = False

		self._showVar = Tkinter.BooleanVar()

		gr = RO.Wdg.Gridder(self, sticky="e")
		self.gridder = gr

		gr.gridWdg(
			label = False,
			dataWdg = Tkinter.Label(self, text="Drift Scan"),
			colSpan = 3,
			sticky = "",
		)
		
		
		# axes widgets
		# the labels vary as the coordinate system changes
		# so keep track of them as widgets
		self.axesLabelSet = []
		self.axesWdgSet = []
		for ii in range(2):
			labelWdg = Tkinter.Label(self,
				width=_LabelWidth,
				anchor='e',
			)
			self.axesLabelSet.append(labelWdg)
			
			unitsVar = Tkinter.StringVar()
			
			wdg = RO.Wdg.DMSEntry (self,
				-_MaxVel, _MaxVel,
				defValue = 0,
				helpURL = _HelpPrefix + "XY",
				width = _VelFieldWidth,
				isRelative = True,
				omitExtraFields = True,
				unitsVar = unitsVar,
				unitsSuffix = "/sec",
				callFunc = self._axesChanged,
			)
			self.axesWdgSet.append(wdg)
			
			gr.gridWdg (
				label = labelWdg,
				dataWdg = wdg,
				units = unitsVar,
			)

		# separator widget; the units label makes the units column
		# wide enough to show all version of the units strings
		gr.gridWdg(
			label = "",
			units = Tkinter.Label(self, width=5),
		)
		
		# velocity widget
		unitsVar = Tkinter.StringVar()
		self.velWdg = RO.Wdg.DMSEntry (self,
			0.0, _MaxVel,
			helpURL = _HelpPrefix + "VelAngle",
			isRelative = True,
			omitExtraFields = True,
			width = _VelFieldWidth,
			unitsVar = unitsVar,
			unitsSuffix = "/sec",
			callFunc = self._velAngChanged,
			helpText = "Total scan velocity"
		)

		gr.gridWdg(
			label = Tkinter.Label(self,
				text = "Vel",
				anchor = "e",
				width = _LabelWidth,
			),
			dataWdg = self.velWdg,
			units = unitsVar,
		)
		
		# angle widget
		self.angleWdg = RO.Wdg.FloatEntry (self,
			-360.0, 360.0,
			helpURL = _HelpPrefix + "VelAngle",
			width = _AngFieldWidth,
			defFormat = "%.0f",
			callFunc = self._velAngChanged,
		)

		gr.gridWdg(
			label = Tkinter.Label(self,
				text = "Angle",
				anchor = "e",
				width = _LabelWidth,
			),
			dataWdg = self.angleWdg,
			units = RO.StringUtil.DegStr,
		)
		
		defButton = RO.Wdg.Button(self,
			text = "Defaults",
			command = self.restoreDefault,
			helpText = "Restore defaults (reset to 0)",
		)
		gr.gridWdg(None, defButton)
		
		gr.allGridded()
		
		def formatFunc(inputCont):
			name = inputCont.getName()
			wdgList = inputCont.getWdgList()
			if not inputCont.allEnabled():
				return ''
			valList = [wdg.getNum() / 3600.0 for wdg in wdgList]
			if valList == [0.0, 0.0]:
				return ''
			return '/%s=(%.6f, %.6f)' % (name, valList[0], valList[1])

		self.inputCont = RO.InputCont.WdgCont (
			name = "ScanVelocity",
			wdgs = self.axesWdgSet,
			formatFunc = formatFunc,
		)
		self._axesChanged()

		userModel = userModel or TUI.TCC.UserModel.getModel()
		userModel.coordSysName.addCallback(self._coordSysChanged, callNow = True)

	def getShowVar(self):
		return self._showVar

	def _coordSysChanged (self, coordSys):
		"""Update the display when the coordinate system is changed.
		"""
		posLabels = RO.CoordSys.getSysConst(coordSys).posLabels()

		for ind in range(2):
			axisStr = posLabels[ind]
			self.axesLabelSet[ind]["text"] = "Vel %s" % (axisStr,)
			self.axesWdgSet[ind].helpText = "%s component of scan velocity" % (axisStr,)
		self.angleWdg.helpText = \
			"Tangent angle: 0 = increasing %s; 90 = increasing %s" % \
			tuple(posLabels)
	
	def _axesChanged (self, *args):
		"""Call whenever axes input is changed.
		Set vel, ang to match.
		"""
		try:
			self._axesUpdating = True
			# print "_axesChanged"
			if self._velAngUpdating:
				# print "velAng being updated; returning"
				return
			xyVel = [wdg.getNum() for wdg in self.axesWdgSet]
			try:
				vel, ang = RO.MathUtil.rThetaFromXY(xyVel)
			except ValueError:
				# too near pole; pick something sane
				vel, ang = 0.0, 0.0
			# print "x, y vel =", xVel, yVel
			# print "vel, ang = ", vel, ang
			self._velAngUpdating = True
			self.velWdg.set(vel)
			self.angleWdg.set(ang)
			self._velAngUpdating = False
			valueList = self.inputCont.getValueList()
			if valueList and not self._showVar.get():
				self._showVar.set(True)

		finally:
			self._axesUpdating = False
	
	def _velAngChanged (self, *args):
		"""Call whenever vel or ang input is changed.
		Set axes to match.
		"""
		try:
			self._velAngUpdating = True
			# print "_velAngChanged"
			if self._axesUpdating:
				# print "axes being updated; returning"
				return
			vel = self.velWdg.getNum()
			ang = self.angleWdg.getNum()
			xyVel = RO.MathUtil.xyFromRTheta((vel, ang))
			# print "vel, ang = ", vel, ang
			# print "x, y vel =", xyVel
			self._axesUpdating = True
			for ind in range(2):
				self.axesWdgSet[ind].set(xyVel[ind])
			self._axesUpdating = False
		finally:
			self._velAngUpdating = False


if __name__ == "__main__":
	import CoordSysWdg

	root = RO.Wdg.PythonTk()
	def printOptions():
		print testFrame.getString()
		
	def clear():
		testFrame.clear()
		
	getButton = Tkinter.Button (root, command=printOptions, text="Print Options")
	getButton.pack()
		
	coordSysWdg = CoordSysWdg.CoordSysWdg(root)
	coordSysWdg.pack()
	
	testFrame = DriftScanWdg(root)
	testFrame.pack()

	root.mainloop()
