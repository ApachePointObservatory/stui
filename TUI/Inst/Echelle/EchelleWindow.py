#!/usr/local/bin/python
from __future__ import generators
"""Status/config and exposure windows for GRIM.

History:
2003-12-08 ROwen
"""
import RO.Alg
import TUI.Inst.ExposeWdg
import StatusConfigWdg

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "None.Echelle Expose",
		defGeom = "+452+280",
		resizable = False,
		wdgFunc = RO.Alg.GenericCallback (
			TUI.Inst.ExposeWdg.ExposeWdg,
			instName = "Echelle",
		),
		visible=False,
	)
	
	tlSet.createToplevel (
		name = "Inst.Echelle",
		defGeom = "+676+280",
		resizable = False,
		wdgFunc = StatusConfigWdg.StatusConfigWdg,
		visible = False,
	)
