#!/usr/local/bin/python
"""FTP Log window

2003-12-17 ROwen
2004-05-18 ROwen	Stopped importing TUI.TUIModel in main code; it wasn't used.
2004-11-05 ROwen	Upped maxTransfers from 1 to 2.
"""
import RO.Alg
import RO.Wdg.FTPLogWdg

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "TUI.FTP Log",
		defGeom = "+835+290",
		wdgFunc = RO.Alg.GenericCallback(
			RO.Wdg.FTPLogWdg.FTPLogWdg,
			maxTransfers = 2,
			helpURL = "TUIMenu/FTPLogWin.html",
		),
		visible = False,
	)
