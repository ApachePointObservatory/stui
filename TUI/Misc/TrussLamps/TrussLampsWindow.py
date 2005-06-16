#!/usr/local/bin/python
"""Status/control window for the Truss Lamps.

History:
2004-10-01 ROwen
2004-12-23 ROwen	Fixed a few comments.
2005-06-16 ROwen	Imported RO.Wdg again in the test code (found by pychecker).
"""
import Tkinter
import RO.Wdg
import StatusCommandWdg
import TUI.TUIModel

_HelpURL = "Misc/TrussLampsWin.html"

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "Misc.Truss Lamps",
		defGeom = "+676+280",
		resizable = False,
		wdgFunc = TrussLampsWdg,
		visible = (__name__ == "__main__"),
	)

class TrussLampsWdg(Tkinter.Frame):
	def __init__(self,
		master,
	**kargs):
		"""Create a new widget to control the Truss Lamps
		"""
		Tkinter.Frame.__init__(self, master=master, **kargs)
		
		tuiModel = TUI.TUIModel.getModel()

		self.statusBar = RO.Wdg.StatusBar(
			master = self,
			helpURL = _HelpURL,
			dispatcher = tuiModel.dispatcher,
			prefs = tuiModel.prefs,
			summaryLen = 10,
		)

		self.inputWdg = StatusCommandWdg.StatusCommandWdg(
			master = self,
			statusBar = self.statusBar,
		)

		row = 0

		self.inputWdg.grid(row=row, column=0, sticky="news")
		row += 1
			
		self.statusBar.grid(row=row, column=0, sticky="ew")
		row += 1

if __name__ == "__main__":
	root = RO.Wdg.PythonTk()
	root.resizable(width=0, height=0)

	import TestData
	
	tlSet = TestData.tuiModel.tlSet

	addWindow(tlSet)
	
	TestData.dispatch()
	
	root.mainloop()
