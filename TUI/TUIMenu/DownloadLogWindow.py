#!/usr/local/bin/python
"""Fetch Log window

2005-07-08 ROwen
"""
import RO.Alg
import RO.Wdg.HTTPLogWdg

_MaxLines = 100
_MaxTransfers = 5

def addWindow(tlSet):
	tlSet.createToplevel (
		name = "TUI.Download Log",
		defGeom = "+835+290",
		wdgFunc = RO.Alg.GenericCallback(
			RO.Wdg.HTTPLogWdg.HTTPLogWdg,
			maxTransfers = _MaxTransfers,
			maxLines = _MaxLines,
			helpURL = "TUIMenu/DownloadLogWin.html",
		),
		visible = False,
	)
