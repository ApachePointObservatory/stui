#!/usr/local/bin/python
"""Widget to allow users to specify a target position and initiate a slew.

To Do:
- Consider packing widgets to fit N/S. The widgets have to be
modified to take advantage of this, and perhaps this should be
a flag so users aren't forced to do it this way.

History:
2002-06-25 ROwen	First version with history.
2002-08-02 ROwen	Checkbuttons no longer take focus. Added neatenDisplay method.
2002-08-08 ROwen	Added valueDictOK and added a flag for this to the callback.
2002-08-23 ROwen	Bug fix: date wasn't being returned for ICRS
					because the main date widget was hidden.
2003-03-26 ROwen	Added dispatcher arg (wanted by ObjPosWdg).
2003-03-31 ROwen	Modified to use 2003-03-31 ObjPosWdg.
2003-05-29 ROwen	Added help text to the show/hide buttons for the option panels.
2003-06-09 ROwen	Removed dispatcher arg.
2003-07-24 ROwen	Fixed valueDictOK (broken by 2003-07-10 change to ObjPosWdg).
2003-10-24 ROwen	Added userModel input.
2004-05-18 ROwen	Stopped importing string and sys since they weren't used.
					Bug fix: the test code was broken.
2004-09-24 ROwen	Removed restart panel; it wasn't doing anything useful.
"""
import Tkinter
import ObjPosWdg
import RO.Wdg
import MagPMWdg
import DriftScanWdg
import KeepOffsetWdg
import CalibWdg
import AxisWrapWdg
import RO.InputCont

# fix this code so that one cannot hide proper motion information while any is present

class InputWdg (RO.Wdg.InputContFrame):
	"""A widget for specifying information about a slew.

	Inputs:
	- master		master Tk widget -- typically a frame or window
	- userModel		a TUI.TCC.UserModel; specify only if global model
					not wanted (e.g. for checking catalog values)
	"""
	def __init__ (self,
		master = None,
		userModel = None,
	):
		RO.Wdg.InputContFrame.__init__(self, master = master)
		
		# create object position frame
		self.objPosWdg = ObjPosWdg.ObjPosWdg(
			master = self,
			userModel = userModel,
		)
		self.objPosWdg.pack(side=Tkinter.LEFT, anchor=Tkinter.NW)
		
		# create a frame to hold hideable option panels
		optionFrame = Tkinter.Frame(master = self)
				
		# create hideable panel for magnitude and proper motion
		magPMWdg = MagPMWdg.MagPMWdg(
			master = optionFrame,
			userModel = userModel,
			relief = Tkinter.RIDGE,
		)
		
		# create a hideable panel for drift scanning
		driftScanWdg = DriftScanWdg.DriftScanWdg(
			master = optionFrame,
			userModel = userModel,
			relief = Tkinter.RIDGE,
		)
				
		# create hideable panel for keeping offsets
		keepOffsetWdg = KeepOffsetWdg.KeepOffsetWdg(
			master = optionFrame,
			relief = Tkinter.RIDGE,
		)
		
		# create hideable panel for calibration options
		calibWdg = CalibWdg.CalibWdg(
			master = optionFrame,
			userModel = userModel,
			relief = Tkinter.RIDGE,
		)
		
		# create hideable option panel for wrap
		axisWrapWdg = AxisWrapWdg.AxisWrapWdg(
			master = optionFrame,
			userModel = userModel,
			relief = Tkinter.RIDGE,
		)
		
		# list of option widgets, with descriptive text
		optionDescrWdgList = (
			("Mag, PM", magPMWdg, "Show/hide magnitude and proper motion controls"),
			("Drift Scan", driftScanWdg, "Show/hide drift scan controls"),
			("Keep Offsets",  keepOffsetWdg, "Show/hide controls to retain current offsets"),
			("Calibrate", calibWdg, "Show/hide pointing calibration controls"),
			("Axis Wrap", axisWrapWdg, "Show/hide wrap preference controls"),
		)
	
		# create a set of controls to show the optional panels
		self.optButtonWdg = RO.Wdg.OptionPanelControl(self,
			wdgList = optionDescrWdgList,
			labelText="Options:",
			takefocus=0,
		)
		self.optButtonWdg.pack(side=Tkinter.LEFT, anchor=Tkinter.NW)
		optionFrame.pack(side=Tkinter.LEFT, anchor=Tkinter.NW)
		
		# create input container set
		wdgList = [self.objPosWdg] + map(lambda x: x[1], optionDescrWdgList)
		contList = [wdg.inputCont for wdg in wdgList]
		self.inputCont = RO.InputCont.ContList (
			conts = contList,
			formatFunc = RO.InputCont.BasicContListFmt(valSep=""),
		)
		
	def neatenDisplay(self):
		"""Makes sure all input fields are neatened up
		and restore the default focus (the next tab will be into the name field).
		In fact the only ones that matter are the DMS fields (all in SetObjPos)"""
		self.objPosWdg.neatenDisplay()


if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	root.resizable(width=0, height=0)
	
	def doPrint(*args):
		try:
			print "value dict = %s" % (testFrame.getValueDict(),)
			print "command = %r" % (testFrame.getString(),)
		except ValueError, e:
			print "Error:", e

	def restoreDefault():
		print testFrame.restoreDefault()

	testFrame = InputWdg(master = root)
	testFrame.pack()
	
	buttonFrame = Tkinter.Frame(master = root)
	buttonFrame.pack(anchor="nw")

	printButton = Tkinter.Button (buttonFrame, command=doPrint, text="Print")
	printButton.pack(side="left")

	defButton = Tkinter.Button (buttonFrame, command=restoreDefault, text="Default")
	defButton.pack(side="left")

	root.mainloop()
