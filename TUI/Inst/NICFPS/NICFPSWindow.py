#!/usr/local/bin/python
from __future__ import generators
"""Status/config and exposure windows for NIC-FPS.

History:
2004-10-19 ROwen
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import StatusConfigWdg

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "None.NICFPS Expose",
		defGeom = "+452+280",
		resizable = False,
		wdgFunc = RO.Alg.GenericCallback (
			TUI.Inst.ExposeWdg.ExposeWdg,
			instName = "NICFPS",
		),
		visible=False,
	)
	
	tlSet.createToplevel (
		name = "Inst.NICFPS",
		defGeom = "+676+280",
		resizable = False,
		wdgFunc = StatusConfigWdg.StatusConfigWdg,
		visible = (__name__ == "__main__"),
	)


if __name__ == "__main__":
	import RO.Wdg

	root = RO.Wdg.PythonTk()
	root.resizable(width=0, height=0)
	
	import TestData
	tlSet = TestData.tuiModel.tlSet

	addWindow(tlSet)
	tlSet.makeVisible("Inst.NICFPS")
	
	TestData.dispatch()
	
	root.mainloop()
