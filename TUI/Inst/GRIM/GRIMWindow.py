#!/usr/local/bin/python
from __future__ import generators
"""Status/config and exposure windows for GRIM.

History:
2003-08-05 ROwen
2004-05-18 ROwen	Stopped importing RO.Alg and TUI.Inst.ExposeWdg;
					they weren't used.
					Fixed test code to show the GRIM window.
"""
import StatusConfigWdg
import GRIMExposeWdg

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "None.GRIM Expose",
		defGeom = "+452+280",
		resizable = False,
		wdgFunc = GRIMExposeWdg.GRIMExposeWdg,
		visible=False,
	)
	
	tlSet.createToplevel (
		name = "Inst.GRIM",
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
	tlSet.makeVisible("Inst.GRIM")
	
	TestData.dispatch()
	
	root.mainloop()
