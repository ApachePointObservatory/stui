#!/usr/local/bin/python
"""Create the main TCC status window
(which is also the main TUI window, since it has the menus)

History:
2003-06-09 ROwen	added addWindow and renamed from StatusWdg to StatusWindow.
2003-06-25 ROwen	Modified test case to handle message data as a dict
2003-12-17 ROwen	Modified to use renamed TUI.MainMenu.
2004-02-04 ROwen	Modified _HelpURL to match minor help reorg.
2004-02-17 ROwen	Changed buildAutoMenus to buildMenus.
2004-05-18 ROwen	Removed unused local variable in addWindow.
2004-08-11 ROwen	Modified for updated RO.Wdg.Toplevel.
"""
import Tkinter
import AxisStatus
import NetPosWdg
import OffsetWdg
import MiscWdg
import RO.Wdg
import SlewStatus

def addWindow(tlSet):
	"""Set up the main status window
	Use name "None.Status" so it doesn't show up in any menu.
	This is because the menus are in this very window --
	so if you can select the menu, this window is already
	the current window.
	"""
	tlSet.createToplevel(
		name = "None.Status",
		defGeom = "+0+22",
		resizable = False,
		closeMode = RO.Wdg.tl_CloseDisabled,
		wdgFunc = StatusWdg,
	)

_HelpPrefix = "Telescope/StatusWin.html#"

class StatusWdg (Tkinter.Frame):
	def __init__ (self,
		master = None,
	**kargs):
		"""creates a new telescope status frame

		Inputs:
		- master		master Tk widget -- typically a frame or window
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)

		self.netPosWdg = NetPosWdg.NetPosWdg(
			master=self,
			borderwidth=1,
		)
		self.netPosWdg.grid(row=1, column=0, sticky="w")
		
		self.slewStatusWdg = SlewStatus.SlewStatusWdg(
			master = self,
		)
		self.slewStatusWdg.grid(row=1, column=1, sticky="ns")

		self.offsetWdg = OffsetWdg.OffsetWdg(
			master=self,
			borderwidth=1,
			relief="ridge",
		)
		self.offsetWdg.grid(row=2, column=0, columnspan=2, sticky="nwse")
		
		self.miscWdg = MiscWdg.MiscWdg(
			master=self,
			borderwidth=1,
			relief="ridge",
		)
		self.miscWdg.grid(row=3, column=0, columnspan=2, sticky="nwse")
		
		self.axisStatusWdg = AxisStatus.AxisStatusWdg(
			master=self,
			borderwidth=1,
			relief="ridge",
		)
		self.axisStatusWdg.grid(row=4, column=0, columnspan=2, sticky="nwse")

		# set up status bar; this is only for showing help,
		# not command status, so we can omit dispatcher and prefs
		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			helpURL = _HelpPrefix + "StatusBar",
		)
		self.statusBar.grid(row=5, column=0, columnspan=2, sticky="ew")
	

def testShow():
	import TUI.TUIModel

	root = RO.Wdg.PythonTk()

	kd = TUI.TUIModel.getModel(True).dispatcher

	testFrame = StatusWdg (root)
	testFrame.pack()
	
	dataDict = {
		"ObjName": ("test object with a long name",),
		"ObjSys": ("FK4", 2000.0),
		"ObjNetPos": (120.123450, 0.000000, 4494436859.66000, -2.345670, 0.000000, 4494436859.66000),
		"RotType": ("Obj",),
		"RotPos": (3.456789, 0.000000, 4494436895.07921),
		"AxePos": (-350.999, 45, "NAN"),
		"TCCStatus": ("TSH","NNN"),
		"BadAzStatus": (),
		"AzStat": (45.0, 0.0, 4565, 0x145),
		"SlewDuration": (14.0,),
		"SecFocus": (570,),
		"GCFocus": (-300,),
	}
	msgDict = {"cmdr":"me", "cmdID":11, "actor":"tcc", "type":":", "data":dataDict}
	print "Dispatching message:", msgDict, '\n'
	kd.dispatch(msgDict)

	root.mainloop()

if __name__ == "__main__":
	testShow()
