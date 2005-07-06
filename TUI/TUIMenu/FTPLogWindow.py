#!/usr/local/bin/python
"""FTP Log window

2003-12-17 ROwen
2004-05-18 ROwen	Stopped importing TUI.TUIModel in main code; it wasn't used.
2004-11-05 ROwen	Upped maxTransfers from 1 to 2.
2005-06-14 ROwen	Set maxLines to 100 (instead of using default 500)
					and use a constant so test code can easily override.
2005-07-06 ROwen	Increased max transfers from 2 to 5, primarily so that
					a few wedged transfers cannot halt all ftp.
	
"""
import RO.Alg
import RO.Wdg.FTPLogWdg

_MaxLines = 100
_MaxTransfers = 5

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "TUI.FTP Log",
		defGeom = "+835+290",
		wdgFunc = RO.Alg.GenericCallback(
			RO.Wdg.FTPLogWdg.FTPLogWdg,
			maxTransfers = _MaxTransfers,
			maxLines = _MaxLines,
			helpURL = "TUIMenu/FTPLogWin.html",
		),
		visible = False,
	)
